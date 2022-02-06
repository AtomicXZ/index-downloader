import json
from os import path

path = f"{path.dirname(__file__)}/creds.json"

name = input("Enter keyword from index link:  ")
user = input("Enter username for the index:  ")
password = input("Enter password for the index:  ")

try:
    data = json.load(open(path))
except FileNotFoundError:
    data = {}

data[name.lower()] = {"user": user, "password": password}

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)
