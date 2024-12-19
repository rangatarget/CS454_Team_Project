import os
import javalang
import json

index = 0

def process_file_path(file_path):
    # .java 확장자 제거
    if file_path.endswith('.java'):
        file_path = file_path[:-5]  # .java의 길이인 5를 빼줌
    
    # 'org' 왼쪽 부분 제거
    if 'org' in file_path:
        file_path = file_path.split('org', 1)[1]  # 'org'를 기준으로 나누고 오른쪽 부분만 가져옴
    
    return 'org' + file_path

def get_method_index_pair(file_path):
    index = 0
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
            # key = f"{process_file_path(file_path)}::{method.name}::({param_types_str})::{method.position[0]}"
            key = f"{process_file_path(file_path)}::{method.name}::({param_types_str})"
            method_index[key] = index
            
    return method_index

if __name__ == '__main__':

    modified_file_per_bug = {}
    with open('modified_class.txt', 'r') as modified:
        lines = [line.strip() for line in modified.readlines()]
        for line in lines:
            bug_id, modified_class = int(line.split(',')[0]), line.split(',')[1].strip('"')
            modified_class = modified_class.replace('.', '/')
            modified_file_per_bug[bug_id] = modified_class

    previous_co_changed = []
    with open('changed_info.json', 'r') as changed_info:
        changed_info = json.load(changed_info)

    co_change = {}
    co_change_index = {}

    # iterate over reverse bug ids (bigger id -> more past)
    for bug_id in sorted(modified_file_per_bug.keys(), reverse = True):

        # changed method for this bug id
        changed_method = []
        key = f'lang{bug_id}'
        if key in changed_info:
            info = changed_info[key]
            for method in info:
                pos = method.rfind('::')
                method = method[:pos]
                changed_method.append(method)

        # Project-specific file path (35 for Lang)
        if bug_id <= 35:
            file_name = f'/src/main/java/{modified_file_per_bug[bug_id]}.java'
        else:
            file_name = f'/src/java/{modified_file_per_bug[bug_id]}.java'
        file_path = f'./{bug_id}b/{file_name}'

        if os.path.isfile(file_path):
            method_index_dict = get_method_index_pair(file_path)
            
            print("method number:", len(method_index_dict))
            print(method_index_dict)

            # find co-changed methods using previous co-changed methods
            for method in changed_method:
                for co_changed in previous_co_changed:
                    if method in co_changed:
                        if not co_change.get(bug_id):
                            co_change[bug_id] = [co_changed]
                        else:
                            co_change[bug_id].append(co_changed)

            # convert method name to method index
            if bug_id in co_change:
                for co_changed in co_change[bug_id]:
                    co_changed = list(set(co_changed))
                    co_changed_index = []
                    for method in co_changed:
                        co_changed_index.append(method_index_dict[method])
                    if not co_change_index.get(bug_id):
                        co_change_index[bug_id] = [co_changed_index]
                    else:
                        co_change_index[bug_id].append(co_changed_index)

        else:
            print("파일이 존재하지 않습니다.")

        # append previous co-changed methods after extracting method index
        # -> only consider the methods that are co-changed before
        # info of some bug id is missing because method was removed or created
        if len(changed_method) > 1:
            previous_co_changed.append(changed_method)

        # save co-changed method index
        output_dir = "./co_change_methods"
        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(output_dir, f"co_change_{bug_id}.txt")
        with open(output_file, 'w') as out:
            if not co_change_index.get(bug_id):
                out.write("\n")
            else:
                for line in co_change_index[bug_id]:
                    if not line == "\n":
                        out.write(f"{line}\n")
                    else:
                        out.write("\n")
        print(f"Co-change index has been saved to {output_file}")

        print("=" * 80)

    print(co_change_index)