class MySQLConfig(object):
    HOST = 'localhost'
    USER = 'root'
    PASSWORD = '123456'
    AUTOCOMMIT = True


class SQLExecutor(object):
    CREATETABLE = "CREATE TABLE IF NOT EXISTS "
    INSERT = "INSERT INTO "
    SELECTALL = "SELECT * FROM "


class TableConfig(object):
    ID = 'id'
    TIME = 'time'
    SPEAKER = 'speaker'
    TEXT = 'text'
    REPLY = 'reply'
    DESSTR = ID + ' INT NOT NULL,' + \
             SPEAKER + ' VARCHAR(100) NOT NULL,' + \
             TIME + ' DATETIME NOT NULL,' + \
             TEXT + ' TEXT NOT NULL,' + \
             REPLY + ' TEXT NOT NULL,' + \
             'PRIMARY KEY(' + ID + ')'


class RePattern(object):
    TIMEPATTERN = '\[\d{4}-\d{2}-\d{2}\s+([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]]'
    SPEAKERPATTERN = '[^\[]\<{1}([a-zA-Z0-9\-\~\_\.]+)>[^]]'
    COLONReplyPATTREN = '(([a-zA-Z0-9])+):'
    ATREPLYPATTERN = '@(([a-zA-Z0-9])+)'
    URLPATTERN = '(?P<url>https?://[^\s]+)'
    NOFORMATREGION = '(\{noformat\})([\s\S]*?)?(\{noformat\})'
    CODEREGION = '(\{code(.*?)\})([\s\S]*?)?(\{code(.*?)\})'
    COLOREDREGION = '(\{color(.*?)\})([\s\S]*?)?(\{color(.*?)\})'
    NOFORMATTAG = '\{noformat\}'
    CODETAG = '\{code(.*?)\}'
    COLOREDTAG = '\{color(.*?)\}'
    TOKENIZPATTERN = r'''(?x)    # set flag to allow verbose regexps
            (?:[a-zA-Z]\.)+       # abbreviations, e.g. U.S.A.   
           |\$?\d+(?:\.\d+)*%?  # currency and percentages, e.g. $12.40, 82%
           |\w+(?:[-'.]\w+)*   # words with optional internal hyphens\
           |\.\.\.            # ellipsis
           |(?:[.,;"?():-_`])  # these are separate tokens; includes ], [
         '''


class RootDir(object):
    DATAROOT = 'data/raw/'
    STOPWORDROOT = 'data/stopwords/'
    EXPORTROOT = './'


class DialogRef(object):
    REF = ['[<-LINK->]', '[<-CODE->]', '[<-ISSUE->]']


class ModelPath(object):
    FASTTEXTMODELEN300D = 'D:\models\cc.en.300.bin\cc.en.300.bin'


class DisentangleInit(object):
    TOPRANK = 2
    MAXTIMEINTERVAL = 343
    MAXDISTANCE = 10
    THERHOLD = 0.8
    POLYINTERVAL = 120


class DefaultString(object):
    SEPARATOR = '--------------------------------------------------\n'
    NEWLINE = '\n'


class ProjectVersion(object):
    ZOOKEEPER = {'3.0.0': '2008-10-27',
                 '3.0.1': '2008-12-04',
                 '3.1.0': '2009-02-13',
                 '3.1.1': '2009-03-27',
                 '3.1.2': '2009-12-14',
                 '3.2.0': '2009-07-08',
                 '3.2.1': '2009-09-04',
                 '3.2.2': '2009-12-14',
                 '3.3.0': '2010-03-25',
                 '3.3.1': '2010-05-11',
                 '3.3.2': '2010-11-11',
                 '3.3.3': '2011-02-27',
                 '3.3.4': '2011-11-26',
                 '3.3.5': '2012-03-20',
                 '3.3.6': '2012-08-02',
                 '3.4.0': '2011-11-22',
                 '3.4.1': '2011-12-16',
                 '3.4.2': '2011-12-29',
                 '3.4.3': '2012-02-13',
                 '3.4.4': '2012-09-23',
                 '3.4.5': '2012-11-18',
                 '3.4.6': '2014-03-10',
                 '3.4.8': '2016-02-20',
                 '3.4.9': '2016-09-03',
                 '3.4.10': '2017-03-30',
                 '3.4.11': '2017-09-09',
                 '3.4.12': '2018-05-01',
                 '3.4.13': '2018-07-15',
                 '3.4.14': '2019-04-02',
                 '3.5.0': '2014-08-06',
                 '3.5.1': '2015-08-31',
                 '3.5.2': '2016-07-20',
                 '3.5.3': '2017-04-17',
                 '3.5.4': '2018-05-17',
                 '3.5.5': '2019-05-20',
                 '3.5.6': '2019-10-19',
                 '3.5.7': '2020-02-14',
                 '3.5.8': '2020-05-11',
                 '3.5.9': '2021-01-15',
                 '3.5.10': '2022-06-04',
                 '3.6.0': '2020-03-04',
                 '3.6.1': '2020-04-30',
                 '3.6.2': '2020-09-09',
                 '3.6.3': '2021-04-13',
                 '3.7.0': '2021-03-27',
                 '3.7.1': '2022-05-12',
                 '3.8.0': '2022-03-07'}


class CodePattern(object):
    JAVACODEPATTERN = {'import': r'(?m)^\s*import.*;$',
                       'package': r'(?m)^package.*;$',
                       'singlecomment': r'(?m)\s*\/\/.*?[\n\r]',
                       'multicomment': r'(?m)(?s)\s*(\/\*).*?(\*\/)',
                       'class': r'(?m)^.*?class.*?([\n\r])?\{',
                       'assignment': r'(?m)^.*=.*;$',
                       'ifstatement': r'(?m)^.*?if\s*\(.*?\)\s*\{',
                       'elsestatement': r'(?m)^.*?else\s*\{',
                       'functiondef': r'(?m)^.*?([a-zA-Z_][a-zA-Z0-9_])+\s*\(.*?\)\s*?\{',
                       'functionall': r'(?m)^.*\(.*?\).*?;$'}
    JAVACODEPATTERNOPTIONS = {'import': '',
                              'package': '',
                              'singlecomment': '',
                              'multicomment': '',
                              'class': 'MATCH',
                              'assignment': '',
                              'ifstatement': 'MATCH',
                              'elsestatement': 'MATCH',
                              'functiondef': 'MATCH',
                              'functionall': ''}


class StackTracePattern(object):
    JAVAEXCEPTION = r'(([\w<>\$_]+\.)+[\w<>\$_]+((.\s*)Error|(.\s*)Exception){1}(\s|:))'
    JAVAREASON = r'((:?([\s\S]*?)?)(at\s+([\w<>\$_]+\.)+[\w<>\$_]+\s*\(.+?\.java(:)?(\d+)?\)))'
    JAVATRACE = r'(\s*?at\s+([\w<>\$_\s]+\.)+[\w<>\$_\s]+\s*(.+?\.java(:)?(\d+)?\))*)'
    JAVACAUSE = r'(Caused by:).*?(Exception|Error)(.*?)(\s+at.*?\(.*?:\d+\))+'
    JAVASTACKTRACE = JAVAEXCEPTION + JAVAREASON + '?' + JAVATRACE + '*'
    # JAVASTACKTRACE=(([\w<>\$_]+\.)+[\w<>\$_]+((.\s*)Error|(.\s*)Exception){1}(\s|:))((:?([\s\S]*?)?)(at\s+([\w<>\$_]+\.)+[\w<>\$_]+\s*\(.+?\.java(:)?(\d+)?\)))?(\s*?at\s+([\w<>\$_\s]+\.)+[\w<>\$_\s]+\s*(.+?\.java(:)?(\d+)?\))*)*
