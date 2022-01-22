import json
import os


tokens_data = {}


def save_data():
    with open('data.json', 'w+', encoding='utf-8') as file:
        file.seek(0)
        json.dump(tokens_data, file, indent=4, ensure_ascii=False)
        file.truncate()


def load_data():
    if not os.path.exists(f'data.json'):
        mode = 'w+'
    else:
        mode = 'r'
    with open('data.json', mode, encoding='utf-8') as file:
        raw = file.read()
        if raw:
            data = json.loads(raw)

            for token in data.items():
                tokens_data[token[0]] = token[1]
            return data
        return []

