# -*-coding:utf-8-*-
# Author:zhy
# CreateDate: 2020/12/21 16:41
# Description:
import numpy as np
import matplotlib.pyplot as plt
import math
import csv
import random
import time

SHARDS = 100
formation_file = '../../data/formation_latency100000_epoch24.csv'
txs_file = '../../data/blockhash.txt'
C0_CAPACITY_MASTER = SHARDS * 800  # MB
WEIGHT_NUM_DOMAIN_VIEWS = 1.5  #
WEIGHT_AOI = 1.0  #

all_CURVE = []

class SA:
    def __init__(self, formation_file, txs_file):
        # ---- 1 Read the Given path data :
        self.features = {}
        self.gCNT_OPT_SLOTS_J = 0

        formation_lan = []
        txs = []
        txs_total = []
        with open(formation_file, 'r') as f:
            for lines in f:
                line = lines.strip('\n').split(',')
                if 'shard' in line[0]:
                    continue
                formation_lan.append(line)
        seed = 1234
        random.seed(seed)
        with open(txs_file, 'r') as f:
            for lines in f:
                line = lines.strip('\n').split(' ')[-1]
                txs.append(line)
            for i in range(24):
                random.shuffle(txs)
                temp = np.array(txs)
                txs_total.append(temp)

            for count in range(24):
                for j in range(SHARDS):
                    OPT_slot_id = int(count + 1)
                    Controller_id = int(j)
                    dLatency_syn = float(formation_lan[count][j]) + 54.5
                    dSize_domain_view = float(txs_total[count][j])

                    # --- record each item of syn-record
                    self.gCNT_OPT_SLOTS_J = OPT_slot_id

                    if OPT_slot_id not in self.features.keys():
                        self.features[OPT_slot_id] = [[Controller_id, dLatency_syn, dSize_domain_view]]
                    else:
                        self.features[OPT_slot_id].append([Controller_id, dLatency_syn, dSize_domain_view])

            with open("sa_features.csv",'w',encoding='utf-8',newline='') as f:
                writer = csv.writer(f)
                for epoch in range(24):
                    lat = [self.features[epoch + 1][s][1] for s in range(SHARDS)]
                    tx = [self.features[epoch + 1][s][2] for s in range(SHARDS)]
                    print(lat)
                    print(tx)
                    writer.writerow(lat)
                    writer.writerow(tx)

    # define aim function
    def aimFunction(self, epoch, select_index, feature=None, lenth=0):
        dAoI_total = 0.0
        Txs_total = 0
        total_num_of_domainViews = 0
        sysUtility = -9999998
        miningpool = 0
        # print("select_index", select_index)
        for i in range(0, lenth):
            total_num_of_domainViews += select_index[i]
        # ================================================
        # ---- 2 calculate the AoI
        lstLatency_jni = []
        for i in range(0, lenth):
            lstLatency_jni.append(select_index[i] * feature[i][1])

        dMoment_execute_optimization_in_master_tj = max(lstLatency_jni)

        for i in range(0, lenth):
            dAoI_ctrler_i = select_index[i] * (
                    dMoment_execute_optimization_in_master_tj - feature[i][1])  #
            # print("dAoI_ctrler_i", dAoI_ctrler_i)
            dAoI_total += dAoI_ctrler_i
        # ================================================
        # ---- 3 calculate the Txs
        for i in range(0, lenth):
            dSize_domain_jni = select_index[i] * feature[i][2]
            Txs_total += dSize_domain_jni

        ## ---- 4. calculate Objectives
        if C0_CAPACITY_MASTER >= Txs_total and total_num_of_domainViews >= 1:
            # print(total_num_of_domainViews, select_index)
            miningpool = '%.2f' % (Txs_total / dMoment_execute_optimization_in_master_tj)
            sysUtility = Txs_total * WEIGHT_NUM_DOMAIN_VIEWS - dAoI_total * WEIGHT_AOI

        return sysUtility, select_index, total_num_of_domainViews, Txs_total, dAoI_total, miningpool

    def anneal(self, iter=100, epoch=1, feature=None, lenth=0):
        T = 1000  # initiate temperature
        Tmin = 10  # minimum value of terperature
        x = np.zeros((1, lenth), dtype=float)
        x = np.random.uniform(size=x.shape)
        # x = (np.random.rand(SHARDS) * 0.9 + 0.1).tolist()  # initiate x
        utility = -9999998  # initiate result
        t = 0  # time
        curve = []
        Txs_total = 0
        DAoI_total = 0
        Machines = 0  # 选择个数
        miningpool = 0
        while T >= Tmin:
            for i in range(iter):
                # calculate utility
                # utility, select_index, curve, machines, DAoI_total = self.aimFunction(epoch, x)
                # generate a new x in the neighboorhood of x by transform function
                xNew = x + np.random.uniform(size=x.shape, low=-0.055, high=0.055) * T
                # if (0 <= xNew and xNew <= 1):
                # xNew = xNew.tolist()
                for j in range(len(xNew[0])):
                    if xNew[0][j] < 0.5:
                        xNew[0][j] = 0
                    elif xNew[0][j] >= 0.5:
                        xNew[0][j] = 1
                newutility, Leader_pos, machines, txs_total, dAoI_total, miningpool = self.aimFunction(epoch, xNew[0],
                                                                                                       feature, lenth)
                if newutility - utility > 0:
                    x = xNew
                    utility = newutility
                    curve.append(newutility)
                    Txs_total = txs_total
                    DAoI_total = dAoI_total
                    Machines = machines
                else:
                    # metropolis principle
                    p = math.exp(-(utility - newutility) / T)
                    r = np.random.uniform(low=0, high=1)
                    if r < p:
                        x = xNew
            t += 1
            # print(t)
            T = 1000 / (1 + t)

        print(len(x[0]))
        # print(x, utility)
        return utility, x, curve, Machines, Txs_total, DAoI_total, miningpool

    # 监听函数
    def listen(self, epoch):
        Log_final_result = open('SA_online_data.csv','a',encoding='utf-8',newline='')
        writer = csv.writer(Log_final_result)

        L = self.features[epoch]
        L.sort(key=lambda x: x[1], reverse=False)
        first_per = 0.5
        total = 0
        end_per = 0.8
        i = 0
        CURVE = []
        # 判断条件
        while i <= len(L) * end_per:
            if i >= len(L) * first_per and total >= C0_CAPACITY_MASTER:
                lat = [L[i][1] for i in range(i)]
                TXS = [L[i][2] for i in range(i)]
                writer.writerow(lat)
                writer.writerow(TXS)

                # --- End of this function :~
            total = total + L[i][2]
            # print(total, C0_CAPACITY_MASTER)
            i = i + 1
        return

    # 主程序
    def main(self):
        # 新建
        Log_final_result = open('SA_online_data.csv', 'w', encoding='utf-8', newline='')
        Log_final_result.close()

        epoch = 1
        while epoch <= 5:
            print("epoch:", epoch)
            self.listen(epoch)
            epoch = epoch + 1


if __name__ == '__main__':
    sa = SA(formation_file, txs_file)
    for i in range(0, 5):
        sa.main()
