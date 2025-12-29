
import requests
from bs4 import BeautifulSoup
import re
import logging
from datetime import datetime, timezone

# Setup simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_parse():
    # Target a profile that definitely exists and scrape 1 page
    profile_id = 5587599
    url = f"https://www.aoe2insights.com/user/{profile_id}/matches/?page=1"
    
    # Headers to mimic browser
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    logger.info(f"Fetching {url}...")
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        logger.error(f"Failed: {resp.status_code}")
        return

    soup = BeautifulSoup(resp.text, 'html.parser')
    tiles = soup.find_all('div', class_='match-tile')
    logger.info(f"Found {len(tiles)} match tiles.")
    
    if not tiles:
        return

    # Check first tile in detail
    tile = tiles[0]
    
    # 1. Date Span Debug
    print("-" * 40)
    print("DATE DEBUG")
    date_span = tile.find('span', title=True)
    if date_span:
        print(f"Date Span Found. Title: '{date_span['title']}' Text: '{date_span.get_text()}' Parent: {date_span.parent}")
    else:
        print("No span with title found. Dumping info column:")
        info_col = tile.find('div', class_='d-flex flex-column')
        if info_col:
            print(info_col.prettify())

    # 2. Rating Debug
    print("-" * 40)
    print("RATING DEBUG")
    teams_col = tile.find('div', class_='teams')
    if teams_col:
        team_uls = teams_col.find_all('ul', class_='team')
        for i, ul in enumerate(team_uls):
            print(f"Team {i+1}:")
            lis = ul.find_all('li')
            for li in lis:
                p_div = li.find('div', class_='team-player')
                if p_div:
                    name_a = p_div.find('a')
                    name = name_a.get_text().strip() if name_a else "Unknown"
                    
                    rat_small = p_div.find('small', class_='rating')
                    if rat_small:
                        print(f"  Player: {name} | Rating Small HTML: {rat_small}")
                        print(f"  Text content: {rat_small.get_text(separator='|').strip()}")
                    else:
                        print(f"  Player: {name} | No rating small tag found.")

if __name__ == "__main__":
    debug_parse()
