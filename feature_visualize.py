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
                plt.axhline(y=releases.index(v)+1, linestyle='--', color='lightblue')
        plt.xticks(rotation=90, ha='center')
        label = ['version']
        plt.legend(label, loc='upper right')
        plt.savefig(config.RootDir.EXPORTROOT + 'time.png')
        plt.show()

    return




issueDB = pymysql.connect(host=config.MySQLConfig.HOST, user=config.MySQLConfig.USER,
                           password=config.MySQLConfig.PASSWORD,
                           database="issue", autocommit=config.MySQLConfig.AUTOCOMMIT)
issueCursor = issueDB.cursor()
releaseNote = config.ProjectVersion.ZOOKEEPER
timeAnalyze(issueCursor, 'zookeeper', releaseNote)
