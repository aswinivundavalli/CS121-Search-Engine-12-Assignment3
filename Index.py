from pathlib import Path
import json
from bs4 import BeautifulSoup
import re
from collections import defaultdict, Counter
from nltk import stem

STEMMER = stem.PorterStemmer()

class Posting:
    def __init__(self, docid, tfidf):
        self.docid = docid
        self.tfidf = tfidf # frequency counts for now

class BuildIndex:
    def __init__(self, path) -> None:
        self.webPagesPath = path
        self.urlIDMap = {} # key - doc URL, value - document ID
        self.IDUrlMap = {} # key - document ID, value - doc URL
        self.invertedIndex = {} # key - words, values - List of postings (Actual Indexer, in-memory)
    
    def buildIndex(self):
        docNumber = 0 # Initial document number
        path = Path(self.webPagesPath) # one folder while testing
        for file in path.iterdir():
            with open(file) as readFile:
                jsonObj = json.load(readFile)
                
                url = jsonObj["url"]  # might need to defrag again, unsure as it wasn't specified
                if url in self.urlIDMap:  continue
                self.urlIDMap[url] = docNumber
                self.IDUrlMap[docNumber] = url
                
                rawContent = jsonObj["content"]
                content = BeautifulSoup(rawContent, features="html.parser")
                
                content = content.find_all('body')
                for line in content:
                    tokens = [STEMMER.stem(word) if "'" not in word else STEMMER.stem(word.replace("'", ''))
                            for word in re.sub(r"[^a-zA-Z0-9']", " ", line.text.lower()).split()]
                    token_frequency = Counter(tokens)
                    for token in tokens:
                        if token not in self.invertedIndex:
                            self.invertedIndex[token] = list()
                        self.invertedIndex[token].append(Posting(docNumber, token_frequency[token]))
            docNumber += 1
    
    def writeDate(self):
        with open("urlIDMap.txt", 'w') as data:
            jsonObj = json.dumps(self.urlIDMap)
            data.write(jsonObj)
        with open("IDUrlMap.txt", 'w') as data:
            jsonObj = json.dumps(self.IDUrlMap)
            data.write(jsonObj)
        with open("indexes.txt", 'w'): # can't write Posting objects to python file. Have to figure out a way
            print(self.invertedIndex)
            #jsonObj = json.dumps(self.invertedIndex)
            #data.write(jsonObj)
    

if __name__ == "__main__":
    indexer = BuildIndex("DEV/www_stat_uci_edu")
    indexer.buildIndex()
    indexer.writeDate()