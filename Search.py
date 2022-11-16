
def booleanResults(word_search):
  # gets all the pages the term is stored at 
  pass


def getSearchResults(user_query):
  unique_words = set(user_query.split())

  # gets all the pages with the unique results
  for word in unique_words:
    booleanResults(word)


  # for AND results, the result URLS must contain all pages
  results = []
  if len(results) == 0:
    print("No results found")

  return results


# Retrieves and prints the Top 5 URL
def printTopURLS():
  pass


def main():
  user_query = input("Enter a query: ").strip()

  while user_query != "":
    print(user_query)
    new_words = user_query.split()
    for word in new_words:
      print(word)
    user_query = input("Enter a query: ").strip()


if __name__ == "__main__":
  main()