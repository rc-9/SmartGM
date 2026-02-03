### =========================== SETUP =========================== ###

# Data Acquisition
from nba_api.stats.endpoints import playercareerstats

# Data Management
import numpy as np
import pandas as pd

# Utils
import time

### ============================================================= ###





class PlayerCareerStatsFetcher:
    """
    Extracts career statistics for application display.
    """


    def __init__(self):
        self.request_interval = 0.5  # Custom wait-time to avoid API rate limits


    def fetch_career_stats(self, player_id):
        """
        Fetches input player's career statistics and executes processing steps.

        Parameters:
        - player_id (int): Unique NBA player ID

        Returns:
        - career_stats_dfs (list): List of 6 DataFrames containing cumulative stats by season (rs+ps), on a totals, per-game, per-36 basis
        """

        try:

            # Fetch data from NBA API endpoint
            time.sleep(self.request_interval)  # OPTIONAL (buffer for any previous request)
            career_per_game_dfs = playercareerstats.PlayerCareerStats(player_id=player_id, per_mode36='PerGame').get_data_frames()
            time.sleep(self.request_interval)  # OPTIONAL
            career_per_36_dfs = playercareerstats.PlayerCareerStats(player_id=player_id, per_mode36='Per36').get_data_frames()

            # Execute processing methods to retrieve formatted data
            per_game_rs_df, per_game_ps_df = self._process_stats(career_per_game_dfs)
            per_36_rs_df, per_36_ps_df = self._process_stats(career_per_36_dfs)
            per_36_rs_df, per_36_ps_df = per_36_rs_df.drop(columns=['MIN']), per_36_ps_df.drop(columns=['MIN'])

            career_stats_dfs = [per_game_rs_df, per_game_ps_df, per_36_rs_df, per_36_ps_df]
            return career_stats_dfs

        except Exception as e:

            print(f'An error occurred while fetching player stats. Please try again.')
            return {}


    def _process_stats(self, dfs):
        """
        Wrangles the raw statistics from the DataFrame set and returns a processed and filtered set.

        Parameters:
        - dfs (dataframes): Set of DataFrames containing various career statistics, as broken down in API documentation

        Returns:
        - merged_rs_df (dataframe): DataFrame with processed career regular-season stats of interest
        - merged_ps_df (dataframe): DataFrame with processed career post-season stats of interest
        """

        # Distinguish the incoming data by regular & post seasons
        by_szn_rs, summed_szn_rs = dfs[0], dfs[1]  # Regular Season: by season, cumulative
        by_szn_ps, summed_szn_ps = dfs[2], dfs[3]  # Post Season: by season, cumulative

        # Convert age floats to ints to str (for final display on app)
        by_szn_rs['PLAYER_AGE'] = by_szn_rs['PLAYER_AGE'].apply(lambda x: str(int(x)))
        by_szn_ps['PLAYER_AGE'] = by_szn_ps['PLAYER_AGE'].apply(lambda x: str(int(x)))

        # Combine the per-season and all-season dataframes for regular and post season data
        merged_rs_df = pd.concat([by_szn_rs, summed_szn_rs.reindex(columns=by_szn_rs.columns)], ignore_index=True)
        merged_ps_df = pd.concat([by_szn_ps, summed_szn_ps.reindex(columns=by_szn_ps.columns)], ignore_index=True)

        # Fill in missing values as per desired specifications for final output preferences
        merged_rs_df['SEASON_ID'] = merged_rs_df['SEASON_ID'].fillna('TOTAL')
        merged_ps_df['SEASON_ID'] = merged_ps_df['SEASON_ID'].fillna('TOTAL')
        merged_rs_df = merged_rs_df.fillna('--')
        merged_ps_df = merged_ps_df.fillna('--')

        # Convert proportions to percentages
        merged_rs_df[['FG_PCT', 'FG3_PCT', 'FT_PCT']] = (merged_rs_df[['FG_PCT', 'FG3_PCT', 'FT_PCT']] * 100).round(1)
        merged_ps_df[['FG_PCT', 'FG3_PCT', 'FT_PCT']] = (merged_ps_df[['FG_PCT', 'FG3_PCT', 'FT_PCT']] * 100).round(1)

        # Extract missing 2-PT data
        merged_rs_df['2PM'] = merged_rs_df['FGM'] - merged_rs_df['FG3M']
        merged_rs_df['2PA'] = merged_rs_df['FGA'] - merged_rs_df['FG3A']
        merged_rs_df['2P%'] = (merged_rs_df['2PM'] / merged_rs_df['2PA'] * 100).round(1).astype('float64')
        merged_ps_df['2PM'] = merged_ps_df['FGM'] - merged_ps_df['FG3M']
        merged_ps_df['2PA'] = merged_ps_df['FGA'] - merged_ps_df['FG3A']
        merged_ps_df['2P%'] = (merged_ps_df['2PM'] / merged_ps_df['2PA'] * 100).round(1)

        # Label percentile values with percentage symbols for easy-to-read display
        merged_rs_df[['2P%', 'FG3_PCT', 'FT_PCT']] = merged_rs_df[['2P%', 'FG3_PCT', 'FT_PCT']].applymap(lambda x: f'{x}%')
        merged_ps_df[['2P%', 'FG3_PCT', 'FT_PCT']] = merged_rs_df[['2P%', 'FG3_PCT', 'FT_PCT']].applymap(lambda x: f'{x}%')

        # Remove unwanted columns and rename for cleaner front-end app display
        columns_of_interest = [
            'SEASON_ID', 'TEAM_ABBREVIATION', 'PLAYER_AGE', 'GP', 'GS', 'MIN',
            'PTS', 'REB', 'OREB', 'AST', 'TOV',
            'FG_PCT', '2PM', '2PA', '2P%', 'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT'
        ]
        column_names = [
            'SEASON', 'TEAM', 'AGE', 'GP', 'GS', 'MIN',
            'PTS', 'REB', 'OREB', 'AST', 'TOV',
            'FG%', '2PM', '2PA', '2P%', '3PM', '3PA', '3P%', 'FTM', 'FTA', 'FT%'
        ]
        merged_rs_df = merged_rs_df.rename(columns=dict(zip(columns_of_interest, column_names)))
        merged_rs_df = merged_rs_df[column_names]
        merged_ps_df = merged_ps_df.rename(columns=dict(zip(columns_of_interest, column_names)))
        merged_ps_df = merged_ps_df[column_names]

        return merged_rs_df, merged_ps_df





def main(player_id):

    fetcher = PlayerCareerStatsFetcher()
    career_stats_dfs = fetcher.fetch_career_stats(player_id)
    for df in career_stats_dfs:
        print(df)


if __name__ == '__main__':
    main(2544)  # Test stand-alone functionality with example player ID