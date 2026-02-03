### ===================================== SETUP ===================================== ###
### ================================================================================= ###

# Data Source
from nba_api.stats.static import players

# Data Management
import json
import numpy as np
import pandas as pd

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from streamlit.components.v1 import html
from st_tabs import TabBar

# Project Modules
from submodules.pp_fetch_bio_info import PlayerInfoFetcher
from submodules.pp_scrape_bio_desc import PlayerBioScraper
from submodules.pp_fetch_off_stats import PlayerCareerStatsFetcher
from submodules.pp_generate_shot_charts import ShotChartGenerator
from utils.pp_md_templates import get_welcome_pg_html, progress_tracker, get_pp_header_html, get_pp_tab_html, get_player_bio_subtitle
from utils.pp_md_templates import get_pp_bio_leftcol_html, get_pp_bio_rightcol_html, get_pp_tab_header, highlight_border_selected_rows

# Utils
from IPython.display import display, HTML, IFrame, Image
import os
import requests
import sys
import time

# Settings
st.set_page_config(
    page_title='NBA Profiler',
    page_icon=':sun:',
    layout='wide',
    initial_sidebar_state='expanded',
    # menu_items={
    #     'Get Help': 'https://www.finalwebsitename.com/help',
    #     'Report a bug': 'https://www.finalwebsitename.com/bug',
    #     'About': ''
    # }
)
st.markdown(
    """
    <style>
        * {
        overflow-anchor: none !important;
        }
    </style>""",
    unsafe_allow_html=True
)
cwd = os.getcwd()
while not cwd.endswith('NBA-Profiler'):
    cwd = os.path.dirname(cwd)
sys.path.append(cwd)

# Define paths (relative to user OS) for files to be used
LOGO_PATH = os.path.join(cwd, './utils/images/sb_logo_dark_no_bg.png')
SHOT_FILTER_PARAMS_PATH = os.path.join(cwd, './utils/shot_chart_params.json')
STATIC_PLAYER_DATA_PATH = os.path.join(cwd, './data/static_player_data.pkl')
TEAM_INFO_PATH = os.path.join(cwd, './data/nba_teams.json')

# Pre-Requisite file loading
with open(TEAM_INFO_PATH, 'r') as f:
    nba_teams = json.load(f)
with open(SHOT_FILTER_PARAMS_PATH, 'r') as f:
    sc_params = json.load(f)
static_player_data = pd.read_pickle(STATIC_PLAYER_DATA_PATH)


### CACHED FUNCTIONS -- SEE SUBMODULES FOR DETAILED IMPLEMENTATIONS

@st.cache_data
def fetch_player_info(player_id):
    return PlayerInfoFetcher().fetch_player_info(player_id)

@st.cache_data
def fetch_player_awards(player_id):
    return PlayerInfoFetcher().fetch_player_awards(player_id)

@st.cache_data
def fetch_player_bio(player_id):
    return PlayerBioScraper().fetch_player_bio(player_id)

@st.cache_data
def fetch_career_stats(player_id):
    return PlayerCareerStatsFetcher().fetch_career_stats(player_id)

@st.cache_data
def fetch_total_shot_data(player_id, seasons):
    return ShotChartGenerator().fetch_total_shot_data(player_id, seasons)

### ================================================================================= ###
### ================================================================================= ###





### =========================== BASE-PAGE CONFIGURATIONS =========================== ###
### ================================================================================= ###

# Set up logo on top of the side panel
st.sidebar.markdown('<div style="padding-top: 40px;"></div>', unsafe_allow_html=True)  # Spacing
st.sidebar.image(LOGO_PATH, width=200)

# Set up tool selection box in the side panel
st.sidebar.title('**Launch an app:**')
tool = st.sidebar.selectbox(
    'Player | Lineup | Team | Game',
    ['', 'Player Profiler', 'Lineup Profiler', 'Team Profiler', 'Game Profiler'],
)

# Configure welcome page when tool not selected yet
if tool == '':

    ### WELCOME PAGE
    @st.fragment
    def config_base_page():

        # Retrieve custom HTML instructions and load into welcome page
        title_mkdwn, welcome_msg_mkdwn = get_welcome_pg_html()  # SEE SUBMODULE 'pp_md_templates.py' FOR DETAILS
        st.markdown(title_mkdwn, unsafe_allow_html=True)
        st.markdown(welcome_msg_mkdwn, unsafe_allow_html=True)

        ### (TEMP) Design a progress bar for users to track project in its journey -- To Be Deleted!!
        st.title('')
        st.write('(PROGRESS TRACKER -- TEMP USE ONLY)')
        for tool, details in progress_tracker.items():
            if details['Completed']:
                st.markdown(f'✅ **{tool}** - Ready to use!')
            else:
                st.markdown(f'🔲 **{tool}** - In Progress ⏳')
            for subsection, status in details['Subsections'].items():
                if status:
                    st.markdown(f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;✅ {subsection}')
                else:
                    st.markdown(f'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🚧 {subsection}')
            if not details['Completed']:
                progress = sum(1 for status in details['Subsections'].values() if status) / len(details['Subsections'])
                st.progress(progress)
    config_base_page()

### ================================================================================= ###
### ================================================================================= ###





### ============================== PLAYER PROFILE TOOL ============================== ###
### ================================================================================= ###

if tool == 'Player Profiler':

    # Retrieve sorted list of active NBA players and set up user options
    active_players_df = pd.DataFrame(players.get_active_players())  # STATIC API
    player_names = active_players_df.sort_values('first_name', ascending=True)['full_name'].tolist()
    selected_player = st.sidebar.selectbox('Select an active player:', options=[''] + player_names)

    # Set up sequence of events after user selects a player
    if selected_player:

        # Retrieve selected player's ID from STATIC API
        player_id = active_players_df.loc[active_players_df['full_name'] == selected_player, 'id'].values[0]

        # If static data available, retrieve bio info for selected player (SEE UTILITY NOTEBOOK 'generate_static_data.ipynb' FOR DETAILS)
        if player_id in static_player_data.id.values:
            player_info = static_player_data.loc[static_player_data.id == player_id, 'player_info'].iloc[0]
            player_awards = pd.DataFrame(json.loads(static_player_data.loc[static_player_data.id == player_id, 'player_awards'].iloc[0]))
            bio_desc = static_player_data.loc[static_player_data.id == player_id, 'player_bio_desc'].iloc[0]

        # If static data unavailable, use API sources (SEE SUBMODULES 'pp_fetch_bio_info.py' & 'pp_scrape_bio_desc.py' FOR DETAILS)
        else:
            player_info = fetch_player_info(player_id)
            player_awards = fetch_player_awards(player_id)
            bio_desc = fetch_player_bio(player_id)

        team_colors = player_info['current_team_colors']  # To be used for color scheme in app design

        # Generate a profile header with desired elements and custom markdown
        pp_md_header_content = get_pp_header_html(player_id, player_info, player_awards)  # SEE SUBMODULE 'pp_md_templates.py' FOR DETAILS
        st.markdown(pp_md_header_content, unsafe_allow_html=True)

        # Set up distinct tabs for each exploration, with custom markdown
        tabs = st.tabs(['**PLAYER BIO**', '**OFFENSIVE PROFILE**', '**DEFENSIVE PROFILE**', '**PLAYER EVOLUTION**', '**PLAYER INSIGHTS**'])
        pp_md_tab_content = get_pp_tab_html(team_colors)  # SEE SUBMODULE 'pp_md_templates.py' FOR DETAILS
        st.markdown(pp_md_tab_content, unsafe_allow_html=True)

        # Retrieve available seasons for selected player (with missing-case handling) and set up user options (default=latest)
        season_options = player_info['played_seasons']
        if season_options == [] or player_info['no_playdata_available'] == True:
            st.error(f'{selected_player} has not played any official games yet. \
                    This page will automatically update when there is sufficient data. \n\nPlease select another player.')
            st.stop()
        selected_seasons = st.sidebar.multiselect('Select one or more seasons:', options=season_options, default=[season_options[0]])

        # Finishing sidebar touches
        st.sidebar.markdown('<div style="margin-top: 0px; padding-bottom: 0px"></div>', unsafe_allow_html=True)  # Spacing
        st.sidebar.markdown('<hr style="border-top: 2px solid #333; margin-top: 3px;">', unsafe_allow_html=True)
        st.sidebar.write(f'Navigate through the tabs to uncover {selected_player}\'s on-court profile.')
        st.sidebar.markdown('<small style="font-family: sans-serif; font-size: 9px; color: #000000;">'
            '*DATA SOURCE: NBA-API | SYNERGY*''</small>', unsafe_allow_html=True)

        ### DEBUG MODE -- TO BE DELETED(?)
        st.sidebar.markdown('<div style="padding-top: 750px; padding-bottom: 0px"></div>', unsafe_allow_html=True)  # Spacing
        if st.sidebar.button('Clear Cache & Refresh Stats', width=200):
            st.cache_data.clear()  # Clears all st.cache_data decorators
            st.cache_resource.clear()  # Clears all st.cache_resource decorators



        # Set up sequence of events after user/auto selects season(s)
        if selected_seasons:

            ### ============================== BIO TAB ============================== ###
            ### ===================================================================== ###
            with tabs[0]:

                @st.fragment
                def config_pp_bio_tab():

                    # Separate column containers in the PLAYER BIO tab
                    left_bio_col, middle_bio_col, right_bio_col = st.columns([1, 2, 1])

                    # Designate left column for basic player info
                    with left_bio_col:
                        pp_md_bio_leftcol_content = get_pp_bio_leftcol_html(player_info)  # SEE SUBMODULE 'pp_md_templates.py' FOR DETAILS
                        st.markdown(pp_md_bio_leftcol_content, unsafe_allow_html=True)

                    # Designate right column for player awards
                    with right_bio_col:
                        pp_md_bio_rightcol_content = get_pp_bio_rightcol_html(player_awards, team_colors)  # SEE SUBMODULE 'pp_md_templates.py' FOR DETAILS
                        st.markdown(pp_md_bio_rightcol_content, unsafe_allow_html=True)

                    # Designate middle column for section name and NBA's official player bio description
                    with middle_bio_col:

                        # Section Banner
                        pp_md_bio_title_content = get_player_bio_subtitle(team_colors, player_info['first_name'])  # SEE SUBMODULE 'pp_md_templates.py' FOR DETAILS
                        st.markdown(pp_md_bio_title_content, unsafe_allow_html=True)
                        st.markdown('<div style="padding-top: 15px;"></div>', unsafe_allow_html=True)  # Spacing

                        # Section Content
                        html(bio_desc, height=1085, scrolling=True)

                config_pp_bio_tab()


            ### ============================== OP TAB ============================== ###
            ### ==================================================================== ###
            with tabs[1]:

                # Output section title/header
                pp_op_header_html = get_pp_tab_header('OFFENSIVE PROFILE', team_colors)  # SEE SUBMODULE 'pp_md_templates.py' FOR DETAILS
                st.markdown(pp_op_header_html, unsafe_allow_html=True)


                ### CAREER OVERVIEW TABLE ###
                ### ===================== ###

                @st.fragment
                def config_pp_career_table():

                    # Retrieve offensive career (per-game, per-36) statistics (SEE SUBMODULE 'pp_fetch_off_stats.py' FOR DETAILS)
                    per_game_rs_df, per_game_ps_df, per_36_rs_df, per_36_ps_df = fetch_career_stats(player_id)

                    with st.expander('Career Overview', expanded=True, ):
                        # Create columns to designate dropdown menus on the side and chart title in the middle
                        col1, col2, col3 = st.columns([1, 2, 1])
                        with col1:
                            selected_season_segment = st.selectbox('Season Segment', ['Regular-Season', 'Post-Season'], index=0)  # Season-Type Selection
                        with col2:
                            st.markdown('<h4 style="text-align: center;">Career Overview</h4>', unsafe_allow_html=True)  # Subsection Title
                        with col3:
                            selected_per_mode = st.selectbox('Per-Basis', ['Per-Game', 'Per-36-Minutes'], index=0)  # Per-Mode Selection

                        # Display the selected DataFrame based on user selections
                        career_dfs = {
                            ('Regular-Season', 'Per-Game'): per_game_rs_df, ('Regular-Season', 'Per-36-Minutes'): per_36_rs_df,
                            ('Post-Season', 'Per-Game'): per_game_ps_df, ('Post-Season', 'Per-36-Minutes'): per_36_ps_df,
                        }
                        selected_df = career_dfs.get((selected_season_segment, selected_per_mode))
                        if selected_df is not None:
                            st.dataframe(highlight_border_selected_rows(selected_df, 'SEASON', 'TOTAL'), hide_index=True)

                    st.markdown(f"""<div style="height: 9px; background: linear-gradient(90deg, {team_colors[0]} 70%, {team_colors[1]} 98%);
                                border-radius: 12px; margin-top: 10px; margin-bottom: 16px"></div>""", unsafe_allow_html=True)

                config_pp_career_table()


                ### SHOT CHART & SCORING ###
                ### ==================== ###
                # FUTURE TO-DO:  ADV GAME CONTEXT |  # point_diff_nullable   # context_filter_nullable

                @st.fragment
                def config_pp_scoring_prof():

                    # Gather baseline shot data w/o any adv filters (SEE SUBMODULES 'pp_generate_shot_charts.py' FOR DETAILS)
                    total_plyr_shot_data, total_league_shot_data, game_log = fetch_total_shot_data(player_id, selected_seasons)

                    # Set up subsection title and high-level button setup in columns
                    st.markdown('<h4 style="text-align: center;">Scoring Profile</h4>', unsafe_allow_html=True)
                    st.markdown('<div style="margin-bottom: 0px;"></div>', unsafe_allow_html=True)  # Spacing

                    # Set up filter options
                    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])

                    with col1:
                        selected_szn_segment = st.selectbox('Season Segment', list(sc_params['selected_szn_segment'].keys()), index=0)
                        selected_location = st.selectbox('Game Location', list(sc_params['selected_location'].keys()), index=None,  placeholder='-all locations-')

                    with col2:
                        selected_start = st.selectbox('Start Date', game_log['DISPLAY_OPTION'].tolist(), index=None, placeholder='-all games-')
                        selected_game_segment = st.selectbox('Game Segment', list(sc_params['selected_game_segment'].keys()), index=None, placeholder='-all segments-')

                    with col3:
                        if selected_start:
                            selected_end = st.selectbox('End Date', game_log['DISPLAY_OPTION'].tolist(), index=game_log['DISPLAY_OPTION'].tolist().index(selected_start))
                        else:
                            selected_end = st.selectbox('End Date', game_log['DISPLAY_OPTION'].tolist(), index=None, placeholder='-all games-')
                        selected_game_situation = st.selectbox('Game Situation', list(sc_params['selected_game_situation'].keys()), index=None, placeholder='-all situations-')

                    with col4:
                        selected_opp = st.selectbox('Opponent', list(sc_params['selected_opp'].keys()), index=None, placeholder='-all teams-')
                        selected_outcome = st.selectbox('Game Outcome', list(sc_params['selected_outcome'].keys()), index=None, placeholder='-all outcomes-')

                    col1, col2 = st.columns([3, 1,])

                    with col1:
                        if selected_start and selected_start == selected_end:
                            default_sc_type = 'Make/Miss [V1]'
                        else:
                            default_sc_type = 'Hex-Bin [V1]'
                        selected_sc_type = st.segmented_control('Shot-Chart Type', label_visibility='visible', options=['Make/Miss [V1]', 'Make/Miss [V2]', 'Hex-Bin [V1]', 'Hex-Bin [V2]'], default=default_sc_type)

                    with col2:
                        st.markdown('<div style="margin-top: 19px;"></div>', unsafe_allow_html=True)  # Spacing
                        regenerate_shot_chart = st.button('Apply Filters', type='primary', width=200)

                    # Generate default (cumulative season) shot chart, if button unpressed
                    if not regenerate_shot_chart:
                        ax = ShotChartGenerator().plot_shot_data(player_id, total_plyr_shot_data, total_league_shot_data, selected_sc_type, team_colors)
                        st.pyplot(ax.figure)

                    # Generate filtered shot chart, if button pressed
                    elif regenerate_shot_chart:

                        # Reformat start and end dates with proper versions
                        if selected_start:
                            selected_start = game_log[game_log['DISPLAY_OPTION'] == selected_start]['GAME_DATE'].iloc[0]
                        if selected_end:
                            selected_end = game_log[game_log['DISPLAY_OPTION'] == selected_end]['GAME_DATE'].iloc[0]

                        SCG = ShotChartGenerator()
                        filters = {
                            'selected_szn_segment': selected_szn_segment,
                            'selected_location': selected_location,
                            'selected_start': selected_start,
                            'selected_end': selected_end,
                            'selected_game_segment': selected_game_segment,
                            'selected_game_situation': selected_game_situation,
                            'selected_opp': selected_opp,
                            'selected_outcome': selected_outcome
                        }
                        filtered_plyr_shot_data, filtered_league_shot_data = SCG.fetch_filtered_shot_data(player_id, selected_seasons, filters=filters)

                        ax = SCG.plot_shot_data(player_id, filtered_plyr_shot_data, filtered_league_shot_data, selected_sc_type, team_colors)
                        st.pyplot(ax.figure)

                config_pp_scoring_prof()

















            ### ============================== DP TAB ============================== ###
            ### ==================================================================== ###
            with tabs[2]:

                # Retrieve shot data (SEE SUBMODULE 'pp_fetch_shot_data.py' FOR DETAILS)
                # per_game_rs_df, per_game_ps_df, per_36_rs_df, per_36_ps_df = fetch_career_stats(player_id)

                # Output section title/header
                pp_dp_header_html = get_pp_tab_header('DEFENSIVE PROFILE', team_colors)  # SEE SUBMODULE 'pp_md_templates.py' FOR DETAILS
                st.markdown(pp_dp_header_html, unsafe_allow_html=True)











            ### ============================== PE TAB ============================== ###
            ### ==================================================================== ###
            with tabs[3]:

                # Output section title/header
                pp_pe_header_html = get_pp_tab_header('PLAYER EVOLUTION', team_colors)  # SEE SUBMODULE 'pp_md_templates.py' FOR DETAILS
                st.markdown(pp_pe_header_html, unsafe_allow_html=True)







            ### ============================= MISC TAB ============================= ###
            ### ==================================================================== ###
            with tabs[4]:

                # Output section title/header
                pp_misc_header_html = get_pp_tab_header('PLAYER INSIGHTS', team_colors)  # SEE SUBMODULE 'pp_md_templates.py' FOR DETAILS
                st.markdown(pp_misc_header_html, unsafe_allow_html=True)






### ================================================================================= ###
### ================================================================================= ###





### ============================== LINEUP PROFILE TOOL ============================== ###
### ================================================================================= ###

if tool == 'Lineup Profiler':
    st.markdown("""
        <div style='text-align: left;'>
            <h1 style='font-size: 75px;'>NBA Profiler: Lineups</h1>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("""
        <p style='font-size: 20px;'>
            <br><br>Under Development</p>
    """, unsafe_allow_html=True)

### ================================================================================= ###
### ================================================================================= ###





### =============================== TEAM PROFILE TOOL =============================== ###
### ================================================================================= ###

if tool == 'Team Profiler':
    st.markdown("""
        <div style='text-align: left;'>
            <h1 style='font-size: 75px;'>NBA Profiler: Teams</h1>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("""
        <p style='font-size: 20px;'>
            <br><br>Under Development</p>
    """, unsafe_allow_html=True)

### ================================================================================= ###
### ================================================================================= ###





### =============================== GAME SUMMARY TOOL =============================== ###
### ================================================================================= ###



### ================================================================================= ###
### ================================================================================= ###
