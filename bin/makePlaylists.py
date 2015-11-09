#!/usr/bin/env python

"""\
MakePlaylists
- Recursively creates an '000.m3u' in each directory where music files are
  contained

Usage: MakePlaylists [baseDir]

Switches: --help, -h
          --listFile,-l <listFileName>   (default is 000.m3u)
          --cleanUp, -c    Search for list files and remove them
"""


import sys
import os

#------------------------------------------------------------------------------
def main(argv):

    
    baseDir = os.getcwd()
    listFileName = '000.m3u'
    musicFileExts = ['.mp3', '.mpc', '.wma', 'wav']
    cleanUp = False
    

    if len(argv) == 1:
        print __doc__
        return -1
    
    try:
        import getopt
        optList, optRemainder = getopt.gnu_getopt(argv[1:], 'hRl:c', ['help', 'recursive', 'listFile=', 'cleanUp'])
    except getopt.GetoptError, e:
        print __doc__
        print "! Syntax error: ",e
        return -1

    doRecursive = False
 
    for n,v in optList:
        if n == '--help' or n == '-h':
            print __doc__
            return 0
        if n == '--recursive' or n == '-R':
            doRecursive = True
        if n == '--listFile' or n == '-l':
            listFileName = v
        if n == '--cleanUp' or n == '-c':
            cleanUp = True

    if len(optRemainder) > 0:
        baseDir = optRemainder[0]
        if not os.path.isdir(baseDir):
            print '! baseDir is not valid'
            return -1

    
    def cleanUpPlaylists(base):
        print 'Removing all "%s" files from tree' % (listFileName)
        count = 0
        for root, dirs, files in os.walk(base, topdown=False):
            for file in files:
                if file == listFileName:
                    os.unlink(os.path.join(root, file))
                    count += 1
        print '- %d files removed' % (count)


    if cleanUp:
        return cleanUpPlaylists(baseDir)

    def genPlaylist(base):
        musicFiles = []

        for root, dirs, files in os.walk(base, topdown=False):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in musicFileExts:
                    fileName = os.path.abspath(os.path.join(root, file))[len(os.path.abspath(base))+1:]
                    musicFiles.append(fileName)                

        if musicFiles:
            musicFiles.sort()
            print ' - %s' % (base)
#            for file in musicFiles:
#                print ' - %s' % (file)
#            print ''

            fileName = os.path.join(base, listFileName)   
            f = open(fileName, 'wt')
            for file in musicFiles:
                f.write('%s\n'% (file))
            f.close()
            # if linux : chmod - remove X priveledges

    print 'Generating "%s" files in tree' % (listFileName)
    genPlaylist(baseDir)
    for root, dirs, files in os.walk(baseDir, topdown=False):
        for d in dirs:        
            genPlaylist(os.path.join(root, d))        

    return 0

#-------------------------------------------------------------------------------
if __name__ == '__main__' or __name__ == sys.argv[0]:

    sys.exit(main(sys.argv))

#-------------------------------------------------------------------------------
# end
