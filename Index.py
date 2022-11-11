from pathlib import Path
import json
from bs4 import BeautifulSoup
import re
from collections import defaultdict
from nltk import stem


tokenFrequency = defaultdict(dict)
urlIDMap = {}
reverseUrlIDMap = {}
stemmer = stem.PorterStemmer()

storeIndex = {
    "tokens": tokenFrequency,
    "map": urlIDMap,
    # More efficient for checking if url's been mapped but uses more memory to store extra dict
    "reverseMap": reverseUrlIDMap
}


class Posting:
    def __init__(self, docid: int, tokens: list, url: str):
        self.docid = docid
        self.tokens = tokens
        self.url = url
        self.tfidf = defaultdict(int)  # use freq counts for now

    def mapID(self):
        if reverseUrlIDMap.get(self.url) is None:
            urlIDMap[self.docid] = self.url
            reverseUrlIDMap[self.url] = self.docid
            return True
        return False

    def tokenFreqs(self):
        for token in self.tokens:
            self.tfidf[token] += 1
        for k, v in self.tfidf.items():
            tokenFrequency[k][self.docid] = v


def main():
    docid = 0
    # path = Path("C:/SearchEngine/developer/DEV/")
    # for dir in path.iterdir():
    #     for file in dir.iterdir():
    #         pass
    path = Path("C:/SearchEngine/developer/DEV/www_stat_uci_edu") # one folder while testing
    for file in path.iterdir():
        with open(file) as readFile:
            jsonObj = json.load(readFile)
            url = jsonObj["url"]  # might need to defrag again, unsure as it wasn't specified
            rawContent = jsonObj["content"]
            content = BeautifulSoup(rawContent, features="html.parser")
            content = content.find_all('body')
            for line in content:
                tokens = [stemmer.stem(word) if "'" not in word else stemmer.stem(word.replace("'", ''))
                          for word in re.sub(r"[^a-zA-Z0-9']", " ", line.text.lower()).split()]
                page = Posting(docid, tokens, url)
                if page.mapID():
                    docid += 1
                    page.tokenFreqs()
    print(urlIDMap, reverseUrlIDMap)
    print()
    print(tokenFrequency)


with open("data.txt", 'w') as data:
    jsonObj = json.dumps(storeIndex)
    data.write(jsonObj)



# html find_all
main()
