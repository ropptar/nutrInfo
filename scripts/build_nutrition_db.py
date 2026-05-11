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
    "api_key": environ.get('USDA_API_KEY'),
}

headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

proxies = {"http": "socks5://127.0.0.1:10808", "https": "socks5://127.0.0.1:10808"}

nutrition = pd.DataFrame(
    columns=["Name", "Description", "Calories", "Fat", "Protein", "Carbs", "Fiber", "Sodium"]
)

fix_queries = {
    # Previously fixed — still needed
    "chocolate": "milk chocolate",
    "popcorn": "air popped popcorn",
    "fried meat": "pork fresh ground cooked",

    # New fixes
    "wine": "alcoholic beverage wine table red",
    "juice": "orange juice raw",
    "peanut": "peanuts raw all types",
    "egg": "egg whole raw fresh",
    "apple": "apples raw with skin",
    "olives": "olives ripe canned",
    "peach": "peaches raw",
    "orange": "oranges raw all commercial varieties",
    "steak": "beef top sirloin steak raw",
    "banana": "bananas raw",
    "kiwi": "kiwifruit green raw",
    "melon": "melon cantaloupe raw",
    "salad": "lettuce green leaf raw",
}

# read ingredient mappings
with open(datasetPath / "category_id.txt", "r") as category_id:
    lines = category_id.readlines()[1:]

    for i, line in enumerate(lines, start=1):
        original_name = " ".join(line.strip().split()[1:])
        pos = f"[{i}/{len(lines)}]"

        print(f"{pos} Processed {original_name}...")
        query_name = original_name
        if fix_queries.get(original_name):
            query_name = fix_queries[original_name]
            print(pos, "Replaced:", query_name)

        params["query"] = query_name
        print('queried:', query_name)
        response = get(
            url="https://api.nal.usda.gov/fdc/v1/foods/search",
            params=params,
            headers=headers,
            proxies=proxies,
            verify=False
        )
        if response.status_code == 200:
            response = response.json()
            if len(response["foods"]) > 0:
                stats = {
                    (n["nutrientName"].lower()): n["value"]
                    for n in response["foods"][0]["foodNutrients"]
                }
                nutrition = pd.concat(
                    [
                        nutrition,
                        pd.DataFrame(
                            data=[
                                {
                                    "Name": original_name,
                                    "Description": response["foods"][0]['description'],
                                    "Calories": stats.get("energy"),
                                    "Fat": stats.get("total lipid (fat)"),
                                    "Protein": stats.get("protein"),
                                    "Carbs": stats.get("carbohydrate, by difference"),
                                    "Fiber": stats.get("fiber, total dietary"),
                                    "Sodium": stats.get("sodium, na"),
                                }
                            ]
                        ),
                    ],
                    ignore_index=True,
                )
            else:
                print(f"{pos} ERROR processing {original_name}({query_name}): none found!")
        #sleep(0.3)
print(f"Done, saved {len(nutrition)} out of {len(lines)} nutrients")

nutrition.to_csv(ROOT_DIR / "data/nutrition_db.csv")
