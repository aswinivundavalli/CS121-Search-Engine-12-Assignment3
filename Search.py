
# gets all the postings the term is stored at 
def booleanResults(word_search, inverted_index):
  postings = list(inverted_index[word_search])
  return postings


def getSearchResults(user_query, inverted_index):
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