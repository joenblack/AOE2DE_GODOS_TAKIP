
import requests
from bs4 import BeautifulSoup
import re

# Try explicit page 1
URL = "https://www.aoe2insights.com/user/11729559/matches/?page=1"

def probe():
    print(f"Fetching {URL}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    resp = requests.get(URL, headers=headers)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print("Failed to fetch.")
        return

    soup = BeautifulSoup(resp.content, "html.parser")
    
    # Try finding any table or list
    # The site uses divs for matches usually
    tiles = soup.find_all('div', class_='match-summary-card')
    print(f"Found {len(tiles)} match tiles.")
    
    if len(tiles) == 0:
        # Dump some html to see what we got
        print("No tiles found. Dumping first 500 chars of body:")
        body = soup.find('body')
        if body:
            print(body.get_text()[:500])
        else:
            print("No body tag found.")
        return

    for i, tile in enumerate(tiles[:3]):
        print(f"\n--- Match {i+1} ---")
        
        # Check Ladder Type
        ladder_div = tile.find('div', class_='ladder-type')
        ladder_text = ladder_div.get_text(strip=True) if ladder_div else "N/A"
        print(f"Ladder: {ladder_text}")
        
        # Check Players and Ratings
        teams_col = tile.find('div', class_='teams')
        if teams_col:
            team_uls = teams_col.find_all('ul', class_='team')
            for t_idx, ul in enumerate(team_uls):
                lis = ul.find_all('li')
                for li in lis:
                    p_div = li.find('div', class_='team-player')
                    if not p_div: continue
                    
                    p_link = p_div.find('a')
                    p_name = p_link.get_text().strip() if p_link else "Unknown"
                    
                    # Find Rating
                    rat_small = p_div.find('small', class_='rating')
                    # Get RAW html of rating
                    rating_html = str(rat_small) if rat_small else "None"
                    # Get text
                    rating_text = rat_small.get_text(strip=True) if rat_small else "N/A"
                    
                    if "Kataklysm" in p_name: # Focus on our target player
                        print(f"Player: {p_name}")
                        print(f"Rating HTML: {rating_html}")
                        print(f"Rating Text Clean: {rating_text}")

if __name__ == "__main__":
    probe()
