from pathlib import Path
import json
from bs4 import BeautifulSoup
import re
from collections import defaultdict, Counter
from nltk import stem
from urllib.parse import urldefrag

STEMMER = stem.PorterStemmer()


# class Posting:
#     def __init__(self, docid, tfidf):
#         self.docid = docid
#         self.tfidf = tfidf  # frequency counts for now


class BuildIndex:
    def __init__(self, path) -> None:
        self.webPagesPath = path
        self.urlIDMap = {}  # key - doc URL, value - document ID
        self.IDUrlMap = {}  # key - document ID, value - doc URL
        self.invertedIndex = {}  # key - words, values - List of postings (Actual Indexer, in-memory)

    def buildIndex(self):
        docNumber = 0  # Initial document number
        path = Path(self.webPagesPath)  # one folder while testing
        for file in path.iterdir():
            with open(file) as readFile:
                jsonObj = json.load(readFile)

                url = urldefrag(jsonObj["url"]).url  # defragged
                if url in self.urlIDMap:
                    continue
                self.urlIDMap[url] = docNumber
                self.IDUrlMap[docNumber] = url

                rawContent = jsonObj["content"]
                content = BeautifulSoup(rawContent, features="html.parser")

                content = content.find_all('body')
                for line in content:
                    tokens = [STEMMER.stem(word) if "'" not in word else STEMMER.stem(word.replace("'", ''))
                              for word in re.sub(r"[^a-zA-Z0-9']", " ", line.text.lower()).split()]
                    token_frequency = Counter(tokens)
                    for token, frequency in token_frequency.items(): # fixed, was iterating over tokens (not a set) and duplicaiting values
                        if token not in self.invertedIndex:
                            self.invertedIndex[token] = list()
                        # postingObj = Posting(docNumber, frequency)
                        # self.invertedIndex[token].append(postingObj.__dict__)
                        self.invertedIndex[token].append((docNumber, frequency))
            docNumber += 1

    def writeData(self):
        with open("urlIDMap.txt", 'w') as data:
            jsonObj = json.dumps(self.urlIDMap)
            data.write(jsonObj)
        with open("IDUrlMap.txt", 'w') as data:
            jsonObj = json.dumps(self.IDUrlMap)
            data.write(jsonObj)
        with open("index.txt", 'w') as data:  # can't write Posting objects to python file. Have to figure out a way
            jsonObj = json.dumps(self.invertedIndex)
            data.write(jsonObj)


if __name__ == "__main__":
    indexer = BuildIndex("/DEV/www_stat_uci_edu")
    indexer.buildIndex()
    indexer.writeData()