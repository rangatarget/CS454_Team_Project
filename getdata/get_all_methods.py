import os
import javalang
import sys
import json
import torch

index = 0

def process_file_path(file_path):
    if file_path.endswith('.java'):
        file_path = file_path[:-5]

    if 'org' in file_path:
        file_path = file_path.split('org', 1)[1]
    
    return 'org' + file_path

def get_method_index_pair(file_path):
    global index
    method_index = {}
    
    with open(file_path, 'r', encoding='utf-8') as file:
        java_code = file.read()

    tree = javalang.parse.parse(java_code)
    for node in tree.types:
        for method in node.methods:
            index += 1

            param_types = [param.type.name for param in method.parameters] if method.parameters else []
            param_types_str = ', '.join(param_types)

            key = f"{process_file_path(file_path)}::{method.name}::({param_types_str})::{method.position[0]}"
            method_index[key] = index
            
    return method_index

if __name__ == '__main__':
    index = 0
    file_path = '/home/dlgudwls/CS454/javaprojects/lang_22_buggy/src/main/java/org/apache/commons/lang3/math/Fraction.java'
    
    if len(sys.argv) > 1 and sys.argv[1]: ## get label
        file_path = sys.argv[1]
        id = sys.argv[2]
        if os.path.isfile('/home/dlgudwls/CS454/javaprojects/' + file_path):
            method_index_dict = get_method_index_pair('/home/dlgudwls/CS454/javaprojects/' + file_path)
        else:
            method_index_dict = get_method_index_pair('/home/dlgudwls/CS454/javaprojects/' + file_path.replace('/main', ''))
        json_file_path = 'changed_methods.json'

        with open(json_file_path, 'r') as file:
            data = json.load(file)

        fault_index = []
        value_list = data[id]
        if value_list[0].split('::')[0] + '.java' == 'org' + file_path.split('org', 1)[1]:
            print(value_list)
            for value in value_list:
                fault_index.append(method_index_dict[value])
        label = torch.zeros(len(list(method_index_dict)))
        for index in fault_index:
            label[index-1] = 1
        torch.save(label, f'label_m/lang{id[4:]}.pt')

    else:
        if os.path.isfile(file_path):
            method_index_dict = get_method_index_pair(file_path)
            
            print(len(method_index_dict))
            print(method_index_dict)
        else:
            print("no file")
