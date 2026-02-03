### =========================== SETUP =========================== ###
# Data Acquisition
import PIL.Image
from nba_api.stats.endpoints import shotchartdetail

# Data Management
import numpy as np
import pandas as pd

# Visualization
from io import BytesIO
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from matplotlib.colors import Normalize
import matplotlib.image as mpimg
from matplotlib.patches import Rectangle, Circle, Arc
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import PIL
from PIL import Image
import scipy.ndimage as ndimage
from scipy.ndimage import gaussian_filter
import seaborn as sns
import streamlit as st

# Utils
from IPython.display import display, HTML, IFrame, Image
import json
import os
import sys
import requests
import time
import urllib.request

# Settings
cwd = os.getcwd()
while not cwd.endswith('NBA-Profiler'):
    cwd = os.path.dirname(cwd)
sys.path.append(cwd)

# Define paths (relative to user OS) for files to be used
pwd = os.getcwd()
TEAM_INFO_PATH = os.path.join(cwd, './data/nba_teams.json')
SHOT_FILTER_PARAMS_PATH = os.path.join(cwd, './utils/shot_chart_params.json')
BRICK_IMG_PATH = './utils/images/brick.png'
BUCKET_IMG_PATH = './utils/images/bucket.png'
WOOD1_IMG_PATH = './utils/images/wood1.png'
WOOD2_IMG_PATH = './utils/images/wood2.png'
LOGO_IMG_PATH = './utils/images/sb_logo_dark_no_bg.png'

# Pre-Requisite file loading
with open(TEAM_INFO_PATH, 'r') as f:
    nba_teams = json.load(f)
with open(SHOT_FILTER_PARAMS_PATH, 'r') as f:
    sc_params = json.load(f)

### ============================================================= ###



class ShotChartGenerator:
    """
    Gathers shot data for NBA player based on selected filter(s).
    """


    def __init__(self):
        self.request_interval = 1  # Custom wait-time to avoid API rate limits


    def fetch_total_shot_data(self, player_id, seasons):
        """
        Fetches and compiles shot data for all input seasons.

        Parameters:
        player_id (int): Unique player id number
        seasons (list): List containing strings of seasons of interest (format for each season: 'YYYY-YY'; default: most recent season)

        Returns:
        total_plyr_shot_data (dataframe): DataFrame containing player shot data for entirety of input seasons
        total_league_shot_data (dataframe): DataFrame containing league-wide shot data for entirety of input seasons
        game_log (dataframe): DataFrame containing formatted game dates & location info for front-end usage
        """

        total_plyr_shot_data = pd.DataFrame()
        total_league_shot_data = pd.DataFrame()

        # Iterate through each season and gather necessary data
        for season in seasons:

            ### REGULAR-SEASON SHOT DATA
            rs_shot_data = shotchartdetail.ShotChartDetail(
                player_id=player_id,
                team_id=0,
                season_nullable=season,
                season_type_all_star='Regular Season',
                context_measure_simple='FGA',
            ).get_data_frames()
            rs_plyr_shot_data, rs_league_shot_data = rs_shot_data[0], rs_shot_data[1]

            rs_plyr_shot_data['SEASON'], rs_league_shot_data['SEASON'] = season, season
            total_plyr_shot_data = pd.concat([total_plyr_shot_data, rs_plyr_shot_data], ignore_index=True)
            total_league_shot_data = pd.concat([total_league_shot_data, rs_league_shot_data], ignore_index=True)
            time.sleep(self.request_interval)  # OPTIONAL

        # Combine multiple seasons into single aggregate to use for hex-bin comparisons
        total_league_shot_data = self._aggregate_league_data(total_league_shot_data)

        # Extract game logs from the total played games to display as user-select options on front-end
        game_log = self._extract_game_log(total_plyr_shot_data)

        return total_plyr_shot_data, total_league_shot_data, game_log


    def fetch_filtered_shot_data(self, player_id, seasons, filters):
        """
        Fetches and compiles shot data for all input options.

        Parameters:
        player_id (int): Unique player id number
        seasons (list): List containing strings of seasons of interest (format for each season: 'YYYY-YY'; default: most recent season)
        filters (dict): Filter selections from front-end user input

        Returns:
        filtered_plyr_shot_data (dataframe): DataFrame containing filtered player shot data for all input restrictions
        filtered_league_shot_data (dataframe): DataFrame containing filtered league-wide shot data for all input restrictions
        """

        filtered_plyr_shot_data = pd.DataFrame()
        filtered_league_shot_data = pd.DataFrame()

        filter_params = self._parse_filters(filters)

        # Iterate through each season and gather necessary data
        for season in seasons:

            shot_data = shotchartdetail.ShotChartDetail(
                player_id=player_id,
                context_measure_simple='FGA',
                season_nullable=season,
                team_id=0,
                **filter_params
            ).get_data_frames()
            plyr_shot_data, league_shot_data = shot_data[0], shot_data[1]

            plyr_shot_data['SEASON'], league_shot_data['SEASON'] = season, season
            filtered_plyr_shot_data = pd.concat([filtered_plyr_shot_data, plyr_shot_data], ignore_index=True)
            filtered_league_shot_data = pd.concat([filtered_league_shot_data, league_shot_data], ignore_index=True)
            time.sleep(self.request_interval)  # OPTIONAL

        # Combine multiple seasons into single aggregate to use for hex-bin comparisons
        filtered_league_shot_data = self._aggregate_league_data(filtered_league_shot_data)

        return filtered_plyr_shot_data, filtered_league_shot_data


    def plot_shot_data(self, player_id, plyr_shot_data, league_shot_data, plot_type='Make/Miss [V1]', team_colors=['#28282B', '#28282B']):
        """
        Generates shot chart for input shot data.

        Parameters:
        plyr_shot_data (dataframe): DataFrame containing player shot records-of-interest
        league_shot_data (dataframe): DataFrame containing league shot records-of-interest
        plot_type (str): Plot style preference
        team_colors (list): List of player's team colors for personalization

        Returns:
        fig (MatPlotLib figure): Shot-chart figure based on input data
        """

        # Output error message if selected filters yielded no data
        if plyr_shot_data.empty:
            return st.error(f'No shot data available for the selected filters.'), st.stop()

        # Initialize court figure
        ax = self._draw_court(player_id, team_colors)


        ### STANDARD MAKE / MISS VERSION
        if plot_type == 'Make/Miss [V1]':
            size_factor = 1 if len(plyr_shot_data) < 30 else 0.5
            sns.scatterplot(
                data=plyr_shot_data,
                x='LOC_X',
                y='LOC_Y',
                hue='SHOT_MADE_FLAG',
                style='SHOT_MADE_FLAG',
                palette={0: 'red', 1: 'green'},
                markers={0: (4, 1, 45), 1: (8, 0, 45)},
                size='SHOT_MADE_FLAG',
                sizes={0: 200 * size_factor, 1: 100 * size_factor},
                alpha=0.6,
                ax=ax
            )

            ax.get_legend().remove()

        ### ALTERNATIVE MAKE / MISS VERSION
        elif plot_type == 'Make/Miss [V2]':
            make_marker = mpimg.imread(BUCKET_IMG_PATH)
            miss_marker = mpimg.imread(BRICK_IMG_PATH)

            for _, row in plyr_shot_data.iterrows():
                x, y, made = row['LOC_X'], row['LOC_Y'], row['SHOT_MADE_FLAG']
                img = make_marker if made == 1 else miss_marker
                im = OffsetImage(img, zoom=0.025)
                ab = AnnotationBbox(im, (x, y), frameon=False)
                ax.add_artist(ab)


        ### HEX-BIN VERSION
        elif plot_type == 'Hex-Bin [V1]':

            # Create a hexbin plot for shot data with color based on FG% and size based on frequency
            # Calculate shooting percentage for each hexbin
            # We need to get the x, y, and shot made data
            shot_data = plyr_shot_data[['LOC_X', 'LOC_Y', 'SHOT_MADE_FLAG']]

            # Compute the hexbin grid
            hb = ax.hexbin(
                shot_data['LOC_X'],
                shot_data['LOC_Y'],
                gridsize=30,  # You can adjust the grid size as necessary
                cmap='Blues',  # Color map for FG% (you can adjust this to suit your preference)
                mincnt=1  # Avoid empty hexagons
            )

            # Calculate the shooting percentage (FG%)
            fg_percentage = shot_data.groupby([shot_data['LOC_X'], shot_data['LOC_Y']])['SHOT_MADE_FLAG'].mean()

            # Normalize the frequency for sizing the hexagons
            frequency = shot_data.groupby([shot_data['LOC_X'], shot_data['LOC_Y']]).size()

            # Loop over each hexbin to adjust the color based on FG% and size based on frequency
            for (x, y), fg_pct in fg_percentage.items():
                hex_color = plt.cm.YlGnBu(fg_pct)  # Apply the color map
                hex_size = frequency[(x, y)] * 10  # Scale size by frequency (adjust multiplier if necessary)
                ax.scatter(x, y, s=hex_size, c=[hex_color], alpha=0.6, edgecolors="none", marker='o')

            # Add colorbar for shooting percentage (FG%)
            # cb = plt.colorbar(hb.collections[0], ax=ax)
            # cb.set_label('Shooting Percentage')


            # ax.get_legend().remove()

            # # Compute the league average field goal percentage
            # league_avg_fg_pct = league_shot_data.groupby(
            #     ['SHOT_ZONE_BASIC', 'SHOT_ZONE_AREA', 'SHOT_ZONE_RANGE']
            # ).apply(lambda group: group['FGM'].sum() / group['FGA'].sum()).reset_index()
            # league_avg_fg_pct.columns = ['SHOT_ZONE_BASIC', 'SHOT_ZONE_AREA', 'SHOT_ZONE_RANGE', 'LEAGUE_FG_PCT']

            # # Merge player data with league averages for comparison
            # plyr_shot_data = plyr_shot_data.merge(
            #     league_avg_fg_pct,
            #     on=['SHOT_ZONE_BASIC', 'SHOT_ZONE_AREA', 'SHOT_ZONE_RANGE'],
            #     how='left'
            # )
            # plyr_shot_data['FG_DIFF'] = plyr_shot_data['SHOT_MADE_FLAG'] - plyr_shot_data['LEAGUE_FG_PCT']

            # # Calculate shot frequency for bin sizes
            # hexbin_counts, xedges, yedges = np.histogram2d(
            #     plyr_shot_data['LOC_X'], plyr_shot_data['LOC_Y'], bins=30
            # )
            # hexbin_size = hexbin_counts.flatten()

            # # Plot hexbin with color indicating FG% vs league average
            # hexbin = ax.hexbin(
            #     plyr_shot_data['LOC_X'],
            #     plyr_shot_data['LOC_Y'],
            #     gridsize=30,
            #     C=plyr_shot_data['FG_DIFF'],
            #     cmap='coolwarm',
            #     norm=Normalize(vmin=-0.15, vmax=0.15),
            #     mincnt=1,
            #     reduce_C_function=np.mean,
            #     edgecolors='none',
            #     alpha=0.8
            # )

            # # Adjust bin sizes to reflect shot frequency
            # for collection in hexbin.collections:
            #     collection.set_array(hexbin_size)

            # # Add colorbar for FG% vs league average
            # cbar = plt.colorbar(hexbin, ax=ax, orientation='horizontal')
            # cbar.set_label('FG% vs League Avg (±%)', rotation=0, labelpad=5)
            # cbar.ax.tick_params(labelsize=8)

            # # Add a color scale for the shot frequency (size of bins)
            # freq_cbar = ax.figure.colorbar(hexbin, ax=ax, orientation='vertical')
            # freq_cbar.set_label('Shot Frequency', rotation=270, labelpad=10)

        return ax


    def _aggregate_league_data(self, league_shot_data):
        """
        Combines league shot data from multiple seasons (for each shot type combination) for hex-bin usage.

        Parameters:
        league_shot_data (dataframe): DataFrame containing compiled league-wide data

        Returns:
        aggregated_league_shot_data (dataframe): DataFrame containing combined league-wide shot data for all seasons
        """

        aggregated_league_shot_data = (league_shot_data.groupby(
            ['SHOT_ZONE_BASIC', 'SHOT_ZONE_AREA', 'SHOT_ZONE_RANGE']).agg({
                'FGA': 'mean', 'FGM': 'mean','FG_PCT': 'mean'}).reset_index())

        return aggregated_league_shot_data


    def _extract_game_log(self, player_shot_data):
        """
        Extracts player games and dates from retrieved shot data, without needing extra API call.

        Parameters:
        player_shot_data (dataframe): DataFrame containing player shot data

        Returns:
        game_log (dataframe): DataFrame containing formatted game dates & location info for front-end usage
        """

        # Retrieve columns relevant to the game location, date, and teams playing
        game_log = player_shot_data[['TEAM_NAME', 'GAME_DATE', 'HTM', 'VTM']].copy()

        # Keep single record for each game
        game_log = game_log.drop_duplicates(subset='GAME_DATE', keep='first')

        # Convert full team name to abbreviation (standardized with HTM and VTM)
        game_log['TEAM_ABBV'] = game_log['TEAM_NAME'].map({v: k for k, v in nba_teams['TEAM_NAMES'].items()})

        # Re-order data with recent dates first, and convert dates into parameter-acceptable format
        game_log = game_log.sort_values(by='GAME_DATE', ascending=False).reset_index(drop=True)
        game_log['DISPLAY_OPTION'] = game_log['GAME_DATE'].apply(lambda x: x[4:6] + '/' + x[6:])
        game_log['GAME_DATE'] = game_log['GAME_DATE'].apply(lambda x: x[0:4] + '-' + x[4:6] + '-' + x[6:])

        # Format opponent and game location info into the display option column & remove old columns
        game_log['DISPLAY_OPTION'] = np.where(
            game_log['TEAM_ABBV'] == game_log['HTM'],                # If player's team is HOME TEAM
            game_log['DISPLAY_OPTION'] + ' vs. ' + game_log['VTM'],  # Add AWAY TEAM as opponent
            game_log['DISPLAY_OPTION'] + ' @ ' + game_log['HTM']     # Otherwise, add HOME TEAM as opponent
        )
        game_log = game_log[['GAME_DATE', 'DISPLAY_OPTION']]

        return game_log


    def _parse_filters(self, filters):
        """
        Parses through the input filter selections and maps to API-compatible parameters.

        Parameters:
        filters (dict): Dict of filter names and input filter selections

        Returns:
        parsed_filters (dict): API-compatible parameter names and corresponding values
        """

        parsed_filters = {}

        for filter_name, selected_value in filters.items():

            # Only parse filter if a user-selection was made
            if selected_value != None:

                # Handle dates separately (not part of shot_chart_params.json)
                if filter_name == 'selected_start':
                    parsed_filters['date_from_nullable'] = selected_value
                elif filter_name == 'selected_end':
                    parsed_filters['date_to_nullable'] = selected_value

                # Translate other filter selections to API-compatible versions using pre-made conversion doc
                else:
                    api_param_name = sc_params[filter_name][selected_value][0]
                    api_value = sc_params[filter_name][selected_value][1]
                    parsed_filters[api_param_name] = api_value

        return parsed_filters


    def _draw_court(self, player_id, team_colors, court_color='white', line_color='black', line_width=1, title=None):
        """
        Draws a half-court basketball court for shot chart visualization.

        Parameters:
        team_colors (list): List of player's team colors for personalization
        court_color (str): Color preference for main court
        line_color (str): Color preference for border lines
        line_width (int): Preference for border line widths
        title (str): Optional title for the visual

        Returns:
        ax (mpl ax): Matplotlib Axis object with applied court design

        Notes:
        - Measured inches were scaled down by 1.2 to appropriately match in MatPlotLib
        - All painted lines on the court are 2 in. wide
        """

        fig, ax = plt.subplots(figsize=(11, 10.34))  # Half-Court Size: 50'x47'

        # RESTRICTED AREA
        hoop = Circle((0, 0), radius=7.5, linewidth=2, color=line_color, fill=False)  # Hoop center set as origin; Radius: 9"
        backboard = Rectangle((-30, -12.5), 60, 0, linewidth=2, color=line_color)  # Backboard 15" behind origin; Length: 72"
        hoop_bb_connector = Rectangle((0, -12.5), 0, 5, linewidth=6, color=line_color)  # OPTIONAL connector element
        ra_arc = Arc((0, 0), 80, 80, theta1=0, theta2=180, linewidth=line_width, color=line_color)  # Arc Radius from origin: 96"
        ra_left = Rectangle((-40, -12.5), 0, 12.5, linewidth=line_width, color=line_color)  # OPTIONAL line to close out till backboard
        ra_right = Rectangle((40, -12.5), 0, 12.5, linewidth=line_width, color=line_color)  # OPTIONAL line to close out till backboard

        # PAINT AREA
        outer_box = Rectangle((-80, -52.5), 160, 190, linewidth=line_width, edgecolor=line_color, facecolor='none', fill=False)  # Paint starts 63" behind origin; Size: 16'x19'
        ft_outer_arc = Arc((0, 137.5), 120, 120, theta1=0, theta2=180, linewidth=line_width, color=line_color, fill=False)  # Paint ends 165" from origin
        ft_inner_arc = Arc((0, 137.5), 120, 120, theta1=180, theta2=0, linewidth=line_width, color=line_color, linestyle=(0, (25, 15)))  # Paint ends 165" from origin

        # THREE-POINT LINE
        left_corner = Rectangle((-220, -52.5), 0, 142, linewidth=line_width, color=line_color)  # 3-PT Corner line is 22' from origin; Length: 14' (142 used for cleaner fit / compensate MatPlotLib discrepancies)
        right_corner = Rectangle((220, -52.5), 0, 141, linewidth=line_width, color=line_color)  # 3-PT Corner line is 22' from origin; Length: 14'
        three_arc = Arc((0, 0), 475, 475, theta1=21.9, theta2=157.75, linewidth=line_width, color=line_color)  # ATB 3-PT arc is 23'9" (or 285") from origin (so arc diameter is 570")

        # OUTER SEGMENTS (court borders)
        court_border = Rectangle((-250, -52.5), 500, 470, linewidth=line_width, edgecolor='black', fill=False)  # Half-Court Size: 50'x47'
        half_court_outer_arc = Arc((0, 417.5), 120, 120, theta1=180, theta2=0, linewidth=line_width, color=line_color)  # Half-Court Outer arc Radius: 6'
        half_court_inner_arc = Arc((0, 417.5), 40, 40, theta1=180, theta2=0, linewidth=0, color=line_color)  # Half-Court Inner arc Radius: 2'
        left_throw_in_line = Rectangle((-250, 227.5), 30, 0, linewidth=line_width, color=line_color)  # 28' from end; Length: 3'
        right_throw_in_line = Rectangle((250, 227.5), -30, 0, linewidth=line_width, color=line_color)  # 28' from end; Length: 3'

        # Add elements to the ax
        court_patches = [court_border, outer_box, hoop, backboard, ra_arc, ft_outer_arc, ft_inner_arc, left_throw_in_line, right_throw_in_line,
                        left_corner, right_corner, three_arc, half_court_outer_arc, half_court_inner_arc, hoop_bb_connector, ra_left, ra_right]
        for patch in court_patches:
            ax.add_patch(patch)

        # Load textures and logo images
        wood_texture_one = mpimg.imread(WOOD1_IMG_PATH)
        wood_texture_two = mpimg.imread(WOOD2_IMG_PATH)
        wood_texture_one = ndimage.rotate(wood_texture_one, 90)
        wood_texture_two = ndimage.rotate(wood_texture_two, 90)
        sb_logo_dark = mpimg.imread(LOGO_IMG_PATH)
        sb_logo_dark = np.flipud(sb_logo_dark)

        outer_shade, outer_alpha = wood_texture_one, 0.25
        midrange_shade, midrange_alpha = wood_texture_one, 0.6
        paint_shade, paint_alpha = wood_texture_two, 0.4

        # Apply textures and logo onto court
        ax.imshow(midrange_shade, extent=[-250, 250, -52.5, 417.5], alpha=midrange_alpha, aspect='auto')
        ax.imshow(paint_shade, extent=[-80, 80, -52.5, 137.5], alpha=paint_alpha, aspect='auto')
        ax.imshow(sb_logo_dark, extent=[-60, 60, 358.5, 417.5], alpha=1, aspect='auto')

        # Create high-resolution binary masks for three-point line and court areas
        resolution = 300
        x = np.linspace(-250, 250, resolution)
        y = np.linspace(-52.5, 417.5, resolution)
        xv, yv = np.meshgrid(x, y)
        distance_from_center = np.sqrt(xv**2 + yv**2)

        # Create a strict binary mask (no gradient) for areas outside the three-point arc
        three_point_radius = 475/2
        mask_arc = distance_from_center > three_point_radius

        # Create binary mask for left corner (to the left of -220, extend it along baseline)
        left_corner_x = -220
        mask_left = xv < left_corner_x

        # Create binary mask for right corner (to the right of +220, extend it along baseline)
        right_corner_x = 220
        mask_right = xv > right_corner_x

        # Combine all masks (arc + left corner + right corner)
        combined_mask = mask_arc | mask_left | mask_right

        # Resize the wood texture to match the mask resolution
        wood_texture_resized = ndimage.zoom(outer_shade, (resolution / outer_shade.shape[0], resolution / outer_shade.shape[1], 1))

        # Apply the binary mask to the resized texture
        wood_texture_masked = np.copy(wood_texture_resized)
        for c in range(wood_texture_masked.shape[2]):
            wood_texture_masked[:, :, c] *= combined_mask

        # Flip the masked texture vertically to match the inverted y-axis
        wood_texture_masked = np.flipud(wood_texture_masked)

        # Plot the masked texture
        ax.imshow(wood_texture_masked, extent=[-250, 250, -52.5, 417.5], alpha=outer_alpha, aspect='auto')


        ### PLOT SPECIFICATIONS

        # Dimensions for the court and the border
        xlim_a, xlim_b, ylim_a, ylim_b = -250-15, 250+15, -52.5-15, 417.5+15

        # Convert team colors to RGBA
        start_color_rgba, end_color_rgba = mcolors.to_rgba(team_colors[0]), mcolors.to_rgba(team_colors[1])

        # Set up gradient image and interpolate across RGBA channels
        gradient = np.linspace(0, 1, 500).reshape(1, -1)
        transition_point = 0.75
        gradient[:,:int(500 * transition_point)] = 0
        gradient[:,int(500 * transition_point):] = np.linspace(0, 1, 500 - int(500 * transition_point)).reshape(1, -1)
        gradient_image = np.ones((1, 500, 4))
        for i in range(4):
            gradient_image[:, :, i] = gradient * end_color_rgba[i] + (1 - gradient) * start_color_rgba[i]

        # Output border image
        ax.imshow(gradient_image,extent=[xlim_a, 251, ylim_a, -52.5], aspect='auto', alpha=1, zorder=0)
        ax.imshow(gradient_image,extent=[xlim_a, 251, 417.5, ylim_b], aspect='auto', alpha=1, zorder=0)

        # Add non-gradient borders and finalize specifications
        plt.xlim(xlim_a, xlim_b)
        plt.ylim(ylim_a, ylim_b)
        plt.fill_betweenx((ylim_a, ylim_b-0.5), xlim_a, -251 , color=team_colors[0], alpha=1)
        plt.fill_betweenx((ylim_a, ylim_b-0.5), 251, xlim_b, color=team_colors[1], alpha=1)
        plt.axis('off')
        plt.gca().invert_yaxis()
        if title:
            plt.title(title, fontsize=16)

        # Add player photo [OPTIONAL]
        req = requests.get(f'https://cdn.nba.com/headshots/nba/latest/260x190/{player_id}.png')
        player_image = PIL.Image.open(BytesIO(req.content)).rotate(180).transpose(PIL.Image.FLIP_LEFT_RIGHT)
        ax.imshow(player_image, extent=[-265, -120, 320.5, 432.5], aspect='auto', zorder=2)

        return ax





def main(player_id, seasons=[None]):

    SCG = ShotChartGenerator()
    shot_data, league_data, game_log = SCG.fetch_total_shot_data(player_id=player_id, seasons=seasons)
    ax = SCG.plot_shot_data(shot_data, league_data, plot_type='Make/Miss [V1]')
    plt.show()

if __name__ == '__main__':
    main(2544, ['2022-23'])  # Test stand-alone functionality with example player ID