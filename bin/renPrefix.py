#!/usr/bin/env python

"""
Rename a the prefix
- strip filename prefix to the last <seperator> and then add the <new prefix>

Usage: RENPREFIX <file spec> <seperator> <new prefix>

"""

import os
import sys
import glob

def showUsage():
    print __doc__

#-------------------------------------------------------------------------------
def main(argv):
    
    try:
        import getopt
        optList, optRemainder = getopt.gnu_getopt(argv[1:], '', [])
    except getopt.GetoptError, e:
        print "! Syntax error: ",e
        showUsage()
        return -1
        
    if len(optRemainder) < 3 :
        showUsage()
        return -1

    fileSpec = optRemainder[0]
    seperator = optRemainder[1]
    newPrefix = optRemainder[2];
    
    fileList = glob.glob(fileSpec);
    if not fileList:
        print '! No files found?'
        showUsage()
        return -2
        
    print 'RenPrefix '+seperator+' '+newPrefix+' '+fileSpec
    print
        
    for file in fileList:
        path,name = os.path.split(file)
        
        i = name.rfind(seperator, )
        if i > 0:
            name = newPrefix + name[i:]
        
            newFile =  os.path.join(path, name)
            
            print file+' -> '+newFile
            
            os.rename(file, newFile)
        else:
            print 'Skip: '+file
    
        
    return 0
    
    
#-------------------------------------------------------------------------------
if __name__ == '__main__' or __name__ == sys.argv[0]:

    sys.exit(main(sys.argv[0:]))

#-------------------------------------------------------------------------------
# end

