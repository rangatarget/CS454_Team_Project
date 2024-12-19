import json
import os, torch
import warnings

warnings.filterwarnings("ignore")
json_file_path = 'changed_methods.json'

with open(json_file_path, 'r') as file:
    data = json.load(file)

existing_index = [int(id[4:]) for id in data.keys()]

for i in reversed(existing_index):
    print(f'id : lang{i}')
    current_feature1 = torch.load(f'feature1/lang{i}.pt').tolist()
    feature3 = []
    for j in range(len(current_feature1)):
        highest_cosine = None
        corresponding_feature2 = None
        searchspace = [ind for ind in existing_index if ind > i and data[f'lang{ind}'][0].split('::')[0] == data[f'lang{i}'][0].split('::')[0]]
        for k in searchspace:
            current_one_method = torch.tensor(current_feature1[j]).clone().tolist()
            fault_index = torch.load(f'label_m/lang{k}.pt')
            previous_methods = torch.load(f'feature1/lang{k}.pt').tolist()
            for w in range(len(previous_methods)):
                if w not in fault_index:
                    continue
                faulty_method = previous_methods[w]
                len1 = len(current_one_method)
                len2 = len(faulty_method)
                if len1 < len2:
                    current_one_method += [torch.zeros(torch.tensor(current_one_method[0]).size())] * (len2 - len1)
                else:
                   faulty_method += [torch.zeros(torch.tensor(faulty_method[0]).size())] * (len1 - len2)
                
                cosine_score = 0
                for v1 in range(len(faulty_method)):
                        cosine_score += torch.nn.functional.cosine_similarity(torch.tensor(faulty_method[v1]).unsqueeze(0), torch.tensor(current_one_method[v1]).unsqueeze(0)).item()
                cosine_score /= len(current_one_method)    

                if (highest_cosine == None) or cosine_score > highest_cosine:
                    highest_cosine = cosine_score
                    corresponding_feature2 = torch.load(f'feature2/lang{k}.pt')[w]
        if corresponding_feature2:
            feature3.append(corresponding_feature2)
        else:
            feature3.append((None, None))
    torch.save(feature3, f'feature3/lang{i}.pt')
