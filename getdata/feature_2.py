import javalang
import re
from main import Tree
import numpy as np
import torch
import sys
index = 0

def convert_to_tree(node, loaded_glove):
    global index
    vec_dict = {}
    tree_node = Tree()
    index += 1
    tree_node.id = index
    subtokens = extract_subtokens(str(node))
    vec_for_node = generate_embeddings(subtokens, loaded_glove)
    vec_dict[index] = vec_for_node
    if hasattr(node, 'children'):
        for child in node.children:
            if child == None or []:
                continue
            if isinstance(child, list):
                for littlechild in child:
                    child_tree, child_vec_dict = convert_to_tree(littlechild, loaded_glove)
                    tree_node.add_child(child_tree)
                    vec_dict.update(child_vec_dict)
            else:
                child_tree, child_vec_dict = convert_to_tree(child, loaded_glove)
                tree_node.add_child(child_tree)
                vec_dict.update(child_vec_dict)
    return tree_node, vec_dict

def method_to_tree(file_path, glove_path='glove.6B.100d.txt'):
    global index
    with open(file_path, 'r', encoding='utf-8') as file:
        java_code = file.read()
    tree = javalang.parse.parse(java_code)

    loaded_glove = load_glove_embeddings(glove_path)
    method_info = []
    for node in tree.types:
        for method in node.methods:
            if method.name == 'isNumber':
                method.documentation = None
            index = 0
            method_tree, vector_dict = convert_to_tree(method, loaded_glove)
            method_info.append((method_tree, vector_dict))
    return method_info, [m.name for m in node.methods]

def load_glove_embeddings(glove_file):
    embeddings = {}
    with open(glove_file, 'r', encoding='utf-8') as f:
        for line in f:
            values = line.split()
            word = values[0]
            vector = np.array(values[1:], dtype='float32')
            embeddings[word] = vector
    return embeddings

def extract_subtokens(text):
    cleaned_text = re.sub(r'[^\w\s]', ' ', text)
    tokens = cleaned_text.split()
    subtokens = []
    for token in tokens:
        split_tokens = re.findall(r'[A-Z][a-z]*|[a-z]+', token)
        subtokens.extend(split_tokens)
    lower_subtokens = [subtoken.lower() for subtoken in subtokens]
    return lower_subtokens

def generate_embeddings(tokens, glove_embeddings):
    embeddings = []
    for token in tokens:
        if token in glove_embeddings:
            embeddings.append(glove_embeddings[token])
    if len(embeddings) == 0:
        return np.zeros((1,100))
    return np.mean(embeddings, axis=0) 

if __name__ == "__main__":
    classname = sys.argv[1]
    bug_id = sys.argv[2]
    file_path = '/home/dlgudwls/CS454/javaprojects/' + classname
    method_info, methods = method_to_tree(file_path)
    print(len(method_info))
    torch.save(method_info, f'feature2/{bug_id}.pt')
