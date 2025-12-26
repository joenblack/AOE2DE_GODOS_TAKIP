import requests
import os
from config import settings

def get_dump_info():
    """Fetch the list of available dumps from AoEStats."""
    try:
        response = requests.get(settings.AOESTATS_DUMP_URL)
        response.raise_for_status()
        data = response.json()
        return data # returns a dict with 'matches' and 'players' keys containing url and updated_at
    except Exception as e:
        print(f"Error fetching dump info: {e}")
        return None

def download_file(url, target_path):
    """Download a file from a URL to a target path."""
    try:
        if os.path.exists(target_path):
            print(f"File {target_path} already exists. Skipping download for now (TODO: check timestamp).")
            return target_path

        print(f"Downloading {url} to {target_path}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded {target_path}")
        return target_path
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None
