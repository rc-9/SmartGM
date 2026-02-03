### =========================== SETUP =========================== ###

# Data Acquisition
import requests
from bs4 import BeautifulSoup

# Utils
import time

### ============================================================= ###



class PlayerBioScraper:
    """
    Extracts player bio for application display.
    """


    def __init__(self):
        self.base_url = 'https://www.nba.com/player/{}/bio'  # base URL for player bio webpage
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'
        }
        self.request_interval = 0.5  # Custom wait-time to avoid API rate limits


    def fetch_player_bio(self, player_id):
        """
        Scrapes the bio description from the league webpage for a given player ID.

        Parameters:
        - player_id (int): Unique NBA player ID

        Returns:
        - bio_info (str): Bio description or an empty string if not found
        """

        try:

            # Construct the player's bio URL and send GET request
            time.sleep(self.request_interval)  # OPTIONAL (buffer for any previous request)
            url = self.base_url.format(player_id)
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()  # Raise error for bad HTTP responses

            # Parse the response HTML and locate the bio section
            soup = BeautifulSoup(response.text, 'html.parser')
            bio_section = soup.find('div', class_='PlayerBio_player_bio__kIsc_')

            # Extract the bio information
            bio_info = bio_section.get_text(separator='\n', strip=True) if bio_section else ''
            formatted_bio = self._clean_bio_text(bio_info, player_id)

            return formatted_bio

        except Exception:

            print(f'An error occurred while fetching player info. Please try again.')
            return {}


    def _clean_bio_text(self, bio_text, player_id):
        """
        Processes the raw bio text to add section titles and paragraph breaks.

        Parameters:
        - bio_text (str): The raw bio text

        Returns:
        - formatted_text (str): Cleaned and formatted bio text
        """

        # Set up baseline text/position and designate search keywords to use as breaking sections
        formatted_text = ''
        current_position = 0
        section_keywords = ['PROFESSIONAL CAREER', 'PLAYOFF HISTORY', 'BEFORE NBA', 'PERSONAL LIFE']


        # Iterate through the section keywords and insert paragraph breaks before them
        for keyword in section_keywords:
            keyword_index = bio_text.find(keyword, current_position)
            # Check if the keyword is found in the text and append accordingly
            if keyword_index != -1:
                formatted_text += f'{bio_text[current_position:keyword_index].strip()}\n'  # Append upto keyword
                formatted_text += f'\n<h4>{keyword}</h4>\n'  # Append keyword as header
                current_position = keyword_index + len(keyword)
        # Append any remaining text after the last keyword
        if current_position < len(bio_text):
            formatted_text += f'{bio_text[current_position:].strip()}'

        # Handle case with missing bio info altogether
        if formatted_text == '':
            formatted_text += 'No bio found on NBA player page. Please check back for updates.'

        # Finalize formatting per custom specifications
        formatted_text += (
            f'<br><br>'
            f'<small style="font-family: sans-serif; font-size: 10px;">'
            f'SOURCE: <a href="https://www.nba.com/player/{player_id}" target="_blank" '
            f'style="text-decoration: none; color: #000000;">NBA Player Page</a>'  # #5A99D4
            f'</small>'
        )
        formatted_text = (
            f'<div style="font-family: sans-serif; font-size: 14px; line-height: 1.6;">'
            + formatted_text.replace('<h4>', '<h4 style="text-align: center;">')
            + '</div>'
        )

        return formatted_text



def main(player_id):

    scraper = PlayerBioScraper()
    bio = scraper.fetch_player_bio(player_id)
    print(f'Player ID: {player_id}\nBio:\n{bio}')

if __name__ == '__main__':
    main(2544)  # Test stand-alone functionality with example player ID