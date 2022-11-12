from pathlib import Path
import json
from bs4 import BeautifulSoup
import re
from collections import Counter
from nltk import stem
from urllib.parse import urldefrag
import sys

STEMMER = stem.PorterStemmer()
BATCH_SIZE = 3000000  # bytes
PATH = "DEV/"
PARTIALINDEXPATH = "partialIndices/partialIndex_"
FULLINDEXPATH = "full_Index/index.jsonl"


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
        path = Path(self.webPagesPath)  # one folder while testing
        for dir in path.iterdir():
            for file in dir.iterdir():
                with open(file) as readFile:
                    jsonObj = json.load(readFile)

                    url = urldefrag(jsonObj["url"]).url  # defragged
                    if url in self.urlIDMap:
                        continue
                    self.urlIDMap[url] = docNumber
                    self.IDUrlMap[docNumber] = url

                    rawContent = jsonObj["content"]
                    content = BeautifulSoup(rawContent, features="html.parser")
                    content = content.find_all()
                    for line in content:
                        tokens = [STEMMER.stem(word) if "'" not in word else STEMMER.stem(word.replace("'", ''))
                                  for word in re.sub(r"[^a-zA-Z0-9']", " ", line.text.lower()).split()]
                        token_frequency = Counter(tokens)
                        for token, frequency in token_frequency.items():
                            if token not in self.invertedIndex:
                                self.invertedIndex[token] = list()
                            self.invertedIndex[token].append((docNumber, frequency))
                self.filesProcessed += 1

                docNumber += 1
                if sys.getsizeof(self.invertedIndex) >= BATCH_SIZE:
                    self.writePartialIndexesToFile()

            print(dir)
        if self.invertedIndex:
            self.writePartialIndexesToFile()

    def writeData(self):
        with open("urlIDMap.txt", 'w') as data:
            jsonObj = json.dumps(self.urlIDMap)
            data.write(jsonObj)
        with open("IDUrlMap.txt", 'w') as data:
            jsonObj = json.dumps(self.IDUrlMap)
            data.write(jsonObj)

    def writePartialIndexesToFile(self):
        """ writes current inverted index to file when size of dict is >= 3mb """

        path = f"{PARTIALINDEXPATH}{self.partialFileIndex}.jsonl"
        with open(path, 'w') as f:
            sortedIndex = sorted(self.invertedIndex.items(), key=lambda x: x[0])
            self.invertedIndex = {}
            for k, v in sortedIndex:
                keyValAsJson = json.dumps({k: v})
                f.write(keyValAsJson + "\n")
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

        with open(FULLINDEXPATH, 'w') as final: # open final index
            generators = [self.generateLine(n) for n in self.partialIndexFiles]  # generator obj for each partial
            nextWords = []  # stores most recent word yielded from each generator
            toBePopped = set()  # pops off generator when empty

            for i, gen in enumerate(generators):
                currMapping = list(next(gen).items())
                nextWords.append((currMapping[0][0], currMapping[0][1], generators[i]))  # store k,v pair w/ gen obj

            while generators:
                nextWords.sort(key=lambda x: x[0])  # sort yielded words
                getNextVals = [nextWords[0][2]]  # initialize list to get next value from generator
                merged = nextWords[0][1]  # initialize values that may be merged if there is a word match
                i = 1
                while i < len(nextWords) - 1:
                    if nextWords[i][0] == nextWords[i - 1][0]:
                        merged.extend(nextWords[i][1])  # same word, merge values
                        getNextVals.append(nextWords[i][2])
                    else:
                        break
                    i += 1

                self.tokensProcessed += 1
                keyValAsJson = json.dumps({nextWords[i - 1][0]: merged})  # write k,v pair into final index
                final.write(keyValAsJson + "\n")
                nextWords = nextWords[len(getNextVals):]  # remove written word

                for i, gen in enumerate(getNextVals):
                    try:
                        currMapping = list(next(gen).items())
                        nextWords.append((currMapping[0][0], currMapping[0][1], gen))  # store new k,v pair w/ gen obj
                    except StopIteration:
                        toBePopped.add(gen)  # queue generator for removal as it's empty
                generators = [gen for gen in generators if gen not in toBePopped]
                toBePopped = set()

            for file in self.partialIndexFiles:  # remove partial indices
                Path(file).unlink()



if __name__ == "__main__":
    indexer = BuildIndex(PATH)
    indexer.buildIndex()
    indexer.writeData()
    indexer.mergeFiles()