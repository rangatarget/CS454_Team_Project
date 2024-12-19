import json
import subprocess
import os

# JSON 파일 경로
json_file_path = 'changed_methods.json'

# JSON 파일 읽기
with open(json_file_path, 'r') as file:
    data = json.load(file)

feature_num = 2

# 각 키에 대해 처리
for key, value_list in data.items():
    if value_list:  # 리스트가 비어있지 않은 경우
        # 첫 번째 원소에서 클래스명 추출
        first_value = value_list[0]
        class_name = first_value.split('::')[0]  # "::"로 나누고 첫 번째 부분을 가져옴
        if int(key[4:])< 55:
            continue
        # 문자열 조합
        feature_string = f"lang_{key[4:]}_buggy/src/java/{class_name}.java"

        # feature_1.py 실행
        subprocess.run(['python3', f'feature_{feature_num}.py', feature_string, key])

        # 결과 출력 (옵션)
        print(f"Executed feature_{feature_num}.py with argument: {feature_string}")
