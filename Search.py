from LoadData import LoadData
from nltk import stem
import re
from collections import Counter
from math import log10, ceil
from numpy import dot
from numpy.linalg import norm
from time import process_time
from MaxHeap import MaxHeap as heap


STEMMER = stem.PorterStemmer()
FILESPROCESSED = 53792


class DocRelevance:
    """stores docID and cosine similarity after vector processing"""

    def __init__(self, docID, cosineSimilarity):
        self.docID = docID
        self.cosineSimilarity = cosineSimilarity

    def __gt__(self, right):
        if isinstance(right, int):
            return self.cosineSimilarity > right
        return self.cosineSimilarity > right.cosineSimilarity


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
        wordFrequency.update(searchWords)  # keep count for words in query to calc tf
        wordPostings = dict()  # dict of words and their corresponding posting tuples

        tStart = process_time()
        for word in wordFrequency.keys():  # iterate through words, find pointer in index, add words/postings to dict
            wordOffsetInIndexFile = self.loadData.getWordPositionInIndex(word)
            if wordOffsetInIndexFile is not None:
                posting = self.loadData.getPosting(wordOffsetInIndexFile, word)
                if (log10(FILESPROCESSED / len(posting))) > .5:  # only store words with IDF value above this threshold
                    wordPostings[word] = posting
        tStop = process_time()
        print("Elapsed time during loop1 in ms:", (tStop - tStart) * 1000)

        tStart = process_time()
        incrementer = 0
        docVectors = dict()  # store tfidf vector for each document
        queryVector = []  # query tfidf vector
        vectorLen = len(wordPostings.keys())  # get query vector len to initialize docVectors to that size
        for word, postings in wordPostings.items():
            for docID, tfidf in postings:  # initialize and update doc vectors
                if docID not in docVectors:
                    docVectors[docID] = [0 if val != incrementer else tfidf for val in range(vectorLen)]
                else:
                    docVectors[docID][incrementer] = tfidf
            incrementer += 1
            # update query vector
            queryVector.append(round((1 + log10(wordFrequency[word])) * (log10(FILESPROCESSED/len(postings))), 2))
        tStop = process_time()
        print("Elapsed time during loop2 in ms:", (tStop - tStart) * 1000)

        tStart = process_time()
        cosineSimHeap = heap()  # store cosine similarity vectors in a heap
        maxZeros = vectorLen - int(ceil(vectorLen*.7))  # set value for max allowable non-matches -- not slow I'm dumb
        for docID, docVector in docVectors.items():  # compute cosine similarity, insert vector object into heap
            if docVector.count(0) <= maxZeros:
                cosineSimHeap.insert(DocRelevance(docID, dot(queryVector, docVector) /
                                                  (norm(queryVector) * norm(docVector))))
        tStop = process_time()
        print("Elapsed time during loop3 in ms:", (tStop - tStart) * 1000)

        return [self.loadData.IDUrlMap[str(heapMax.docID)] for _ in range(5)
                if (heapMax := cosineSimHeap.extractMax()) is not None]

    @staticmethod
    def top5Results(results, resType=""):
        print(resType)
        for i, docID in enumerate(results[:5]):
            print(f"{i+1}. {docID}")
        print()


def main():
    searchEngine = SearchEngine()
    user_query = input("Enter a query: ")
    while user_query != "":
        tStart = process_time()
        # booleanResults = searchEngine.booleanSearch(user_query)
        cosineSimResults = searchEngine.cosineSimilarity(user_query)
        # searchEngine.top5Results(booleanResults, "boolean results")
        searchEngine.top5Results(cosineSimResults, "cosine similarity results")
        tStop = process_time()
        print("Elapsed time during the search in ms:", (tStop - tStart) * 1000)

        user_query = input("Enter a query: ")


if __name__ == "__main__":
    main()