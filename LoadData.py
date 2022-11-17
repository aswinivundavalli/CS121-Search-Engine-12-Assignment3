import json
from BTrees.OOBTree import OOBTree

WORDINDEXTREE = OOBTree()
IDURLMAP = None


def loadIDtoURLmap() -> None:
    """loads ID to URL mappings"""

    global IDURLMAP
    with open("IDUrlMap.json", 'r') as URLmap:
        IDURLMAP = json.load(URLmap)


def createWordBTree() -> None:
    """stores words and their corresponding place in the main index in a btree """

    with open("full_index/index.jsonl", "r") as index:
        offset = 0
        for line in index:
            jsonObj = json.loads(line)
            WORDINDEXTREE.insert(list(jsonObj.keys())[0], offset)
            offset += len(line) + 1


def getWordPositionInIndex(word: str) -> int:
    """takes a word as an argument and returns its position in the main index file"""

    return WORDINDEXTREE[word] if word in WORDINDEXTREE else None  # will probably stem in main before func call


def getPosting(offset: int, word: str) -> list:
    """finds word in index using offset, loads json, returns list of postings"""

    with open("full_index/index.jsonl", "r") as index:  # will change this once integrated to keep file open always
        index.seek(offset)
        jsonline = json.loads(index.readline())
        return jsonline[word]
