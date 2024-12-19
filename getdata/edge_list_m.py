import javalang
import re
from main import Tree
import numpy as np
file_path = '/home/dlgudwls/CS454/javaprojects/lang_1_fixed/src/main/java/org/apache/commons/lang3//math/NumberUtils.java'
file_path_without_extension = file_path[:-5]
class_name = file_path_without_extension.split('/')[-1]

def find_calling(node, all_methods):
    calling = []
    if isinstance(node, javalang.tree.MethodInvocation):
        if node.qualifier:
            func_name = str(node.qualifier) + '::' + str(node.member)
        else:
            func_name = class_name + '::' + str(node.member)

        func_name = func_name
        if func_name in all_methods:
            calling.append(func_name)

    if hasattr(node, 'children'):
        for child in node.children:
            if child == None or []:
                continue
            if isinstance(child, list):
                for littlechild in child:
                    calling = calling + find_calling(littlechild, all_methods)
            else:
                calling = calling + find_calling(child, all_methods)
    return calling

def get_all_methods(file_path):
    methods = []
    with open(file_path, 'r', encoding='utf-8') as file:
        java_code = file.read()

    tree = javalang.parse.parse(java_code)
    for node in tree.types:
        for method in node.methods:
            methods.append(class_name + '::' + str(method.name))
    return methods

def get_all_callings(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        java_code = file.read()

    tree = javalang.parse.parse(java_code)

    calling_relation = {}
    for node in tree.types:
        for method in node.methods:
            calling = find_calling(method, get_all_methods(file_path))
            calling_relation[class_name + '::' + str(method.name) + '::' + str(method.position[0])] = calling
    return calling_relation

if __name__ == "__main__":
    call_rel = get_all_callings(file_path)
    print(len(call_rel))
    print(call_rel)