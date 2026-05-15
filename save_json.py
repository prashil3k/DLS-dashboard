import json, sys, os

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def save(subdir, filename, data):
    path = os.path.join(data_dir, subdir, filename)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved {path} ({len(data.get('pages', data.get('keywords', [])))} rows)")

if __name__ == "__main__":
    print("Helper ready")
