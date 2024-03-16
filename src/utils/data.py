import json

from src.models.info import InfoEncoder

file_path = "src/utils/data.json"


# Writing to JSON file
def WriteToJson(data):
    with open(file_path, "w") as json_file:
        json.dump(data, json_file, indent=4, cls=InfoEncoder)


# Reading from JSON file
def ReadFromJson(custom: str):
    if custom != "":
        file_path = custom
    with open(file_path, "r") as json_file:
        data = json.load(json_file)
        return data
