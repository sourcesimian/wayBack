#! /usr/bin/env python

"""
mediaIndex

Index media files

Usage: mediaIndex <command> <args>

Commands: update <basePath> [<titleImage>]
          fetch <basePath>

"""

import os
import sys
import glob

#-------------------------------------------------------------------------------
def getMontageList(basePath):

    montageList = []

    for root, dirs, files in os.walk(basePath):

        montageFile = os.path.join(root, 'montage.jpg')

        if os.path.isfile(montageFile):
            montageList.append(montageFile)

    return montageList

#-------------------------------------------------------------------------------
def writefetchScript(montageList, outputDir):
    import stat

    os.makedirs(outputDir)

    fetchScriptName  = os.path.join(outputDir, 'doFetchMontages.sh')

    fetchScript  = open(fetchScriptName, 'wt')
    fetchScript.write('#! /bin/bash\n')
    fetchScript.write('\n')

    for montageFile in montageList:
        mangledMontageFile = 'montage.'+os.path.split(montageFile)[0].replace('/', '~')+'.jpg'

        fetchScript.write('cp "%s" "%s"\n' % (montageFile, mangledMontageFile))

    fetchScript.close()
    os.chmod(fetchScriptName, stat.S_IRWXU)



#-------------------------------------------------------------------------------
def getMontageStatus(basePath):

    missingList = []
    outdatedList = []
    multipleList = []
    goodList = []

    for root, dirs, files in os.walk(basePath):

        globList = glob.glob(os.path.join(root, 'PIC*.jpg'))
        if not globList:
            continue

        montageList = glob.glob(os.path.join(root, 'montage.*'))
        if len(montageList) > 2:
            multipleList.append(root)
            continue
        if not montageList:
            missingList.append(root)
            continue
        montageFile = montageList[0]

        montageStat = os.stat(montageFile)

        for imageFile in globList:
            imageStat = os.stat(imageFile)

            if montageStat.st_mtime < imageStat.st_mtime:
                outdatedList.append(root)
                break
        else:
            goodList.append(root)

    return {
        'missingList': missingList,
        'outdatedList': outdatedList,
        'multipleList': multipleList,
        'goodList': goodList
    }


#-------------------------------------------------------------------------------
class MediaIndexBuilder:
    def __init__(self, outputDir):
        self._outputDir = outputDir
        self._indexDict = {}

    def addMediaFile(self, indexFile, mediaFile):
        if not indexFile in self._indexDict:
            self._indexDict[indexFile] = []
        self._indexDict[indexFile].append(mediaFile)

    def writeScripts(self):
        pass


#-------------------------------------------------------------------------------
def writeGenScript(outputDir, folderList, scriptSuffix, findSpecs, titleThumbFile=None):
    import stat

    os.makedirs(outputDir)

    genScriptName  = os.path.join(outputDir, 'doMakeMontages.%s.sh' % (scriptSuffix))
    thumbScriptName = os.path.join(outputDir, 'doMakeThumbs.%s.sh' % (scriptSuffix))
    copyScriptName = os.path.join(outputDir, 'doCopyMontages.%s.sh' % (scriptSuffix))

    genScript  = open(genScriptName, 'wt')
    genScript.write('#! /bin/bash\n')
    genScript.write('\n')

    copyScript = open(copyScriptName, 'wt')
    copyScript.write('#! /bin/bash\n')
    copyScript.write('\n')

    thumbScript = open(thumbScriptName, 'wt')
    thumbScript.write('#! /bin/bash\n')
    thumbScript.write('\n')

    counter = 0
    for folder in folderList:
        counter += 1
        localMontageFile = 'montage.%d.jpg' % (counter)
        montageFile = os.path.join(folder, 'montage.jpg')

        copyScript.write('cp "%s" "%s"\n' % (localMontageFile, montageFile))
        montageFile = localMontageFile

        listFileName =  'list.%d.lst' % counter
        listFile = open(os.path.join(outputDir, listFileName), 'wt')

        genScript.write('echo "* %s"\n' % folder)

        if titleThumbFile:
            listFile.write('%s\n' % titleThumbFile)

        fileList = []
        for findSpec in findSpecs:
            fileList += glob.glob(os.path.join(folder, findSpec))

        fileList = list(set(fileList))
        fileList.sort()

        thumbsDir = 'thumbs.%d'%counter

        thumbsDirRequired = False
        for i in xrange(len(fileList)):
            if os.path.splitext(fileList[i])[1] in ('.avi', '.mov'):
                thumbsDirRequired = True
                src = fileList[i]
                dst = os.path.join(thumbsDir, os.path.split(fileList[i])[1])
                fileList[i] = dst

                thumbScript.write('ffmpeg  -itsoffset -1 -i "%s" -vcodec mjpeg -vframes 1 -an -f rawvideo -s 640x480 "%s"\n' % (src, dst))

        for line in fileList:
            listFile.write('%s\n' % line)

        if thumbsDirRequired:
            os.makedirs(os.path.join(outputDir, thumbsDir))

        genScript.write('feh -i -y 300 -E 300 -W 3000 -O "%s" -f "%s"\n' % (montageFile, listFileName))
        genScript.write('\n')

    genScript.close()
    os.chmod(genScriptName, stat.S_IRWXU)

    copyScript.close()
    os.chmod(copyScriptName, stat.S_IRWXU)

    thumbScript.close()
    os.chmod(thumbScriptName, stat.S_IRWXU)

#-------------------------------------------------------------------------------
def main(argv):

    titleThumbFile = None
    if len(argv) < 2:
        print __doc__
        return -1

    cmd = argv[1]

    try:
        import getopt
        optList, optRemainder = getopt.gnu_getopt(argv[2:], '', [])
    except getopt.GetoptError, e:
        print "! Syntax error: ",e
        showUsage()
        return -1

    if len(optRemainder) < 1 :
        print __doc__
        return -1

    if cmd == 'update':
        basePath = optRemainder[0]
        if len(optRemainder) > 1:
            titleThumbFile = optRemainder[1]

        statusDict = getMontageStatus(basePath)

        outputDir = 'updateMontage.%s' % os.getpid()

        writeGenScript(outputDir, statusDict['missingList'], 'missing', ['PIC*.jpg', 'PIC*.gif', 'PIC*.tif', 'PIC*.mov', 'PIC*.avi'], titleThumbFile)

    elif cmd == 'fetch':
        basePath = optRemainder[0]
        if len(optRemainder) > 1:
            titleThumbFile = optRemainder[1]

        montageList = getMontageList(basePath)

        outputDir = 'montageFetch.%s' % os.getpid()

        writefetchScript(montageList, outputDir)

    else:
        print '! Command "%s" not found' % cmd


    print 'Done: %d' % os.getpid()
    return 0

#-------------------------------------------------------------------------------
if __name__ == '__main__' or __name__ == sys.argv[0]:

    sys.exit(main(sys.argv[0:]))

#-------------------------------------------------------------------------------
# end

