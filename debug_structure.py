from bs4 import BeautifulSoup
import re

def analyze():
    print("Analyzing last_response.html...")
    with open("last_response.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    print(f"Content Length: {len(content)}")
    
    # 1. Search for <table
    params = ["<table", "class=[\"'].*?table.*?[\"']", "page=\d+", "/match/"]
    
    for p in params:
        print(f"\n--- Searching for: {p} ---")
        matches = list(re.finditer(p, content, re.IGNORECASE))
        print(f"Found {len(matches)} matches.")
        for i, m in enumerate(matches[:3]):
            start = max(0, m.start() - 50)
            end = min(len(content), m.end() + 50)
            print(f"Match {i}: ...{content[start:end]}...")

    # 2. BS4 Analysis
    soup = BeautifulSoup(content, 'html.parser')
    tables = soup.find_all('table')
    print(f"\nBS4 found {len(tables)} tables.")
    
    # Check for match links
    links = soup.find_all('a', href=re.compile(r'/match/\d+'))
    print(f"BS4 found {len(links)} match links.")
    if links:
        link = links[0]
        print(f"Match Link: {link}")
        print("Parents:")
        for p in link.parents:
            print(f"  Tag: {p.name}, Class: {p.get('class')}")
            if p.name == 'body': break


if __name__ == "__main__":
    analyze()
