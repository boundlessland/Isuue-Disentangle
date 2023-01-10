from enum import Enum, unique

import pandas as pd
import pymysql
from nltk import regexp_tokenize, pos_tag
from nltk.tokenize import sent_tokenize
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
import re

import config

from embedding import TextEncoder
import stackTraceFilter
import codeFilter


def getUrls(s):
    """
    Get the location of the url in the string based on the regular expression
    :param s: string
    :return: urlLst: list, list of url-regions, each url-region contains 4 attributes, namely, start index, end index,
               tag, url
               example: [[0, 50, 'url', 'http://zookeeper.apache.org/doc/trunk/recipes.html']]
    """
    urlPattern = config.RePattern.URLPATTERN
    urlLst = []
    for match in re.finditer(urlPattern, s, flags=re.DOTALL):
        urlLst.append([match.start(), match.end(), 'url', s[match.start(): match.end()]])
    return urlLst


def getIssueByProject(cursor, name):
    """
    Find all issues under the project from the database according to the project name
    :param cursor: cursor, issue database cursor
    :param name: string, project name
    :return: issueDf: dataframe, each issue contains 18 columns, namely issue_id, issue_key, project,
               create_time, update_time, resolve_time, issue_type, summary, description, priority, status, resolution,
               assignee, creator, reporter, environment, watch_count, labels
               example:       issue_id       issue_key  ... watch_count           labels
                        0     12397720     ZOOKEEPER-1  ...           0
                        1     12397969    ZOOKEEPER-10  ...           1
                        2     12401030   ZOOKEEPER-100  ...           2
                        3     12499290  ZOOKEEPER-1000  ...          51
                        4     12499435  ZOOKEEPER-1002  ...           4  ; documentation
    """
    sqlValues = config.SQLExecutor.SELECTALL + "ISSUE WHERE PROJECT='" + name + "'"
    issueLst = [[]]
    if cursor.execute(sqlValues) != 0:
        issueLst = [list(u) for u in cursor.fetchall()]
    else:
        print('Wrong project name')
    issueDf = pd.DataFrame(issueLst, columns=['issue_id', 'issue_key', 'project', 'create_time', 'update_time',
                                              'resolve_time', 'issue_type', 'summary', 'description', 'priority',
                                              'status', 'resolution', 'assignee', 'creator', 'reporter', 'environment',
                                              'watch_count', 'labels'], index=[i for i in range(0, len(issueLst))])
    return issueDf


def getIssueByKey(cursor, key):
    """
    Find all issues from the database according to the issue key
    :param cursor: cursor, issue database cursor
    :param key: string, issue key
    :return: issueDf: dataframe, issue contains 18 columns, namely issue_id, issue_key, project, create_time,
               update_time, resolve_time, issue_type, summary, description, priority, status, resolution, assignee,
               creator, reporter, environment, watch_count, labels
             example:    issue_id       issue_key    project  ... environment watch_count labels
                      0  12514611  ZOOKEEPER-1128  ZOOKEEPER  ...        None           1
    """
    sqlValues = config.SQLExecutor.SELECTALL + "ISSUE WHERE ISSUE_KEY='" + key + "'"
    issue = [[]]
    if cursor.execute(sqlValues) == 1:
        issue = [[list(u) for u in cursor.fetchall()][0]]
    else:
        print("Wrong issue key")
    issueDf = pd.DataFrame(issue, columns=['issue_id', 'issue_key', 'project', 'create_time', 'update_time',
                                           'resolve_time', 'issue_type', 'summary', 'description', 'priority',
                                           'status', 'resolution', 'assignee', 'creator', 'reporter', 'environment',
                                           'watch_count', 'labels'], index=[0])
    return issueDf


def getColoredRegion(s):
    """
    Sometimes the reporter will color some paragraphs in the issue to highlight the key points. Get the location of the
    colored regions in the string based on the regular expression
    :param s: string
    :return: coloredRegion: list, list of colored regions, each colored region contains 4 attributes, namely start index,
               end index, tag, highlights
               example: [[297, 350, '{color:#ff0000}', ' any requests(include zkCli.sh)']]
    """
    coloredRegion = []
    for match in re.finditer(config.RePattern.COLOREDREGION, s, flags=re.DOTALL):
        tmp = s[match.start(): match.end()]
        tag = re.search(config.RePattern.COLOREDTAG, tmp, flags=re.DOTALL)
        tagLength = tag.end() - tag.start()
        # coloredRegion[3]是去除了tag的
        coloredRegion.append([match.start(), match.end(), tag.group(0), tmp[tagLength: -7]])
    return coloredRegion


def removeColorTag(s, regions):
    """
    Based on the position information obtained in getColoredRegion(s), remove the color tag from the string
    :param s: string
    :param regions: list, coloredRegion, example: [[297, 350, '{color:#ff0000}', ' any requests(include zkCli.sh)']]
    :return: s: string
    """
    regions.sort(key=lambda x: x[0], reverse=True)  # 倒序排列
    for r in regions:
        s = s[: r[0]] + ' ' + r[3] + ' ' + s[r[1]:]
    return s


def getExplicitCodeRegion(s):
    """
    Some code regions in the issue are explicitly indicated. Get the location of the code regions in the string based
    on the regular expression
    :param s: string
    :return: codeRegion: list, list of code regions, each code region contains 4 attributes, namely, start index,
               end index, tag, code
               example: [[536, 1978, '{code:java}', '\r\n//my zookeeper pods\r\n[root@node1 ~]# kubectl get po -nsa -o
                          ...
                          server.3=itoa-zookeeper-service3:2888:3888:participant\r\nversion=0\r\n'],
                        [2646, 4002, '{code:java}', '\r\n//177.177.166.244\r\n\r\n
                          ...
                          zk_max_proposal_size    162\r\nzk_min_proposal_size    32\r\n\r\n'],
                        [4062, 6265, '{code:java}', '\r\n[zk: itoa-zookeeper-service1:2181,itoa-zookeeper-service2:2181,
                          ...
                          unix 2 [ ] STREAM CONNECTED 2243034965 109187/java\r\n"]]

    """
    codeRegion = []
    patternPairLst = [[config.RePattern.NOFORMATREGION, config.RePattern.NOFORMATTAG],
                      [config.RePattern.CODEREGION, config.RePattern.CODETAG]]
    for patternPair in patternPairLst:
        for match in re.finditer(patternPair[0], s, flags=re.DOTALL):
            tmp = s[match.start(): match.end()]
            tag = re.search(patternPair[1], tmp, flags=re.DOTALL)
            tagLength = tag.end() - tag.start()
            # codeRegion[3]保存的字符串是去除了tag的，因为tag会导致CodeFilter识别错误
            if tag.group(0).startswith('{code'):
                codeRegion.append([match.start(), match.end(), tag.group(0), tmp[tagLength: -6]])
            else:
                codeRegion.append([match.start(), match.end(), tag.group(0), tmp[tagLength: -tagLength]])
    return codeRegion


def minimalRegions(regions):
    """
    De duplication according to the start position and end position. Similar to makeMinimalSet(codeRegions) in
    codeFilter.py, but tags are not considered here. The results of this step are only used as intermediate products  to
    facilitate data cleaning.
    :param regions: list, list of all non-language regions mentioned above, each region contains 4 attributes, namely
             start index, end index, tag, non-language content
             example: [[0, 505, 'functiondef', 'int zoo_amulti(zhandle_t *zh, int count, const zoo_op_t *ops,\r\n
                        ...
                        queue_completion(&clist, entry, 0); //queue it will\xa0segment\xa0errors }\r'],
                       [505, 806, 'functiondef', '\n\r\n\xa0\r\n\r\n\xa0\r\n\r\n
                        ...
                        add_to_front); \xa0\xa0\xa0\xa0unlock_completion_list(list); }\r'],
                       [327, 364, 'singlecomment', ' //\xa0not initialize for cond or lock \r'],
                       [471, 505, 'singlecomment', ' //queue it will\xa0segment\xa0errors }\r'],
                       [505, 575, 'singlecomment', '\n\r\n\xa0\r\n\r\n\xa0\r\n\r\n // do lock or unlock which have not
                        been initialized!! \r'],
                       [805, 826, 'singlecomment', '\r\n\r\n // oh my god!! \r'],
                       [826, 967, 'functiondef', '\n int\xa0unlock_completion_list(completion_head_t\xa0*l)\r\n\r\n
                        ...
                        return\xa0p_thread_mutex_unlock(&l->lock); }']]
    :return: newRegions: list, list of all non-language regions mentioned above, each region contains 4 attributes, namely
               start index, end index, tag, non-language content
               example: [[0, 967, 'functiondef,functiondef,singlecomment,functiondef', 'int zoo_amulti(zhandle_t *zh,
                          ...
                          p_thread_mutex_unlock(&l->lock); }']]
    """
    regions.sort(key=lambda x: x[0])  # 正序排列
    newRegions = []
    for i in range(0, len(regions)):
        thisRegion = regions[i]
        isContained = False
        for j in range(0, len(newRegions)):
            thatRegion = newRegions[j]
            if thisRegion[1] <= thatRegion[1]:  # 去重
                isContained = True
                break
            elif thisRegion[0] <= thatRegion[1]:  # 融合
                thatRegion[3] = thatRegion[3] + thisRegion[3][(thatRegion[1] - thisRegion[0]):]
                thatRegion[1] = thisRegion[1]
                thatRegion[2] = thatRegion[2] + ',' + thisRegion[2]
                isContained = True
                newRegions[j] = thatRegion  # 更新融合后的region
                break
        if not isContained:
            newRegions.append([thisRegion[0], thisRegion[1], thisRegion[2], thisRegion[3]])  # list对象机制
    newRegions.sort(key=lambda x: x[0], reverse=True)  # 倒序输出，方便剪裁
    return newRegions


def cleanStr(s):
    """
    Remove all nonverbal content from the string
    :param s: string, raw
    :return: result: list, generate cleaned string for raw text, each result contains 3 columns, namely raw_string,
               non_language_regions, cleaned_string
               example:['http://zookeeper.apache.org/doc/trunk/recipes.html\nThe current recipe for Lock has the wrong
                        ...
                        System.out.println("Continue to seek");\n            }\n        }\n{code} ',
                        [[0, 51, 'url,singlecomment', 'http://zookeeper.apache.org/doc/trunk/recipes.html\n'],
                         ...
                         [3861, 3871, 'functiondef', '        }\n']],
                        ' The current recipe for Lock has the wrong process.\nSpecifically, for the \n"4.
                        ...
                        \nzookeeper.apache.org/doc/trunk/recipes.html\nI\'ve got the lock and release it']

    """
    # 在所有操作开始前先抛弃{color}标签，为简化代码逻辑，这里直接在text上进行删除（后续位标都会发生变化）
    if s:
        coloredRegion = getColoredRegion(s)
        s = removeColorTag(s, coloredRegion)
        resultLst = [s]
        nonLanguageRegion = getNonLanguage(s)
        resultLst.append(nonLanguageRegion)
        miniRegion = minimalRegions(nonLanguageRegion)
        # print(nonLanguageRegion)
        # 由于句子的顺序不影响后续分析，在去除nonLanguage部分时被去除的注释直接加在文本后即可
        for r in miniRegion:
            s = s[: r[0]] + ' ' + s[r[1]:]
        for a in nonLanguageRegion:
            if a[2] == 'singlecomment':
                s = s + '\n' + a[3].strip()[2:]
            elif a[2] == 'multicomment':
                s = s + '\n' + a[3].strip()[2: -2]
        s = s.replace(u'\xa0', ' ')  # 去除超文本空格
        resultLst.append(s)
        # print(resultLst)
    else:
        resultLst = ['', [], '']
    return resultLst


def getNonLanguage(s):
    """
    Get all non-language region in string. Including getUrls(s), getExplicitCodeRegion(s), javaStackTraceFilter(s),
    javaCodeFilter(s)
    :param s: string
    :return: nonLanguage: list, list of non-language regions, each region contains 4 attributes, namely
               start index, end index, tag, non-language content
               example: [[0, 505, 'functiondef', 'int zoo_amulti(zhandle_t *zh, int count, const zoo_op_t *ops,\r\n
                          ...
                          queue_completion(&clist, entry, 0); //queue it will\xa0segment\xa0errors }\r'],
                         [505, 806, 'functiondef', '\n\r\n\xa0\r\n\r\n\xa0\r\n\r\n
                          ...
                          add_to_front); \xa0\xa0\xa0\xa0unlock_completion_list(list); }\r'],
                         [327, 364, 'singlecomment', ' //\xa0not initialize for cond or lock \r'],
                         [471, 505, 'singlecomment', ' //queue it will\xa0segment\xa0errors }\r'],
                         [505, 575, 'singlecomment', '\n\r\n\xa0\r\n\r\n\xa0\r\n\r\n // do lock or unlock which have not
                          been initialized!! \r'],
                         [805, 826, 'singlecomment', '\r\n\r\n // oh my god!! \r'],
                         [826, 967, 'functiondef', '\n int\xa0unlock_completion_list(completion_head_t\xa0*l)\r\n\r\n
                          ...
                          return\xa0p_thread_mutex_unlock(&l->lock); }']]
    """
    nonLanguage = []
    if s:
        nonLanguage.extend(getUrls(s))
        explicitCodeRegion = getExplicitCodeRegion(s)
        nonLanguage.extend(explicitCodeRegion)
        # 处理无显示标明的代码区的情况
        if len(explicitCodeRegion) == 0:
            stackTrace, cause = stackTraceFilter.javaStackTraceFilter(s)
            code = codeFilter.javaCodeFilter(s)
            nonLanguage.extend(stackTrace)
            nonLanguage.extend(cause)
            nonLanguage.extend(code)
        # 处理显式标明的代码区中的
        else:
            for region in explicitCodeRegion:
                # stackTrace, cause, code可能相互包含，这里的位标已经和最初不一样了，裁剪时要加上region的偏移量
                # print(region)
                stackTrace, cause = stackTraceFilter.javaStackTraceFilter(region[3])
                code = codeFilter.javaCodeFilter(region[3])
                for st in stackTrace:
                    st[0] = st[0] + region[0] + len(region[2])
                    st[1] = st[1] + region[0] + len(region[2])
                for ca in cause:
                    ca[0] = ca[0] + region[0] + len(region[2])
                    ca[1] = ca[1] + region[0] + len(region[2])
                for co in code:
                    co[0] = co[0] + region[0] + len(region[2])
                    co[1] = co[1] + region[0] + len(region[2])
                    # print(co)
                    # print(text[co[0]: co[1]])
                    # print(text[co[0]: co[1]] == co[3])
                nonLanguage.extend(stackTrace)
                nonLanguage.extend(cause)
                nonLanguage.extend(code)
            # 处理显式标明的代码区之前的情况
            region = explicitCodeRegion[0]
            newText = s[: region[0]]  # 位标偏移量为0
            stackTrace, cause = stackTraceFilter.javaStackTraceFilter(newText)
            code = codeFilter.javaCodeFilter(newText)
            nonLanguage.extend(stackTrace)
            nonLanguage.extend(cause)
            nonLanguage.extend(code)
            # 处理显式标明的代码区之间的情况
            for i in range(0, len(explicitCodeRegion)):
                region = explicitCodeRegion[i]
                if i == len(explicitCodeRegion) - 1:
                    newText = s[region[1]:]
                else:
                    newText = s[region[1]: explicitCodeRegion[i + 1][0]]
                    # 位标偏移量为region[1]
                stackTrace, cause = stackTraceFilter.javaStackTraceFilter(newText)
                code = codeFilter.javaCodeFilter(newText)
                for st in stackTrace:
                    st[0] = st[0] + region[1]
                    st[1] = st[1] + region[1]
                for ca in cause:
                    ca[0] = ca[0] + region[1]
                    ca[1] = ca[1] + region[1]
                for co in code:
                    co[0] = co[0] + region[1]
                    co[1] = co[1] + region[1]
                nonLanguage.extend(stackTrace)
                nonLanguage.extend(cause)
                nonLanguage.extend(code)
    nonLanguageFinal = []
    for n in nonLanguage:  # 由于url会被误认为singlecomment，需要进行排除
        if n[2] == 'singlecomment':
            valid = True
            for m in nonLanguage:
                if m[2] == 'url' and m[0] < n[0] < m[1]:
                    valid = False
                    break
            if valid:
                nonLanguageFinal.append(n)
        else:
            nonLanguageFinal.append(n)
    return nonLanguageFinal


def tokenize(s, level):
    """
    Tokenize a sentence or paragraph into words
    :param s: string
    :param level: string, {sentence, paragraph},indicate whether the input is a sentence or a paragraph
    :return: wordsLst: list, if the input is a sentence, it's a one-dimensional array, while if the input is a
               paragraph, it's a two-dimensional array.
    """
    pattern = config.RePattern.TOKENIZPATTERN
    wordsLst = []
    if len(s) == 0:
        return wordsLst
    if level == 'sentence':  # 输入为句子
        wordsLst = [w.lower() for w in regexp_tokenize(s, pattern)]
    elif level == 'paragraph':
        sentLst = sent_tokenize(s)
        for sen in sentLst:
            wordsLst.append([w.lower() for w in regexp_tokenize(sen, pattern)])
        # print(words)
    # print(wordsLst)
    return wordsLst


@unique
class PartOfSpeech(Enum):
    J = wordnet.ADJ
    V = wordnet.VERB
    N = wordnet.NOUN
    R = wordnet.ADV


def reduction(wordsLst):
    """
    Restoring the part of speech of a word in a sentence
    :param wordsLst: list, a list of words
    :return: reducedWords: list
    """
    wordTags = pos_tag(wordsLst)  # 获取单词的词性
    wnl = WordNetLemmatizer()
    reducedWords = []
    for tag in wordTags:
        if tag[1][0] in PartOfSpeech.__members__:
            newTag = PartOfSpeech[tag[1][0]].value
            reducedWords.append(wnl.lemmatize(tag[0], pos=newTag))  # 词性还原
        else:
            reducedWords.append(tag[0])
    return reducedWords


def removeStopwords(wordsLst):
    """
    Remove stop words from sentences
    :param wordsLst: list, a list of words
    :return: newWordsLst: list
    """
    stopwords = config.RootDir.STOPWORDROOT + 'en_stopwords.txt'
    try:
        with open(stopwords, "r", encoding='utf-8') as f:
            stopwordsLst = f.read().splitlines()
        f.close()
    except IOError:
        print('Cannot find stopwords')
    newWordsLst = [w for w in wordsLst if w not in stopwordsLst and not isNumber(w)]  # 去除停用词和数字
    # print(newWordsLst)
    return newWordsLst


def isNumber(s):
    """
    Judge whether the string is a number
    :param s: string
    :return: bool
    """
    if s.count(".") == 1:  # 小数的判断
        if s[0] == "-":
            s = s[1:]
        if s[0] == ".":
            return False
        s = s.replace(".", "")
        if s.isdigit():
            return True
        else:
            return False
    elif s.count(".") == 0:  # 整数的判断
        if s[0] == "-":
            s = s[1:]
        if s.isdigit():
            return True
        else:
            return False
    else:
        return False


def preprocess(issueDf, encoder):
    """
    public
    :param encoder:
    :param issueDf:
    :return:
    """
    defaultLst = ['ZOOKEEPER-1517', 'ZOOKEEPER-1929', 'ZOOKEEPER-2481', 'ZOOKEEPER-2483', 'ZOOKEEPER-2484',
                  'ZOOKEEPER-2485', 'ZOOKEEPER-2486', 'ZOOKEEPER-2493', 'ZOOKEEPER-2499', 'ZOOKEEPER-2502',
                  'ZOOKEEPER-2529', 'ZOOKEEPER-2577', 'ZOOKEEPER-2610', 'ZOOKEEPER-2679', ]
    textEncoder = TextEncoder('fasttext')
    for index, issue in issueDf.iterrows():
        # print(index)
        # if issue['issue_key'] in defaultLst:
        #     issueDf.at[index, 'summary'] = [issue['summary'], [], '', [], []]
        #     continue
        try:
            # textLst = [issue['summary'], issue['description']]
            summary = cleanStr(issue['summary'])
            summary.append(removeStopwords(reduction(tokenize(summary[2], 'sentence'))))
            # summary.append(textEncoder.getSentenceVector(summary[3]))
            issueDf.at[index, 'summary'] = summary  # 从字符串转化为了结果列表
            # if issue['issue_key'] in defaultLst:
            #     issueDf.at[index, 'description'] = [issue['description'], [], '', [], []]
            # else:
            #     description = cleanStr(issue['description'])
            #     description.append(
            #         [removeStopwords(reduction(wL)) for wL in tokenize(description[2], 'paragraph')])
            #     vecLst = [textEncoder.getSentenceVector(s) for s in description[3]]
            #     description.append(vecLst)
            #     issueDf.at[index, 'description'] = description  # 从字符串转化为了结果列表
        except Exception as e:
            print(e)
            print(issue)
    print('preprocess done')
    return issueDf


def exportToFile(filename, s):
    filepath = config.RootDir.EXPORTROOT + filename
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(s)
        f.write(config.DefaultString.NEWLINE)
    f.close()
    return True


# issueDB = pymysql.connect(host=config.MySQLConfig.HOST, user=config.MySQLConfig.USER,
#                           password=config.MySQLConfig.PASSWORD,
#                           database="issue", autocommit=config.MySQLConfig.AUTOCOMMIT)
# issueCursor = issueDB.cursor()
# # issueDataFrame = getIssueByProject(issueCursor, 'zookeeper')
# # print(issueDataFrame)
# issueDataFrame = getIssueByKey(issueCursor,
#                                "zookeeper-572")  # 测试数据包括2049,1014,3288,3634,4334,3914,3882,4238,4288,4299, 1517
# issueDataFrame = preprocess(issueDataFrame, 'fasttext')
# print(issueDataFrame['summary'][0])
