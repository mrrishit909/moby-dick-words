"""Step 1: the full text of Moby-Dick from Project Gutenberg (ebook #2701; public domain in the United States).

    ./venv/bin/python download.py   -> data/pg2701.txt (not committed), results/pull.json
"""
import json
import re
import ssl
import urllib.request
from datetime import date
from pathlib import Path

import certifi

HERE = Path(__file__).parent
URL = "https://www.gutenberg.org/cache/epub/2701/pg2701.txt"
CTX = ssl.create_default_context(cafile=certifi.where())


def main():
    (HERE / "data").mkdir(exist_ok=True)
    (HERE / "results").mkdir(exist_ok=True)
    raw = urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "research-portfolio (Rishit Raj Mathur)"}), context=CTX, timeout=120).read()
    (HERE / "data" / "pg2701.txt").write_bytes(raw)
    text = raw.decode("utf-8")
    info = {"pulled": date.today().isoformat(), "url": URL, "bytes": len(raw), "gutenberg_last_updated": re.search(r"Most recently updated: ([^\n]+)", text).group(1).strip(),
            "start_marker": "*** START OF THE PROJECT GUTENBERG EBOOK" in text, "end_marker": "*** END OF THE PROJECT GUTENBERG EBOOK" in text}
    (HERE / "results" / "pull.json").write_text(json.dumps(info, indent=2) + "\n")
    print(info)


if __name__ == "__main__":
    main()
