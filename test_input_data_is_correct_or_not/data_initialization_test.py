# -*-coding:utf-8-*-
# Author:Xiaowen Peng
# CreateDate: 2020/12/29 20:19
# Description:
'''测试初始化的数据是否一样'''

import csv

MAFILE = 'ma_features.csv'
SAFILE = 'sa_features.csv'

madata = []
sadata = []

with open(MAFILE,'r') as f:
    reader = csv.reader(f)
    for row in reader:
        row = [eval(row[i]) for i in range(len(row))]
        madata.append(row)

with open(SAFILE,'r') as f:
    reader = csv.reader(f)
    for row in reader:
        row = [eval(row[i]) for i in range(len(row))]
        sadata.append(row)

len_madata = len(madata)
len_sadata = len(sadata)
assert len_madata == len_sadata

import numpy as np
for i in range(0,len_madata,2):
    latency_ma = madata[i]
    latency_sa = sadata[i]
    txs_ma = madata[i+1]
    txs_sa = sadata[i+1]


    latency_ma = np.array(latency_ma)
    latency_sa = np.array(latency_sa)
    txs_ma = np.array(txs_ma)
    txs_sa = np.array(txs_sa)

    tmp = np.equal(latency_ma,latency_sa)

    diff_lat_idx = np.argwhere(tmp == False)

    tmp = np.equal(txs_ma,txs_sa)
    diff_txs_idx = np.argwhere(tmp == False)

    # diff_lat_idx.reshape(1,)
    # diff_txs_idx.reshape(1,)
    if len(diff_lat_idx) > 1:
        diff_lat_idx = np.concatenate(diff_lat_idx)
    if len(diff_txs_idx) > 1:
        diff_txs_idx = np.concatenate(diff_txs_idx)

    print(i / 2, "===============")
    print("diff_lat_idx = ", diff_lat_idx)
    print("diff_txs_idx = ", diff_txs_idx)

    if len(diff_lat_idx) > 0:
        print("diff latency_ma :",latency_ma[diff_lat_idx])
        print("diff latency_sa :",latency_sa[diff_lat_idx])
    if len(diff_txs_idx) > 0:
        print("diff txs_ma :",txs_ma[diff_txs_idx])
        print("diff txs_sa :",latency_sa[diff_txs_idx])