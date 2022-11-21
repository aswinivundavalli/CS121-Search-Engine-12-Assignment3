import sys


class MaxHeap:

    def __init__(self):
        self._size = 0  # heap size
        self._heap = []
        self._heap.append(sys.maxsize)
        self._root = 1  # root of heap starts at index 1

    @staticmethod
    def _parent(pos):
        """return node's parent"""

        return pos // 2

    @staticmethod
    def _leftChild(pos):
        """return node's left child"""

        return pos * 2

    @staticmethod
    def _rightChild(pos):
        """return node's right child"""

        return (pos * 2) + 1

    def getSize(self):
        """return size of heap"""

        return self._size

    def _hasTwoChildren(self, pos):
        """check if node has two children, return bool"""

        return self._size >= self._rightChild(pos)

    def _hasOneChild(self, pos):
        """check if node has one child, return bool"""

        return self._size >= self._leftChild(pos)

    def _swap(self, parIdx, childIdx):
        """swap parent and child nodes"""

        self._heap[parIdx], self._heap[childIdx] = self._heap[childIdx], self._heap[parIdx]

    def _heapify(self, pos):
        """restructure heap after extraction"""

        if self._hasTwoChildren(pos):
            if (self._heap[pos] < self._heap[self._leftChild(pos)] or
                    self._heap[pos] < self._heap[self._rightChild(pos)]):

                if self._heap[self._rightChild(pos)] < self._heap[self._leftChild(pos)]:
                    self._swap(pos, self._leftChild(pos))
                    self._heapify(self._leftChild(pos))

                else:
                    self._swap(pos, self._rightChild(pos))
                    self._heapify(self._rightChild(pos))

        if self._hasOneChild(pos):
            if self._heap[pos] < self._heap[self._leftChild(pos)]:
                self._swap(pos, self._leftChild(pos))
                self._heapify(self._leftChild(pos))

    def insert(self, element):
        """insert node into heap"""

        self._size += 1
        self._heap.append(element)

        currentIndex = self._size

        while self._heap[currentIndex] > self._heap[self._parent(currentIndex)]:
            self._swap(currentIndex, self._parent(currentIndex))
            currentIndex = self._parent(currentIndex)

    def extractMax(self):
        """extract value at root (max val)"""

        if self._size != 0:
            maxVal = self._heap[self._root]
            self._heap[self._root] = self._heap[self._size]
            self._size -= 1
            self._heap.pop()
            self._heapify(self._root)

            return maxVal
