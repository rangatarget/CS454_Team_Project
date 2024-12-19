import os
import javalang
import re
import json

index = 0

def process_file_path(file_path):
    # .java 확장자 제거
    if file_path.endswith('.java'):
        file_path = file_path[:-5]  # .java의 길이인 5를 빼줌
    
    # 'org' 왼쪽 부분 제거
    if 'org' in file_path:
        file_path = 'org' + file_path.split('org', 1)[1]  # 'org'를 기준으로 나누고 오른쪽 부분만 가져옴
    
    return file_path

def get_method_index_pair(file_path):
    global index
    method_index = {}
    
    with open(file_path, 'r', encoding='utf-8') as file:
        java_code = file.read()

    tree = javalang.parse.parse(java_code)
    for node in tree.types:
        for method in node.methods:
            index += 1
            
            # 입력 자료형 추출
            param_types = [param.type.name for param in method.parameters] if method.parameters else []
            param_types_str = ', '.join(param_types)  # 입력 자료형을 문자열로 변환
            
            # 키 생성
            key = f"{process_file_path(file_path)}::{method.name}::({param_types_str})::{method.position[0]}"
            method_index[key] = index
            
    return method_index

def parse_changes(file_path):
    changes = {}
    file_paths = {}
    
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    current_lang = None
    for line in lines:
        line = line.strip()
        if line.startswith("Changes in lang_"):
            current_lang = line.split(":")[0].split(" ")[2]  # lang_1, lang_2 등
            changes[current_lang] = []
        elif line.startswith("diff -r"):
            # diff 명령어에서 파일 경로 추출
            paths = line.split()[2:4]  # diff 명령어의 3번째와 4번째 요소가 두 경로
            file_paths[current_lang] = paths
            continue
        elif current_lang and line:
            # 알파벳 앞의 숫자만 추출
            extracted_numbers = re.findall(r'(\d+)(?=[acd])', line)
            for num in extracted_numbers:
                # ','로 구분된 경우에도 처리
                if ',' in num:
                    split_nums = num.split(',')
                    for n in split_nums:
                        changes[current_lang].append(int(n))  # 정수로 변환하여 추가
                else:
                    changes[current_lang].append(int(num))  # 정수로 변환하여 추가
    
    return changes, file_paths

def find_changed_methods(lines, buggy_methods, fixed_methods):
    index = 0
    change_methods = []
    method_in_buggy = get_method_index_pair(buggy_methods)
    method_in_fixed = get_method_index_pair(fixed_methods)
    if len(method_in_buggy) != len(method_in_fixed):
        print(str(buggy_methods) + "File added or deleted")
        return []
    for line in lines:
        got = False
        for i, method in enumerate(method_in_buggy.keys()):
            parts = method.split('::')
            line_number_str = parts[-1]
            line_number = int(line_number_str)
            if i > 0 and int(line) < line_number:
                print(list(method_in_buggy.keys())[i-1])
                change_methods.append(list(method_in_buggy.keys())[i-1])
                got = True
                break
        if not got:
            change_methods.append(list(method_in_buggy.keys())[len(list(method_in_buggy.keys()))-1])
    change_methods = list(set(change_methods))
    change_methods.sort(key=lambda x: int(x.split('::')[-1]))
    return change_methods

if __name__ == '__main__':
    changed = {}
    changes, filepath = parse_changes('changed_lines.txt')

    for bug_id in changes.keys():
        buggy_file_path = filepath[bug_id][0]
        fixed_file_path = filepath[bug_id][1]

        if os.path.isfile(buggy_file_path) and os.path.isfile(fixed_file_path):
            change_methods = find_changed_methods(changes[bug_id], buggy_file_path, fixed_file_path)
            
            if len(change_methods):
                changed[bug_id.split('_')[0]+bug_id.split('_')[1]] = change_methods
        else:
            print("파일이 존재하지 않습니다.")
    
    with open('changed_methods.json', 'w', encoding='utf-8') as json_file:
        json.dump(changed, json_file, ensure_ascii=False, indent=4)
