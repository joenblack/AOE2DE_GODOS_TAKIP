import sys
import os
import json
import logging

logging.basicConfig(level=logging.INFO)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from services.etl.aoe2insights import fetch_full_match_history

PID = 5587599 # DaRKN'

def test():
    print(f"Testing scraper for PID: {PID}")
    # Fetch only 1 page for testing
    matches = fetch_full_match_history(PID, max_pages=1)
    print(f"Fetched {len(matches)} matches.")
    if matches:
        print("First match sample:")
        print(json.dumps(matches[0], indent=2, default=str))

if __name__ == "__main__":
    test()
