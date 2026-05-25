"""Extract gsc-pages MCP responses from the session JSONL transcript and save as data files."""

import json
import os
import re

TRANSCRIPT = "/Users/prashil3k/.claude/projects/-Users-prashil3k-Documents-Claude-Code/e99fb810-663d-4c41-8d50-e5846ed3a117.jsonl"
BASE = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(BASE, "data", "pages")
KEYWORDS_DIR = os.path.join(BASE, "data", "keywords")

os.makedirs(PAGES_DIR, exist_ok=True)
os.makedirs(KEYWORDS_DIR, exist_ok=True)


def extract_pages():
    with open(TRANSCRIPT, "r") as f:
        lines = f.readlines()

    # We need to pair tool_use calls (with date params) to their tool_result responses
    # Strategy: find all tool_use IDs for gsc-pages calls, note the month,
    # then find the corresponding tool_result with that ID

    tool_calls = {}  # id -> month
    tool_results = {}  # id -> parsed data

    for line_num, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Extract content blocks from message
        msg = entry.get("message", entry)
        content = msg.get("content", [])
        if isinstance(content, str):
            continue
        if not isinstance(content, list):
            continue

        for block in content:
            if not isinstance(block, dict):
                continue

            # Tool use: gsc-pages call with date_from
            if block.get("type") == "tool_use" and "gsc-pages" in block.get("name", ""):
                tool_id = block.get("id", "")
                inp = block.get("input", {})
                date_from = inp.get("date_from", "")
                if date_from and tool_id:
                    month = date_from[:7]
                    where = inp.get("where", "")
                    # Only count calls with the correct /tutorials/ filter
                    if "/tutorials/" in str(where):
                        tool_calls[tool_id] = month

            # Tool result: response to a previous call
            if block.get("type") == "tool_result":
                tool_id = block.get("tool_use_id", "")
                if tool_id not in tool_calls:
                    continue

                result_content = block.get("content", "")
                text = ""
                if isinstance(result_content, str):
                    text = result_content
                elif isinstance(result_content, list):
                    for sub in result_content:
                        if isinstance(sub, dict) and sub.get("type") == "text":
                            text = sub.get("text", "")
                            break

                if text:
                    try:
                        data = json.loads(text)
                        if "pages" in data and isinstance(data["pages"], list):
                            tool_results[tool_id] = data
                    except json.JSONDecodeError:
                        pass

    # Now match calls to results
    month_data = {}
    for tool_id, month in tool_calls.items():
        if tool_id in tool_results:
            data = tool_results[tool_id]
            page_count = len(data["pages"])
            # Keep the one with more pages if duplicate month
            if month not in month_data or len(month_data[month]["pages"]) < page_count:
                month_data[month] = data
                print(f"  {month}: {page_count} pages (tool_id: {tool_id[:20]}...)")

    print(f"\nTotal months with data: {len(month_data)}")

    # Save to files
    for month, data in sorted(month_data.items()):
        path = os.path.join(PAGES_DIR, f"pages_{month}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  Saved {path} ({len(data['pages'])} pages)")

    return month_data


def extract_keywords():
    with open(TRANSCRIPT, "r") as f:
        lines = f.readlines()

    tool_calls = {}  # id -> month
    tool_results = {}  # id -> parsed data

    for line_num, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg = entry.get("message", entry)
        content = msg.get("content", [])
        if isinstance(content, str):
            continue
        if not isinstance(content, list):
            continue

        for block in content:
            if not isinstance(block, dict):
                continue

            if block.get("type") == "tool_use" and "gsc-keywords" in block.get("name", ""):
                tool_id = block.get("id", "")
                inp = block.get("input", {})
                date_from = inp.get("date_from", "")
                if date_from and tool_id:
                    month = date_from[:7]
                    where = inp.get("where", "")
                    if "/tutorials/" in str(where):
                        tool_calls[tool_id] = month

            if block.get("type") == "tool_result":
                tool_id = block.get("tool_use_id", "")
                if tool_id not in tool_calls:
                    continue

                result_content = block.get("content", "")
                text = ""
                if isinstance(result_content, str):
                    text = result_content
                elif isinstance(result_content, list):
                    for sub in result_content:
                        if isinstance(sub, dict) and sub.get("type") == "text":
                            text = sub.get("text", "")
                            break

                if text:
                    try:
                        data = json.loads(text)
                        if "keywords" in data and isinstance(data["keywords"], list):
                            tool_results[tool_id] = data
                    except json.JSONDecodeError:
                        pass

    month_data = {}
    for tool_id, month in tool_calls.items():
        if tool_id in tool_results:
            data = tool_results[tool_id]
            kw_count = len(data["keywords"])
            if month not in month_data or len(month_data[month]["keywords"]) < kw_count:
                month_data[month] = data
                print(f"  {month}: {kw_count} keywords (tool_id: {tool_id[:20]}...)")

    print(f"\nTotal months with data: {len(month_data)}")

    for month, data in sorted(month_data.items()):
        path = os.path.join(KEYWORDS_DIR, f"keywords_{month}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"  Saved {path} ({len(data['keywords'])} keywords)")

    return month_data


if __name__ == "__main__":
    print("=== Extracting gsc-pages data from transcript ===\n")
    pages = extract_pages()
    print(f"\nDone. Saved {len(pages)} months of pages data.")

    print("\n=== Extracting gsc-keywords data from transcript ===\n")
    keywords = extract_keywords()
    print(f"\nDone. Saved {len(keywords)} months of keywords data.")
