#!/usr/bin/env python37
# -*- coding: utf-8 -*-
# @Time    : 2022/11/14 16:37
# @Author  : jsx
# @File    : stackTraceFilter.py
# @Description : Find JAVA stacktrace and cause in the string. Improved based on infozilla.
import re

import config


def findJavaExceptions(s):
    """
    Exception is the base of stacktrace and cause. Find all JAVA exceptions in the string based on the regular expression
    :param s: string
    :return: exceptionLst: list, list of exception regions, each cause region contains 4 attributes, namely start index,
               end index, tag, exception
               example: [[692, 717, 'exception', 'diskjava.io.EOFException:'],
                         [2788, 2825, 'exception', 'abnormallyjava.lang.RuntimeException:']]
    """
    exceptionLst = []
    pattern = config.StackTracePattern.JAVAEXCEPTION
    for match in re.finditer(pattern, s, flags=re.DOTALL | re.MULTILINE):
        if len(exceptionLst) > 0:
            gapStr = s[exceptionLst[-1][0]: match.start()]
            if gapStr.count('at') >= 10:  # exception按at分行，相距小于10行的exception视为属于同一个exception
                exceptionLst.append([match.start(), match.end(), 'exception', s[match.start(): match.end()]])
        else:
            exceptionLst.append([match.start(), match.end(), 'exception', s[match.start(): match.end()]])
    return exceptionLst


def findJavaStackTrace(s):
    """
    Find all JAVA stacktrace and cause in the string based on the regular expression
    :param s: string
    :return: stackTraceLst: list, list of stacktrace regions, each stacktrace region contains 4 attributes, namely
               start index, end index, tag, stacktrace
               example: [[0, 1676, 'stacktrace', 'abnormallyjava.lang.RuntimeException: Unable to run quorum server
                          ...
                          at org.apache.zookeeper.server.quorum.QuorumPeer.loadDataBase(QuorumPeer.java:1146)']]
             causeLst: list, list of cause regions, each cause region contains 4 attributes, namely start index,
               end index, tag, cause
               example: [[511, 1676, 'cause', 'Caused by: java.io.EOFException: null
                          ...
                          at org.apache.zookeeper.server.quorum.QuorumPeer.loadDataBase(QuorumPeer.java:1146)']]
    """
    stackTraceLst = []
    causeLst = []
    pattern = config.StackTracePattern.JAVASTACKTRACE
    for match in re.finditer(pattern, s, flags=re.DOTALL | re.MULTILINE):
        stackTraceLst.append([match.start(), match.end(), 'stacktrace', s[match.start(): match.end()]])
    pattern = config.StackTracePattern.JAVACAUSE
    for match in re.finditer(pattern, s, flags=re.DOTALL | re.MULTILINE):
        causeLst.append([match.start(), match.end(), 'cause', s[match.start(): match.end()]])
    return stackTraceLst, causeLst


def javaStackTraceFilter(s):
    """
    Public. Find all JAVA stacktrace and cause in the string based on the regular expression
    :param s: string
    :return: stackTraceLst: list, list of stacktrace regions, each stacktrace region contains 4 attributes, namely
               start index, end index, tag, stacktrace
               example: [[692, 2208, 'stacktrace', 'diskjava.io.EOFException: null
                          ...
                          at org.apache.zookeeper.server.quorum.QuorumPeerMain.main(QuorumPeerMain.java:91)'],
                         [2788, 4464, 'stacktrace', 'abnormallyjava.lang.RuntimeException: Unable to run quorum server
                          ...
                          at org.apache.zookeeper.server.quorum.QuorumPeer.loadDataBase(QuorumPeer.java:1146)']]
             causeLst: list, list of cause regions, each cause region contains 4 attributes, namely start index,
               end index, tag, cause
               example: [[3299, 4464, 'cause', 'Caused by: java.io.EOFException: null
                          ...
                          at org.apache.zookeeper.server.quorum.QuorumPeer.loadDataBase(QuorumPeer.java:1146)']]
    """
    stackTraceLst = []
    causeLst = []
    exceptionLst = findJavaExceptions(s)
    if len(exceptionLst) > 0:
        for i in range(0, len(exceptionLst) - 1):
            region = s[exceptionLst[i][0]: exceptionLst[i + 1][0]]  # 按exception的位置分割string
            stackTraceTmp, causeTmp = findJavaStackTrace(region)
            # 在文本中的真实位置要加上region的偏移量
            for st in stackTraceTmp:
                st[0] = st[0] + exceptionLst[i][0]
                st[1] = st[1] + exceptionLst[i][0]
            for c in causeTmp:
                c[0] = c[0] + exceptionLst[i][0]
                c[1] = c[1] + exceptionLst[i][0]
            stackTraceLst.extend(stackTraceTmp)
            causeLst.extend(causeTmp)
            if len(stackTraceTmp) == 0 and len(causeTmp) == 0:
                stackTraceLst.append(exceptionLst[i])
        region = s[exceptionLst[-1][0]:]
        stackTraceTmp, causeTmp = findJavaStackTrace(region)
        for st in stackTraceTmp:
            st[0] = st[0] + exceptionLst[-1][0]
            st[1] = st[1] + exceptionLst[-1][0]
        for c in causeTmp:
            c[0] = c[0] + exceptionLst[-1][0]
            c[1] = c[1] + exceptionLst[-1][0]
        stackTraceLst.extend(stackTraceTmp)
        causeLst.extend(causeTmp)
        if len(stackTraceTmp) == 0 and len(causeTmp) == 0:
            stackTraceLst.append(exceptionLst[-1])
    return stackTraceLst, causeLst


# s = "2022-10-19 02:03:07,876 [myid:3] - INFO  [main:o.a.z.s.q.QuorumPeer@2549] - QuorumPeer communication is not secured! (SASL auth disabled)2022-10-19 02:03:07,876 [myid:3] - INFO  [main:o.a.z.s.q.QuorumPeer@2574] - quorum.cnxn.threads.size set to 202022-10-19 02:03:07,877 [myid:3] - INFO  [main:o.a.z.s.p.FileSnap@85] - Reading snapshot /home/edge/middleware/zookeeper/data/data/version-2/snapshot.1409ce9ac72022-10-19 02:03:07,883 [myid:3] - INFO  [main:o.a.z.s.DataTree@1705] - The digest in the snapshot has digest version of 2, with zxid as 0x1409ce9acc, and digest value as 816041257652022-10-19 02:03:11,662 [myid:3] - ERROR [main:o.a.z.s.q.QuorumPeer@1200] - Unable to load database on diskjava.io.EOFException: null    at java.base/java.io.DataInputStream.readInt(Unknown Source)    at org.apache.jute.BinaryInputArchive.readInt(BinaryInputArchive.java:96)    at org.apache.zookeeper.server.persistence.FileHeader.deserialize(FileHeader.java:67)    at org.apache.zookeeper.server.persistence.FileTxnLog$FileTxnIterator.inStreamCreated(FileTxnLog.java:707)    at org.apache.zookeeper.server.persistence.FileTxnLog$FileTxnIterator.createInputArchive(FileTxnLog.java:725)    at org.apache.zookeeper.server.persistence.FileTxnLog$FileTxnIterator.goToNextLog(FileTxnLog.java:693)    at org.apache.zookeeper.server.persistence.FileTxnLog$FileTxnIterator.next(FileTxnLog.java:774)    at org.apache.zookeeper.server.persistence.FileTxnSnapLog.fastForwardFromEdits(FileTxnSnapLog.java:361)    at org.apache.zookeeper.server.persistence.FileTxnSnapLog.lambda$restore$0(FileTxnSnapLog.java:267)    at org.apache.zookeeper.server.persistence.FileTxnSnapLog.restore(FileTxnSnapLog.java:312)    at org.apache.zookeeper.server.ZKDatabase.loadDataBase(ZKDatabase.java:285)    at org.apache.zookeeper.server.quorum.QuorumPeer.loadDataBase(QuorumPeer.java:1146)    at org.apache.zookeeper.server.quorum.QuorumPeer.start(QuorumPeer.java:1132)    at org.apache.zookeeper.server.quorum.QuorumPeerMain.runFromConfig(QuorumPeerMain.java:229)    at org.apache.zookeeper.server.quorum.QuorumPeerMain.initializeAndRun(QuorumPeerMain.java:137)    at org.apache.zookeeper.server.quorum.QuorumPeerMain.main(QuorumPeerMain.java:91)2022-10-19 02:03:11,663 [myid:3] - INFO  [main:o.a.z.m.p.PrometheusMetricsProvider@570] - Shutdown executor service with timeout 10002022-10-19 02:03:11,739 [myid:3] - INFO  [main:o.e.j.s.AbstractConnector@383] - Stopped ServerConnector@5b03b9fe{HTTP/1.1, (http/1.1)}{zookeeper-default-2.zookeeper.default.svc.cluster.local:8080}2022-10-19 02:03:11,742 [myid:3] - INFO  [main:o.e.j.s.h.ContextHandler@1159] - Stopped o.e.j.s.ServletContextHandler@17bffc17{/,null,STOPPED}2022-10-19 02:03:11,746 [myid:3] - ERROR [main:o.a.z.s.q.QuorumPeerMain@114] - Unexpected exception, exiting abnormallyjava.lang.RuntimeException: Unable to run quorum server     at org.apache.zookeeper.server.quorum.QuorumPeer.loadDataBase(QuorumPeer.java:1201)    at org.apache.zookeeper.server.quorum.QuorumPeer.start(QuorumPeer.java:1132)    at org.apache.zookeeper.server.quorum.QuorumPeerMain.runFromConfig(QuorumPeerMain.java:229)    at org.apache.zookeeper.server.quorum.QuorumPeerMain.initializeAndRun(QuorumPeerMain.java:137)    at org.apache.zookeeper.server.quorum.QuorumPeerMain.main(QuorumPeerMain.java:91)Caused by: java.io.EOFException: null    at java.base/java.io.DataInputStream.readInt(Unknown Source)    at org.apache.jute.BinaryInputArchive.readInt(BinaryInputArchive.java:96)    at org.apache.zookeeper.server.persistence.FileHeader.deserialize(FileHeader.java:67)    at org.apache.zookeeper.server.persistence.FileTxnLog$FileTxnIterator.inStreamCreated(FileTxnLog.java:707)    at org.apache.zookeeper.server.persistence.FileTxnLog$FileTxnIterator.createInputArchive(FileTxnLog.java:725)    at org.apache.zookeeper.server.persistence.FileTxnLog$FileTxnIterator.goToNextLog(FileTxnLog.java:693)    at org.apache.zookeeper.server.persistence.FileTxnLog$FileTxnIterator.next(FileTxnLog.java:774)    at org.apache.zookeeper.server.persistence.FileTxnSnapLog.fastForwardFromEdits(FileTxnSnapLog.java:361)    at org.apache.zookeeper.server.persistence.FileTxnSnapLog.lambda$restore$0(FileTxnSnapLog.java:267)    at org.apache.zookeeper.server.persistence.FileTxnSnapLog.restore(FileTxnSnapLog.java:312)    at org.apache.zookeeper.server.ZKDatabase.loadDataBase(ZKDatabase.java:285)    at org.apache.zookeeper.server.quorum.QuorumPeer.loadDataBase(QuorumPeer.java:1146)    ... 4 common frames omitted2022-10-19 02:03:11,747 [myid:3] - INFO  [main:o.a.z.a.ZKAuditProvider@42] - ZooKeeper audit is disabled.2022-10-19 02:03:11,749 [myid:3] - ERROR [main:o.a.z.u.ServiceUtils@48] - Exiting JVM with code 1 "
# stackLst, cLst = javaStackTraceFilter(s)
# for line in stackLst:
#     print(line)
#     print(s[line[0]: line[1]])
#     print(s[line[0]: line[1]] == line[3])
# print()
# for line in cLst:
#     print(line)
#     print(s[line[0]: line[1]])
#     print(s[line[0]: line[1]] == line[3])
