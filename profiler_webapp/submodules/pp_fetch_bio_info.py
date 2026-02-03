### =========================== SETUP =========================== ###

# Data Acquisition
from nba_api.stats.endpoints import commonplayerinfo, playerawards

# Data Management
import pandas as pd

# Utils
from datetime import datetime
import json
import os
import sys
import time

# Settings
cwd = os.getcwd()
while not cwd.endswith('NBA-Profiler'):
    cwd = os.path.dirname(cwd)
sys.path.append(cwd)

# Define paths (relative to user OS) for files to be used
TEAM_INFO_PATH = os.path.join(cwd, './data/nba_teams.json')

# Load necessary files
with open(TEAM_INFO_PATH, 'r') as f:
    nba_teams = json.load(f)

### ============================================================= ###



class PlayerInfoFetcher:
    """
    Extracts player bio details for application display.
    """


    def __init__(self):
        self.request_interval = 1  # Custom wait-time to avoid API rate limits


    def fetch_player_info(self, player_id):
        """
        Retrieves and compiles basic player information.

        Parameters:
        - player_id (int): Unique NBA player ID

        Returns:
        - player_info (dict): Dictionary containing structured player information
        """

        try:

            # Fetch data from the NBA API
            time.sleep(self.request_interval)  # OPTIONAL (buffer for any previous request)
            common_player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id).get_data_frames()
            player_info, career_summary, played_seasons = common_player_info[0], common_player_info[1], common_player_info[2]

            # Extract relevant information and conduct necessary transformations
            player_info = {
                'first_name': player_info['FIRST_NAME'].values[0],
                'last_name': player_info['LAST_NAME'].values[0],
                'position': player_info['POSITION'].values[0],
                'height': player_info['HEIGHT'].values[0],
                'weight': player_info['WEIGHT'].values[0],
                'age': self._convert_birthdate_to_age(player_info['BIRTHDATE'].values[0]),
                'jersey_number': player_info['JERSEY'].values[0],
                'current_team_abbv': player_info['TEAM_ABBREVIATION'].values[0],
                'current_team_id': player_info['TEAM_ID'].values[0],
                'current_team_name': player_info['TEAM_NAME'].values[0],
                'nba_experience': str(player_info['SEASON_EXP'].values[0]) + ' Years'
                                    if player_info['SEASON_EXP'].values[0] != 1
                                    else str(player_info['SEASON_EXP'].values[0]) + ' Year',
                'country': player_info['COUNTRY'].values[0],
                'pre_nba_affiliation': player_info['LAST_AFFILIATION'].values[0],
                'draft_year': player_info['DRAFT_YEAR'].values[0],
                'draft_round': player_info['DRAFT_ROUND'].values[0],
                'draft_number': player_info['DRAFT_NUMBER'].values[0],

                'played_seasons': self._format_played_seasons(played_seasons),  # Available season options for further data retrieval
                'no_playdata_available': len(career_summary)==0,  # Binary value to determine if error message should be prompted in app
                'current_team_colors': nba_teams['TEAM_COLORS'].get(player_info['TEAM_ABBREVIATION'].values[0], ["#1c1e21", "#ffffff"])  # Default W/B if not on roster
            }

            return player_info

        except Exception as e:

            print(f'An error occurred while fetching player info. Please try again.')
            return {}


    def fetch_player_awards(self, player_id):
        """
        Retrieves and compiles player honors.

        Parameters:
        - player_id (int): Unique NBA player ID

        Returns:
        - player_awards (DataFrame): Dataframe containing structured player award info
        """

        try:

            # Fetch data from the NBA API
            player_award_info = playerawards.PlayerAwards(player_id=player_id).get_data_frames()[0]

            # Extract relevant information and conduct necessary transformations
            player_award_info = pd.DataFrame(player_award_info[['DESCRIPTION']].value_counts()).reset_index()

            return player_award_info

        except Exception as e:

            print(f'An error occurred while fetching player award info: {e}. Try again.')
            return {}


    def _convert_birthdate_to_age(self, birthdate):
        """
        Calculates age based on birth date.

        Parameters:
        - birthdate (date): Player birth date

        Returns:
        - age (int): Player current age, rounded down to nearest integer
        """

        age = int((datetime.now() - datetime.strptime(birthdate.split('T')[0], '%Y-%m-%d')).days / 365)

        return age


    def _format_played_seasons(self, played_seasons):
        """
        Formats and sorts the played seasons.

        Parameters:
        - played_seasons (DataFrame): DataFrame containing season data

        Returns:
        - formatted_seasons (list): List of formatted season strings in descending order
        """

        # Remove prefix to season start year and get unique season start years (i.e., 12023 to designate preseason of 2023-2024 season --> 2023)
        formatted_seasons = played_seasons.SEASON_ID.apply(lambda x: int(str(x)[1:])).drop_duplicates()

        # Convert season start years to a string containing start and last two digits of end year (i.e., 2023 --> "2023-24")
        formatted_seasons = formatted_seasons.apply(lambda x: f'{x}-{str(x + 1)[2:]}').sort_values(ascending=False).to_list()

        return formatted_seasons



def main(player_id):

    fetcher = PlayerInfoFetcher()
    player_info = fetcher.fetch_player_info(player_id)
    for key, value in player_info.items():
        print(f'{key}: {value}')

if __name__ == '__main__':
    main(2544)  # Test stand-alone functionality with example player ID