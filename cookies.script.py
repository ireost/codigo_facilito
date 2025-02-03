import json

cookies_list = []

with open("cookies_get.json", "r") as file:
    for line in file:
        if not line.startswith("#") and line.strip():
            parts = line.split("\t")
            if len(parts) == 7:
                cookies_list.append({
                    "domain": parts[0],
                    "flag": parts[1] == "TRUE",
                    "path": parts[2],
                    "secure": parts[3] == "TRUE",
                    "expiration": int(parts[4]) if parts[4].isdigit() else None,
                    "name": parts[5],
                    "value": parts[6].strip()
                })

with open("cookies.json", "w") as json_file:
    json.dump(cookies_list, json_file, indent=4)

print("✓ Cookies convertidas y guardadas en cookies.json")

