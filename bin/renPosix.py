#!/usr/bin/env python

"""\
Remove non POSIX compatable chars from file names

Usage: renPosix <path> [<file spec>]

Switches: -R  - recursive
          -s,--show  - show illegal file names
          --dryrun  - don't make any changes to disk
"""

import os
import sys
import shutil
import glob
import sre_constants

validChars = ''
validChars += r" !#$%&'()+,-."
validChars += r'0123456789'
validChars += r':;=@'
validChars += r'abcdefghijklmnopqrstuvwxyz'
validChars += r'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
validChars += r'[]^_{}~'

replaceChars = {}


def showUsage():
    print __doc__
    print "Valid chars:\n"+validChars
    print

#-------------------------------------------------------------------------------
def processDir(path, fileSpec, show=True, dryrun=True):
    global title
    title = False    
    
    def showTitle():
        global title        
        if not title:    
            print '\nIn: %s' % (path)
            title = True

    try:
        files = glob.glob(os.path.join(path, fileSpec))
    except sre_constants.error:
        sys.stderr.write("! Can't process: %s {%s}\n" % (path, fileSpec))
        return

    for file in files:
    
        dir = None
        oldName = None
        if os.path.isfile(file) or os.path.isdir(file):
            dir,oldName = os.path.split(file)
        else:
            continue

        if len(oldName) >= 255:
            s = os.path.splitext(oldName)
            oldName = s[0][:255-len(s[1])] + s[1]
            print " - Truncated to 255 chars"
        
        newName = ''
        changed = False
        
        if show:
            for ch in oldName:
                if not ch in validChars:
                    showTitle()
                    print '? ',oldName
                    break
        else:
            once = False        
            for ch in oldName:
                if not ch in validChars:
                    showTitle()
                    if not once:                
                        print '? ',oldName
                        once = True
                    changed = True
                    if ch in replaceChars:
#                        print "->",replaceChars[ch]
                        ch = replaceChars[ch]
                    else:
                        while True:                        
                            try:
                                inp = raw_input(' '* (3+oldName.find(ch))+ '^: ')
                            except:
                                sys.exit(1)
                                inp = ''
                                break
                            
                            for t in inp:
                                if not t in validChars:
                                    break
                            else:
                                break   
                        replaceChars[ch] = inp
                        #print inp
                        ch = inp
                        
                newName += ch

            if changed == True:
                print " -",newName
                try:
                    if not dryrun:
                        shutil.move(os.path.join(path, oldName), os.path.join(path, newName))
                    pass
                except:
                    print "   ! FAILED"+chr(7)


#-------------------------------------------------------------------------------
def main(argv):
    
    if len(argv) < 2 :
        showUsage()
        return -1
        
    try:
        import getopt
        optList, optRemainder = getopt.gnu_getopt(argv[1:], 'Rs', ['show', 'dryrun'])
    except getopt.GetoptError, e:
        print "! Syntax error: ",e
        showUsage()
        return -1

    recursive = False
    show = False
    dryrun = False
    for n,v in optList:
        if n == '--recursive' or n == '-R':
            recursive = True
        if n == '--show' or n == '-s':
            show = True
        if n == '--dryrun':
            dryrun = True
    
    fileSpec = '*'    
    if len(optRemainder) < 1:
        showUsage()
        return -1

    basePath = optRemainder[0]

    if len(optRemainder) >= 2:
        fileSpec = optRemainder[1]

    print "renPrefix: %s {%s}" % (basePath, fileSpec)    
    if recursive:
        processDir(basePath, fileSpec, show, dryrun)
        for root, dirs, files in os.walk(basePath, topdown=False):
            for dir in dirs:
                processDir(os.path.join(root, dir),  fileSpec, show, dryrun)
    else:
        processDir(basePath, fileSpec, show, dryrun)

    return 0

#-------------------------------------------------------------------------------
if __name__ == '__main__' or __name__ == sys.argv[0]:

    sys.exit(main(sys.argv[0:]))

#-------------------------------------------------------------------------------
# end

