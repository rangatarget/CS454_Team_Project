import json
import subprocess

json_file_path = 'changed_methods.json'

with open(json_file_path, 'r') as file:
    data = json.load(file)



for key, value_list in data.items():
    if value_list:
        first_value = value_list[0]
        class_name = first_value.split('::')[0]

        feature_string = f"lang_{key[4:]}_buggy/src/main/java/{class_name}.java"
        print(feature_string)

        subprocess.run(['python3', f'get_all_methods.py', feature_string, key])

        print(f"Executed get_all_methods.py with argument: {feature_string}")
