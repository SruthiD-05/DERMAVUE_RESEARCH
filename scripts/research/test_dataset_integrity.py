import unittest

from dataset_integrity import hamming_distance


class DatasetIntegrityTests(unittest.TestCase):
    def test_hamming_distance(self):
        self.assertEqual(hamming_distance("0000", "0011"), 2)
        self.assertEqual(hamming_distance("1010", "1010"), 0)


if __name__ == "__main__":
    unittest.main()
