import re, javalang
import numpy as np
import torch
import sys, os

def remove_comments(code):
    code = re.sub(r'//.*', '', code)
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    return code

def extract_methods_from_java_file(file_path, function_lines):
    with open(file_path, 'r') as file:
        java_code = file.read()
    
    lines = java_code.splitlines()
    functions = []

    for i in range(len(function_lines)):
        start_line = function_lines[i][0]
        end_line = function_lines[i][1]

        function_content = "\n".join(lines[start_line:end_line]).strip()
        cleaned_code = remove_comments(function_content)
        functions.append(extract_subtokens(cleaned_code))
    return functions

def extract_subtokens(text):
    cleaned_text = re.sub(r'[^\w\s]', ' ', text)
    tokens = cleaned_text.split()
    subtokens = []
    for token in tokens:
        split_tokens = re.findall(r'[A-Z][a-z]*|[a-z]+', token)
        subtokens.extend(split_tokens)
    lower_subtokens = []
    for subtoken in subtokens:
        lower_subtokens.append(subtoken.lower())
    return lower_subtokens

def get_last_line(node):
    max_line = 0
    if hasattr(node, 'children'):
        for child in node.children:
            if child == None or []:
                continue
            if isinstance(child, list):
                for littlechild in child:
                    if hasattr(node, 'position') and node.position:
                        max_line = max(get_last_line(littlechild), node.position[0])
                    else:
                        max_line = get_last_line(littlechild)
            else:
                if hasattr(node, 'position') and node.position:
                    max_line = max(get_last_line(child), node.position[0])
                else:
                    max_line = get_last_line(child)
    return max_line

def method_to_subtokens(java_file_path):

    with open(java_file_path, 'r', encoding='utf-8') as file:
            java_code = file.read()

    tree = javalang.parse.parse(java_code)

    method_start_end = []
    for node in tree.types:
        for method in node.methods:
            if hasattr(node, 'position') and node.position:
                end_line = get_last_line(method)
            else:
                end_line = 0
            method_start_end.append((method.position[0], end_line))

    methods = extract_methods_from_java_file(java_file_path, method_start_end)
    return methods

def load_glove_embeddings(glove_file):
    embeddings = {}
    with open(glove_file, 'r', encoding='utf-8') as f:
        for line in f:
            values = line.split()
            word = values[0]
            vector = np.array(values[1:], dtype='float32')
            embeddings[word] = vector
    return embeddings

def generate_embeddings(tokens, glove_embeddings):
    embeddings = []
    for token in tokens:
        if token in glove_embeddings:
            embeddings.append(glove_embeddings[token])
    return embeddings

def get_all_embeddings(java_file_path):
    glove_embeddings = load_glove_embeddings('glove.6B.100d.txt')
    subtokens = method_to_subtokens(java_file_path)
    embeddings = []
    max_len = 0
    for content in subtokens:
        data = generate_embeddings(content, glove_embeddings)
        max_len = max(max_len, len(data))
        embeddings.append(data)
    for vectors in embeddings:
        lenvector = len(vectors)
        for i in range(max_len - lenvector):
            vectors.append(np.zeros((100, )))
    return torch.tensor(np.array(embeddings))

if __name__ == '__main__':
    classname = sys.argv[1]
    bug_id = sys.argv[2]
    file_path = '/home/dlgudwls/CS454/javaprojects/' + classname
    if not os.path.exists(file_path):
        file_path = file_path.replace('/main', '')
    emb = get_all_embeddings(file_path)
    print(emb.shape)
    torch.save(emb, f'feature1/{bug_id}.pt')
    