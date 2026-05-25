"""Helper to save MCP response JSON to the correct data/pages/ or data/keywords/ file."""
import json, sys, os

BASE = os.path.dirname(os.path.abspath(__file__))

def save_pages(month, data):
    path = os.path.join(BASE, "data", "pages", f"pages_{month}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    count = len(data.get("pages", []))
    print(f"Saved {path} ({count} pages)")

def save_keywords(month, data):
    path = os.path.join(BASE, "data", "keywords", f"keywords_{month}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    count = len(data.get("keywords", []))
    print(f"Saved {path} ({count} keywords)")

if __name__ == "__main__":
    print("Import and call save_pages(month, data) or save_keywords(month, data)")
