from pathlib import Path
from requests import get
import pandas as pd
from time import sleep

ROOT_DIR = Path(__file__).resolve().parent.parent
datasetPath = ROOT_DIR / "data/raw/foodseg103/"

params = {
    'query':'',
    'dataType':'SR Legacy',
    'sortBy':'fdcId',
    'api_key':''
}

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

proxies = {
    'http':'socks5://127.0.0.1:10808',
    'https':'socks5://127.0.0.1:10808'
}

nutrition = pd.DataFrame(columns=['Name', 'Calories', 'Fat', 'Protein', 'Carbs', 'Fiber', 'Sodium'])

# read ingredient mappings
with open(datasetPath / "category_id.txt", "r") as category_id:
    for i, line in enumerate(category_id.readlines()[1:], start=1):
        ingredient_name = ' '.join(line.strip().split()[1:]) 
        params['query'] = ingredient_name
        response = get(url = "https://api.nal.usda.gov/fdc/v1/foods/search", params=params, headers=headers, proxies=proxies)
        if response.status_code == 200:
            response = response.json()
            if len(response['foods']) > 0:
                stats = { (n['nutrientName'].lower()):n['value'] for n in response['foods'][0]['foodNutrients']}
                nutrition = pd.concat([nutrition, pd.DataFrame(data=[{
                    'Name':ingredient_name,
                    'Calories':stats.get('energy'),
                    'Fat':stats.get('total lipid (fat)'),
                    'Protein':stats.get('protein'),
                    'Carbs':stats.get('carbohydrate, by difference'),
                    'Fiber':stats.get('fiber, total dietary'),
                    'Sodium':stats.get('sodium, na'),
                }])], ignore_index=True)
                print(f"[{i}/103] Processed {ingredient_name}...")
            else:
                print(f"[{i}/103] ERROR processing {ingredient_name}: none found!")
        sleep(.3)
print(f"Done, saved {len(nutrition)} out of 103 nutrients")
nutrition.to_csv(ROOT_DIR/"data/nutrition_db.csv")