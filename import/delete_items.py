#!/usr/bin/env python3
"""Delete DSpace items listed in a "coes_id uuid" text file (one per line,
as produced by find_items_by_coes_id.py).

Requires DSPACE_REST_URL, DSPACE_ADMIN_EMAIL, DSPACE_ADMIN_PASSWORD env vars.

Usage:
    python3 delete_items.py to_process_list.txt
"""
import sys
import urllib.error
import urllib.request

from dspace_rest import BASE_SERVER, get_auth_headers


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    headers = get_auth_headers()

    with open(sys.argv[1]) as f:
        lines = [l.strip().split() for l in f if l.strip()]

    ok, fail = 0, 0
    for cid, uuid in lines:
        req = urllib.request.Request(
            f"{BASE_SERVER}/api/core/items/{uuid}", method="DELETE", headers=headers
        )
        try:
            with urllib.request.urlopen(req) as resp:
                if resp.status == 204:
                    ok += 1
                else:
                    fail += 1
                    print(f"{cid} {uuid} -> unexpected status {resp.status}")
        except urllib.error.HTTPError as e:
            fail += 1
            print(f"{cid} {uuid} -> HTTP {e.code}")

    print(f"Deleted OK: {ok}, Failed: {fail}")


if __name__ == "__main__":
    main()
