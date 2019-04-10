import jsonschema
import json

# схема проверки json файла
schema = {
    "type": "object",
    "properties": {
        "checks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "command": {"type": "string"},
                    "success": {"type": "boolean"}
                }
            }
        }
    }
}

print("Используем схему для проверки json:")
print(json.dumps(schema, indent=2))  # приятна для глаза структура

# схема проверяемого json файла
with open('C:\\Users\\IT\\.PyCharmEdu2018.3\\config\\scratches\\Checks.json','r')as lafa:
    data = json.load(lafa)

print("Исходные данные проверяемого json файла:")
print(json.dumps(data, indent=2))  # приятна для глаза структура
print("Проверка входных данных с помощью jsonschema:")
try:
    jsonschema.validate(data, schema)

except jsonschema.exceptions.SchemaError:
    print('wtfk')
