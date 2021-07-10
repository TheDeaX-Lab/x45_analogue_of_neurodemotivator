import json

def read_json_from_filename(filename: str):
    with open(filename) as f:
        return json.load(f)


def write_json_to_filename(filename: str, json_obj):
    with open(filename, 'w') as f:
        json.dump(json_obj, f)