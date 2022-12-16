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

import config
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
# # # print(issueDataFrame)
# # issueDataFrame = getIssueByKey(issueCursor,
# #                               "zookeeper-572")  # 测试数据包括2049,1014,3288,3634,4334,3914,3882,4238,4288,4299, 1517
# issueDataFrame = preprocess(issueDataFrame, 'fasttext')
# matrix = buildTextGraph(issueDataFrame)
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
np.savetxt('new2.csv', matrix.T, delimiter=',')
print(len(matrix))
print(len(matrix[0]))
classification = getConnectionGraph(matrix)
with open('result.txt', 'w', encoding='utf-8') as f:
    for c in classification:
        for id in c:
            f.write(str(id) + '     ' + issueDataFrame.iloc[id]['summary'] + '\n')
        f.write(config.DefaultString.SEPARATOR)
f.close()