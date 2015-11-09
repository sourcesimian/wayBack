#! /usr/bin/env python

"""
Sort FAT

A simple tool to alphapetically sort your FAT entries, typically
for use with dumb MP3 players that don't sort by file name.

USAGE: sortFAT.py [<basePath>]

If you don't specify a <basePath> it will run at the locaion of this script
(but will prompt you first)

It sorts the FAT recursively from the location of this script.
It does this by moving the contents of each direcrory
alphabetically into a temp directory, then remove the original
and rename the temp to that of the original. Simples !!!
"""


import os
import sys
import shutil


#-------------------------------------------------------------------------------
def makeDir(path):
#    print ' + %s' % path
    os.makedirs(path)

#-------------------------------------------------------------------------------
def delDir(path):
#    print ' - %s' % (path)
    os.rmdir(path)

#-------------------------------------------------------------------------------
def moveFile(src, dst):
#    print ' : %s -> %s' % (src, dst)
    shutil.move(src, dst)

#-------------------------------------------------------------------------------
def stringCompareNoCase(a, b):
    return cmp(a.lower(), b.lower())

#-------------------------------------------------------------------------------
def sorttree(dirname):
     if os.path.exists(dirname):
        for root,dirs,files in os.walk(dirname, topdown=False):
            if root == dirname: continue
            print ' * %s' % root

            base,dirName = os.path.split(root)
            tmpName = dirName + '.sortFATtmp'
            srcDir = os.path.join(base, dirName)
            tmpDir = os.path.join(base, tmpName)

            moveFile(srcDir, tmpDir)

            makeDir(srcDir)

            if dirs:
                dirList = dirs
                dirList.sort(stringCompareNoCase)
                for dir in dirList:
                    src = os.path.join(tmpDir, dir)
                    dst = os.path.join(srcDir, dir)
                    moveFile(src,dst)

            if files:
                fileList = files
                fileList.sort(stringCompareNoCase)

                for file in fileList:
                    src = os.path.join(tmpDir, file)
                    dst = os.path.join(srcDir, file)
                    moveFile(src,dst)

            delDir(tmpDir)



#-------------------------------------------------------------------------------
def main(argv):

    try:
        import getopt
        optList, optRemainder = getopt.gnu_getopt(argv[1:], 'h', ['help'])
    except getopt.GetoptError, e:
        print __doc__
        print "! Syntax error: ",e
        return -1

    prompt = False
    basePath = None

    for n,v in optList:
        if n in ('--help','-h'):
            print __doc__
            return 0

    if len(optRemainder) > 0:
        basePath = optRemainder[0]
        if not os.path.isdir(basePath):
            print '! baseDir is not valid'
            return -1
    else:
        basePath = os.path.split(__file__)[0]
        try:
            raw_input('SortFAT will alphabetically sort the filesystem in:\n -> "%s"\nPress ENTER to continue or ^C to quit.' % basePath)
        except KeyboardInterrupt:
            print '\n! User Interrupted'
            return 1
        prompt = True

    print 'FAT sorting the tree in: %s' % basePath

    sorttree(basePath)

    if prompt:
        raw_input('\SortFAT has completed its work\nPress ENTER to exit.')
    else:
        print 'Done'
    return 0

#-------------------------------------------------------------------------------
if __name__ == '__main__' or __name__ == sys.argv[0]:

    sys.exit(main(sys.argv))

#-------------------------------------------------------------------------------
# end
