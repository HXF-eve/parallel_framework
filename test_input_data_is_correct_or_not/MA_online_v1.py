# -*-coding:utf-8-*-
# Author:Xiaowen Peng
# CreateDate: 2020/12/27 10:02
# Description:

import copy
import random
import math
import time
import csv
import threading
import numpy as np
from SimulateTime import SimulateTime
from GeneralTool import GeneralTool

seed = 1234
random.seed(seed)

DISPALY_SWITCH = False
DISPLAT_STEP = 100
# 周期记录MA过程中的utility
TS_LENGTH_LISTEN_SYSOBJ = 1  #

class MA_PX:
    def __init__(self, latency, txs_total, shard, epoch, C0_CAPACITY_MASTER, step_to_run):
        self.shard = shard
        self.epoch = epoch
        self.latency = None
        self.txs_total = None

        self.C0_CAPACITY_MASTER = C0_CAPACITY_MASTER

        self.WEIGHT_NUM_TX = 1.5
        self.WEIGHT_AOI = 1.0
        self.Beta = 20              ## The parameter in the theoretical derivation.
        self.Tau = 10

        Total_steps = 500
        self.STEP_TO_RUN = step_to_run
        self.T_threshold_An_EPOCH = Total_steps * self.STEP_TO_RUN  ## The total running period of system.

        self.Cumulative_Notification_times_X = 0
        self.Cumulative_TimerX_countDown_times = 0

        self.MODE_TIMER_X_CHECK = 'ONLY-1TIMER-EXPIRES-ALLOWED-PER-TIME'

        self.OBJ_FUN = []

        self.latency = latency
        self.txs_total = txs_total

        # self.latency = np.array(formation_lan).astype('float') + 54.5  # 加上consensus latency
        # self.txs_total = np.array(txs_total).astype('float')

        return

    def Initialization(self, nEpoch_j):
        # ----1 初始化
        # n = 1,2,... shard
        # i = 0, 1, ..., shard-1
        self.fn_x_ji = np.zeros((self.shard + 1, self.shard)).astype(int)   # feasible solutions to theMVComproblem
        self.I_list_all_shards = [i for i in range(self.shard)]
        self.objTool = GeneralTool('LatencySDNControlPlane2019')
        self.CURVE_IN_EPOCH = [[] for i in range(self.epoch)]

        # ----2 randomly pick n shard-indices from I
        for n in range(1, self.shard + 1):
            I_subset = self.objTool.Get_a_number_of_random_samples_from_a_list(self.I_list_all_shards, n)

            total_numTx = np.sum(self.txs_total[nEpoch_j][I_subset])

            # 小于C0_CAPACITY_MASTER 才是feasible
            if self.C0_CAPACITY_MASTER >= total_numTx:
                self.fn_x_ji[n][I_subset] = 1

        ## -----3. initialize the Var_x_ji.
        # self.Var_x_ji = np.zeros((self.shard,)).astype(int)

        self.Var_x_ji = {}
        for i in self.I_list_all_shards:
            if i not in self.Var_x_ji.keys():
                self.Var_x_ji[i] = 0
            self.Var_x_ji[i] = 0  ### EoF:~

        return

    def MarkovApproximateFunc(self, nEPOCH_idx):
        global TS_LENGTH_LISTEN_SYSOBJ

        ### ================ Reset the simulation time for each OPT-Slot.
        current_ts = 0.0  #
        self.objSysTime = SimulateTime(self.STEP_TO_RUN, 1.0)  ##
        # n = 1,2, ..., shard, 下标从1 开始取值, n = shard 时取不到，退出Set_timers_for_all_fjn， 因此为空
        self.Timers_fjn = [[] for i in range(self.shard + 1)]

        ### ================ Set all timers for the first time. ================
        ##------- Set-timer for flows:
        '''设置self.Timers_fjn'''
        self.Set_timers_for_all_fjn(nEPOCH_idx, current_ts)

        # print(self.Timers_fjn)    # for debug

        step_times_in_a_EPOCH = 0
        start_time = time.time()
        while (current_ts <= self.T_threshold_An_EPOCH):

            self.objSysTime.TimeStepForward()  ##
            current_ts = self.objSysTime.Get_CurrentTime()  ##
            step_times_in_a_EPOCH += 1  ##

            ##### -- I. listen to the event of any timerX's expiration.
            ret_TIMER_RESET_Msg, lstTimers_already_reseted = self.check_timerX_and_do_swap(current_ts, nEPOCH_idx)

            # debug
            # print(ret_TIMER_RESET_Msg, lstTimers_already_reseted)

            ### -- III.2 listen to the event of any Shard's RESET X_Msg.
            if 1 == ret_TIMER_RESET_Msg:
                self.RESET_all_Timers_for_fn_except_specified_ones(nEPOCH_idx, lstTimers_already_reseted,
                                                                   current_ts)
            else: # ret_TIMER_RESET_Msg = 0
                pass

            ### -- IV.  record performance of system periodically.
            if (step_times_in_a_EPOCH % TS_LENGTH_LISTEN_SYSOBJ == 0):
                current_ts = self.objSysTime.Get_CurrentTime()
                self.print_current_performance(nEPOCH_idx, current_ts)


            # # debug
            # print(self.Timers_fjn)

            # debug
            global DISPLAT_STEP
            if DISPALY_SWITCH and step_times_in_a_EPOCH % DISPLAT_STEP == 0:
                end_time = time.time()
                used_time = end_time - start_time
                print("current_ts = ",current_ts, "T_threshold_An_EPOCH = ",
                      self.T_threshold_An_EPOCH, ";",DISPLAT_STEP," epoch used time = ", used_time)
                start_time = time.time()

            time.sleep(0.00001)

        return

    def Pick_the_best_config_fn_at_end_of_each_EPOCH(self, nEPOCH_idx):
        Dct_fn_bestUtility_pairs = {}

        for nLen_config_n in range(1, self.shard + 1):
            utility, wNumViews, wAoI = self.Get_system_utility_under_a_fn(nEPOCH_idx, nLen_config_n)

            if nLen_config_n not in Dct_fn_bestUtility_pairs.keys():
                Dct_fn_bestUtility_pairs[nLen_config_n] = utility

        ### --- get the best utility and the corresponding fn
        if Dct_fn_bestUtility_pairs:
            n_fn_best_utility = self.objTool.Get_the_key_with_max_value_of_a_dict(Dct_fn_bestUtility_pairs)

            ### ======= Copy the fn_target into the Var_x_ji
            for i in self.I_list_all_shards:
                if i not in self.Var_x_ji.keys():
                    self.Var_x_ji[i] = self.fn_x_ji[n_fn_best_utility][i]
                self.Var_x_ji[i] = self.fn_x_ji[n_fn_best_utility][i]  ### EoF:~

    def Record_system_utility_at_end_of_each_EPOCH(self, nEpoch_j):
        total_num_of_shards = 0
        dAoI_total = 0.0
        Txs_total = 0

        for i in self.I_list_all_shards:
            total_num_of_shards += self.Var_x_ji[i]

        # ---- 2 calculate the AoI
        dSynLatency_shards = self.latency[nEpoch_j]
        # 这里可以加速: Var_x_ji变成 list类型

        lstLatency_jni = []
        for i in self.I_list_all_shards:
            lstLatency_jni.append(self.Var_x_ji[i] * dSynLatency_shards[i])
        dMoment_execute_optimization_in_master_tj = max(lstLatency_jni)
        for i in self.I_list_all_shards:
            dAoI_shards_i = self.Var_x_ji[i] * (
                    dMoment_execute_optimization_in_master_tj - dSynLatency_shards[i])  #
            dAoI_total += dAoI_shards_i

        # ---- 3 calculate the Txs
        dNumTx_shard = self.txs_total[nEpoch_j]
        for i in self.I_list_all_shards:
            dnumTx_jni = self.Var_x_ji[i] * dNumTx_shard[i]
            Txs_total += dnumTx_jni

        ## ---- 3. calculate Objectives
        sysUtility = Txs_total * self.WEIGHT_NUM_TX - dAoI_total * self.WEIGHT_AOI

        # 记录
        self.OBJ_FUN = sysUtility
        self.last_miningpool = Txs_total / dMoment_execute_optimization_in_master_tj
        self.last_total_num_of_shards = total_num_of_shards
        self.last_dAoI_total = dAoI_total
        self.last_Txs_total = Txs_total

    ''' ----------------------------------被调用函数 print_current_performance----------------------------------------'''
    def print_current_performance(self, nEPOCH_idx, current_ts):
        Dct_fn_bestUtility_pairs = {}
        for nLen_config_n in range(1, self.shard + 1):
            utility, wNumViews, wAoI = self.Get_system_utility_under_a_fn(nEPOCH_idx, nLen_config_n)
            Dct_fn_bestUtility_pairs[nLen_config_n] = utility

        n_fn_best_utility = self.objTool.Get_the_key_with_max_value_of_a_dict(Dct_fn_bestUtility_pairs)
        utility_best = Dct_fn_bestUtility_pairs[n_fn_best_utility]
        self.CURVE_IN_EPOCH[nEPOCH_idx].append(utility_best)



    ''' ----------------------------------被调用函数check_timerX_and_do_swap------------------------------------------'''
    ''' ----------------------------------被调用函数check_timerX_and_do_swap------------------------------------------'''
    ''' ----------------------------------被调用函数check_timerX_and_do_swap------------------------------------------'''

    def RESET_all_Timers_for_fn_except_specified_ones(self, nEpoch_j, lstTimers_not_to_reset, Current_ts):
        for nLen_config_n in range(1, self.shard + 1):
            if nLen_config_n not in lstTimers_not_to_reset:
                self.Set_timer_for_a_config(nEpoch_j, nLen_config_n, Current_ts)  ## EoF :~

    def check_timerX_and_do_swap(self, current_ts, nEPOCH_idx):
        nOPTSlot_j = nEPOCH_idx
        ret_TIMER_RESET_Msg = 0  #
        lstTimers_already_reseted = []  # [(nOPTSlot_j,nLen_config_n),...]

        #  老师的代码是 当epoch》2时， Timer_fjn 包括了前面的epoch
        # 这里是找到最小值
        retLst_timerX_check_result = self.Check_expiration_of_timer_fjn(current_ts)
        if len(retLst_timerX_check_result) > 0:

            ## ===== a. Do swap
            for key, val in retLst_timerX_check_result.items():
                ### ---- a.1 Read the SFInst-TD holding information.
                nLen_config_n = key
                i_IU_old = val[2]
                i_NIU_new = val[3]

                ### ---- a.2 Replace operations:
                self.fn_x_ji[nLen_config_n][i_IU_old] = 0  #
                self.fn_x_ji[nLen_config_n][i_NIU_new] = 1  #

                ### ---- a.3  !!!! Clear-the-expired-timerX-item after_replacement.
                self.Timers_fjn[nLen_config_n] = []

                ### ---- a.4 Reset timers for the elements in retLst_timerX_check_result
                self.Set_timer_for_a_config(nOPTSlot_j, nLen_config_n, current_ts)
                lstTimers_already_reseted.append(nLen_config_n)

                ### ---- a.5 !!! Record the timer's time-out times.
                self.Cumulative_TimerX_countDown_times += 1

            ## ===== b. Clear the checking-notebook for this round.
            retLst_timerX_check_result.clear()  ##

            ### ===== c. Lable the flag now, after swapping the time-outed items !!!!
            ret_TIMER_RESET_Msg = 1  #

            ### ===== d. !!! Record the times of RESET-Event.
            self.Cumulative_Notification_times_X += 1  #### EoF:~

        # retLst_timerX_check_result 可能为空， 则返回0， 和 []
        return ret_TIMER_RESET_Msg, lstTimers_already_reseted  ## EoF:~

    def Check_expiration_of_timer_fjn(self, current_ts):
        '''返回最小值 dict类型   key = n,  value = Times_fjn的value'''
        tem_timer_len_sortor = {}  ## {(nOPTSlot_j, nLen_config_n): length_of_timer}

        ########## ---- 1. check each timer.
        for idx, val in enumerate(self.Timers_fjn):
            if len(val) == 0:  # 头尾
                continue
            Timer_begin = val[0]
            Len_timer = val[1]
            if (current_ts >= Timer_begin + Len_timer):  # 满足条件 找最小值
                tem_timer_len_sortor[idx] = Len_timer

        lst_targetkeys = []
        if tem_timer_len_sortor:
            lst_targetkeys = min(tem_timer_len_sortor, key=tem_timer_len_sortor.get)

        ret_timer_result = {}
        if lst_targetkeys:
            ret_timer_result[lst_targetkeys] = self.Timers_fjn[lst_targetkeys]

        return ret_timer_result

    ''' ------------------------------------被调用函数Set_timers_for_all_fjn------------------------------------------'''
    ''' ------------------------------------被调用函数Set_timers_for_all_fjn------------------------------------------'''
    ''' ------------------------------------被调用函数Set_timers_for_all_fjn------------------------------------------'''

    def Set_timers_for_all_fjn(self, nEpoch_j, Current_ts):
        '''设置self.Timers_fjn'''
        for nLen_config_n in range(1, self.shard + 1):
            self.Set_timer_for_a_config(nEpoch_j, nLen_config_n, Current_ts)  ## EoF :~

    def Set_timer_for_a_config(self, nEpoch_j, nLen_config_n, Current_ts):
        Log_final_result = open(
            'MAonline_data/TimerLog_' + 'MA' + '_online_' + str(self.shard) + '_' + str(self.C0_CAPACITY_MASTER) + str(
                1.5) + '.txt', 'a')

        # 计算self.fn_x_ji[n]   0 和 1的长度
        lst_InUse_ONE_valued_var_x_ji = self.find_all_ONE_valued_x_ji_from_fn(nEpoch_j, nLen_config_n)
        lst_NotInUse_ZERO_valued_var_x_ji = self.find_all_ZERO_valued_x_ji_from_fn(nEpoch_j, nLen_config_n)
        NUM_IU_var_x_ji = len(lst_InUse_ONE_valued_var_x_ji)
        NUM_NIU_var_x_ji = len(lst_NotInUse_ZERO_valued_var_x_ji)

        if 0 == NUM_IU_var_x_ji:
            # print("not feasible solution")
            # self.Timers_fjn[nLen_config_n] = [] 本身就是空的
            return -1
        if 0 == NUM_NIU_var_x_ji:
            return -1

        # fixme

        if (NUM_IU_var_x_ji > 0 and NUM_NIU_var_x_ji > 0):
            rdm_idx_InUse_ONE_valued_var_x_ji = self.objTool.Get_a_random_element_from_a_list(
                lst_InUse_ONE_valued_var_x_ji)

            CNT_find_times = 0
            while True:
                CNT_find_times += 1
                rdm_idx_NotInUse_ZERO_valued_var_x_ji = self.objTool.Get_a_random_element_from_a_list(
                    lst_NotInUse_ZERO_valued_var_x_ji)

                if self.Is_feasible_if_swap_a_pair_of_var_x_ji(nEpoch_j, nLen_config_n,
                                                               rdm_idx_InUse_ONE_valued_var_x_ji,
                                                               rdm_idx_NotInUse_ZERO_valued_var_x_ji):
                    break  ##
                if CNT_find_times > self.shard:
                    break  ##

            if (-1 != rdm_idx_NotInUse_ZERO_valued_var_x_ji):
                ### ===== 3. calculate the system obj-value if swap values of x{^j}_{i_old} and x{^j}_{i_new}
                utility_after_swap = self.Estimate_system_utility_under_a_fn_if_swap_Xji_old_and_new(nEpoch_j,
                                                                                                     nLen_config_n,
                                                                                                     rdm_idx_InUse_ONE_valued_var_x_ji,
                                                                                                     rdm_idx_NotInUse_ZERO_valued_var_x_ji)

                utility_cur_fnXji, wNumViews, wAoI = self.Get_system_utility_under_a_fn(nEpoch_j, nLen_config_n)
                # print(utility_after_swap)
                # print(utility_cur_fnXji, wNumViews, wAoI)

                ### ===== 5. generate a random exponentially distributed timer T_n for fn_x_ji with mean that is
                ### =====    equal to (equation-stationary-distribution), i.e.,(1/lambda_exp_random_number_seed),
                ### =====    and record it into Timers_fjn.
                exp_item = 0.0  #
                utility_diff = utility_after_swap - utility_cur_fnXji  ##
                utility_diff /= 500

                try:
                    exp_item = math.exp(self.Tau - 0.5 * self.Beta * (utility_diff))
                    if exp_item == 0:
                        exp_item = math.exp(-10)


                # print("exp_item", exp_item)
                except OverflowError:
                    exp_item = math.exp(60)  ### !!!!!!!	Avoid overflow-computing.

                #### ======= use exp_item:
                mean_timer_exp = 1.0 * exp_item / (self.shard - nLen_config_n)  ##

                if math.exp(-100) > math.fabs(mean_timer_exp - 0.0):
                    mean_timer_exp = math.exp(-25)  ##

                lambda_exp_random_number_seed = 1.0 / mean_timer_exp
                Timer_val_exp = random.expovariate(
                    lambda_exp_random_number_seed)

                ## -- 8. Record the necessary information into timers.
                ######## Initialize or Update this timer:
                self.Timers_fjn[nLen_config_n] = [Current_ts, Timer_val_exp,
                                                  rdm_idx_InUse_ONE_valued_var_x_ji,
                                                  rdm_idx_NotInUse_ZERO_valued_var_x_ji,
                                                  utility_cur_fnXji, utility_after_swap]


        Log_final_result.write('\t\t-nEpoch_j\t%d\t-Utility_diff\t%s\t-exp_item\t%s'
                        '\t-mean_timer_exp\t%s\t-Timer_val_exp\t%s\n' % (
                    nEpoch_j, utility_diff, exp_item, mean_timer_exp, Timer_val_exp))
        return 0 # 有解
        ## EoF:~



    def Get_system_utility_under_a_fn(self, nEpoch_j, nLen_config_n):
        temp_fn_j = np.array(self.fn_x_ji[nLen_config_n])
        utility_cur_fnXji, wNumViews, wAoI = self.Get_system_utility(nEpoch_j, temp_fn_j)
        return utility_cur_fnXji, wNumViews, wAoI

    def Estimate_system_utility_under_a_fn_if_swap_Xji_old_and_new(self, nEpoch_j, nLen_config_n, i_old_IU, i_new_NIU):
        temp_fn_j = np.array(self.fn_x_ji[nLen_config_n])
        temp_fn_j[i_old_IU] = 0  #
        temp_fn_j[i_new_NIU] = 1  #

        sysUtility, _, _ = self.Get_system_utility(nEpoch_j, temp_fn_j)
        return sysUtility  #####EoF:~

    def Get_system_utility(self, nEpoch_j, temp_fn_j):
        ## ===== C. Calculate the fake system utility using temp_fn_j
        # ---- 1 calculate the total_num_of_shards
        total_num_of_shards = np.sum(temp_fn_j)

        if total_num_of_shards == 0:
            return -1, -1, -1

        # ---- 2 calculate the AoI  , 注意这里要取的是self.latency
        idx_temp_fn_j = np.concatenate(np.argwhere(temp_fn_j))
        lstLatency_jni = self.latency[nEpoch_j][idx_temp_fn_j]
        dMoment_execute_optimization_in_master_tj = np.max(lstLatency_jni)
        dAoI_total = np.sum(dMoment_execute_optimization_in_master_tj - lstLatency_jni)

        # ---- 3 calculate the Txs
        Txs_total = np.sum(self.txs_total[nEpoch_j][idx_temp_fn_j])

        ## ---- 4. calculate Objectives
        sysUtility = Txs_total * self.WEIGHT_NUM_TX - dAoI_total * self.WEIGHT_AOI
        return sysUtility, Txs_total * self.WEIGHT_NUM_TX, dAoI_total * self.WEIGHT_AOI  #####EoF:~  #####EoF:~

    def Is_feasible_if_swap_a_pair_of_var_x_ji(self, nEpoch_j, nLen_config_n,
                                               i_idx_IU_ONE_valued_var_x_ji, i_idx_test_NIU_ZERO_valued_var_x_ji):
        ## ===== A. get a copy of fn_x_ji  deep copy !!
        temp_fn_j = np.array(self.fn_x_ji[nLen_config_n])

        ## ===== B. swap the i_old and i_new
        temp_fn_j[i_idx_IU_ONE_valued_var_x_ji] = 0  #
        temp_fn_j[i_idx_test_NIU_ZERO_valued_var_x_ji] = 1  #

        # ---- 1 calculate the total_numTx_of_shards_collected at the master
        idx_temp_fn_j = np.concatenate(np.argwhere(temp_fn_j))
        total_numTx_of_shards_after_swap = np.sum(self.txs_total[nEpoch_j][idx_temp_fn_j])

        # 交换后，总数还是小于区块的C hat
        if self.C0_CAPACITY_MASTER >= total_numTx_of_shards_after_swap:
            return 1
        else:
            return 0  ##EoF:~

    def find_all_ONE_valued_x_ji_from_fn(self, nEpoch_j, nLen_config_n):
        tmp = self.fn_x_ji[nLen_config_n][:]
        One_return = np.argwhere(tmp == 1)
        if len(One_return > 0):
            One_return = np.concatenate(One_return)
        return One_return

    def find_all_ZERO_valued_x_ji_from_fn(self, nEpoch_j, nLen_config_n):
        tmp = self.fn_x_ji[nLen_config_n][:]
        Zeros_return = np.argwhere(tmp == 0)
        if len(Zeros_return > 0):
            Zeros_return = np.concatenate(Zeros_return)
        return Zeros_return

all_CURVE = []
class MA_online:
    def __init__(self, shard, numepoch):

        # 读全部数据
        self.shard = shard
        self.numepoch = numepoch

        formation_file = '../../data/formation_latency100000_epoch24.csv'
        txs_file = '../../data/blockhash.txt'

        formation_lan = []
        txs = []
        txs_total = []
        with open(formation_file, 'r') as f:
            for i, lines in enumerate(f):
                line = lines.strip('\n').split(',')
                if 'shard' in line[0]:  # 跳过第一行 标签
                    continue
                formation_lan.append(line[0:self.shard])  # 取所需要shard部分
                if i == self.numepoch + 1:  # 取固定epoch
                    break

        with open(txs_file, 'r') as f:
            for lines in f:
                line = lines.strip('\n').split(' ')[-1]
                txs.append(line)
            for i in range(self.numepoch):
                random.shuffle(txs)
                temp = np.array(txs)
                txs_total.append(temp[0:self.shard])  # 1378*epoch

            self.latency = np.array(formation_lan).astype('float') + 54.5  # 加上consensus latency
            self.txs_total = np.array(txs_total).astype('float')

        with open("ma_features.csv",'w',encoding='utf-8',newline='') as f:
            writer = csv.writer(f)
            for epoch in range(24):
                lat = list(self.latency[epoch])
                tx = list(self.txs_total[epoch])
                # print(lat)
                # print(tx)
                writer.writerow(lat)
                writer.writerow(tx)

    def online_solution(self,latency, txs_total,feasible_shard):
        STEP_TO_RUN = 0.001
        # 只运行一个epoch
        epoch = 1
        ma = MA_PX(latency, txs_total, feasible_shard, 1, self.C0_CAPACITY_MASTER, STEP_TO_RUN)
        nEPOCH_idx = 0
        ma.Initialization(nEPOCH_idx)
        start_time = time.time()

        ma.MarkovApproximateFunc(nEPOCH_idx)
        ma.Pick_the_best_config_fn_at_end_of_each_EPOCH(nEPOCH_idx)
        ma.Record_system_utility_at_end_of_each_EPOCH(nEPOCH_idx)

        end_time = time.time()
        used_time = end_time - start_time
        print("this solution total used time", used_time)


        return ma.last_total_num_of_shards, ma.OBJ_FUN, ma.last_Txs_total, ma.last_dAoI_total, ma.last_miningpool, ma.CURVE_IN_EPOCH


    def listening(self,epoch):

        self.C0_CAPACITY_MASTER = 800 * self.shard
        self.WEIGHT_NUM_DOMAIN_VIEWS = 1.5

        Log_final_result = open('MA_online_data.csv','a',encoding='utf-8',newline='')
        writer = csv.writer(Log_final_result)

        # 读取当前epoch的latency, txs_toal数据 并按latency 排序
        L = list(self.latency[epoch])
        TXS = list(self.txs_total[epoch])
        res = sorted(zip(L,TXS), key=lambda x:x[0])
        L, TXS = zip(*res)   # tuple类型

        first_per = 0.5     # 开始条件
        total = 0
        end_per = 0.8       # 结束条件
        i = 0

        CURVE = []
        CURVE_IN_EPOCH = []

        # 判断条件
        while i <= len(L) * end_per:
            if i >= len(L) * first_per and total >= self.C0_CAPACITY_MASTER:
                print("start, i = {0}".format(i))
                # 调用初始化函数
                Latency = np.array(L[0:i]).reshape(1,i)
                txs_total = np.array(TXS[0:i]).reshape(1,i)

                writer.writerow(L[0:i])
                writer.writerow(TXS[0:i])

            total += TXS[i]
            i += 1
        # while end

        return

    def main(self, run_epoch):
        # 新建
        Log_final_result = open('MA_online_data.csv', 'w', encoding='utf-8', newline='')
        Log_final_result.close()

        for epoch in range(run_epoch):
            print("======epoch:", epoch)
            self.listening(epoch)

if __name__ == '__main__':

    shard = 100
    total_epoch = 24
    maonline = MA_online(shard,total_epoch)

    run_epoch = 5
    maonline.main(run_epoch)




