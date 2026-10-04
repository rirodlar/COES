#!/usr/bin/env python3
"""Build a coes_id -> item UUID map by paging through all items in DSpace,
matching on dc.identifier.other. Used to find items for update/dedup/removal
in later incremental loads.

Requires DSPACE_REST_URL, DSPACE_ADMIN_EMAIL, DSPACE_ADMIN_PASSWORD env vars.

Usage:
    python3 find_items_by_coes_id.py [--start N] [--end N] [-o output.txt]
"""
import argparse
import json
import urllib.request

from dspace_rest import BASE_SERVER, get_auth_headers


def fetch_all_items(headers):
    mapping = {}
    size = 100
    page = 0
    while True:
        url = f"{BASE_SERVER}/api/core/items?size={size}&page={page}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            d = json.loads(resp.read())
        items = d.get("_embedded", {}).get("items", [])
        if not items:
            break
        for item in items:
            vals = item.get("metadata", {}).get("dc.identifier.other", [])
            if vals:
                mapping[vals[0]["value"]] = item["uuid"]
        total_pages = d.get("page", {}).get("totalPages", 1)
        page += 1
        if page >= total_pages:
            break
    return mapping


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("-o", "--output", default="to_process_list.txt")
    args = parser.parse_args()

    headers = get_auth_headers()
    mapping = fetch_all_items(headers)
    print(f"Total items indexed: {len(mapping)}")

    found = []
    for i in range(args.start, args.end + 1):
        cid = f"WEB-{i:05d}"
        uuid = mapping.get(cid)
        if uuid:
            found.append((cid, uuid))
        else:
            print(f"NOT FOUND: {cid}")

    print(f"Matched: {len(found)}")
    with open(args.output, "w") as f:
        for cid, uuid in found:
            f.write(f"{cid} {uuid}\n")
    print(f"Written to {args.output}")


if __name__ == "__main__":
    main()
