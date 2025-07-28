import json

# Исходный файл (ваш текущий формат)
with open('ingredients_old.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Конвертация в формат фикстур
output = []
for idx, item in enumerate(data, start=1):
    output.append({
        "model": "recipes.ingredient",  
        "pk": idx,
        "fields": {
            "name": item["name"],
            "measurement_unit": item["measurement_unit"]
        }
    })

# Сохранение нового файла
with open('ingredients.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)