import hashlib

class SimHash():
    def __init__(self, words_frequency_map={}):
        self.words_frequency_map = words_frequency_map
        self.finger_print = self.compute_finger_print()

    def compute_finger_print(self):
        vector = [0] * 128
        words = self.words_frequency_map.keys()
        for word in words:
            hash_value = int(self.compute_hash(word), 2)
            for i in range(128):
                if hash_value & (1 << i):
                    vector[i] = vector[i] + self.words_frequency_map[word]
                else:
                    vector[i] -= self.words_frequency_map[word]

        fingerprint = 0
        for i in range(128):
            if vector[i] >= 0: fingerprint += 1 << i
        return fingerprint

    def compute_hash(self, word):
        result = hashlib.md5(word.encode("utf-8"))
        return bin(int(result.hexdigest(), base=16)).replace("0b", "")

    def distance(self, finger_print):
        distance = 0
        for i in range(127, -1, -1):
            b1 = finger_print >> i & 1
            b2 = self.finger_print >> i & 1
            if b1 != b2: distance += 1
        return distance