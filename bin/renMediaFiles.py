#! /usr/bin/env python

"""
renMediaFiles - Rename images and video files to my naming convention

    PICCCMMYYDDX_NNNN.ext
        CCMMYYDD - the date the picture was taken
        X        - a code for the camera, eg: A, B, C ... 
        NNNN     - the image number from the EXIF or the original filename
        .ext     - always converted to lowercase

    'exiftool' is required: http://www.sno.phy.queensu.ca/~phil/exiftool/

Usage:
  renMediaFiles [options] [<fileSpec>] [<fileSpec>]
    If no <fileSpec> is given then file paths will be read from STDIN.
    --rename        - actually do a rename
    --list          - do a dry run

    --nocache       - Run the tool without caching the results of exiftool
    --recursive,-R  - look for files based on the <fileSpec>s recursively
                      Remember wild cards may be expanded by your shell
                      so you may need to "quote" the args, eg:
                        renMediaFiles --rename "/myPics/*.JPG" 

Examples:
  find . -iname "*.JPG" -o -iname "*.AVI" | renMediaFiles --rename
  renMediaFiles "/myPics/*.JPG" "/myPics/*.jpg" "/myPics/*.AVI" "/myPics/*.avi"
  renMediaFiles "/myPics/*.JPG" "/myPics/*.jpg" --rename
"""

import os
import sys
import glob
import datetime
import json
import tempfile
import pickle
import re
import renMediaFiles_config

#===============================================================================
def getFileCameraCode(fileInfo):
   
    return renMediaFiles_config.getFileCameraCode(fileInfo)

#===============================================================================
def getFormattedFileName(fileInfo):

    cameraCode = getFileCameraCode(fileInfo)

    fileExt = os.path.splitext(fileInfo['filePath'])[1]
    fileName = os.path.split(fileInfo['filePath'])[1][:-len(fileExt)]

    imageDate = getFileCameraDate(fileInfo)
    if not imageDate:    # There is not enough EXIF data to get image date, can do nothing
        return None 

    if not cameraCode:
        # Camera is unknown, is it already named in PIC format, if so do nothing
        if re.match('%s20\d{2}[01]{1}\d{1}[0123]{1}\d{1}.*' % renMediaFiles_config.filePrefix, fileName):
            return None

        # Guest cameras - with EXIF data
        formattedFileName =  '%s%s_%s%s' % (renMediaFiles_config.filePrefix, imageDate.strftime('%Y%m%d'), fileName, fileExt.lower())
    else:
        # Known camera
        imageNo = getFileNumber(fileInfo)

        # Look for '.' suffixes
        suffix = None
        s = fileName.split('.',1)
        if len(s) > 1:
            suffix = s[1]

        formattedFileName =  '%s%s%s_%s' % (renMediaFiles_config.filePrefix, imageDate.strftime('%Y%m%d'), cameraCode, imageNo)
        if suffix:
            formattedFileName += '.%s' % suffix
        formattedFileName += fileExt.lower()

    return formattedFileName

#===============================================================================
def getFileCameraDate(fileInfo):

    exifDict = fileInfo['exifDict']

    originalTime = None
    if 'CreateDate' in exifDict: # DateTimeOriginal
        try:
            originalTime = datetime.datetime.strptime(exifDict['CreateDate'], '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            originalTime = None
    elif 'DateTimeOriginal' in exifDict:
        originalTime = datetime.datetime.strptime(exifDict['DateTimeOriginal'], '%Y-%m-%dT%H:%M:%S')

    return originalTime

#===============================================================================
def getFileNumber(fileInfo):

    exifDict = fileInfo['exifDict']
    fileName = os.path.split(fileInfo['filePath'])[1]
    fileExt = os.path.splitext(fileInfo['filePath'])[1]

    if 'FileNumber' in exifDict:
        imageNo = exifDict['FileNumber'][-4:]
    elif '_' in fileName:
        imageNo = fileName[:-len(fileExt)].split('_')[-1]
    else:
        imageNo = None

    return imageNo

#===============================================================================
def runSubProcess(args):

    import subprocess

    try:
        p = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            #cwd=cwd,
            #env=env
            )
    except:
        sys.stderr.write('Failed to launch subprocess: \'%s\'\n' % (args[0]))
        return None,None

    ## Stdin
#    if len(inlines) > 0:
#        p.stdin.writelines(inlines)
    p.stdin.close()

    ## Stdout
    outlines = p.stdout.readlines()
    p.stdout.close()

    ## Stderr
    errlines = p.stderr.readlines()
    p.stderr.close()

    
    retCode = p.wait()
    
    if len(errlines):
        for line in errlines:
            sys.stderr.write(' ! %s' % line)

    return outlines,errlines

#===============================================================================
def getMediaFileExif(image):

    args = ['/usr/bin/env', 'exiftool', '-fast1', '-json', '-S', '-d', '%Y-%m-%dT%H:%M:%S', image]

    out,err = runSubProcess(args)

    if not out:
        return None
    content = ''.join(out)
#    print content
    exifJson = json.loads(unicode(content, errors='replace').encode('utf-8'))

    exifDict = exifJson[0]
    return exifDict

#===============================================================================
def getMediaFileInfoDict(fileGen, cache):

    # Scan file specs
    fileInfoDict = {}
    scanExifList = []

    sys.stderr.write('\r- Scanning file info ...')
    sys.stderr.flush()

    for filePath in fileGen:
        if filePath in fileInfoDict: continue

        stat = os.stat(filePath)
        fileInfo = {'fileSize': stat.st_size, 'fileTime': stat.st_mtime,} 

        if cache.hasFileInfoChanged(filePath, fileInfo):
            scanExifList.append(filePath)
        else:
            fileInfo = cache.getFileInfo(filePath)
        fileInfo['filePath'] = filePath

        fileInfoDict[filePath] = fileInfo
    sys.stderr.write('\r                        .\r')
    sys.stderr.flush()


    # Extract EXIF info from files
    scanCount = 0
    totalCount = len(scanExifList)
    for filePath in scanExifList:
        scanCount += 1
        sys.stderr.write('\r- Reading EXIF data for %d of %d files ...' % (scanCount, totalCount))
        #sys.stderr.write('\n')
        sys.stderr.flush()

        exifDict= getMediaFileExif(filePath)
        fileInfoDict[filePath]['exifDict'] = exifDict

        cacheFileInfo = {
            'fileSize': fileInfoDict[filePath]['fileSize'],
            'fileTime': fileInfoDict[filePath]['fileTime'],
            'exifDict': exifDict
        }
        cache.setFileInfo(filePath, cacheFileInfo)

    if scanExifList:
        sys.stderr.write('\r                                                                \r')
        sys.stderr.flush()

    return fileInfoDict

#===============================================================================
def fullPathSort(a,b):
    aP,aN = os.path.split(a)
    bP,bN = os.path.split(b)

    if aP == bP:
        return cmp(aN, bN)
    return cmp(aP, bP)

#===============================================================================
def renameFiles(fileInfoDict, cache, doIt=False):

    fileInfoDictKeys = fileInfoDict.keys()
    fileInfoDictKeys.sort(fullPathSort)


    countRen = 0
    countSkip = 0
    countOk = 0

    if not doIt:
        print '#! /bin/bash'

    for fileName in fileInfoDictKeys:
        fileInfo = fileInfoDict[fileName]

        formattedFileName = getFormattedFileName(fileInfo)

        src = fileInfo['filePath']
        if formattedFileName:
            if not os.path.isfile(src):
                continue
            p,n = os.path.split(src)
            if n == formattedFileName:
                print '# OK: %s' % (src)
                countOk += 1
                continue
            dst = os.path.join(p, formattedFileName)

            if os.path.isfile(dst):
                if src.lower() != dst.lower():
                    print '# ERR  %s' % (src)
                    sys.stderr.write('! already exists: "%s"\n' % dst)
                    sys.stderr.write('! so cannot rename: "%s"\n' % src)
                    continue

            print 'mv  "%s"  "%s"' % (src, dst)
            if doIt:
                os.rename(src, dst)
                cache.renameFile(src, dst)
            countRen += 1
        else:
            print '#    %s' % (src)
            countSkip += 1

    # Output results
    sys.stderr.write('\rRESULT: Ren=%d, Ok=%d, Skip=%d\n' % (countRen, countOk, countSkip))

#===============================================================================
class Cache:
    def __init__(self):
        self._fileName = os.path.join(tempfile.gettempdir(), 'renMediaFiles-EXIF.cache')
        self._cacheDict = {}
        self._changed = False

    #---------------------------------------------------------------------------
    def hasChanged(self):
        return self._changed

    #---------------------------------------------------------------------------
    def load(self):
        if os.path.isfile(self._fileName):
            sys.stderr.write('\r- Loading cache ...')
            sys.stderr.flush()
            try:
                self._cacheDict = pickle.load(open(self._fileName, 'rt'))
            except EOFError:
                os.unlink(self._fileName)
                self._cacheDict = {}
            sys.stderr.write('\r                        .\r')
            sys.stderr.flush()
        else:
            self._cacheDict = {}

    #---------------------------------------------------------------------------
    def save(self):
        sys.stderr.write('\r- Saving cache ...')
        sys.stderr.flush()
        pickle.dump(self._cacheDict, open(self._fileName, 'wt'))
        sys.stderr.write('\r                        .\r')
        sys.stderr.flush()
        self._changed = False

    #---------------------------------------------------------------------------
    def clear(self):
        if os.path.isfile(self._fileName):
            os.unlink(self._fileName)
        self._cacheDict = {}

    #---------------------------------------------------------------------------
    def setFileInfo(self, fileName, fileInfo):
        if not fileInfo:
            return

        fullFilePath = self._getRealPath(fileName)

        self._cacheDict[fullFilePath] = fileInfo
        self._changed = True

    #---------------------------------------------------------------------------
    def getFileInfo(self, fileName):
        fullFilePath = self._getRealPath(fileName)

        if fullFilePath in self._cacheDict:
            return self._cacheDict[fullFilePath]
        return None

    #---------------------------------------------------------------------------
    def renameFile(self, src, dst):
        fullSrc = self._getRealPath(src)
        fullDst = self._getRealPath(dst)

        if fullSrc in self._cacheDict:
            self._cacheDict[fullDst] = self._cacheDict[fullSrc]
            del self._cacheDict[fullSrc]
            self._changed = True

    #---------------------------------------------------------------------------
    def hasFileInfoChanged(self, fileName, fileInfo):

        fullFilePath = self._getRealPath(fileName)

        # If found and unchanged in the cache then use the EXIF fron the cache
        if fullFilePath in self._cacheDict and \
           self._cacheDict[fullFilePath]['fileSize'] == fileInfo['fileSize'] and \
           self._cacheDict[fullFilePath]['fileTime'] == fileInfo['fileTime']:
            return False

        return True

    #---------------------------------------------------------------------------
    def show(self):
        cacheKeys = self._cacheDict.keys()
        cacheKeys.sort(fullPathSort)

        for fullFilePath in cacheKeys:
            print fullFilePath

    #---------------------------------------------------------------------------
    def _getRealPath(self, fileName):
        return os.path.realpath(os.path.abspath(fileName))

#===============================================================================
def genFilesFromSpecs(fileSpecs, recurse=False):
    # Generate file names from file spec
    for fileSpec in fileSpecs:
        if '*' in fileSpec:
            if recurse:
                path,spec = os.path.split(fileSpec)
                if not path: path = '.'
                for root, d, f in os.walk(path, topdown=False):
                    globSpec = os.path.join(root,spec)
                    for g in glob.glob(globSpec):
                        yield g
                return
            else:
                for g in glob.glob(fileSpec):
                    yield g
                return
        if os.path.isfile(fileSpec):
            yield fileSpec

#===============================================================================
def genFilesFromStdin():
    for line in sys.stdin:
        filePath = line.rstrip()
        if not os.path.isfile(filePath): continue
        yield filePath

#===============================================================================
def main(argv):

    if len(argv) == 1:
        print __doc__
        return -1

    noCache = False
    recurse = False
    doRename = False
    doList = False

    try:
        import getopt
        optList, optRemainder = getopt.gnu_getopt(argv[1:], 'R',
        ['help', 'nocache', 'recursive', 'rename', 'list', 'listcache', 'clearcache'])
    except getopt.GetoptError, e:
        print __doc__
        print "! Syntax error: ",e
        return -1

    for n,v in optList:
        if n in ('--help',):
            print __doc__
            return 0
        if n in ('--nocache',):
            noCache = True
        if n in ('--recursive','-R'):
            recurse = True
        if n in ('--rename',):
            doRename = True
        if n in ('--list',):
            doList = True
        if n in ('--listcache',):
            cache = Cache()
            cache.load()
            cache.show()
            return 0
        if n in ('--clearcache',):
            cache = Cache()
            cache.clear()
            return 0

    fileSpecs = optRemainder

    if doList and doRename:
        sys.stderr.write('! Too many and incompatible options\n')
        return -1

    if not doList and not doRename:
        sys.stderr.write('! No operation selected\n')
        return -1

    if fileSpecs:
        fileGen = genFilesFromSpecs(fileSpecs, recurse=recurse)
    else:
        fileGen = genFilesFromStdin()

    # Setup cache
    cache = Cache()
    if noCache==False:
        cache.load()

    fileInfoDict = getMediaFileInfoDict(fileGen, cache)

    if noCache==False and cache.hasChanged():
        cache.save()

    if doList:
        renameFiles(fileInfoDict, cache, False)
    elif doRename:
        renameFiles(fileInfoDict, cache, True)

    # Save cache if changed
    if noCache==False and cache.hasChanged():
        cache.save()

    return


#===============================================================================
if __name__ == '__main__' or __name__ == sys.argv[0]:

    sys.exit(main(sys.argv))

#===============================================================================
# end
