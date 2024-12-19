import numpy as np
import os.path as osp
import torch
import os
from main import Tree
from torch_geometric.data import Data

index = []

k = 1
for bug_id in range(1, 66):
    if not os.path.exists(osp.join(os.getcwd(), 'custom_processed/feature1/lang{}.pt'.format(bug_id))):
        continue
    
    feature1 = torch.load(osp.join(os.getcwd(), 'custom_processed/feature1/lang{}.pt'.format(bug_id)))
    feature2 = torch.load(osp.join(os.getcwd(), 'custom_processed/feature2/lang{}.pt'.format(bug_id)))
    feature3 = torch.load(osp.join(os.getcwd(), 'custom_processed/feature3/lang{}.pt'.format(bug_id)))
    feature4 = torch.load(osp.join(os.getcwd(), 'custom_processed/coverage_matrices_torch/coverage_matrix_{}.pt'.format(bug_id)))
    edge_list = torch.load(osp.join(os.getcwd(), 'custom_processed/edges_torch/lang{}.pt'.format(bug_id)))
    y = torch.load(osp.join(os.getcwd(), 'custom_processed/labels/label_{}.pt'.format(bug_id)))

    feature1 = feature1.to(torch.float32)

    for i in range(len(feature2)):
        for value in feature2[i][1].values():
            value = torch.tensor(value)

    for i in range(len(feature3)):
        if feature3[i][1] is None:
            continue
        for value in feature3[i][1].values():
            value = torch.tensor(value)

    feature4 = np.array(feature4)
    feature4 = torch.tensor(feature4).to(torch.float32)

    edge_list = np.array(edge_list) - 1
    edge_list = torch.tensor(edge_list)

    new_data = Data(
        x=[feature1, feature2, feature3, feature4],
        y=y,
        edge_index=edge_list
    )

    torch.save(new_data, 'custom_processed/data_{}.pt'.format(k))
    index.append([k])

    k += 1

np.save(osp.join(os.getcwd(), 'custom_processed/index.npy'), index)