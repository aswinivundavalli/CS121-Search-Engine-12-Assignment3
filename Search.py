from LoadData import LoadData
from nltk import stem
import re
from collections import Counter
from math import log10
from numpy import dot
from numpy.linalg import norm



STEMMER = stem.PorterStemmer()
FILESPROCESSED = 53792


class SearchEngine:
    def __init__(self):
        self.loadData = LoadData()

    def booleanSearch(self, userQuery: str):
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
        return [self.loadData.IDUrlMap[str(doc)] for doc in documentsSet]

    def cosineSimilarity(self, userQuery: str):
        wordFrequency = Counter()
        searchWords = [STEMMER.stem(word) for word in
                       re.sub(r"[^a-zA-Z0-9\s]", "", userQuery.lower()).split()]
        wordFrequency.update(searchWords)
        unstoredWords = set()
        wordPostings = dict()

        for word in wordFrequency.keys():
            wordOffsetInIndexFile = self.loadData.getWordPositionInIndex(word)
            if wordOffsetInIndexFile is not None:
                wordPostings[word] = self.loadData.getPosting(wordOffsetInIndexFile, word)
            else:
                unstoredWords.add(word)

        for word in unstoredWords:
            wordFrequency.pop(word)

        incrementer = 0
        docVectors = dict()
        queryVector = []
        vectorLen = len(wordFrequency.keys())
        for word, postings in wordPostings.items():
            for docID, tfidf in postings:
                if docID not in docVectors:
                    docVectors[docID] = [0 if val != incrementer else tfidf for val in range(vectorLen)]
                else:
                    docVectors[docID][incrementer] = tfidf
            incrementer += 1
            queryVector.append(round((1 + log10(wordFrequency[word])) * (log10(FILESPROCESSED/len(postings))), 2))
        # print(f"doc vectors ->  {docVectors}")
        # print(f"query vector ->  {queryVector}")

        cosineSim = []
        for docID, docVector in docVectors.items():
            cosineSim.append((docID, dot(queryVector, docVector)/(norm(queryVector) * norm(docVector))))
        cosineSim.sort(key=lambda x: x[1], reverse=True)
        #print(f"cosine sim ->  {cosineSim[:5]}")
        return [self.loadData.IDUrlMap[str(doc[0])] for doc in cosineSim[:5]]

    def top5Results(self, results, type=""):
        print(type)
        for i, docID in enumerate(results[:5]):
            print(f"{i+1}. {docID}")
        print()


def main():
    searchEngine = SearchEngine()
    user_query = input("Enter a query: ").strip()
    while user_query != "":
        booleanResults = searchEngine.booleanSearch(user_query)
        cosineSimResults = searchEngine.cosineSimilarity(user_query)
        searchEngine.top5Results(booleanResults, "boolean results")
        searchEngine.top5Results(cosineSimResults, "cosine similarity results ")
        user_query = input("Enter a query: ").strip()


if __name__ == "__main__":
    main()
