from pathlib import Path
from requests import get
import pandas as pd
from os import environ
from time import sleep
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT_DIR = Path(__file__).resolve().parent.parent
datasetPath = ROOT_DIR / "data/raw/foodseg103/"

params = {
    "query": "",
    "dataType": "SR Legacy",
    "format": "abridged",
    "nutrients": "208,204,203,205,291,307",
    "api_key": environ.get("USDA_API_KEY"),
}

headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

proxies = {"http": "socks5://127.0.0.1:10808", "https": "socks5://127.0.0.1:10808"}

nutrition = []

fdc_overrides = {
    "egg tart": "175069",
    "french fries": "170452",
    "ice cream": "167575",
    "cheese butter": "173418",
    "cake": "174951",
    "coffee": "171890",
    "juice": "169100",
    "milk": "171266",
    "walnut": "170187",
    "grape": "174683",
    "pork": "168287",
    "rice": "169712",
    "pie": "175012",
    "tofu": "172475",
    "eggplant": "169352",
    "avocado": "171705",
    "potato": "170438",
    "tomato": "170457",
    "carrot": "170393",
    "green beans": "169961",
    "soup": "172736",
}

query_overrides = {
    "chocolate": "milk chocolate",
    "popcorn": "air popped popcorn",
    "fried meat": "pork fresh ground cooked",
    "wine": "alcoholic beverage wine table red",
    "juice": "orange juice raw",
    "peanut": "peanuts raw all types",
    "egg": "egg whole raw fresh",
    "apple": "apples raw with skin",
    "olives": "olives ripe canned",
    "peach": "peaches raw",
    "orange": "oranges raw all commercial varieties",
    "steak": "generic raw beef steak",
    "banana": "bananas raw",
    "sauce": "tomato chili sauce",
    "kiwi": "kiwifruit green raw",
    "melon": "melon cantaloupe raw",
    "salad": "lettuce green leaf raw",
}

url = "https://api.nal.usda.gov/fdc/v1/"
endpoint = ""
# read ingredient mappings
with open(datasetPath / "category_id.txt", "r") as category_id:
    lines = category_id.readlines()[1:]

    for i, line in enumerate(lines, start=1):
        original_name = " ".join(line.strip().split()[1:])
        pos = f"[{i}/{len(lines)}]"
        print(f"{pos} Processing {original_name}...")

        query_name = original_name
        if original_name in fdc_overrides:
            override_id = str(fdc_overrides[original_name])
            endpoint = "food/" + override_id  # query exact food by id
            print(pos, "Found override:", override_id)
        else:
            if original_name in query_overrides:
                query_name = query_overrides[
                    original_name
                ]  # if more accurate name provided, use that
                print(pos, "Replaced:", query_name)
            endpoint = "foods/search"  # search by name
            params["query"] = query_name

        response = get(
            url=url + endpoint,
            params=params,
            headers=headers,
            proxies=proxies,
            verify=False,
        )
        if response.status_code != 200:
            print(
                f"{pos} ERROR processing {original_name}({query_name}): non-success API status code: {response.status_code}"
            )
            print(f"{url=}; {endpoint=}; {response=}")
            exit(1)
            continue

        response = response.json()

        food = response
        valueField = "amount"
        numberField = "number"
        if "foods" in endpoint:  # non-id lookup
            if len(response["foods"]) == 0:
                print(
                    f"{pos} ERROR processing {original_name}({query_name}): none found!"
                )
                continue
            food = response["foods"][0]
            valueField = "value"
            numberField = "nutrientNumber"

        stats = {n[numberField]: n[valueField] for n in food["foodNutrients"]}

        nutrition.append(
            {
                "Name": original_name,
                "Description": food["description"],
                "Calories": stats.get("208"),
                "Fat": stats.get("204"),
                "Protein": stats.get("203"),
                "Carbs": stats.get("205"),
                "Fiber": stats.get("291"),
                "Sodium": stats.get("307"),
            }
        )

df = pd.DataFrame(nutrition)
df.to_csv(ROOT_DIR / "data/nutrition_db.csv")

print(f"Done, saved {len(nutrition)} out of {len(lines)} nutrients")
