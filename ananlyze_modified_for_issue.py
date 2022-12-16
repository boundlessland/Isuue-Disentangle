import re

import pymysql
import pandas as pd
import config


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
