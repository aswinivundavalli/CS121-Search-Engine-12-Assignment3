from LoadData import LoadData
from nltk import stem
import re

STEMMER = stem.PorterStemmer()

class SearchEngine:
    def __init__(self):
        self.loadData = LoadData()

    def booleanSeach(self, userQuery):
        # same transformation is applied on input query string
        searchWords = [STEMMER.stem(word) for word in
                                  re.sub(r"[^a-zA-Z0-9\s]", "", userQuery.lower()).split()]
        searchWords = set(searchWords)
        documentsSet = set()

        for word in searchWords:
            wordOffsetInIndexFile = self.loadData.getWordPositionInIndex(word)
            if wordOffsetInIndexFile is not None:
                postings = self.loadData.getPosting(wordOffsetInIndexFile, word)
                docIDs = set([item[0] for item in postings])
                if len(documentsSet) == 0:
                    documentsSet = docIDs
                else:
                    # find intersected documents - only for boolean search
                    docs = set([item[0] for item in postings])
                    documentsSet = documentsSet.intersection(docs)
        return documentsSet

def main():
    user_query = input("Enter a query: ").strip()
    searchEngine = SearchEngine()
    while user_query != "":
        results = searchEngine.booleanSeach(user_query)
        print(results)
        user_query = input("Enter a query: ").strip()

if __name__ == "__main__":
    main()