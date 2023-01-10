import re

import pymysql
import pandas as pd
import config
from gensim import corpora, models


def getLabelCount(cursor, projectName: str) -> dict:
    """
    Statistic labels in project
    :param cursor: cursor, issue database cursor
    :param projectName: string
    :return: labelDic: dic, a dic of label-count pair,
               example:{'documentation': 12, 'client': 5, 'dependencies': 2, 'maven': 4, 'pull-request-available': 819}
    """
    sqlValue = "SELECT LABELS FROM ISSUE WHERE PROJECT='" + projectName + "' AND NOT LABELS=''"
    if cursor.execute(sqlValue) != 0:
        labelsLst = [u[0] for u in cursor.fetchall()]
    else:
        return {}
    labelDic = {}
    for labels in labelsLst:
        for l in re.split("[;,]", labels):
            l = l.strip()
            if l != '':
                if l in labelDic.keys():
                    labelDic[l] = labelDic[l] + 1
                else:
                    labelDic[l] = 1
    return labelDic


def getComponentCount(cursor, projectName: str) -> dict:
    """
        Statistic labels in project
        :param cursor: cursor, issue database cursor
        :param projectName: string
        :return: componentDic: dic, a dic of component-count pair,
                   example:{'server': 1022, 'c client': 400, 'java client': 398, 'tests': 289, 'documentation': 269}
        """
    sqlValue = "SELECT COMPONENT FROM ISSUE_COMPONENT WHERE ISSUE_KEY like '" + projectName + "%'"
    if cursor.execute(sqlValue) != 0:
        componentsLst = [u[0] for u in cursor.fetchall()]
    else:
        return {}
    componentDic = pd.value_counts(componentsLst).to_dict()
    return componentDic


def getAllComponents(cursor, projectName: str):
    sqlValue = "SELECT * FROM ISSUE_COMPONENT WHERE ISSUE_KEY like '" + projectName + "%'"
    if cursor.execute(sqlValue) != 0:
        componentsLst = [list(u) for u in cursor.fetchall()]
    return componentsLst


# 生成LDA模型
def LDAModel(words_list):
    # 构造词典
    # Dictionary()方法遍历所有的文本，为每个不重复的单词分配一个单独的整数ID，同时收集该单词出现次数以及相关的统计信息
    dictionary = corpora.Dictionary(words_list)
    # print(dictionary)
    # print('打印查看每个单词的id:')
    # print(dictionary.token2id)  # 打印查看每个单词的id

    # 将dictionary转化为一个词袋
    # doc2bow()方法将dictionary转化为一个词袋。得到的结果corpus是一个向量的列表，向量的个数就是文档数。
    # 在每个文档向量中都包含一系列元组,元组的形式是（单词 ID，词频）
    corpus = [dictionary.doc2bow(words) for words in words_list]
    # print('输出每个文档的向量:')
    # print(corpus)  # 输出每个文档的向量

    # LDA主题模型
    # num_topics -- 必须，要生成的主题个数。
    # id2word    -- 必须，LdaModel类要求我们之前的dictionary把id都映射成为字符串。
    # passes     -- 可选，模型遍历语料库的次数。遍历的次数越多，模型越精确。但是对于非常大的语料库，遍历太多次会花费很长的时间。
    lda_model = models.ldamodel.LdaModel(corpus=corpus, num_topics=2, id2word=dictionary, passes=10)
    return lda_model


def topicExtract(summaryLst, validLen=5):
    ldaModel = LDAModel(summaryLst)
    keyWords = ldaModel.show_topic(0, validLen)
    kvDict = {}
    for kv in keyWords:
        kvDict[kv[0]] = str(kv[1])
    return kvDict


def NMI():
    return
# issueDB = pymysql.connect(host=config.MySQLConfig.HOST, user=config.MySQLConfig.USER,
#                           password=config.MySQLConfig.PASSWORD,
#                           database="issue", autocommit=config.MySQLConfig.AUTOCOMMIT)
# issueCursor = issueDB.cursor()
# labelDic = getComponentCount(issueCursor, 'Zookeeper')
# print(type(labelDic))
# print(labelDic)
# labelLst = sorted(labelDic.items(), key=lambda x: x[1], reverse=True)
# for l in labelLst:
#     print(l)
