from __future__ import print_function

import argparse

import scipy.sparse as sp
import numpy as np
import torch

import data_utils
import time

ap = argparse.ArgumentParser()
ap.add_argument("-d", "--dataset", type=str, default="aifb",
                help="Dataset string ('aifb', 'mutag', 'bgs', 'am')")
ap.add_argument("-e", "--epochs", type=int, default=50,
                help="Number training epochs")
ap.add_argument("-hd", "--hidden", type=int, default=16,
                help="Number hidden units")
ap.add_argument("-do", "--dropout", type=float, default=0.,
                help="Dropout rate")
ap.add_argument("-b", "--bases", type=int, default=-1,
                help="Number of bases used (-1: all)")
ap.add_argument("-lr", "--learnrate", type=float, default=0.01,
                help="Learning rate")
ap.add_argument("-l2", "--l2norm", type=float, default=0.,
                help="L2 normalization of input weights")

fp = ap.add_mutually_exclusive_group(required=False)
fp.add_argument('--validation', dest='validation', action='store_true')
fp.add_argument('--testing', dest='validation', action='store_false')
ap.set_defaults(validation=True)

args = vars(ap.parse_args())
print(args)

# Define parameters
DATASET = args['dataset']
NB_EPOCH = args['epochs']
VALIDATION = args['validation']
LR = args['learnrate']
L2 = args['l2norm']
HIDDEN = args['hidden']
BASES = args['bases']
DO = args['dropout']


def csr_zero_rows(csr, rows_to_zero):
    """Set rows given by rows_to_zero in a sparse csr matrix to zero.
    NOTE: Inplace operation! Does not return a copy of sparse matrix."""
    rows, cols = csr.shape
    mask = np.ones((rows,), dtype=np.bool)
    mask[rows_to_zero] = False
    nnz_per_row = np.diff(csr.indptr)

    mask = np.repeat(mask, nnz_per_row)
    nnz_per_row[rows_to_zero] = 0
    csr.data = csr.data[mask]
    csr.indices = csr.indices[mask]
    csr.indptr[1:] = np.cumsum(nnz_per_row)
    csr.eliminate_zeros()
    return csr


def csc_zero_cols(csc, cols_to_zero):
    """Set rows given by cols_to_zero in a sparse csc matrix to zero.
    NOTE: Inplace operation! Does not return a copy of sparse matrix."""
    rows, cols = csc.shape
    mask = np.ones((cols,), dtype=np.bool)
    mask[cols_to_zero] = False
    nnz_per_row = np.diff(csc.indptr)

    mask = np.repeat(mask, nnz_per_row)
    nnz_per_row[cols_to_zero] = 0
    csc.data = csc.data[mask]
    csc.indices = csc.indices[mask]
    csc.indptr[1:] = np.cumsum(nnz_per_row)
    csc.eliminate_zeros()
    return csc


def sp_vec_from_idx_list(idx_list, dim):
    """Create sparse vector of dimensionality dim from a list of indices."""
    shape = (dim, 1)
    data = np.ones(len(idx_list))
    row_ind = list(idx_list)
    col_ind = np.zeros(len(idx_list))
    return sp.csr_matrix((data, (row_ind, col_ind)), shape=shape)


def sp_row_vec_from_idx_list(idx_list, dim):
    """Create sparse vector of dimensionality dim from a list of indices."""
    shape = (1, dim)
    data = np.ones(len(idx_list))
    row_ind = np.zeros(len(idx_list))
    col_ind = list(idx_list)
    return sp.csr_matrix((data, (row_ind, col_ind)), shape=shape)


def get_neighbors(adj, nodes):
    """Takes a set of nodes and a graph adjacency matrix and returns a set of neighbors."""
    sp_nodes = sp_row_vec_from_idx_list(list(nodes), adj.shape[1])
    sp_neighbors = sp_nodes.dot(adj)
    neighbors = set(sp.find(sp_neighbors)[1])  # convert to set of indices
    return neighbors


def bfs(adj, roots):
    """
    Perform BFS on a graph given by an adjaceny matrix adj.
    Can take a set of multiple root nodes.
    Root nodes have level 0, first-order neighors have level 1, and so on.]
    """
    visited = set()
    current_lvl = set(roots)
    while current_lvl:
        for v in current_lvl:
            visited.add(v)

        next_lvl = get_neighbors(adj, current_lvl)
        next_lvl -= visited  # set difference
        yield next_lvl

        current_lvl = next_lvl


from dgl.contrib.data import load_data
data = load_data(dataset='aifb')
num_nodes = data.num_nodes
num_rels = data.num_rels
num_classes = data.num_classes
labels = data.labels
train_idx = data.train_idx
# split training and validation set
val_idx = train_idx[:len(train_idx) // 5]#前20%做验证
train_idx = train_idx[len(train_idx) // 5:]#剩下做训练

# edge type and normalization factor
edge_type = torch.from_numpy(data.edge_type)
edge_norm = torch.from_numpy(data.edge_norm).unsqueeze(1)

labels = torch.from_numpy(labels).view(-1)


if __name__=='__main__':
    data_utils.start()