# TODO: load ID/URL mappings dict.  Load json for each term in search.  Merge common IDs for each term, create vector
#  to compute cosine similarity

# gets all the postings the term is stored at
def booleanResults(word_search, inverted_index):
  # TODO: Cannot load full index all at once.  Need to either built a sub-index of essentially pointers to certain
  #  words in our index to make searching faster " term “ape” is at position 1311, “apple” is at position 1345, etc."
  #  and "seeK," or find a library that does something similar/more efficient

  postings = list(inverted_index[word_search])
  return postings


def getSearchResults(user_query, inverted_index):
  #TODO: Use stemmer on the words that are searched to match them with index

  unique_words = set(user_query.split())
  search_words = set()
  
  # for each word, check if the term exists in the index
  for word in unique_words:
    if word in inverted_index:
      search_words.add(word)

  oneWordMatches = set()

  # gets all the pages where at least one word from the query matches
  for word in search_words:
    getPostings = booleanResults(word, inverted_index)
    for posting in getPostings:
      if posting not in oneWordMatches:
        oneWordMatches.add(posting)

  best_results = set()

  # filter out results that do not contain all the query matches
  for posting in oneWordMatches:
    allTerms = True
    for word in search_words:
      postings = inverted_index[word]
      if posting not in postings:
        allTerms = False
        break

      # if doc contains all words, add it to the results
      if allTerms:
        best_results.add(posting)
      
  return best_results


# Retrieves and prints 5 URLS for each query
def printTopURLS(results):
  if len(results) == 0:
    print("No Results Found")
  else:
    print(results)


def main():
  user_query = input("Enter a query: ").strip()

  # get the inverted_index from the 
  inverted_index = {}

  while user_query != "":
    results = getSearchResults(user_query, inverted_index)
    printTopURLS(results)
    user_query = input("Enter a query: ").strip()


if __name__ == "__main__":
  main()