import torch
from torch.nn import GRU, Dropout, ReLU, Linear, Module, Softmax
from torch.autograd import Variable as Var
from torch_geometric.nn import GCNConv
import numpy as np


class TreeSummarize(Module):
    def __init__(self, in_dim, mem_dim, dropout1):
        super(TreeSummarize, self).__init__()
        self.in_dim = in_dim
        self.mem_dim = mem_dim
        self.ioux = Linear(self.in_dim, 3 * self.mem_dim)
        self.iouh = Linear(self.mem_dim, 3 * self.mem_dim)
        self.fx = Linear(self.in_dim, self.mem_dim)
        self.fh = Linear(self.mem_dim, self.mem_dim)
        self.H = []
        self.drop = Dropout(dropout1)

    def node_forward(self, inputs, child_c, child_h):
        if isinstance(inputs, np.ndarray):
            inputs = torch.from_numpy(inputs)

        if inputs.dtype != torch.float32:
            inputs = inputs.float()

        while inputs.dim() >= 2:
            inputs = inputs.squeeze(0)

        inputs = torch.unsqueeze(inputs, 0)
        child_h_sum = torch.sum(child_h, dim=0)
        iou = self.ioux(inputs) + self.iouh(child_h_sum)

        if iou.dim() == 3:
            iou = iou.squeeze(0)

        i, o, u = torch.split(iou, iou.size(1) // 3, dim=1)
        i, o, u = torch.sigmoid(i), torch.sigmoid(o), torch.tanh(u)

        f = torch.sigmoid(self.fh(child_h) + self.fx(inputs).repeat(len(child_h), 1))
        fc = torch.mul(f, child_c)
        c = torch.mul(i, u) + torch.sum(fc, dim=0)
        h = torch.mul(o, torch.tanh(c))
        self.H.append(h)
        return c, h

    def forward(self, data):
        tree = data[0]
        inputs = data[1]
        _ = [self.forward([tree.children[idx], inputs]) for idx in range(tree.num_children)]

        if tree.num_children == 0:
            child_c = torch.zeros(1, self.mem_dim, dtype=torch.float32, device=inputs[tree.id].device)
            child_h = torch.zeros(1, self.mem_dim, dtype=torch.float32, device=inputs[tree.id].device)
        else:
            child_c, child_h = zip(*map(lambda x: x.state, tree.children))
            child_c, child_h = torch.cat(child_c, dim=0), torch.cat(child_h, dim=0)
        tree.state = self.node_forward(inputs[tree.id], child_c, child_h)
        return tree.state


class FixLocator(torch.nn.Module):
    def __init__(self, h_size, feature_representation_size, drop_out_rate, layer_num, code_cover_len):
        super(FixLocator, self).__init__()
        self.h_size = h_size
        self.layer_num = layer_num
        self.code_cover_len = code_cover_len
        self.feature_representation_size = feature_representation_size
        self.drop_out_rate = drop_out_rate
        self.tree_1 = TreeSummarize(self.feature_representation_size, self.h_size*3, self.drop_out_rate)
        self.tree_2 = TreeSummarize(self.feature_representation_size, self.h_size*3, self.drop_out_rate)
        self.gru_1 = GRU(input_size=self.feature_representation_size, hidden_size=self.h_size*3, batch_first=True)
        for i in range(self.layer_num):
            exec('self.conv_method_{} = GCNConv(self.h_size*4, self.h_size*4)'.format(i))
        self.dropout = Dropout(self.drop_out_rate)
        self.relu = ReLU(inplace=True)
        self.resize_1 = Linear(self.h_size*3, self.h_size)
        self.resize_2 = Linear(self.h_size*3, self.h_size)
        self.resize_3 = Linear(self.h_size*3, self.h_size)
        self.resize_4 = Linear(self.code_cover_len, self.h_size)
        self.resize_7 = Linear(self.h_size * 4, 2)
        self.softmax = Softmax(dim=1)

    def forward(self, data):
        node_features = data.x

        edge_info_1 = data.edge_index

        if edge_info_1.dtype != torch.int64:
            edge_info_1 = edge_info_1.long()

        feature_1 = node_features[0]
        feature_2 = node_features[1]
        feature_3 = node_features[2]
        feature_4 = node_features[3]

        feature_vec1, _ = self.gru_1(feature_1)
        feature_vec1 = self.dropout(feature_vec1)
        feature_vec1 = torch.reshape(feature_vec1[:, -1, :], (-1, 3*self.h_size))
        feature_vec4 = feature_4

        feature_vec2 = None
        for i in range(len(feature_2)):
            if i == 0:
                if feature_2[i][0] == None:
                    feature_vec2 = torch.zeros(1, self.h_size*3, dtype=torch.float32)
                else:
                    _, feature_vec2 = self.tree_1(feature_2[i])
            else:
                if feature_2[i][0] == None:
                    feature_vec_temp = torch.zeros(1, self.h_size*3, dtype=torch.float32)
                else:
                    _, feature_vec_temp = self.tree_1(feature_2[i])
                feature_vec2 = torch.cat((feature_vec2, feature_vec_temp), 0)

        feature_vec3 = None
        for i in range(len(feature_3)):
            if i == 0:
                if feature_3[i][0] == None:
                    feature_vec3 = torch.zeros(1, self.h_size*3, dtype=torch.float32)
                else:
                    _, feature_vec3 = self.tree_2(feature_3[i])
            else:
                if feature_3[i][0] == None:
                    feature_vec_temp = torch.zeros(1, self.h_size*3, dtype=torch.float32)
                else:
                    _, feature_vec_temp = self.tree_2(feature_3[i])
                feature_vec3 = torch.cat((feature_vec3, feature_vec_temp), 0)

        f_1 = self.resize_1(feature_vec1)
        f_2 = self.resize_2(feature_vec2)
        f_3 = self.resize_3(feature_vec3)
        f_4 = self.resize_4(feature_vec4)

        if f_4.shape[0] < f_1.shape[0]:
            zeros = torch.zeros((1, f_1.shape[1]), dtype=torch.float32)
            f_4 = torch.cat((zeros, f_4), 0)
        elif f_4.shape[0] > f_1.shape[0]:
            f_4 = f_4[1:, :]

        m_f = torch.cat((f_1, f_2, f_3, f_4), 1)

        for i in range(self.layer_num):
            if i < self.layer_num-1:
                exec('m_f = self.conv_method_{}(m_f, edge_info_1)'.format(i))
                m_f = self.relu(m_f)
            if i == self.layer_num-1:
                exec('m_f = self.conv_method_{}(m_f, edge_info_1)'.format(i))
                m_f = self.resize_7(m_f)
                m_f = self.softmax(m_f)

        return m_f.transpose(0, 1)