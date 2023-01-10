#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/12/13 23:09
# @Author  : jsx
# @File    : issue_disentangle.py
# @Description :
import csv

import networkx as nx
import numpy as np
import pymysql
from sklearn import metrics
import config
from ananlyze_modified_for_issue import topicExtract, getAllComponents
from preprocess_modified_for_issue import getIssueByProject, preprocess, getIssueByKey


def textSim(senVec1, senVec2):
    # '''欧式距离'''
    # return np.linalg.norm(senVec1-senVec2)
    """余弦相似"""
    return np.dot(senVec1, senVec2) / (np.linalg.norm(senVec1) * (np.linalg.norm(senVec2)))


def buildTextGraph(issueDf):
    n = issueDf.shape[0]
    CGMatrix = np.zeros((n, n))
    for index, issue in issueDf.iterrows():
        summaryVec = issue['summary'][4]
        if len(summaryVec) != 300:
            print(index)
            print(issue['summary'])
        if len(summaryVec) == 0:
            continue
        for thatIndex, thatIssue in issueDf.iterrows():
            if thatIndex != index:
                thatSummaryVec = thatIssue['summary'][4]
                if len(thatSummaryVec) != 0:
                    similarity = textSim(summaryVec, thatSummaryVec)
                if similarity > config.DisentangleInit.THERHOLD:
                    CGMatrix[index][thatIndex] = similarity
    np.savetxt('new1.csv', CGMatrix.T, delimiter=',')
    return CGMatrix


def calDescription(issueDf):
    n = issueDf.shape[0]
    CGMatrix = np.zeros((n, n))
    for index, issue in issueDf.iterrows():
        descriptionVec = issue['description'][4]
        if len(descriptionVec) == 0:
            continue
        for thatIndex, thatIssue in issueDf.iterrows():
            if thatIndex != index:
                thatDescriptionVec = thatIssue['description'][4]
                if len(thatDescriptionVec) != 0:
                    maxSim = 0
                    for sen1 in descriptionVec:
                        for sen2 in thatDescriptionVec:
                            if len(sen1) != 300 or len(sen2) != 300:
                                continue
                            similarity = textSim(sen1, sen2)
                            if similarity > maxSim:
                                maxSim = similarity
                    CGMatrix[index][thatIndex] = maxSim
    np.savetxt('new3.csv', CGMatrix.T, delimiter=',')
    return CGMatrix


def getConnectionGraph(CGMatrix):
    CG = nx.Graph(CGMatrix)
    issueLst = [list(c) for c in list(nx.connected_components(CG))]
    print(issueLst)
    return issueLst


issueDB = pymysql.connect(host=config.MySQLConfig.HOST, user=config.MySQLConfig.USER,
                          password=config.MySQLConfig.PASSWORD,
                          database="issue", autocommit=config.MySQLConfig.AUTOCOMMIT)
issueCursor = issueDB.cursor()
issueDataFrame = getIssueByProject(issueCursor, 'zookeeper')
# # print(issueDataFrame)
# issueDataFrame = getIssueByKey(issueCursor,
#                               "zookeeper-572")  # 测试数据包括2049,1014,3288,3634,4334,3914,3882,4238,4288,4299, 1517
issueDataFrame = preprocess(issueDataFrame, 'fasttext')
# matrix = calDescription(issueDataFrame)
# issueClassification = getConnectionGraph(matrix)
matrix = np.zeros((4163, 4163))
b = np.loadtxt("new1.csv", delimiter=",")
b = b.T
for x in range(0, 4163):
    # print(x)
    row = []
    for y in range(0, 4163):
        k = float(b[x][y])
        if k > 0.85:
            matrix[x][y] = k
        else:
            matrix[x][y] = 0
# np.savetxt('new2.csv', matrix.T, delimiter=',')
classification = getConnectionGraph(matrix)
classification.sort(key=lambda c: len(c), reverse=True)
componentClass = {'server': 0, 'client': 1, 'tests': 2, 'documentation': 3, 'build': 4, 'quorum': 5, 'scripts': 6,
                  'leaderElection': 7, 'security': 8, 'metric system': 9, 'jmx': 10, 'jute': 11, 'default other': 12}
answerLst = getAllComponents(issueCursor, 'zookeeper')
classifyResult = []
for i in range(0, len(componentClass.keys())):
    classifyResult.append([])
print(len(classifyResult))
for c in classification:
    if len(c) >= 5:
        summaryLst = []
        for id in c:
            summaryLst.append(issueDataFrame.iloc[id]['summary'][3])
        topicLst = topicExtract(summaryLst, 5).items()
        topicLst = sorted(topicLst, key=lambda x: x[1], reverse=True)
        print(topicLst)
        # print(topicLst)
        for key in topicLst:
            if key[0] in componentClass.keys():
                classifyResult[componentClass[key[0]]].extend([issueDataFrame.iloc[id]['issue_key'] for id in c])
                break
        else:
            classifyResult[componentClass['default other']].extend([issueDataFrame.iloc[id]['issue_key'] for id in c])
A = []
B = []
menu = {}
# for answer in answerLst:
#     if answer[1] in componentClass.keys():
#         if answer[0] in menu.keys():
#             if A[menu[answer[0]]] > componentClass[answer[1]]:
#                 A[menu[answer[0]]] = componentClass[answer[1]]
#         else:
#             A.append(componentClass[answer[1]])
#             menu[answer[0]] = len(A) - 1
#             flag = True
#             for cla in range(0, len(classifyResult)):
#                 if flag:
#                     for id in classifyResult[cla]:
#                         if id == answer[0]:
#                             B.append(cla)
#                             flag = False
#                             break
#             if flag:
#                 B.append(12)
for answer in answerLst:
    if answer[1] in componentClass.keys():
        for cla in range(0, len(classifyResult)):
            for id in classifyResult[cla]:
                if id == answer[0]:
                    if answer[0] in menu.keys():
                        if A[menu[answer[0]]] > componentClass[answer[1]]:
                            A[menu[answer[0]]] = componentClass[answer[1]]
                    else:
                        A.append(componentClass[answer[1]])
                        menu[answer[0]] = len(A) - 1
                        B.append(cla)
                    break
print(len(A))
print(A)
print(B)
print('NMI:' + str(metrics.normalized_mutual_info_score(A, B)))
# with open('result.txt', 'w', encoding='utf-8') as f:
#     for c in classification:
#         for id in c:
#             f.write(str(issueDataFrame.iloc[id]['issue_key']) + '     ' + str(issueDataFrame.iloc[id]['summary'][0]) + '\n')
#         f.write(config.DefaultString.SEPARATOR)
# f.close()
