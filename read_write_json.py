import json


def read_from_json(file):
    file = 'data/files/' + file
    with open(file) as j_file:
        f = j_file.read()
        data = json.loads(f)
        return data


def write_to_json(data):
    with open('data/files/data.json', 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
