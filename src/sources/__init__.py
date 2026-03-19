"""
MoltStreet Intelligence — Data Sources
Shared HTTP utility + base fetcher.
"""
import json
import time
import urllib.request
import urllib.error


def fetch_json(url: str, retries: int = 3, timeout: int = 20, headers: dict = None) -> dict | list | None:
    """Fetch JSON from URL with retries and exponential backoff."""
    hdrs = {"User-Agent": "MoltStreet/3.0", "Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:  # Rate limited
                wait = 2 ** (attempt + 1) * 5
                print(f"    [RATE LIMIT] Waiting {wait}s...")
                time.sleep(wait)
            elif e.code >= 500:
                time.sleep(2 ** attempt)
            else:
                print(f"    [HTTP {e.code}] {url[:80]}")
                return None
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print(f"    [FAIL] {url[:80]}: {e}")
                return None
    return None
