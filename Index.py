import ast
import json
import os
import pandas as pd
import re

from bs4 import BeautifulSoup
from collections import defaultdict, Counter, OrderedDict
from nltk import stem
from pathlib import Path
from sortedcontainers import SortedDict
from urllib.parse import urldefrag

STEMMER = stem.PorterStemmer()
BATCH_SIZE = 2000

class BuildIndex:
    def __init__(self, path) -> None:
        self.webPagesPath = path
        self.urlIDMap = {}  # key - doc URL, value - document ID
        self.IDUrlMap = {}  # key - document ID, value - doc URL
        self.invertedIndex = SortedDict()  # key - words, values - List of postings (Actual Indexer, in-memory)
        self.partialIndexFiles = [] # list to store the partial index files generated
        self.partialFileIndex = 0 # Used to name the partial index file

    def buildIndex(self):
        docNumber = 0  # Initial document number
        path = Path(self.webPagesPath)  # one folder while testing

        filesProcessedSoFar = 0 # To keep track of no.of files processed in a batch
        partialFileIndex = 0 # Used to name the partial index file

        for dir in path.iterdir():
            for file in dir.iterdir():
                with open(file) as readFile:
                    jsonObj = json.load(readFile)

                    url = urldefrag(jsonObj["url"]).url  # defragged
                    if url in self.urlIDMap: continue
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

                filesProcessedSoFar += 1
                if filesProcessedSoFar == BATCH_SIZE:
                    filesProcessedSoFar = 0
                    self.writePartialIndexesToFile("partialIndices/ParialIndex_{}.json".format(self.partialFileIndex))
                    self.partialIndexFiles.append("partialIndices/ParialIndex_{}.json".format(self.partialFileIndex))
                    self.partialFileIndex += 1
                    self.invertedIndex = SortedDict()
                docNumber += 1
        
        if filesProcessedSoFar < BATCH_SIZE:
            self.writePartialIndexesToFile("partialIndices/ParialIndex_{}.json".format(self.partialFileIndex))
            self.partialIndexFiles.append("partialIndices/ParialIndex_{}.json".format(self.partialFileIndex))
            self.partialFileIndex += 1

        self.mergeFiles()

    def writePartialIndexesToFile(self, fileName):
        with open(fileName, 'w') as f: 
            indexData = {"tokens": list(self.invertedIndex.keys()), "indices": self.invertedIndex}
            json.dump(indexData, f)
        self.invertedIndex = {}

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
    
    def mergeFiles(self):
        print(self.partialIndexFiles)
        while(len(self.partialIndexFiles) > 1):
            file1 = self.partialIndexFiles.pop(0)
            file2 = self.partialIndexFiles.pop(0)
            
            merged_file = "partialIndices/ParialIndex_{}.json".format(self.partialFileIndex)
            self.partialFileIndex += 1
            self.partialIndexFiles.insert(0, merged_file)

            with open(file1, 'r') as f:
                data_1 = json.load(f)
                file1_tokens = data_1["tokens"]
                num_tokens_file_1 = len(file1_tokens)

            with open(file2, 'r') as f:
                data_2 = json.load(f)
                file2_tokens = data_2["tokens"]
                num_tokens_file_2 = len(file2_tokens)
            
            merged_result = {}
            merged_result["tokens"] = []
            merged_result["indices"] = {}

            p1, p2 = 0, 0
            while p1 < num_tokens_file_1 and p2 < num_tokens_file_2:
                if file1_tokens[p1] < file2_tokens[p2]:
                    merged_result["indices"][file1_tokens[p1]] = data_1["indices"][file1_tokens[p1]]
                    merged_result["tokens"].append(file1_tokens[p1])
                    p1 += 1
                elif file1_tokens[p1] > file2_tokens[p2]:
                    merged_result["indices"][file2_tokens[p2]] = data_2["indices"][file2_tokens[p2]]
                    merged_result["tokens"].append(file2_tokens[p2])
                    p2 += 1
                else:
                    merged_result["indices"][file1_tokens[p1]] = data_1["indices"][file1_tokens[p1]] + data_2["indices"][file2_tokens[p2]]
                    merged_result["tokens"].append(file1_tokens[p1])
                    p1 += 1
                    p2 += 1

            while p1 < num_tokens_file_1:
                merged_result["indices"][file1_tokens[p1]] = data_1["indices"][file1_tokens[p1]]
                p1 += 1

            while p2 < num_tokens_file_2:
                merged_result["indices"][file2_tokens[p2]] = data_2["indices"][file2_tokens[p2]]
                p2 += 1

            os.remove(file1)
            os.remove(file2)
            with open(merged_file, 'w') as f: 
                json.dump(merged_result, f)
        print(self.partialIndexFiles)


if __name__ == "__main__":
    indexer = BuildIndex("DEV/")
    indexer.buildIndex()
    indexer.writeData()