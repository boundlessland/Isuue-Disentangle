#!/usr/bin/env python37
# -*- coding: utf-8 -*-
# @Time    : 2022/11/13 18:03
# @Author  : jsx
# @File    : codeFilter.py
# @Description : Find JAVA code in the string. Improved based on infozilla.
import pymysql
import config
import re


def javaCodeFilter(s):
    """
    Public. Find all JAVA code in the string based on the regular expression
    :param s: string
    :return: codeRegions: list, list of code regions, each code region contains 4 attributes, namely start index,
               end index, tag, code
               example: [[0, 545, 'functiondef', 'int zoo_amulti(zhandle_t *zh, int count, const zoo_op_t *ops,\r\n
                          ...
                          queue_completion(&clist, entry, 0); //queue it will\xa0segment\xa0errors{color}}\r'],
                         [545, 866, 'functiondef', '\n\r\n\xa0\r\n\r\n\xa0\r\n\r\n
                          ...
                          \xa0\xa0\xa0\xa0unlock_completion_list(list); }\r'],
                         [341, 384, 'singlecomment', ' //\xa0not initialize for cond or lock{color}\r'],
                         [505, 545, 'singlecomment', ' //queue it will\xa0segment\xa0errors{color}}\r'],
                         [573, 635, 'singlecomment', '// do lock or unlock which have not been initialized!!{color}\r'],
                         [867, 1047, 'functiondef', '\r\n{color:#FF0000}// oh my god!!{color}\r\n int\xa0
                          ...
                          \xa0\xa0\xa0\xa0return\xa0p_thread_mutex_unlock(&l->lock); }'],
                         [884, 906, 'singlecomment', '// oh my god!!{color}\r']]
    """
    codeRegions = []
    # for each keyword - pattern pair find the corresponding occurences!
    for keyword in config.CodePattern.JAVACODEPATTERN.keys():
        pattern = config.CodePattern.JAVACODEPATTERN[keyword]
        patternOptions = config.CodePattern.JAVACODEPATTERNOPTIONS[keyword]
        if patternOptions == "MATCH":
            for match in re.finditer(pattern, s, flags=re.DOTALL):
                indexStart = match.start()
                indexEnd = match.end()
                offset = findmatch(s, '{', '}', indexEnd-1)  # 一些java关键词是伴随着{}出现的，如if-else语句，通过findmatch方法找到{}的范围
                codeRegion = [indexStart, indexEnd + offset, keyword, s[indexStart: indexEnd + offset]]
                codeRegions.append(codeRegion)
        else:
            for match in re.finditer(pattern, s, flags=re.DOTALL):
                indexStart = match.start()
                indexEnd = match.end()
                codeRegion = [indexStart, indexEnd, keyword, s[indexStart: indexEnd]]
                codeRegions.append(codeRegion)
    codeRegions = makeMinimalSet(codeRegions)  # 匹配得到的codeRegions是相互重叠的，使用makeMinimalSet方法获得最小集（无论是否重叠，注释都不会被抛弃）
    return codeRegions


def findmatch(s, opening, closing, start):
    """
    findMatch() returns the offset where the next closing is found. If not found return 0. Can handle nesting.
    :param s: string
    :param opening: char, example: '{'
    :param closing: char, example: '}'
    :param start: int, Decide where to start searching
    :return: position: int
    """
    s = s[start:]
    level = 0
    position = 0
    for c in s:
        position = position + 1
        if c == opening:
            level = level + 1
        if c == closing:
            level = level - 1
            if level == 0:
                return position

    return 0


def makeMinimalSet(codeRegions):
    """
    De duplication according to the start position and end position.
    :param codeRegions: list, list of code regions, each code region contains 4 attributes, namely start index,
             end index, tag, code
             example: [[341, 384, 'singlecomment', ' //\xa0not initialize for cond or lock{color}\r'],
                       [505, 545, 'singlecomment', ' //queue it will\xa0segment\xa0errors{color}}\r'],
                       [573, 635, 'singlecomment', '// do lock or unlock which have not been initialized!!{color}\r'],
                       [884, 906, 'singlecomment', '// oh my god!!{color}\r'],
                       [0, 545, 'functiondef', 'int zoo_amulti(zhandle_t *zh, int count, const zoo_op_t *ops,\r\n
                        ...
                        queue_completion(&clist, entry, 0); //queue it will\xa0segment\xa0errors{color}}\r'],
                       [197, 866, 'functiondef', '\r\n;\r\n struct MultiHeader mh = \\{-1, 1, -1};\r\n
                        ...
                        \xa0\xa0\xa0\xa0unlock_completion_list(list); }\r'],
                       [867, 1047, 'functiondef', '\r\n{color:#FF0000}// oh my god!!{color}\r\n
                        ...
                        \xa0\xa0\xa0\xa0return\xa0p_thread_mutex_unlock(&l->lock); }']]
    :return: miniSet: list, list of code regions, each code region contains 4 attributes, namely start index,
               end index, tag, code
               example: [[0, 545, 'functiondef', 'int zoo_amulti(zhandle_t *zh, int count, const zoo_op_t *ops,\r\n
                          ...
                          queue_completion(&clist, entry, 0); //queue it will\xa0segment\xa0errors{color}}\r'],
                         [545, 866, 'functiondef', '\n\r\n\xa0\r\n\r\n\xa0\r\n\r\n
                          ...
                          \xa0\xa0\xa0\xa0unlock_completion_list(list); }\r'],
                         [341, 384, 'singlecomment', ' //\xa0not initialize for cond or lock{color}\r'],
                         [505, 545, 'singlecomment', ' //queue it will\xa0segment\xa0errors{color}}\r'],
                         [573, 635, 'singlecomment', '// do lock or unlock which have not been initialized!!{color}\r'],
                         [867, 1047, 'functiondef', '\r\n{color:#FF0000}// oh my god!!{color}\r\n
                          ...
                          \xa0\xa0\xa0\xa0return\xa0p_thread_mutex_unlock(&l->lock); }'],
                         [884, 906, 'singlecomment', '// oh my god!!{color}\r']]
    """
    codeRegions.sort(key=lambda x: x[0])  # Sort it Ascending(by start position)
    miniSet = []
    for i in range(0, len(codeRegions)):
        thisRegion = codeRegions[i]
        isContained = False
        if thisRegion[2] == 'multicomment':  # 根据定义，多行注释不会包含在单行注释中
            isContained = False
        elif thisRegion[2] == 'singlecomment':  # 单行注释可能包括在多行注释中
            for j in range(0, i):
                thatRegion = codeRegions[j]
                if thatRegion[2] == 'multicomment' and thatRegion[1] >= thisRegion[1]:
                    isContained = True
                    break
        else:
            for j in range(0, i):
                thatRegion = codeRegions[j]
                if thatRegion[1] >= thisRegion[1]:
                    isContained = True
                    break
        if not isContained:
            if thisRegion[2] != 'multicomment' and thisRegion[2] != 'singlecomment':
                for thatRegion in miniSet:
                    if thatRegion[1] >= thisRegion[0]:
                        thisRegion[3] = thisRegion[3][thatRegion[1] - thisRegion[0]:]
                        thisRegion[0] = thatRegion[1]
            miniSet.append(thisRegion)
    return miniSet


# sqlValue = "SELECT * FROM ISSUE WHERE ISSUE_KEY='ZOOKEEPER-4299'"
# issueDB = pymysql.connect(host=config.MySQLConfig.HOST, user=config.MySQLConfig.USER,
#                           password=config.MySQLConfig.PASSWORD,
#                           database="issue", autocommit=config.MySQLConfig.AUTOCOMMIT)
# issueCursor = issueDB.cursor()
#
# if issueCursor.execute(sqlValue) != 0:
#     issueLst = [list(u) for u in issueCursor.fetchall()]
# str = issueLst[0][8]
# code = javaCodeFilter(str)
# # for c in code:
#     print(c)
# print()
# code = makeMinimalSet(code)
# for c in code:
#     print(c)
