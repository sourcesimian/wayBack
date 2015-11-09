#!/usr/bin/env python

"""
Usage: hash <fileName>
"""

import os
import sys

import glob
import hashlib

#-------------------------------------------------------------------------------
def main(argv):

    if len(argv) == 1:
        print __doc__
        return
    
    base,name = os.path.split(argv[1])

    hashs = getFileMD5Hashs(base, name, True)
    
    for h in hashs:
        print "%s : %s" % (h, hashs[h])
    
#-------------------------------------------------------------------------------
def error(msg):
    #sys.stderr.write('! %s\n' % (msg))
    print '! %s' % (msg)
    
#-------------------------------------------------------------------------------
def getFileMD5Hashs(baseDir, fileSpec, recursive=False):

    ret = {}
    
    files = glob.glob(os.path.join(baseDir, fileSpec))

    for file in files:
        filename = os.path.join(baseDir, file)
        
        if os.path.isdir(filename):
            tmp = getFileMD5Hashs(filename, fileSpec, recursive)
            for h in tmp:
                if h in ret:
                    error('dup: %s' % (ret[h]))
                    error('     %s' % (tmp[h]))
                    x,f1 = os.path.split(ret[h])
                    x,f2 = os.path.split(tmp[h])
                    if os.name == 'nt':
                        f1 = f1.lower()
                        f2 = f2.lower()
                    if f1 != f2:
                        error('     NAME CHANGE')

                        
                    
                ret[h] = tmp[h]

        fileHash = getFileMD5Hash(file)
        if not fileHash:
            continue
    
        ret[fileHash] = filename

    return ret

#-------------------------------------------------------------------------------
def getFileMD5Hash(filename):
    if not os.path.isfile(filename):
        return None
        
    try:
        f = open(filename, 'rb')
    except:
        error('can\'t open: %s' % (filename))
        return None
    m = hashlib.md5()

    while 1:
        data = f.read(4096)
        if not data:
            break
        m.update(data)
   
    f.close()
    return m.hexdigest()
    
#-------------------------------------------------------------------------------
if __name__ == '__main__' or __name__ == sys.argv[0]:

    sys.exit(main(sys.argv))

#-------------------------------------------------------------------------------
# end
