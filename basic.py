import os
import json
import numpy as np
import pandas as pd
import random
from time import sleep
import copy
import matplotlib.pyplot as plt
from pylab import plot
import pylab as pl


def TestCiviExist(turn,civi_dict,civi_id,reason):
    global record_text
    civi_dict[civi_id]['owned_galaxy_num'] = len(list(civi_dict[civi_id]['owned_galaxy'].keys()))
    if civi_dict[civi_id]['owned_galaxy_num'] == 0:
        civi_dict[civi_id]['extinct'] = reason
        civi_dict[civi_id]['extinct_turn'] = turn
        civi_dict[civi_id]['living_turn'] = turn -  civi_dict[civi_id]['original_turn']
        text_ = 'turn {}: civi {} has extincted due to {}...'.format(str(turn),civi_id,reason)
        print (text_)
        record_text = record_text + text_ + '\n'
    return civi_dict

def GetDistance(first_id,second_id):
    first_coordinate = [int(i) for i in first_id.split()]
    second_coordinate = [int(i) for i in second_id.split()]
    distance = (first_coordinate[0]-second_coordinate[0])**2 + (first_coordinate[1]-second_coordinate[1])**2
    return distance

def GetAudit(n,turn,setting,civi_dict,coordinate_dict,report_dict,report_original_dict,communicate_dict,attack_dict,record_text):
    WFM = setting['war_flexible_gau_mean']
    WFS = setting['war_flexible_gau_sigma']
    WFMin = setting['war_flexible_min']
    WarC = setting['war_coefficient']
    BWO = setting['basic_war_odds']
    MDC = setting['merged_discount_coefficient']
    CCR = setting['combining_coefficient_report']
    CombC = setting['combining_coefficient']
    SafeDistance = setting['SafeDistance']
    ReportInterval = setting['report_interval']

    attack_dict_copy = copy.deepcopy(attack_dict)
    for attack_from_id in attack_dict_copy.keys():
        for attack_index,attack_info in enumerate(attack_dict[attack_from_id]):
            attack_info[2] = attack_info[2]-1
            if attack_info[2] > 0:
                continue
            attack_to_id = attack_info[0]
            if coordinate_dict[attack_to_id]['exist'] == 0 and coordinate_dict[attack_to_id]['DFA'] == 1:
                continue
            attacked_part = coordinate_dict[attack_to_id]['owner']
            attacker = attack_info[3]
            if attacked_part == 0:
                coordinate_dict[attack_to_id]['exist'] = 0
                coordinate_dict[attack_to_id]['DFA'] = 1
                continue
            else:
                to_tech_level = civi_dict[attacked_part]['tech_level']
                civi_dict[attacked_part]['dark_forest_attacked'] += 1
            from_tech_level = attack_info[1]
            tech_gap = from_tech_level-to_tech_level
            prob_ = random.random()
            if prob_<((tech_gap/WarC)+BWO)*((max(random.gauss(WFM,WFS),WFMin))):
                coordinate_dict[attack_to_id]['exist'] = 0
                coordinate_dict[attack_to_id]['DFA'] = 1
                del civi_dict[attacked_part]['owned_galaxy'][attack_to_id]
                civi_dict = TestMainGlaxy(civi_dict,attacked_part,attack_to_id)
                civi_dict[attacked_part]['owned_galaxy_num'] = len(list(civi_dict[attacked_part]['owned_galaxy'].keys()))
                civi_dict[attacked_part]['owned_resource'] = sum([coordinate_dict[i]['resource'] for i in list(civi_dict[attacked_part]['owned_galaxy'].keys())])
                text_ = 'turn {}: civi {} has gotten dark forest attack on galaxy {} from {}...'.format(str(turn),attacked_part,attack_to_id,attacker)
                print (text_)
                record_text = record_text + text_ + '\n'
                civi_dict[attacker]['dark_forest_successful_attacker'] += 1
                civi_dict = TestCiviExist(turn,civi_dict,attacked_part,'DarkForestAttack')
            else:
                text_ = 'turn {}: civi {} has gotten dark forest attack on galaxy {} but survived...'.format(str(turn),attacked_part,attack_to_id)
                print (text_)
                record_text = record_text + text_ + '\n'
                civi_dict[attacked_part]['dark_forest_survive_attacked'] += 1
            if attack_info[2] <= 0:
                attack_dict[attack_from_id].remove(attack_info)

    report_original_dict_copy = copy.deepcopy(report_original_dict) 
    for report_id in report_original_dict_copy.keys():
        for rep_idx,rep_item in enumerate(report_original_dict_copy[report_id]):
            if rep_item[-1] >= ReportInterval:
                report_original_dict_copy[report_id].remove(rep_item)
            rep_item[-1] += 1
    
    report_dict_copy = copy.deepcopy(report_dict) 
    for report_id in report_dict_copy.keys():
        sub_lists = []
        # sub_lists_ids = []
        for sub_list in report_dict[report_id]:
            # or sub_list[-1] in sub_lists_ids
            if sub_list in sub_lists :
                continue
            sub_lists.append(sub_list)
            # sub_lists_ids.append(sub_list[-1])
        report_dict[report_id] = sub_lists
        for report_time,report_range in enumerate(report_dict[report_id]):
            if report_range[0:4] == [0,n-1,0,n-1]:
                report_dict[report_id].remove(report_range)
            report_range = [max(report_range[0]-1,0),min(report_range[1]+1,n-1),max(report_range[2]-1,0),min(report_range[3]+1,n-1),report_range[4]]
            for i in range(report_range[0],report_range[1]+1):
                for j in range(report_range[2],report_range[3]+1):
                    if i not in [report_range[0],report_range[1]+1] and j not in [report_range[2],report_range[3]+1]:
                        continue
                    touched_id = ' '.join([str(i),str(j)])
                    touched_civi_id = coordinate_dict[touched_id]['owner']
                    sent_civi_id = report_range[4]
                    if sent_civi_id == touched_civi_id:
                        continue
                    if coordinate_dict[touched_id]['exist'] == 0 or coordinate_dict[touched_id]['owner'] == 0:
                        continue
                    if civi_dict[touched_civi_id]['extinct'] != 'nan':
                        continue
                    if civi_dict[touched_civi_id]['tech_level'] < setting['treshold_for_report']:
                        continue
                    if civi_dict[touched_civi_id]['civi_type'] == 'communicate':
                        commu_degree = (civi_dict[sent_civi_id]['tech_level'] - civi_dict[touched_civi_id]['tech_level'])*CCR/CombC
                        if civi_dict[sent_civi_id]['extinct'] != 'nan':
                            continue
                        key_com = (sent_civi_id,touched_civi_id)
                        if key_com not in communicate_dict.keys():
                            communicate_dict[key_com] = commu_degree
                        else:
                            communicate_dict[key_com] += commu_degree
                        text_ = 'turn {}: civi {} and civi {} has communicated on radio to dgree {}...'.format(str(turn),sent_civi_id,touched_civi_id,commu_degree)
                        print (text_)
                        record_text = record_text + text_ + '\n'
                        civi_dict[sent_civi_id]['coummunicate_times'] += 1
                        civi_dict[touched_civi_id]['coummunicate_times'] += 1
                        if touched_id not in report_dict.keys():
                            report_dict[touched_id] = []
                        if [i,i,j,j,touched_civi_id] in report_dict[touched_id]:
                            continue
                        report_dict[touched_id].append([i,i,j,j,touched_civi_id])
                        text_ = 'turn {}: civi {} has radio on {} to feedback...'.format(str(turn),touched_civi_id,touched_id)
                        civi_dict[touched_civi_id]['reporting_self_times'] += 1
                        print (text_)
                        record_text = record_text + text_ + '\n'
                    elif (civi_dict[touched_civi_id]['civi_type'] == 'attack' and civi_dict[touched_civi_id]['tech_level']>setting['treshold_for_deathattack']) \
                        or (civi_dict[touched_civi_id]['civi_type'] == 'hide' and civi_dict[touched_civi_id]['tech_level']>setting['treshold_for_deathattack'] and GetDistance(report_id,touched_id)>SafeDistance):
                        if coordinate_dict[touched_id]['exist'] == 0:
                            continue
                        if touched_id not in attack_dict.keys():
                            attack_dict[touched_id] = []
                        if report_id in [i[0] for i in attack_dict[touched_id]]:
                            continue
                        attack_dict[touched_id].append([report_id,civi_dict[touched_civi_id]['tech_level'],GetDistance(touched_id,report_id),touched_civi_id])
                        text_ = 'turn {}: civi {} has launched dark forest attack to {}...'.format(str(turn),touched_civi_id,report_id)
                        civi_dict[touched_civi_id]['dark_forest_attacker'] += 1
                        print (text_)
                        record_text = record_text + text_ + '\n'
    
    def MergingProcess(turn,civi_id_1,civi_id_2,civi_dict,MDC,coordinate_dict):
        global record_text
        civi_dict[civi_id_2]['extinct'] = 'merged'
        civi_dict[civi_id_2]['extinct_turn'] = turn  
        civi_dict[civi_id_2]['living_turn'] = turn -  civi_dict[civi_id_2]['original_turn']
        for galaxy in list(civi_dict[civi_id_2]['owned_galaxy'].keys()):
            coordinate_dict[galaxy]['owner'] = civi_id_1
            civi_dict[civi_id_1]['owned_galaxy'][galaxy] = coordinate_dict[galaxy]['resource']*MDC
            civi_dict[civi_id_1]['owned_galaxy_num'] = len(list(civi_dict[civi_id_1]['owned_galaxy'].keys()))
            civi_dict[civi_id_1]['owned_resource'] = sum([coordinate_dict[i]['resource'] for i in list(civi_dict[civi_id_1]['owned_galaxy'].keys())])
            del civi_dict[civi_id_2]['owned_galaxy'][galaxy]
            civi_dict[civi_id_2]['owned_galaxy_num'] = len(list(civi_dict[civi_id_2]['owned_galaxy'].keys()))
            civi_dict[civi_id_2]['owned_resource'] = sum([coordinate_dict[i]['resource'] for i in list(civi_dict[civi_id_2]['owned_galaxy'].keys())])
            coordinate_dict,civi_dict = TechResource(coordinate_dict,galaxy,civi_dict,civi_id_1)
        text_ = 'turn {}: civi {} has merged civi {}...'.format(str(turn),civi_id_1,civi_id_2)
        print (text_)
        record_text = record_text + text_ + '\n'
        civi_dict[civi_id_1]['taken_merge_times'] += 1

        return civi_dict

    communicate_dict_copy = copy.deepcopy(communicate_dict)
    for key_com in communicate_dict_copy:
        (civi_id_1,civi_id_2) = key_com
        if civi_dict[civi_id_1]['extinct'] != 'nan' or civi_dict[civi_id_2]['extinct'] != 'nan':
            del communicate_dict[key_com]
            continue
        if communicate_dict[key_com] >= 1:
            civi_dict = MergingProcess(turn,civi_id_1,civi_id_2,civi_dict,MDC,coordinate_dict)
            del communicate_dict[key_com]
        elif communicate_dict[key_com] <= -1:
            civi_dict = MergingProcess(turn,civi_id_2,civi_id_1,civi_dict,MDC,coordinate_dict)
            del communicate_dict[key_com]
    
    for civi_id in civi_dict.keys():
        civi_dict[civi_id]['living_turn'] = turn - civi_dict[civi_id]['original_turn']
    print ('report_dict: \n',report_dict)
    print ('communicate_dict: \n',communicate_dict)        
    print ('attack_dict: \n',attack_dict)
    return civi_dict,coordinate_dict,report_dict,communicate_dict,attack_dict,record_text


def AttackProcess(turn,atk_from_id,atk_coordinate,WarC,BWO,setting,coordinate_dict,civi_dict,report_dict,attacker,attacked,atk_to_id,atk_to_coordinate):
    tech_gap = civi_dict[attacker]['tech_level'] - civi_dict[attacked]['tech_level']
    WFM = setting['war_flexible_gau_mean']
    WFS = setting['war_flexible_gau_sigma']
    WFMin = setting['war_flexible_min']
    global record_text

    def RecordVicLose(civi_dict,winner,loser):
        if civi_dict[winner]['tech_level'] >= civi_dict[loser]['tech_level']:
            civi_dict[winner]['victory_better_times'] += 1
            civi_dict[loser]['lose_worse_times'] += 1
        elif civi_dict[winner]['tech_level'] < civi_dict[loser]['tech_level']:
            civi_dict[winner]['victory_worse_times'] += 1
            civi_dict[loser]['lose_better_times'] += 1
        return civi_dict

    if tech_gap>=0:
        
        prob_ = random.random()
        if prob_<((tech_gap/WarC)+BWO)*((max(random.gauss(WFM,WFS),WFMin))):
            coordinate_dict[atk_to_id]['owner'] = attacker
            civi_dict[attacker]['owned_galaxy'][atk_to_id] = coordinate_dict[atk_to_id]['resource']
            civi_dict[attacker]['owned_galaxy_num'] = len(list(civi_dict[attacker]['owned_galaxy'].keys()))
            civi_dict[attacker]['owned_resource'] = sum([coordinate_dict[i]['resource'] for i in list(civi_dict[attacker]['owned_galaxy'].keys())])
            del civi_dict[attacked]['owned_galaxy'][atk_to_id]
            civi_dict = TestMainGlaxy(civi_dict,attacked,atk_to_id)
            civi_dict[attacked]['owned_galaxy_num'] = len(list(civi_dict[attacked]['owned_galaxy'].keys()))
            civi_dict[attacked]['owned_resource'] = sum([coordinate_dict[i]['resource'] for i in list(civi_dict[attacked]['owned_galaxy'].keys())])
            civi_dict = TestCiviExist(turn,civi_dict,attacked,'DirectWar')
            text_ = 'turn {}: civi {} and civi {} had a war, and {} won...'.format(str(turn),attacker,attacked,attacker)
            civi_dict = RecordVicLose(civi_dict,attacker,attacked)
            print (text_)
            record_text = record_text + text_ + '\n'
            coordinate_dict,civi_dict = TechResource(coordinate_dict,atk_to_id,civi_dict,attacker)
        else:
            coordinate_dict[atk_from_id]['owner'] = attacked
            civi_dict[attacked]['owned_galaxy'][atk_from_id] = coordinate_dict[atk_from_id]['resource']
            civi_dict[attacked]['owned_galaxy_num'] = len(list(civi_dict[attacked]['owned_galaxy'].keys()))
            civi_dict[attacked]['owned_resource'] = sum([coordinate_dict[i]['resource'] for i in list(civi_dict[attacked]['owned_galaxy'].keys())])
            del civi_dict[attacker]['owned_galaxy'][atk_from_id]
            civi_dict = TestMainGlaxy(civi_dict,attacker,atk_from_id)
            civi_dict[attacker]['owned_galaxy_num'] = len(list(civi_dict[attacker]['owned_galaxy'].keys()))
            civi_dict[attacker]['owned_resource'] = sum([coordinate_dict[i]['resource'] for i in list(civi_dict[attacker]['owned_galaxy'].keys())])
            civi_dict = TestCiviExist(turn,civi_dict,attacker,'DirectAttack')
            text_ = 'turn {}: civi {} and civi {} had a war, and {} won...'.format(str(turn),attacker,attacked,attacked)
            print (text_)
            record_text = record_text + text_ + '\n'
            coordinate_dict,civi_dict = TechResource(coordinate_dict,atk_from_id,civi_dict,attacked)
            civi_dict = RecordVicLose(civi_dict,attacked,attacker)
        civi_dict = TestCiviExist(turn,civi_dict,attacker,'DirectWar')
        civi_dict = TestCiviExist(turn,civi_dict,attacked,'DirectWar')
    else: 
        if civi_dict[attacker]['tech_level']>= setting['treshold_for_report']:
            if atk_to_id not in report_dict.keys():
                report_dict[atk_to_id] = []
            if [atk_coordinate[0],atk_coordinate[0],atk_coordinate[1],atk_coordinate[1],attacked] in report_dict[atk_to_id]:
                pass
            else:
                report_dict[atk_to_id].append([atk_coordinate[0],atk_coordinate[0],atk_coordinate[1],atk_coordinate[1],attacked])
                text_ = 'turn {}: civi {} radio the coordinate of civi {} on galaxy {}'.format(str(turn),attacker,attacked,atk_to_id)
                print (text_)
                record_text = record_text + text_ + '\n'
                civi_dict[attacker]['reporting_others_times'] += 1
    return civi_dict,report_dict,coordinate_dict

def GetEvolvedExplore(n,turn,setting,civi_dict,coordinate_dict,report_dict,report_original_dict,communicate_dict,record_text):
    TInt = setting['treshold_for_intelligence']
    TRepo = setting['treshold_for_report']
    TGT = setting['treshold_for_galaxytravel']
    TDA = setting['treshold_for_deathattack']
    RTC = setting['resource_travel_coefficient']
    CombC = setting['combining_coefficient']
    WarC = setting['war_coefficient']
    BWO = setting['basic_war_odds']
    sigma = setting['setting_gau_sigma']
    RNC = setting['report_num_discount']
    HCD = setting['hide_culture_discount']
    STC = setting['safe_tech_gap']
    MTT = setting['max_galaxy_travel_times']

    def RecordWartimes(civi_dict,atk_from,atk_to):
        civi_dict[atk_from]['direct_attacker_times'] += 1
        civi_dict[atk_to]['direct_attacked_times'] += 1
        civi_dict[atk_from]['direct_war_times'] += 1
        civi_dict[atk_to]['direct_war_times'] += 1
        return civi_dict

    for civi_id in civi_dict.keys():
        if civi_dict[civi_id]['extinct'] != 'nan':
            continue
        if civi_dict[civi_id]['tech_level'] <= TRepo:
            continue
        if civi_dict[civi_id]['civi_type'] == 'communicate':
            reported_ids = []
            report_times = min(int(RNC*civi_dict[civi_id]['owned_galaxy_num'])+1,civi_dict[civi_id]['owned_galaxy_num'])
            for report_time in range(report_times):
                reported_id = random.choice(list(civi_dict[civi_id]['owned_galaxy'].keys()))
                if reported_id in reported_ids:
                    # report_times += 1
                    continue
                civi_dict[civi_id]['reporting_self_times'] += 1
                text_ = 'turn {}: civi {} has reported coordinate of {}...'.format(str(turn),civi_id,reported_id)
                print (text_)
                record_text = record_text + text_ + '\n'
                reported_ids.append(reported_id)
                reported_coordinate = [int(i) for i in reported_id.split()]
                if reported_id not in report_original_dict.keys():
                    report_original_dict[reported_id] = []
                if [reported_coordinate[0],reported_coordinate[0],reported_coordinate[1],reported_coordinate[1],civi_id] in [i[:5] for i in report_original_dict[reported_id]]:
                    continue
                report_original_dict[reported_id].append([reported_coordinate[0],reported_coordinate[0],reported_coordinate[1],reported_coordinate[1],civi_id,0])
                if reported_id not in report_dict.keys():
                    report_dict[reported_id] = []
                if [reported_coordinate[0],reported_coordinate[0],reported_coordinate[1],reported_coordinate[1],civi_id] in report_dict[reported_id]:
                    continue
                report_dict[reported_id].append([reported_coordinate[0],reported_coordinate[0],reported_coordinate[1],reported_coordinate[1],civi_id])
        if civi_dict[civi_id]['tech_level'] <= TGT:
            continue
        
        
        travel_times = min(1+civi_dict[civi_id]['owned_resource']*RTC,MTT)
        if civi_dict[civi_id]['civi_type'] == 'hide':
            travel_times = travel_times*HCD
        travelled_ids = []
        for travel_time in range(max(int(travel_times),1)):
            if civi_dict[civi_id]['extinct'] != 'nan':
                break
            travel_from_id = random.choice(list(civi_dict[civi_id]['owned_galaxy'].keys()))
            travel_from_coordinate = [int(i) for i in travel_from_id.split()]
            if coordinate_dict[travel_from_id]['owner'] != civi_id:
                continue
            prob_ = random.random()
            if prob_<0.25:
                travel_to_coordinate = [travel_from_coordinate[0],min(travel_from_coordinate[1]+1,n-1)]
            elif 0.25<=prob_ and prob_<0.5:
                travel_to_coordinate = [travel_from_coordinate[0],max(travel_from_coordinate[1]-1,0)]
            elif 0.5<=prob_ and prob_<0.75:
                travel_to_coordinate = [min(travel_from_coordinate[0]+1,n-1),travel_from_coordinate[1]]
            else:
                travel_to_coordinate = [max(travel_from_coordinate[0]-1,0),travel_from_coordinate[1]]
            travel_to_id = ' '.join([str(i) for i in travel_to_coordinate])
            if travel_to_id in travelled_ids:
                # travel_times += 1
                continue
            if travel_to_id == travel_from_id:
                continue
            if coordinate_dict[travel_to_id]['owner'] == coordinate_dict[travel_from_id]['owner']:
                travel_times += 1
                continue
            travelled_ids.append(travel_to_id)
            civi_dict[civi_id]['galaxy_travel_times'] +=1
            if coordinate_dict[travel_to_id]['exist'] == 0 and coordinate_dict[travel_to_id]['DFA'] == 1:
                # travel_times += 1
                continue
            civi_dict[civi_id]['galaxy_successful_times'] += 1
            text_ = 'turn {}: civi {} has galaxy travelled to {}...'.format(str(turn),civi_id,travel_to_id)
            print (text_)
            record_text = record_text + text_ + '\n'
            owner_state = coordinate_dict[travel_to_id]['owner']
            if owner_state == 0 or (owner_state != 0 and civi_dict[owner_state]['tech_level']< TInt):
                coordinate_dict[travel_to_id]['owner'] = civi_id
                civi_dict[civi_id]['owned_galaxy'][travel_to_id] = coordinate_dict[travel_to_id]['resource']
                civi_dict[civi_id]['owned_galaxy_num'] = len(list(civi_dict[civi_id]['owned_galaxy'].keys()))
                civi_dict[civi_id]['owned_resource'] = sum([coordinate_dict[i]['resource'] for i in list(civi_dict[civi_id]['owned_galaxy'].keys())])
                civi_dict[civi_id]['taken_without_civi_times'] += 1
                text_ = 'turn {}: civi {} has taken {}...'.format(str(turn),civi_id,travel_to_id)
                print (text_)
                record_text = record_text + text_ + '\n'
                coordinate_dict,civi_dict = TechResource(coordinate_dict,travel_to_id,civi_dict,civi_id)
            else:
                owner_id = coordinate_dict[travel_to_id]['owner']
                if owner_id == civi_id:
                    continue
                elif civi_dict[civi_id]['civi_type'] == 'communicate':
                    if civi_dict[owner_id]['civi_type'] == 'communicate':
                        key_com = (civi_id,owner_id)
                        if civi_id== owner_id:
                            continue
                        if key_com not in list(communicate_dict.keys()):
                            communicate_dict[key_com] = (civi_dict[civi_id]['tech_level'] - civi_dict[owner_id]['tech_level'])/CombC
                        else:
                            communicate_dict[key_com] += (civi_dict[civi_id]['tech_level'] - civi_dict[owner_id]['tech_level'])/CombC
                        civi_dict[civi_id]['coummunicate_times'] += 1
                        text_ = 'turn {}: civi {} and civi {} has communicated, the degree has to be {} ...'.format(str(turn),civi_id,owner_id,str(communicate_dict[key_com]))
                        print (text_)
                        record_text = record_text + text_ + '\n'
                    elif civi_dict[owner_id]['civi_type'] == 'hide':
                        if civi_dict[owner_id]['tech_level'] - civi_dict[civi_id]['tech_level'] > STC:
                            civi_dict,report_dict,coordinate_dict= AttackProcess(turn,travel_to_id,travel_to_coordinate,WarC,BWO,setting,coordinate_dict,civi_dict,report_dict,owner_id,civi_id,travel_from_id,travel_from_coordinate)
                            civi_dict = RecordWartimes(civi_dict,owner_id,civi_id)
                        else:
                            text_ = 'turn {}: civi {} and civi {} has meet, but {} is hiding...'.format(str(turn),civi_id,owner_id,owner_id)
                            print (text_)
                            record_text = record_text + text_ + '\n'
                            continue
                    elif civi_dict[owner_id]['civi_type'] == 'attack':
                        civi_dict,report_dict,coordinate_dict= AttackProcess(turn,travel_to_id,travel_to_coordinate,WarC,BWO,setting,coordinate_dict,civi_dict,report_dict,owner_id,civi_id,travel_from_id,travel_from_coordinate)
                        civi_dict = RecordWartimes(civi_dict,owner_id,civi_id)
                elif civi_dict[civi_id]['civi_type'] == 'hide':
                    if civi_dict[civi_id]['tech_level'] - civi_dict[owner_id]['tech_level'] > STC:
                        civi_dict,report_dict,coordinate_dict= AttackProcess(turn,travel_from_id,travel_from_coordinate,WarC,BWO,setting,coordinate_dict,civi_dict,report_dict,civi_id,owner_id,travel_to_id,travel_to_coordinate)
                        civi_dict = RecordWartimes(civi_dict,civi_id,owner_id)
                elif civi_dict[civi_id]['civi_type'] == 'attack':
                    civi_dict,report_dict,coordinate_dict= AttackProcess(turn,travel_from_id,travel_from_coordinate,WarC,BWO,setting,coordinate_dict,civi_dict,report_dict,civi_id,owner_id,travel_to_id,travel_to_coordinate)
                    civi_dict = RecordWartimes(civi_dict,civi_id,owner_id)
    return civi_dict,coordinate_dict,report_dict,communicate_dict,record_text

def TestMainGlaxy(civi_dict,civi_id,galaxy_id):
    if galaxy_id == civi_dict[civi_id]['main_galaxy']:
        if len(list(civi_dict[civi_id]['owned_galaxy'].keys())) > 0:
            civi_dict[civi_id]['main_galaxy'] = random.choice(list(civi_dict[civi_id]['owned_galaxy'].keys()))
    return civi_dict

def TechResource(coordinate_dict,owned_gala,civi_dict,civi_id):
    global setting
    TRPC = setting['technological_resource_production_coefficient']
    former_explore_level = coordinate_dict[owned_gala]['explore_level']
    coordinate_dict[owned_gala]['explore_level'] = int(civi_dict[civi_id]['tech_level'])
    explore_level_gap = int(civi_dict[civi_id]['tech_level']) - former_explore_level
    if explore_level_gap >0:
        coordinate_dict[owned_gala]['resource'] += sorted([int(i) for i in setting['inital_state'].keys()],reverse=True)[0]*(explore_level_gap+1)*civi_dict[civi_id]['tech_level']*TRPC
    return coordinate_dict,civi_dict

def GetEvolvedTechCon(turn,setting,civi_dict,coordinate_dict,record_text):
    TEC = setting['technological_explosion_coefficient']
    ConC = setting['consume_coefficient']
    setting_gau_mean = setting['setting_gau_mean']
    setting_gau_sigma = setting['setting_gau_sigma']
    setting_gau_min = setting['setting_gau_min']
    resource_warning = setting['resource_warning']
    malthusian_trap = setting['malthusian_trap']
    ProbDisaster = setting['probability_disaster']
    TRV = setting['technology_robust_value']
    for civi_id in civi_dict.keys():
        if civi_dict[civi_id]['extinct'] != 'nan':
            continue
        former_tech_level = civi_dict[civi_id]['tech_level']
        civi_dict[civi_id]['tech_level'] *= (10**random.uniform(TEC[0], TEC[1])+1)
        tech_deve_gap = int(civi_dict[civi_id]['tech_level']) - int(former_tech_level)
        tech_deve_step = int(civi_dict[civi_id]['tech_level']) /int(former_tech_level)
        if tech_deve_step >= 2:
            civi_dict[civi_id]['technology_explosion_times'] += 1
            text_ = 'turn {} : civi {} has happend technology explosion...'.format(str(turn),civi_id)
            print (text_)
            record_text = record_text + text_ + '\n'
        
        civi_dict[civi_id]['consume_rate'] *= ConC*civi_dict[civi_id]['tech_level']*(max(random.gauss(setting_gau_mean,setting_gau_sigma),setting_gau_min))
        for owned_gala in list(civi_dict[civi_id]['owned_galaxy'].keys()):
            decided_prob_disaster = random.random()
            if decided_prob_disaster <= ProbDisaster:
                avoid_prob = random.random()
                if avoid_prob >= civi_dict[civi_id]['tech_level'] / TRV:
                    text_ = 'turn {}: civi {} has happend into disaster in galaxy {}...'.format(str(turn),civi_id,owned_gala)
                    print (text_)
                    record_text = record_text + text_ + '\n'
                    coordinate_dict[owned_gala]['owner'] = 0
                    coordinate_dict[owned_gala]['resource'] = coordinate_dict[owned_gala]['resource']/random.uniform(1, 3)
                    del civi_dict[civi_id]['owned_galaxy'][owned_gala]
                    civi_dict = TestCiviExist(turn,civi_dict,civi_id,'GreatDisaster')
                    civi_dict = TestMainGlaxy(civi_dict,civi_id,owned_gala)
                    civi_dict[civi_id]['disasters_num'] += 1
                    continue
            coordinate_dict,civi_dict = TechResource(coordinate_dict,owned_gala,civi_dict,civi_id)
            coordinate_dict[owned_gala]['resource'] -= civi_dict[civi_id]['consume_rate']
            if coordinate_dict[owned_gala]['resource'] <= 0:
                # coordinate_dict[owned_gala]['exist'] = 0
                coordinate_dict[owned_gala]['owner'] = 0
                coordinate_dict[owned_gala]['RR'] = 1
                civi_dict[civi_id]['out_resource_gala_num'] += 1
                text_ = 'turn {}: civi {} has run out resource for galaxy {}...'.format(str(turn),civi_id,owned_gala)
                print (text_)
                record_text = record_text + text_ + '\n'
                del civi_dict[civi_id]['owned_galaxy'][owned_gala]
                civi_dict = TestMainGlaxy(civi_dict,civi_id,owned_gala)
            else:
                coordinate_dict[owned_gala]['RR'] = 0
        civi_dict[civi_id]['owned_galaxy_num'] = len(list(civi_dict[civi_id]['owned_galaxy'].keys()))
        civi_dict[civi_id]['owned_resource'] = sum([coordinate_dict[i]['resource'] for i in list(civi_dict[civi_id]['owned_galaxy'].keys())])
        if civi_dict[civi_id]['owned_resource'] <= resource_warning*civi_dict[civi_id]['tech_level']:
            civi_dict[civi_id]['civi_type'] = 'attack'
            text_ = 'turn {}: civi {} has transfer to attack civi type due to resource_warning...'.format(str(turn),civi_id)
            print (text_)
            if civi_dict[civi_id]['original_type'] != 'attack':
                civi_dict[civi_id]['changing_type_times'] += 1
            record_text = record_text + text_ + '\n'
        else:
            if civi_dict[civi_id]['civi_type'] != civi_dict[civi_id]['original_type']:
                civi_dict[civi_id]['back_type_times'] += 1
            civi_dict[civi_id]['civi_type'] = civi_dict[civi_id]['original_type']
        if civi_dict[civi_id]['owned_resource'] <= malthusian_trap*civi_dict[civi_id]['tech_level']:
            civi_dict[civi_id]['malthusian_trap'] += 1
            civi_dict[civi_id]['tech_level'] *= 0.5*(max(random.gauss(setting_gau_mean,setting_gau_sigma),setting_gau_min))
            text_ = 'turn {}: civi {} has happended malthusian trap...'.format(str(turn),civi_id)
            print (text_)
            record_text = record_text + text_ + '\n'
        if civi_dict[civi_id]['owned_resource'] <= 0:
            civi_dict[civi_id]['extinct'] = 'resource_out'
            civi_dict[civi_id]['extinct_turn'] = turn
            civi_dict[civi_id]['living_turn'] = turn - civi_dict[civi_id]['original_turn']
            text_ = 'turn {}: civi {} has extincted due to resource_out...'.format(str(turn),civi_id)
            print (text_)
            record_text = record_text + text_ + '\n'
    return civi_dict,coordinate_dict,record_text


def GetEvolvedNew(turn,n,setting,coordinate_dict,civi_dict,record_text):
    global sign_list
    LBC = setting['life_born_coefficient']
    ConC = setting['consume_coefficient']
    setting_gau_mean = setting['setting_gau_mean']
    setting_gau_sigma = setting['setting_gau_sigma']
    setting_gau_min = setting['setting_gau_min']
    for i in range(n):
        for j in range(n):
            coordinate = ' '.join([str(i),str(j)])
            if coordinate_dict[coordinate]['exist'] == 0:
                continue
            owner_state = coordinate_dict[coordinate]['owner']
            if owner_state == 0:
                random_prob = random.random()
                if random_prob<LBC*coordinate_dict[coordinate]['inital_state']*(max(random.gauss(setting_gau_mean,setting_gau_sigma),setting_gau_min)):
                    if len(civi_dict.keys()) == 0:
                        civi_id = str(1)
                        civi_dict[civi_id] = {}
                        text_ = 'turn {}: civi 1 has born...'.format(str(turn))
                        print (text_)
                        record_text = record_text + text_ + '\n'
                    else:
                        civi_id = str(sorted([int(i) for i in civi_dict.keys()],reverse=True)[0]+1)
                        civi_dict[civi_id] = {}
                        text_ = 'turn {}: civi {} has born...'.format(str(turn),civi_id)
                        print (text_)
                        record_text = record_text + text_ + '\n'
                    coordinate_dict[coordinate]['owner'] = civi_id
                    civi_dict[civi_id]['main_galaxy'] = coordinate
                    civi_dict[civi_id]['original_galaxy_gift'] = coordinate_dict[coordinate]['inital_state']
                    civi_dict[civi_id]['tech_level'] = 1
                    civi_dict[civi_id]['consume_rate'] = ConC*civi_dict[civi_id]['tech_level']*(max(random.gauss(setting_gau_mean,setting_gau_sigma),setting_gau_min))
                    civi_dict[civi_id]['owned_galaxy'] = {coordinate:coordinate_dict[coordinate]['resource']}
                    civi_dict[civi_id]['owned_galaxy_num'] = 1
                    civi_dict[civi_id]['owned_resource'] = coordinate_dict[coordinate]['resource']
                    civi_dict = GetType(setting,civi_dict,'civi_type',civi_id,"civi_generate")
                    civi_dict[civi_id]['changing_type_times'] = 0
                    civi_dict[civi_id]['back_type_times'] = 0
                    civi_dict[civi_id]['malthusian_trap'] = 0
                    civi_dict[civi_id]['out_resource_gala_num'] = 0
                    civi_dict[civi_id]['extinct'] = 'nan' 
                    civi_dict[civi_id]['original_turn'] = turn
                    civi_dict[civi_id]['extinct_turn'] = 0   
                    civi_dict[civi_id]['living_turn'] = 0
                    civi_dict[civi_id]['technology_explosion_times'] = 0 
                    civi_dict[civi_id]['reporting_self_times'] = 0   
                    civi_dict[civi_id]['reporting_others_times'] = 0 
                    civi_dict[civi_id]['galaxy_travel_times'] = 0 
                    civi_dict[civi_id]['galaxy_successful_times'] = 0 
                    civi_dict[civi_id]['taken_without_civi_times'] = 0
                    civi_dict[civi_id]['coummunicate_times'] = 0
                    civi_dict[civi_id]['direct_attacker_times'] = 0
                    civi_dict[civi_id]['direct_attacked_times'] = 0
                    civi_dict[civi_id]['direct_war_times'] = 0
                    civi_dict[civi_id]['victory_better_times'] = 0
                    civi_dict[civi_id]['victory_worse_times'] = 0
                    civi_dict[civi_id]['lose_better_times'] = 0
                    civi_dict[civi_id]['lose_worse_times'] = 0
                    civi_dict[civi_id]['dark_forest_attacker'] = 0
                    civi_dict[civi_id]['dark_forest_successful_attacker'] = 0
                    civi_dict[civi_id]['dark_forest_attacked'] = 0
                    civi_dict[civi_id]['dark_forest_survive_attacked'] = 0
                    civi_dict[civi_id]['taken_merge_times'] = 0
                    civi_dict[civi_id]['disasters_num'] = 0
                    civi_dict[civi_id]['sign'] = random.choice(sign_list)
                    
    return coordinate_dict,civi_dict,record_text

def GetType(setting,inital_dict,key_name,id_,run_type):
    inital_state = random.random()
    for key_ in setting[key_name].keys():
        if inital_state >= setting[key_name][key_][0] and \
            inital_state <= setting[key_name][key_][1]:
            if run_type == 'init':
                inital_dict[id_][key_name] = int(key_)
                inital_dict[id_]['resource'] = int(key_)
            elif run_type == 'civi_generate':
                inital_dict[id_][key_name] = key_
                inital_dict[id_]['original_type'] = key_
            break
        else:
            continue
    return inital_dict

def inital_universe(n,setting):
    inital_dict = {}
    for i in range(n):
        for j in range(n):
            coordinate = ' '.join([str(i),str(j)])
            inital_dict[coordinate] = {}
            inital_dict[coordinate]['owner'] = 0
            inital_dict[coordinate]['explore_level'] = 0
            inital_dict[coordinate]['exist'] = 1
            inital_dict[coordinate]['DFA'] = 0
            inital_dict[coordinate]['RR'] = 0
            inital_dict = GetType(setting,inital_dict,'inital_state',coordinate,'init')
    return inital_dict

def DrawGraph(turn,coordinate_dict,civi_dict):
    global output_pictures_path
    color_dict = {'communicate':'g','attack':'r','hide':'blue'}
    

    # fig, ax = plt.subplots(1,1)  
    fig = plt.figure(figsize=(10, 10), dpi=108)
    for gala_id in coordinate_dict:
        gala_coordinate = [int(i) for i in gala_id.split()]
        owner = coordinate_dict[gala_id]['owner']
        if owner ==0 and coordinate_dict[gala_id]['RR'] !=1 and coordinate_dict[gala_id]['DFA'] !=1:
            continue
        if coordinate_dict[gala_id]['DFA'] ==1:
            plt.scatter(gala_coordinate[0], gala_coordinate[1], c='k', marker='x')
        elif coordinate_dict[gala_id]['RR'] ==1:
            plt.scatter(gala_coordinate[0], gala_coordinate[1], c='darkgray', marker='x')
        else:
            color = color_dict[civi_dict[owner]['civi_type']]
            plt.scatter(gala_coordinate[0], gala_coordinate[1], c=color, marker=civi_dict[owner]['sign'])
            if gala_id == civi_dict[owner]['main_galaxy']:
                plt.annotate(owner, (gala_coordinate[0], gala_coordinate[1]))
    plt.xlabel('x')
    plt.ylabel('y')
    plt.xticks([0, 20, 40, 60, 80, 100])
    plt.yticks([0, 20, 40, 60, 80, 100])
    plt.grid(True)
    # plt.show()
    fig.savefig(output_pictures_path.format(str(turn)))




            
if __name__ == '__main__':


    turn_num = 150
    n = 100
    sign_list = ['^' , 'v' , '<' , '>' , 's' , '+' , 'D' , 'd' , 'h' , 'H' , 'p' , '|' , '_' ,   '.' , ',' , 'o','1','2','3','4']

    setting_path = 'etc.json'
    with open(setting_path,"r") as load_f:
        setting = json.load(load_f)

    output_coordinate_path = 'output_coordinate.csv'
    output_civi_path = 'output_civi.csv'
    out_text_path = 'record_log.txt'
    output_pictures_path = './output_pictures/output_{}.png'

    record_text = ''
    
    
    coordinate_dict = inital_universe(n,setting)
    civi_dict = {}
    report_dict = {}
    report_original_dict = {}
    communicate_dict = {}
    attack_dict = {}

    for turn in range(1,turn_num+1):
        # sleep(1)
        coordinate_dict,civi_dict,record_text = GetEvolvedNew(turn,n,setting,coordinate_dict,civi_dict,record_text)
        if civi_dict == {}:
            continue
        living_civi_dict = [civi_id for civi_id in civi_dict.keys() if civi_dict[civi_id]['extinct'] == 'nan']
        if len(living_civi_dict) == 0:
            continue
        civi_dict,coordinate_dict,record_text = GetEvolvedTechCon(turn,setting,civi_dict,coordinate_dict,record_text)
        civi_dict,coordinate_dict,report_dict,communicate_dict,record_text = GetEvolvedExplore(n,turn,setting,civi_dict,coordinate_dict,report_dict,report_original_dict,communicate_dict,record_text)
        civi_dict,coordinate_dict,report_dict,communicate_dict,attack_dict,record_text = GetAudit(n,turn,setting,civi_dict,coordinate_dict,report_dict,report_original_dict,communicate_dict,attack_dict,record_text)
        print (turn)
        if turn % 10 ==0:
            DrawGraph(turn,coordinate_dict,civi_dict)
    
    coordinate_df = pd.DataFrame(coordinate_dict).T
    coordinate_df.to_csv(output_coordinate_path)
    civi_df = pd.DataFrame(civi_dict).T
    civi_df.to_csv(output_civi_path)

    with open(out_text_path,"w") as f:
        f.write(record_text)
    
    


    
