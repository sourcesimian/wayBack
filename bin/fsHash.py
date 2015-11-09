#! /usr/bin/env python

"""\

Usage: fsHash <command> <path>

Options: --db <databaseFile>

"""

dbFilename = '.fsHash.sqlite'

import os
import sys
import sqlite3
import hashlib
import time


#-------------------------------------------------------------------------------
class RunTimer():
    def __init__(self):
        self._start = time.clock()

    def __del__(self):
        print('* Elapsed: %s' % self.elapsedAsString())

    def elapsed(self):
        return time.clock() - self._start

    def elapsedAsString(self):
        return '%f' % self.elapsed()

#-------------------------------------------------------------------------------
class FsHashException(Exception):
    def __init__(self, msg):
        self._msg = msg

    def __str__(self):
        return self._msg
 
#-------------------------------------------------------------------------------
class FileInfo:
    def __init__(self):
        self._filePath = None
        self._path = None
        self._name = None
        self._size = None
        self._mtime = None
        self._md5 = None

    #---------------------------------------------------------------------------
    def fromFile(self, filePath):
        if not os.path.isfile(filePath):
            raise FsHashException('Not found: "%s"' % filePath)
        self._filePath = filePath

        self._path, self._name = os.path.split(filePath)

        self._size = os.path.getsize(self._filePath)
        self._mtime = os.path.getmtime(self._filePath)
        return self

    #---------------------------------------------------------------------------
    def fromDB(self, path, filename, mtime, size, md5):
        self._path = path
        self._name = filename
        self._mtime = mtime
        self._size = size
        self._md5 = md5
        return self

    #---------------------------------------------------------------------------
    def getFullPath(self):
        return os.path.join(self._path, self._name)

    #---------------------------------------------------------------------------
    def getPath(self):
        return self._path

    #---------------------------------------------------------------------------
    def getName(self):
        return self._name

    #---------------------------------------------------------------------------
    def getSize(self):
        return self._size

    def getMTime(self):
    #---------------------------------------------------------------------------
        return self._mtime

    #---------------------------------------------------------------------------
    def getMD5(self):
        if self._md5:
            return self._md5
        f = open(self._filePath, 'rb')
        m = hashlib.md5()

        while 1:
            data = f.read(4096)
            if not data:
                break
            m.update(data)
   
        f.close()
        self._md5 = m.hexdigest()
        return self._md5

    #---------------------------------------------------------------------------
    def __eq__(self, other):
        if self.getFullPath() != other.getFullPath():
            return False
        
        if self.getSize() != other.getSize():
            return False

        if self.getMTime() != other.getMTime():
            return False

        return True


#-------------------------------------------------------------------------------
class HashDB:
    def __init__(self, databaseFile):  # throw sqlite3.OperationalError
        self._con = sqlite3.connect(databaseFile)
        cur = self._con.cursor()
        self._setupTables()
        self._utime = int(time.time())
        self._addCount = 0
        self._updateCount = 0
        self._logFile = databaseFile+'.log'
        open(self._logFile, 'wt').write('Time: %s\n' % (time.ctime()))
                  
    #---------------------------------------------------------------------------
    def _log(self, msg):
        open(self._logFile, 'at').write(msg + '\n')

    #---------------------------------------------------------------------------
    def _setupTables(self):
        cur = self._con.cursor()

        if not self._hasTable('files'):
            cur.execute("create table files (id  INTEGER PRIMARY KEY AUTOINCREMENT, utime INTEGER, path TEXT, name TEXT, mtime INTEGER, size INTEGER, md5 TEXT)")

#            cur.execute("insert into files values ('path', 'name', 12345678, 5, 'hash')")
#            cur.execute("insert into files values ('path1', 'name', 123456780, 6, 'hash1')")

        self._con.commit()
        cur.close()

    #---------------------------------------------------------------------------
    def _hasTable(self, table):
        cur = self._con.cursor()
        t = (table,)
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (t))
        cur.close()
        return True if len([x for x in cur]) > 0 else False

    #---------------------------------------------------------------------------
    def updateFile(self, fileInfo):
        cur = self._con.cursor()

        t = (fileInfo.getPath(),fileInfo.getName(),)
        try:
            cur.execute("select * from files where path=? AND name=?", t)
        except sqlite3.ProgrammingError, e:
            self._log('Error: SELECT '+str(t)+' : '+str(e))
            return
        except:
            self._log('Error: SELECT ' + str(t))
            return

        results = []
        for t in cur:
            results.append(t)
        cur.close()

        if not results:
            self.addFile(fileInfo)
            return True

        if len(results) == 1:
            oldFileInfo = FileInfo().fromDB(*(results[0][2:]))

            if oldFileInfo == fileInfo:
                return False

            id = results[0][0]
            self._updateRecordById(id, fileInfo)
            self._updateCount += 1
            return True


        self._log('Error: duplicate files found in DB '+ str(t))
        return False

    #---------------------------------------------------------------------------
    def _updateRecordById(self, id, fileInfo):
        cur = self._con.cursor()

        t = (self._utime, fileInfo.getPath(), fileInfo.getName(), fileInfo.getMTime(), fileInfo.getSize(), fileInfo.getMD5(), id)
        try:
            cur.execute("UPDATE files SET utime=?, path=?, name=?, mtime=?, size=?, md5=? WHERE id=?", t)
        except:
            self._log('Error: UPDATE ' + str(t))
            return

        self._con.commit()
        cur.close()


    #---------------------------------------------------------------------------
    def addFile(self, fileInfo):
        cur = self._con.cursor()

        t = None
        try:
            t = (self._utime, fileInfo.getPath(), fileInfo.getName(), fileInfo.getMTime(), fileInfo.getSize(), fileInfo.getMD5())
        except IOError, e:
            self._log('Error: IOError ' + str(e))
            return

        try:
            cur.execute("insert into files(utime, path, name, mtime, size, md5) values (?, ?, ?, ?, ?, ?)", t)
        except:
            self._log('Error: INSERT ' + str(t))
            return

        self._con.commit()
        cur.close()

        self._addCount += 1

        #self._log('Info: Adding ' + str(t))


    #---------------------------------------------------------------------------
    def clearFiles(self):
        cur = self._con.cursor()

        cur.execute("DELETE from files")
        
        self._con.commit()
        cur.close()


    #---------------------------------------------------------------------------
    def __del__(self):
        self._log('Info: addCount: %d' % self._addCount)
        self._log('Info: updateCount: %d' % self._updateCount)

        print('* addCount: %d' % self._addCount)
        print('* updateCount: %d' % self._updateCount)
        
#-------------------------------------------------------------------------------
def sizeAsString(size):

    limit = 1

    for unit in ('', 'k', 'M', 'G', 'T', 'P'):
        if size < (limit * 1024):
            return '%d%s' % (int(size/limit), unit) 
        limit *= 1024

    return 'NaN'

#-------------------------------------------------------------------------------
def update(hashDB, basePath):
#    hashDB.clearFiles()

    totalSize = 0

    for root, dirs, files in os.walk(basePath, topdown=False):

        for name in files:
            if name.startswith(dbFilename): continue

            fullPath = os.path.join(root, name)
            try:            
                fileInfo = FileInfo().fromFile(fullPath)
            except FsHashException, e:
                print e
                continue
            res = hashDB.updateFile(fileInfo)
#            hashDB.addFile(fileInfo)
            totalSize += fileInfo.getSize()
            if res: print ('[%s] %s' % (sizeAsString(totalSize), fullPath))

        for name in dirs:
            pass
       
        

#-------------------------------------------------------------------------------
def main(argv):

    try:
        import getopt
        optList, optRemainder = getopt.gnu_getopt(argv[1:], 'h', ['help', 'db='])
    except getopt.GetoptError, e:
        print __doc__
        print "! Syntax error: ",e
        return -1

    prompt = False
    basePath = None
    databaseFile = None

    for n,v in optList:
        if n in ('--help','-h'):
            print __doc__
            return 0

        if n in ('--db',):
            databaseFile = v

    if len (optRemainder) != 2:
        print __doc__
        return -1

    userCommand = optRemainder[0]
    basePath = optRemainder[1]

    if not os.path.isdir(basePath):
        print __doc__
        print ("! Invalid path: '%s'" % basePath)
        return -1

    if not databaseFile:
        databaseFile = os.path.join(basePath, dbFilename)
        
    timer = RunTimer()

    hashDB = None
    hashDB = HashDB(databaseFile)

    if userCommand.lower() == 'update':
        return update(hashDB, basePath)

    return 0

    hashDB.getByName('name')

    f = FileInfo(databaseFile)
    print f.getPath()
    print f.getName()
    print f.getSize()
    print f.getTime()
    print f.getMD5()

    return 0

#-------------------------------------------------------------------------------
if __name__ == '__main__' or __name__ == sys.argv[0]:

    sys.exit(main(sys.argv))

#-------------------------------------------------------------------------------
# end
