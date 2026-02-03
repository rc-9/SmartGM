import logging
import pandas as pd
from utils.max_sum_dac_algorithm import MSSDAC

# Defining the paths for CSV file containing comprehensive player/game statistical information needed (from 2016)
DATA_PATH = './data/intermediate/comprehensive_player_statistic.csv'

def logger_setup():
    """Standardized logging set up with custom handlers & formatters. Implements logging for all submodules executed."""
    logger = logging.getLogger()
    sh, fh = logging.StreamHandler(), logging.FileHandler('../logs_nba3k.log', 'a')
    sh.setFormatter(logging.Formatter('%(message)s'))
    fh.setFormatter(logging.Formatter('%(module)s (%(lineno)d): %(asctime)s | %(levelname)s | %(message)s'))
    logger.setLevel(logging.DEBUG), sh.setLevel(logging.INFO), logger.addHandler(fh), logger.addHandler(sh)
    return logger

class StreakFinder:
    """Implements DAC to find players' best statistical stretch of a season for any particular fantasy category."""

    def __init__(self):
        """Instantiates class attributes for storing input parameters & the processed dataframes to be used."""
        self.player = None
        self.category = None
        self.dates = None
        self.comprehensive_stats_df = None
        self.load_csv()

    def load_csv(self):
        """Loads data from CSV files into dataframe attribute for local reading & analysis."""
        try:
            logging.info('\nLOG: Loading player statistical data since 2016...')
            self.comprehensive_stats_df = pd.read_csv(DATA_PATH, sep=',', header=0, encoding='utf-8', low_memory=False)

        except FileNotFoundError as e:
            logging.error(f'File not found error: {e}')

    def pre_processing(self):
        """Refactor dataframe to only include pertinent game information & categories."""

        logging.debug('Refactoring comprehensive_player_statistic data to fit the requirements of this module...')
        stats_df = self.comprehensive_stats_df.copy()  # To prevent "SettingWithCopy" Warning message
        stats_df = stats_df[[
            'player_id', 'player_name', 'fixture_id', 'played_on',
            'points', 'rebounds', 'assists', 'steals', 'blocks', 'fg%', 'ft%', '3pt%'
        ]]

        # Filter out rows of player IDs with no game records
        stats_df['fixture_id'].fillna(value=0, inplace=True)
        stats_df = stats_df[stats_df.fixture_id != 0]

        # Filter out rows of game records that aren't regular-season games
        stats_df = stats_df[
            (stats_df['fixture_id'] >= 16200000) & (stats_df['fixture_id'] < 16400000) |
            (stats_df['fixture_id'] >= 17200000) & (stats_df['fixture_id'] < 17400000) |
            (stats_df['fixture_id'] >= 18200000) & (stats_df['fixture_id'] < 18400000) |
            (stats_df['fixture_id'] >= 19200000) & (stats_df['fixture_id'] < 19400000) |
            (stats_df['fixture_id'] >= 20200000) & (stats_df['fixture_id'] < 20400000)
            ]
        stats_df.reset_index(drop=True, inplace=True)

        # Fill in na values with empty strings for statistical categories (won't count during mssdac)
        stats_df.fillna(value='', inplace=True)

        self.comprehensive_stats_df = stats_df
        logging.info('LOG: Datasets loaded. Please provide information below to get started...')

    def input_validation(self):
        """Gathers input (player/category) from console, validates parameters (using df), and reacts accordingly."""

        logging.debug('Creating dict to link player names & IDs to use for input validation...')
        player_id_dict = dict(zip(self.comprehensive_stats_df.player_name, self.comprehensive_stats_df.player_id))

        # Gather player of interest from console & check if player exists within dictionary keys
        while self.player is None:
            player_input = input('\nEnter player name: ')
            if player_input == 'quit':
                logging.info('\nProgram has been terminated.')
                exit()
            elif player_input in player_id_dict.keys():
                self.player = player_id_dict[player_input]
            else:
                logging.info('INVALID INPUT: Unable to find player. Try again or enter "quit" to exit.')

        # Gather category of interest from console & validate the input
        cat_list = ['points', 'rebounds', 'assists', 'steals', 'blocks', 'fg%', 'ft%', '3pt%']
        while self.category is None:
            cat_input = input(f'Select a category{cat_list} or enter "all": ')
            if cat_input in cat_list:
                self.category = [cat_input]
            elif cat_input == 'all':
                self.category = cat_list
            else:
                logging.info('INVALID INPUT: That category is unavailable. Please try again.')

        logging.info('\nLOG: Player & Category input parameters have been validated.')

    def execute_MSSDAC(self):
        """Prepares dataset based on input parameters and executes MSSDAC algorithm for each season & category."""

        # Assign local dataframe with filtered out stats to only keep records of the player of interest
        stats_df = self.comprehensive_stats_df[self.comprehensive_stats_df.player_id == self.player]
        stats_df.reset_index(drop=True, inplace=True)
        logging.info('LOG: Preparing data to feed into MSSDAC algorithm...\n')

        # Set up for loops that execute MSSDAC for each season from 2016:2020, and for each category of interest
        for cat in self.category:
            cat_stats_df = stats_df[['fixture_id', 'played_on', cat]]
            logging.info(f'\n---------------------------------------{cat}---------------------------------------')

            for season in [16, 17, 18, 19, 20]:
                season_stats_df = cat_stats_df[
                    (cat_stats_df['fixture_id'] >= (season * 1000000)) &
                    (cat_stats_df['fixture_id'] < ((season + 1) * 1000000))
                    ]

                # Set up if-conditional to only execute for seasons for which there is a record of the player
                if not season_stats_df.empty:

                    # Removing records with NA values (empty strings)
                    season_stats_df = season_stats_df[season_stats_df[cat] != '']

                    # Get mean of the stat category
                    avg_stat = round(season_stats_df[cat].mean(), 1)

                    # Build necessary lists needed to implement MSSDAC
                    dates_list = season_stats_df.played_on.values.tolist()
                    stat_list = season_stats_df[cat].values.tolist()
                    stat_deviation_list = [round(stat_list[i] - avg_stat, 1) for i in range(len(stat_list))]
                    # stat_deviation_list = [round(i - avg_stat, 1) for i in stat_list]

                    # Instantiate MSSDAC imported class & pass in stat_deviation_list
                    dac = MSSDAC()
                    max_value = dac.max_subarray(input_list=stat_deviation_list)
                    self.dates = [dates_list[dac.left_index], dates_list[dac.right_index]]
                    time_frame_stats = stat_list[dac.left_index:dac.right_index]
                    logging.info(f'Best stretch for [{cat}] for [{season+2000}-{season+2001}] season is between: '
                                 f'{self.dates[0]} & {self.dates[1]}')
                    # print(f'sum: {sum(time_frame_stats)}')
                    # print(f'average: {round(sum(time_frame_stats) / len(time_frame_stats),1)}')

def main():
    """Instantiates StreakFinder class & sets up loop to keep conducting searches till told otherwise."""
    logger = logger_setup()
    logging.info('\nThis tool will help look for players\' hot stretches (relative to their season average),'
                 ' in particular stat categories, over the last few seasons.')

    finder = StreakFinder()
    finder.pre_processing()

    again_input = 'Yes'
    while again_input == 'Yes':
        finder.input_validation()
        finder.execute_MSSDAC()
        again_input = input('\nWould you like to conduct another search (enter "Yes" or "No")? ')
        finder.player = finder.category = None  # Reset
    logging.info('\nExecution complete. Goodbye.')

if __name__ == '__main__':
    main()
