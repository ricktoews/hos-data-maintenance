import json
import time
from pathlib import Path

import requests

BASE_URL = "https://api.hos.com/api/v1/programs/{number}"
OUT_DIR = Path("json")
OUT_DIR.mkdir(exist_ok=True)

START = 1420
MAX_CONSECUTIVE_MISSES = 5

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

consecutive_misses = 0
number = START

while True:
    out_file = OUT_DIR / f"{number}.json"

    if out_file.exists():
        print(f"Skipping {number}; already saved")
        consecutive_misses = 0
        number += 1
        continue

    url = BASE_URL.format(number=number)

    try:
        response = session.get(url, timeout=20)

        if response.status_code == 404:
            consecutive_misses += 1
            print(f"{number}: not found ({consecutive_misses} consecutive misses)")

            if consecutive_misses >= MAX_CONSECUTIVE_MISSES:
                print("Stopping: reached likely end of available programs.")
                break

            number += 1
            continue

        response.raise_for_status()
        data = response.json()

        with out_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        title = data.get("title", "(no title)")
        print(f"Saved {number}: {title}")

        consecutive_misses = 0
        time.sleep(0.25)

    except requests.RequestException as e:
        print(f"{number}: request error: {e}")
        time.sleep(2)

    except json.JSONDecodeError:
        print(f"{number}: response was not valid JSON")

    number += 1
