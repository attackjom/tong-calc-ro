#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import requests

API_KEY = "8b7d2377989aa1e839940e81af2d9249"
OUTPUT_FILE = "item_output.json"
REQUEST_DELAY_SEC = 0.2  # small delay to be polite to the API

BASE_URL = "https://www.divine-pride.net/api/database/item/{item_id}?apiKey={api_key}"
SERVER_MAP = {
    1: "iRO",
    2: "thROG",
    3: "kROm",
    4: "dpro",   # ✅ เพิ่ม dpro
}

def normalize_newlines(text: str):
    if not isinstance(text, str):
        return None
    return text.replace("\r\n", "\n").replace("\r", "\n")

def get_first(d, *keys, default=None):
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default

def parse_item_ids(arg: str):
    """Accepts a single int or a range like 460120-460130; returns a list of ints."""
    s = arg.strip()
    if "-" in s:
        a, b = s.split("-", 1)
        start, end = int(a.strip()), int(b.strip())
        step = 1 if end >= start else -1
        return list(range(start, end + step, step))
    return [int(s)]

def fetch_item(item_id: int, server_id: int, session: requests.Session):
    url = BASE_URL.format(item_id=item_id, api_key=API_KEY)
    if server_id in SERVER_MAP:
        url += f"&server={SERVER_MAP[server_id]}"
    r = session.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

def map_to_target(data: dict) -> dict:
    # ✅ weight ต้องไม่มีทศนิยม
    weight_val = get_first(data, "weight", "Weight")
    if weight_val is not None:
        try:
            weight_val = int(float(weight_val))
        except Exception:
            weight_val = None

    return {
        "id": data.get("id"),
        "aegisName": get_first(data, "aegisName", "AegisName"),
        "flavorText": get_first(data, "flavorText", "flavor"),
        "name": get_first(data, "name", "identifiedDisplayName", "identified_name"),
        "unidName": get_first(data, "unidentifiedDisplayName", "unidentified_name"),
        "resName": get_first(data, "resName", "kROName", "krName", "resourceName"),
        "unidResName": get_first(data, "unidentifiedResourceName", "unidentifiedResName"),
        "description": normalize_newlines(get_first(data, "description", "identifiedDescription", "desc")),
        "slots": get_first(data, "slots", "slotCount"),
        "itemTypeId": get_first(data, "itemTypeId", "itemType", "type"),
        "itemSubTypeId": get_first(data, "itemSubTypeId", "itemSubType", "subType"),
        "itemLevel": get_first(data, "itemLevel", "ItemLevel"),
        "attack": get_first(data, "attack", "atk", "ATK"),
        "defense": get_first(data, "defense", "def", "DEF"),
        "weight": weight_val,  # ✅ แก้เป็น int
        "requiredLevel": get_first(data, "requiredLevel", "reqLevel", "RequireLevel"),
        "location": None,
        "compositionPos": None,
        "canGrade": False,
        "usableClass": [],
        "script": {},
    }

def prompt_item_ids():
    while True:
        s = input("Enter item id or range (e.g. 460128 or 460120-460130): ").strip()
        if not s:
            print("Please enter a value.")
            continue
        try:
            ids = parse_item_ids(s)
            if not ids:
                raise ValueError
            return ids
        except Exception:
            print("Invalid format. Enter a single integer or a range like 313376-313387.")

def prompt_server_id():
    tip = "Server id (1=iRO, 2=thROG, 3=kROm, 4=dpro)"
    while True:
        s = input(f"Enter {tip}: ").strip()
        if not s.isdigit():
            print("Please enter a number: 1, 2, 3, or 4.")
            continue
        sv = int(s)
        if sv not in SERVER_MAP:
            print("Invalid server id. Use 1, 2, 3, or 4.")
            continue
        return sv

def main():
    item_ids = prompt_item_ids()
    server_id = prompt_server_id()

    items = {}
    with requests.Session() as session:
        for i, item_id in enumerate(item_ids, 1):
            try:
                data = fetch_item(item_id, server_id, session)
                items[str(item_id)] = map_to_target(data)
                print(f"[OK] {item_id} -> {SERVER_MAP[server_id]}")
            except Exception as e:
                print(f"[WARN] {item_id}: {e}")
            if i < len(item_ids):
                time.sleep(REQUEST_DELAY_SEC)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    print(f"Done. Wrote {len(items)} item(s) to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
