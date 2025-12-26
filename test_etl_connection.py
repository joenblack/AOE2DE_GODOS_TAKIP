from services.etl.aoestats import get_dump_info
import json

def test_api():
    print("Fetching dump info...")
    info = get_dump_info()
    if info:
        print("Success!")
        print(json.dumps(info, indent=2))
    else:
        print("Failed to fetch info.")

if __name__ == "__main__":
    test_api()
