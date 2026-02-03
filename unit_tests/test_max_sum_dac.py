import sys
import unittest

sys.path.insert(0, '..')
from utils.max_sum_dac_algorithm import MSSDAC
sys.path.remove('..')

class TestMSSDAC(unittest.TestCase):

    def test_deviation_list(self):
        """Set up appropriate list needed to instantiate MSSDAC object & test the retrieval of the correct indices."""

        # Set up necessary lists
        test_list = [12, 10, 17, 3, 8, 8, 21, 8, 16]
        avg_value = round(sum(test_list) / len(test_list), 0)  # 11
        deviation_list = [round(i - avg_value, 0) for i in test_list]  # [1, -1, 6, -8, -3, -3, 10, -3, 5]

        # Instantiate & call the algorithm
        test_dac = MSSDAC()
        max_value = test_dac.max_subarray(input_list=deviation_list)
        start_of_streak = test_dac.left_index
        end_of_streak = test_dac.right_index

        # Check if values & indices match what is expected
        self.assertEqual(max_value, 12)
        self.assertEqual(start_of_streak, 6)
        self.assertEqual(end_of_streak, 8)

if __name__ == '__main__':
    unittest.main()
