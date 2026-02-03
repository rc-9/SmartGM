import sys
import logging
import unittest
import pandas as pd

sys.path.insert(0, '..')
from hot_streak_finder import StreakFinder
sys.path.remove('..')

class TestStreakFinder(unittest.TestCase):
    """Carries out unittests for StreakFinder primary methods (load csv & input validation not tested)."""

    def setUp(self):
        logging.disable(logging.CRITICAL)

    def test_pre_processing(self):
        """Set up appropriate dataframes needed to instantiate cleaner object & test the pre-processing methods."""

        test_df = pd.DataFrame({
            'player_id': [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2, 4],
            'player_name': ['A B', 'A B', 'A B', 'A B', 'A B', 'A B', 'A B', 'A B', 'A B', 'A B', 'C D', 'A B', 'D E'],
            'fixture_id': [18200001, 18200002, 18200003, 18200004, 18200005, 18200006,
                           18200007, 18200008, 18200009, 18200010, 18200011, 19400001, None],
            'played_on': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, None, None],
            'points': [12, 10, 17, 3, None, 8, 8, 21, 8, 16, 12, 12, None],
            # Placeholder columns (only testing on one needed)
            'rebounds': [0]*13, 'assists': [0]*13, 'steals': [0]*13, 'blocks': [0]*13,
            'fg%': [0]*13, 'ft%': [0]*13, '3pt%': [0]*13
        })

        test_finder = StreakFinder()
        test_finder.comprehensive_stats_df = test_df
        test_finder.pre_processing()

        # Check if rows with empty fixture_id or fixture_ids designating non-regular-season games have been filtered out
        ret_id = test_finder.comprehensive_stats_df.fixture_id.values.tolist()
        self.assertEqual(ret_id, [
            18200001, 18200002, 18200003, 18200004, 18200005, 18200006, 18200007, 18200008, 18200009, 18200010, 18200011
        ])

        # Check if empty values were replaced with empty strings
        ret_points = test_finder.comprehensive_stats_df.points.values.tolist()
        self.assertEqual(ret_points, [12, 10, 17, 3, '', 8, 8, 21, 8, 16, 12])

    def test_execute_MSSDAC(self):
        """Tests the final processing and executing of MSSDAC algorithm."""

        test_df = pd.DataFrame({
            'player_id': [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3],
            'player_name': ['A B', 'A B', 'A B', 'A B', 'A B', 'A B', 'A B', 'A B', 'A B', 'A B', 'C D'],
            'fixture_id': [18200001, 18200002, 18200003, 18200004, 18200005, 18200006,
                           18200007, 18200008, 18200009, 18200010, 18200011],
            'played_on': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            'points': [12, 10, 17, 3, None, 8, 8, 21, 8, 16, 12],
        })

        test_finder = StreakFinder()
        test_finder.comprehensive_stats_df = test_df
        test_finder.player = 2
        test_finder.category = ['points']
        test_finder.execute_MSSDAC()

        # Check if dates returned equal what is expected
        ret_dates = test_finder.dates
        self.assertEqual(ret_dates, [8, 10])

if __name__ == '__main__':
    unittest.main()
