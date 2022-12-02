from pathlib import Path
import json
from bs4 import BeautifulSoup
import re
from collections import Counter
from nltk import stem
from urllib.parse import urldefrag
import sys
from math import log10
from simHash import SimHash


STEMMER = stem.PorterStemmer()
BATCH_SIZE = 3000000  # bytes
PATH = "DEV/"
PARTIALINDEXPATH = "partialIndices/partialIndex_"
FULLINDEXPATH = "full_Index/index.jsonl"
IMPORTANT_TAGS = ["h1", "h2", "h3", "h4", "strong", "b"]
fingerPrints = list()


class BuildIndex:
    def __init__(self, path) -> None:
        self.webPagesPath = path
        self.urlIDMap = {}  # key - doc URL, value - document ID
        self.IDUrlMap = {}  # key - document ID, value - doc URL
        self.invertedIndex = {}  # key - words, values - List of postings (Actual Indexer, in-memory)
        self.partialIndexFiles = []  # list to store the partial index files generated
        self.partialFileIndex = 0  # Used to name the partial index file
        self.filesProcessed = 0  # unique files
        self.tokensProcessed = 0  # unique tokens

    def buildIndex(self):
        docNumber = 0  # Initial document number
        path = Path(self.webPagesPath)
        for dir in path.iterdir():  # iterate over all directories and their corresponding files
            for file in dir.iterdir():
                with open(file) as readFile:
                    fileDict = json.load(readFile)

                    url = urldefrag(fileDict["url"]).url  # defragged
                    if url in self.urlIDMap:
                        continue
                    self.urlIDMap[url] = docNumber  # map docID and url both ways
                    self.IDUrlMap[docNumber] = url

                    rawContent = fileDict["content"]
                    content = BeautifulSoup(rawContent, features="html.parser")

                    importantWords = set()
                    for tags in content.find_all(IMPORTANT_TAGS):
                        for word in re.sub(r"[^a-zA-Z0-9\s]", "", tags.text.lower()).split():
                            importantWords.add(STEMMER.stem(word))
                    
                    content = content.find_all()
                    token_frequency = Counter()
                    for line in content:
                        if not line.text:
                            continue
                        tokens = [STEMMER.stem(word) for word in
                                  re.sub(r"[^a-zA-Z0-9\s]", "", line.text.lower()).split()]
                        token_frequency.update(tokens)

                    if self.check_near_duplicaton(token_frequency): continue

                    for token, frequency in token_frequency.items():
                        if token not in self.invertedIndex:
                            self.invertedIndex[token] = []
                        
                        if token in importantWords: 
                            # Increase the tf-idf score for important words
                            self.invertedIndex[token].append((docNumber, frequency * 100))
                        else: 
                            self.invertedIndex[token].append((docNumber, frequency))
                self.filesProcessed += 1

                docNumber += 1
                if sys.getsizeof(self.invertedIndex) >= BATCH_SIZE:
                    self.writePartialIndexesToFile()

        if self.invertedIndex:
            self.writePartialIndexesToFile()

    def writeData(self):
        with open("IDUrlMap.json", 'w') as data:
            jsonObj = json.dumps(self.IDUrlMap)
            data.write(jsonObj)

    def writePartialIndexesToFile(self):
        """ writes current inverted index to file when size of dict is >= 3mb """

        path = f"{PARTIALINDEXPATH}{self.partialFileIndex}.jsonl"
        with open(path, 'w') as f:
            sortedIndex = sorted(self.invertedIndex.items(), key=lambda x: x[0])
            self.invertedIndex = {}
            for k, v in sortedIndex:
                keyValAsJson = json.dumps({k: v})  # convert to single json line
                f.write(keyValAsJson + "\n")  # write json
        self.partialFileIndex += 1
        self.partialIndexFiles.append(path)

    @staticmethod
    def generateLine(filename):
        """ create generator object for each partial index.  Yields single key/posting pair """

        with open(filename) as f:
            for line in f:
                yield json.loads(line)

    def mergeFiles(self):
        """ opens main index and all partial indices, sorts and writes all partial indices into main """

        with open(FULLINDEXPATH, 'w') as final:  # open final index
            fileGenerators = [self.generateLine(n) for n in self.partialIndexFiles]  # generator obj for each partial
            nextWords = []  # stores most recent word yielded from each generator
            toBeRemoved = set()  # stores empty generators queued for removal

            for i, gen in enumerate(fileGenerators):
                currGensNext = list(next(gen).items())
                nextWords.append(
                    (currGensNext[0][0], currGensNext[0][1], fileGenerators[i]))  # store k,v pair w/ gen obj

            while fileGenerators:  # loop until all generators empty
                nextWords.sort(key=lambda x: x[0])  # sort yielded words
                getNextVals = [nextWords[0][2]]  # list of generators that need to yield new value
                postings = nextWords[0][1]  # initialize postings of min nextWord, may merge if there is a match later
                i = 1
                while i < len(nextWords):
                    if nextWords[i][0] == nextWords[i - 1][0]:
                        postings.extend(nextWords[i][1])  # same word, merge postings
                        getNextVals.append(nextWords[i][2])
                    else:
                        break
                    i += 1

                self.tokensProcessed += 1
                postings.sort(key=lambda x: x[0])  # sort postings by docid
                postings = self.calulatetfidf(postings)  # change raw frequency to tf-idf
                keyValAsJson = json.dumps({nextWords[i - 1][0]: postings})  # write k,v pair into final index
                final.write(keyValAsJson + "\n")
                nextWords = nextWords[len(getNextVals):]  # remove written word

                for i, gen in enumerate(getNextVals):
                    try:
                        currGensNext = list(next(gen).items())
                        nextWords.append((currGensNext[0][0], currGensNext[0][1], gen))  # store new k,v pair w/ gen obj
                    except StopIteration:
                        toBeRemoved.add(gen)  # queue empty generator for removal
                fileGenerators = [gen for gen in fileGenerators if gen not in toBeRemoved]
                toBeRemoved = set()

            for file in self.partialIndexFiles:  # remove partial indices
                Path(file).unlink()

    def calulatetfidf(self, postingsList: list):
        freqToTfidf = list()
        for posting in postingsList:
            tfidf = round((1 + log10(posting[1])) * (log10(self.filesProcessed / len(postingsList))), 2)
            freqToTfidf.append((posting[0], tfidf))
        return freqToTfidf

    def check_near_duplicaton(self, word_frequencies):
        global fingerPrints
        sh = SimHash(word_frequencies)
        for fp in fingerPrints:
            score = sh.distance(fp)
            if score <= 10:
                return True
        fingerPrints.append(sh.finger_print)
        return False


if __name__ == "__main__":
    indexer = BuildIndex(PATH)
    indexer.buildIndex()
    indexer.writeData()
    indexer.mergeFiles()
