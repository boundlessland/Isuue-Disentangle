import random

import pymysql
import matplotlib.pyplot as plt
from matplotlib.dates import AutoDateLocator, DateFormatter
import matplotlib.dates as mdates
import datetime

import config


def timeAnalyze(cursor, projectName, releaseNote):
    """
    Generate a scatterplot of the relationship between version and issue creation time
    :param cursor: cursor, issue database cursor
    :param projectName: string
    :param releaseNote: dic, dic of version-release-time pair
    :return:
    """
    sqlValue = "select issue.create_time, iv.version from issue join issue_version iv on " \
               "issue.issue_key = iv.issue_key where issue.project='zookeeper'"
    releases = list(releaseNote.items())
    releases = sorted(releases, key=lambda x: x[1])
    releases = [v[0] for v in releases]
    print(releases)
    if cursor.execute(sqlValue) != 0:
        timeVersion = [list(u) for u in cursor.fetchall()]
        x = []
        y = []
        for tv in timeVersion:
            if tv[1] in releases:
                x.append(datetime.datetime.fromisoformat(tv[0][:-9]))
                y.append(releases.index(tv[1]) + 1)
        print(x)
        plt.figure(figsize=(24, 16))
        plt.plot_date(x, y, fmt='g.')
        plt.yticks([i for i in range(1, len(releases) + 1)], releases)
        ax = plt.gca()
        ax.xaxis.set_major_formatter(DateFormatter('%Y-%m'))  # 设置时间显示格式
        ax.xaxis.set_major_locator(AutoDateLocator(maxticks=100))  # 设置时间间隔
        for v in releases:
            if v == '3.5.0':
                t = datetime.datetime.strptime(releaseNote[v], '%Y-%m-%d')
                plt.axvline(x=t, linestyle='--', color='lightblue')
                plt.axhline(y=releases.index(v) + 1, linestyle='--', color='lightblue')
        plt.xticks(rotation=90, ha='center')
        label = ['version']
        plt.legend(label, loc='upper right')
        plt.savefig(config.RootDir.EXPORTROOT + 'time.png')
        plt.show()

    return


def assigneeAnalyze(cursor, projectName):
    """
    Generate a scatterplot of the relationship between assignees and components
    :param cursor: cursor, issue database cursor
    :param projectName: string
    :return:
    """
    sqlValue = "select issue.create_time, ic.component, issue.assignee from issue join issue_component ic on " \
               "issue.issue_key = ic.issue_key where issue.project='" + projectName + "'"
    if cursor.execute(sqlValue) != 0:
        timeComponent = [list(u) for u in cursor.fetchall()]
        assigneesCount = {}
        for tc in timeComponent:
            if not tc[0] is None and not tc[1] is None and not tc[2] is None:
                if tc[2] in assigneesCount.keys():
                    assigneesCount[tc[2]] = assigneesCount[tc[2]] + 1
                else:
                    assigneesCount[tc[2]] = 1
        ac = list(assigneesCount.items())
        ac.sort(key=lambda a: a[1], reverse=True)
        mainAssignees = [ac[i][0] for i in range(15, 20)]
        assigneeColor = {}
        assigneeFirstAppear = {}
        for assignee in mainAssignees:
            assigneeColor[assignee] = randomColor()
            assigneeFirstAppear[assignee] = True
        componentCount = {}
        for tc in timeComponent:
            if not tc[0] is None and not tc[1] is None and not tc[2] is None:
                if tc[1] in componentCount.keys():
                    componentCount[tc[1]] = componentCount[tc[1]] + 1
                else:
                    componentCount[tc[1]] = 1
        cc = list(componentCount.items())
        cc.sort(key=lambda a: a[1], reverse=True)
        mainComponents = [cc[i][0] for i in range(0, 10)]
        # print(components)
        # print(componentCount)
        # print(assigneeColor)
        plt.figure(figsize=(24, 16))
        pointCount = 0
        for tc in timeComponent:
            if not tc[0] is None and tc[1] in mainComponents and tc[2] in mainAssignees:
                x = datetime.datetime.fromisoformat(tc[0][:-9])
                y = mainComponents.index(tc[1]) + 1
                if assigneeFirstAppear[tc[2]]:
                    plt.scatter(x, y, c=assigneeColor[tc[2]], label=tc[2])
                    assigneeFirstAppear[tc[2]] = False
                else:
                    plt.scatter(x, y, c=assigneeColor[tc[2]])
                pointCount = pointCount + 1
        print('共计' + str(pointCount) + '条有效数据')
        plt.yticks([i for i in range(1, len(mainComponents) + 1)], mainComponents)
        ax = plt.gca()
        ax.xaxis.set_major_formatter(DateFormatter('%Y-%m'))  # 设置时间显示格式
        ax.xaxis.set_major_locator(AutoDateLocator(maxticks=100))  # 设置时间间隔
        plt.xticks(rotation=90, ha='center')
        plt.legend(loc='upper right')
        plt.savefig(config.RootDir.EXPORTROOT + 'assignee3.png')
        plt.show()

    return


def randomColor():
    """
    Random Color
    :return: color: string
    """
    color_index = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F']
    color = ''
    for j in range(0, 6):
        color = color + color_index[random.randint(0, len(color_index) - 1)]
    color = '#' + color
    return color


issueDB = pymysql.connect(host=config.MySQLConfig.HOST, user=config.MySQLConfig.USER,
                          password=config.MySQLConfig.PASSWORD,
                          database="issue", autocommit=config.MySQLConfig.AUTOCOMMIT)
issueCursor = issueDB.cursor()
# releaseNote = config.ProjectVersion.ZOOKEEPER
assigneeAnalyze(issueCursor, 'zookeeper')
