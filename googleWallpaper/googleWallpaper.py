#! /usr/bin/python

"""\
GoogleWallpaper v0.1                                          by: Source Simian

Usage: googleWallpaper [options] [query [query]]

Options: -w <width>          Exact image width in pixels
         -h <height>         Exact image height in pixels
         --size <size>       Minimum image size: 1mp, 2mp, 4mp

         --install <mins>    Install wallpaper changer for every <mins> minutes
         --uninstall         Uninstall wallpaper changer
"""
#         --safe <mode>       - Safe mode: off

import os
import sys
import re
import urllib
import urllib2
import random
import tempfile
import ConfigParser
import datetime

try:
    import Image
except ImportError:
    print
    print "ERROR: This application needs the Python Image Library installed"
    if os.name == 'nt':
        print "  You can download an installation here:"
        print "    http://www.pythonware.com/products/pil/"
    elif os.name == 'posix':
        print "  You can install this package by running the following command:"
        print "    sudo apt-get install python-imaging"
        print
    else:
        print "  Try doing a web search \"Python PIL install\"." 
    sys.exit(1)

verbose = True

#===============================================================================
def runSubProcess(args, inlines=[], stdIOHook=None, quiet=False):

    if isinstance(args, unicode):
        args = str(args)
    
    cmdLine = None
    if isinstance(args, str):
        cmdLine = args
        # split string command up into args
        def stripQuotes(x):
            if x[0] == '"' and x[-1] == '"':
                return x[1:-1]
            return x
        import re
        args =  [stripQuotes(x) for x in  re.split(' +(?=(?:[^"]*"[^"]*")*(?![^"]*"))', args)]
        #ioLog.cmdOut('str>>>'+str(args))
    else:
        def addQuotes(x):
            if x.find(' ') != -1:
                return '"'+x+'"'
            return x
        cmdLine = ' '.join([addQuotes(x) for x in args])
        #ioLog.cmdOut('other>>>'+str(args))

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

    if stdIOHook:
        stdIOHook.hook(p, cmdLine)
    
    ## Stdin
    if len(inlines) > 0:
        p.stdin.writelines(inlines)
    p.stdin.close()

    ## Stdout
    outlines = p.stdout.readlines()
    p.stdout.close()

    ## Stderr
    errlines = p.stderr.readlines()
    p.stderr.close()

    
    retCode = p.wait()
    
    if len(errlines) and quiet == False:
        for line in errlines:
            sys.stderr.write(' ! %s' % line)

    return outlines,errlines

#===============================================================================
def restoreBackgroundImage():
    config = Config()

    if os.name == 'nt':
        fileName = config.getValue('originalBackground', 'filename')

        if fileName:
            import ctypes
            import win32con

            ret = ctypes.windll.user32.SystemParametersInfoA(
                    win32con.SPI_SETDESKWALLPAPER,
                    0,
                    fileName,
                    win32con.SPIF_UPDATEINIFILE | win32con.SPIF_SENDWININICHANGE)

    elif os.name == 'posix':
        for option,value in config.sectionItems('originalBackground'):
            args = ['/usr/bin/gconftool-2', '--type', 'string', '--set', '/desktop/gnome/background/%s' % option, '%s' % value] 
            out,err = runSubProcess(args)

    else:
        sys.stderr.write('Not implemented for %s' % os.name)

#===============================================================================
def setBackgroundImage(fileName):

    if os.name == 'nt':
        import ctypes
        import win32con

        strLen = 255
        c_filename = ctypes.c_char_p(' '*strLen)
        ret = ctypes.windll.user32.SystemParametersInfoA(
                win32con.SPI_GETDESKWALLPAPER, strLen, 
                c_filename, win32con.SPIF_UPDATEINIFILE | win32con.SPIF_SENDWININICHANGE)

        if ret:
            if not c_filename.value.startswith(getConfigDir()):
                config = Config()
                config.deleteSection('originalBackground')
                config.setValue('originalBackground', c_filename.value)
                config.store()

        result = ctypes.windll.user32.SystemParametersInfoA(win32con.SPI_SETDESKWALLPAPER, 0,
                    fileName,
                    win32con.SPIF_UPDATEINIFILE | win32con.SPIF_SENDWININICHANGE)

    elif os.name == 'posix':

        def getValue(option):
            args = ['/usr/bin/gconftool-2', '--get', '/desktop/gnome/background/%s' % option] 
            out,err = runSubProcess(args)
            return out[0].rstrip()

        def setValue(option, value):
            args = ['/usr/bin/gconftool-2', '--type', 'string', '--set', '/desktop/gnome/background/%s' % option, '%s' % value] 
            out,err = runSubProcess(args)

        posixOptions = {
            'picture_filename': fileName,
            'primary_color': '#000000000000',
            'picture_options': 'scaled'
        }

        # Preserve orifinal settings
        if not getValue('picture_filename').startswith(getConfigDir()):
            config = Config()
            for option in posixOptions:
                value = getValue(option)
                config.setValue('originalBackground', option, value)
            config.store()

        # Set the new background
        for option in posixOptions:
            value = setValue(option, posixOptions[option])

    else:
        sys.stderr.write('Not implemented for %s' % os.name)

#==============================================================================
class GoogleImages:
    def __init__(self):
        self._imageDict = {}

    #--------------------------------------------------------------------------
    def setQuery(self, query, args):
        self._query = query
        self._args = args

    #--------------------------------------------------------------------------
    def getImageUrl(self, imageIdx):
        if verbose:
            print 'INDEX:', imageIdx
        if imageIdx in self._imageDict:
            return self._imageDict[imageIdx]

        imagesPerPage = 21
        pageNo,imgNo  = divmod(imageIdx, imagesPerPage)
        imageIdx = pageNo * imagesPerPage

        self._args['start'] = '%d' % (imageIdx)
        url = self._getQueryUrl()
        obj = self._fetchUrl(url)
        if not obj:
            return None
        imageUrlList = self._getImageUrlList(obj)

        if verbose:
            print 'QUERY:',url
            print 'COUNT:',len(imageUrlList)

        for imageUrl in imageUrlList:
            self._imageDict[imageIdx] = imageUrl
            imageIdx += 1

        if len(imageUrlList) != imagesPerPage:
            print len(imageUrlList), imagesPerPage
        if len(imageUrlList) <= imgNo:
            return None
        return imageUrlList[imgNo]

    #--------------------------------------------------------------------------
    def _fetchUrl(self, url):
        return fetchUrl(url)

    #--------------------------------------------------------------------------
    def _getImageUrlList(self, obj):
        exp = re.compile('\["/imgres.*?"\]', re.IGNORECASE | re.MULTILINE | re.DOTALL)
        src = obj.read()
        retList = exp.findall(src)
        imageInfoList =  [eval(x) for x in retList]

        return [x[0][len('/imgres?imgurl='):].split('&')[0] for x in imageInfoList]

    #--------------------------------------------------------------------------
    def _getQueryUrl(self):
        baseUrl = 'http://images.google.com/images'
        self._args['q'] = self._query
        return '%s?%s' % (baseUrl, urllib.urlencode(self._args))

#==============================================================================
def getImageUrlList(queryUrl):
    raise "Old"
    if verbose:
        print 'QUERY: %s' % queryUrl

    obj = fetchUrl(queryUrl)

    exp = re.compile('\["/imgres.*?"\]', re.IGNORECASE | re.MULTILINE | re.DOTALL)
    retList = exp.findall(obj.read())

    imageInfoList =  [eval(x) for x in retList]

    return [x[0][len('/imgres?imgurl='):].split('&')[0] for x in imageInfoList]

#==============================================================================
def getGoogleImageUrl(query, args, imageIdx):
    raise "Old"
    imagesPerPage = 20

    baseUrl = 'http://images.google.com/images'
    args['q'] = query

    imageUrlList = getImageUrlList('%s?%s' % (baseUrl, urllib.urlencode(args))) 
    imagesPerPage = len(imageUrlList)
    if verbose:
        print 'IMAGES PER PAGE: %s' % imagesPerPage

    pageNo,imgNo  = divmod(imageIdx, imagesPerPage)
    if pageNo:
        args['start'] = '%d' % (pageNo*imagesPerPage)
        imageUrlList = getImageUrlList('%s?%s' % (baseUrl, urllib.urlencode(args)))

    return imageUrlList[imgNo]

#==============================================================================
def getConfigDir():
    if os.name == 'nt':
        homeDir = os.path.join(os.environ['HOMEDRIVE'], os.environ['HOMEPATH'])
    elif os.name == 'posix':
        homeDir = os.environ['HOME']
    else:
        homeDir = os.path.split(__file__)[0]
    configDir = os.path.join(homeDir, '.googleWallpaper')

    if not os.path.isdir(configDir):
        raw_input('googleWallpaper needs to create the following directory to setup:\n    "%s"\nPress ENTER to continue or Ctrl+C to quit.'  % configDir)

        os.makedirs(configDir)
        if not os.path.isdir:
            sys.stderr.write('! Unable to create config folder: "%s"')
            sys.exit(-1)

    return configDir

#==============================================================================
class Crontab():
    def __init__(self):
        self._lines = []
        self._load()

    #--------------------------------------------------------------------------
    def _load(self):
        args = ['/usr/bin/crontab', '-l']
        out,err = runSubProcess(args)
        self._lines = []
        for line in out:
            self._lines.append(line.rstrip())

    #--------------------------------------------------------------------------
    def store(self):
        cronFile = os.path.abspath(os.path.join(tempfile.gettempdir(), 'googleWallpaper.cron'))
        fh = open(cronFile, 'wt')
        for line in self._lines:
            fh.write('%s\n' % line)
        fh.close()

        args = ['/usr/bin/crontab', cronFile]
        out,err = runSubProcess(args)

    #--------------------------------------------------------------------------
    def removeMatch(self, regExp):
        newLines = []
        for i in xrange(len(self._lines)):
            if not re.search(regExp, self._lines[i]):
                newLines.append(self._lines[i])
        self._lines = newLines

    #--------------------------------------------------------------------------
    def addLine(self, command, mins=None, hours=None, daysOfMonth=None, months=None, daysOfWeek=None, comment=None):
        fields = []
        for val in [mins, hours, daysOfMonth, months, daysOfWeek]:
            if not val: fields.append('*')
            else:       fields.append(','.join(['%d' % x for x in val]))
        fields.append(command)
        if comment:
            fields.append(' # %s' % comment)

        line = ' '.join(fields)

        self._lines.append(line)

#==============================================================================
def installCron(mins):
    cmd = '%s --cron' % os.path.abspath(__file__)

    if os.name == 'posix':
        ct = Crontab()
        ct.removeMatch('googleWallpaper_cron')
        minList = range(0, 60, mins)
        if mins == 1:
            minList = None
        ct.addLine(cmd, minList, comment='googleWallpaper_cron')
        ct.store()
    elif os.name == 'nt':
        import getpass
        args = [os.environ['ComSpec'], '/c',
                'schtasks',
                '/create',
                '/tn', 'googleWallpaper',
                '/sc', 'MINUTE',
                '/ru', getpass.getuser(),
                '/rp', getpass.getpass('Please enter password for "%s": '%getpass.getuser()),
                '/mo', '%d' % mins,
                '/tr', '%s /c "%s"' % (os.environ['ComSpec'], cmd)]
        #print args
        out,err = runSubProcess(args, ['\n'])
        for l in out: print l.rstrip()
        for l in err: print l.rstrip()

#==============================================================================
def uninstallCron():

    if os.name == 'posix':
        ct = Crontab()
        ct.removeMatch('googleWallpaper_cron')
        ct.store()
    elif os.name == 'nt':
        args = [os.environ['ComSpec'], '/c',
                'schtasks',
                '/delete',
                '/tn', 'googleWallpaper',
                '/f']
        out,err = runSubProcess(args)
        for l in out: print l.rstrip()
        for l in err: print l.rstrip()

    restoreBackgroundImage()

#==============================================================================
class Config():
    def __init__(self):
        self._conf = ConfigParser.SafeConfigParser()
        self._configFileName = os.path.join(getConfigDir(), 'googleWallpaper.conf')
        self._conf.read(self._configFileName)

    #--------------------------------------------------------------------------
    def deleteSection(self, section):
        if self._conf.has_section(section):
            self._conf.remove_section(section)

    #--------------------------------------------------------------------------
    def renameSection(self, section, newSection):
        if not self._conf.has_section(section):
            return
        if self._conf.has_section(newSection):
            return
        self._conf.add_section(newSection)
        for option,value in self._conf.items(section):
            self._conf.set(newSection, option, value)
        self._conf.remove_section(section)

    #--------------------------------------------------------------------------
    def setValue(self, section, option, value):
        if not self._conf.has_section(section):
            self._conf.add_section(section)
        self._conf.set(section, option, value)

    #--------------------------------------------------------------------------
    def getValue(self, section, option, defaultValue=None):
        if not self._conf.has_section(section):
            return defaultValue
        if not self._conf.has_option(section, option):
            return defaultValue
        return self._conf.get(section, option)

    #--------------------------------------------------------------------------
    def sectionItems(self, section):
        if self._conf.has_section(section):
            for option,value in self._conf.items(section):
                yield option,value

    #--------------------------------------------------------------------------
    def hasSection(self, section):
        return self._conf.has_section(section)

    #--------------------------------------------------------------------------
    def store(self):
        self._conf.write(open(self._configFileName, 'wt'))


#==============================================================================
def setCronArgs(queryList, args, maxCount):

    config = Config()

    if config.hasSection('cron'):
        if not queryList:
            return
        config.renameSection('cron', 'cron.bak_%s' % (datetime.datetime.now().strftime('%Y%m%dT%H%M%S')))

    i = 0 
    for query in queryList:
        i += 1
        config.setValue('cron', 'query.%d'%i, query)
    for name in args:
        config.setValue('cron', 'arg.%s'%name, '%s'%args[name])

    config.setValue('cron', 'maxCount', '%d' % maxCount)

    config.store()

#==============================================================================
def getCronArgs():

    config = Config()

    queryList = []
    args = {}

    for name,value in config.sectionItems('cron'):
        if name.startswith('arg.'):
            args[name[4:]] = value
        elif name.startswith('query.'):
            queryList.append(value)

    maxCount = int(config.getValue('cron', 'maxCount'))

    return queryList,args,maxCount

#==============================================================================
def randomSetWallpaper(queryList, args, maxCount):
    imageQuery = random.choice(queryList)
    googleImages = GoogleImages()
    googleImages.setQuery(imageQuery, args)
    for i in xrange(5):
        for i in xrange(5):
            imageIndex = random.randint(-1, maxCount)
            imageUrl = googleImages.getImageUrl(imageIndex)
            if imageUrl: break
            if verbose:
                print 'MISS'
        if not imageUrl:
            return -1
        if verbose:
            print 'URL:',imageUrl

        if setBackgroundFromUrl(imageUrl): break

    infoFileName = os.path.join(getConfigDir(), 'currentImage.nfo')
    fh = open(infoFileName, 'wt')
    fh.write('URL: %s\n' % imageUrl)
    fh.close()

#==============================================================================
def setBackgroundFromUrl(imageUrl):

    obj = fetchUrl(imageUrl)
    if not obj:
        return False

    fd,imageFileName = tempfile.mkstemp(prefix='googleWallpaper-')
    os.write(fd, obj.read())
    os.close(fd)

    bmpFileName = os.path.join(getConfigDir(), 'currentImage.bmp')

    bmpImage = Image.open(imageFileName)
    newPath = os.getcwd()
    bmpImage.save(bmpFileName, "BMP")

    setBackgroundImage(bmpFileName)

    os.unlink(imageFileName)
    return True

#==============================================================================
def fetchUrl(url):
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    try:
        obj = opener.open(url)
    except:
        sys.stderr.write('Failed to open: %s\n' % url)
        return None
    return obj

#==============================================================================
def runCron():
    randomSetWallpaper(*getCronArgs())
    return 0

#==============================================================================
def runKeep():
    pass

#==============================================================================
def runBlackList():
    pass

#==============================================================================
def main(argv):

    if len(argv) == 1:
        print __doc__
        return -1

    try:
        import getopt
        optList, optRemainder = getopt.gnu_getopt(argv[1:], 'w:h:',
        ['help', 'maxCount=', 'verbose', 'size=', 'install=', 'uninstall', 'cron', 'keep', 'blacklist'])
    except getopt.GetoptError, e:
        print __doc__
        print "! Syntax error: ",e
        return -1

    queryList = []
    maxCount = 200
    sizeW = 0
    sizeH = 0
    size = None
    safe = 'off'
    install = False

    cronMins = 0
    global verbose

    for n,v in optList:
        if n == '--help':
            print __doc__
            return 0
        if n  == '--verbose':
            verbose = True
        if n == '--maxCount':
            maxCount = int(v)
        if n  == '-w':
            sizeW = int(v)
        if n == '-h':
            sizeH = int(v)
        if n  == '--size':
            size = v
        if n == '--safe':
            safe = v

        if n == '--cron':
            return runCron()
        if n == '--uninstall':
            return uninstallCron()
        if n == '--install':
            cronMins = int(v)
            install = True
        if n == '--keep':
            return runKeep()
        if n == '--blacklist':
            return runBlacklist()

    queryList = optRemainder

    args = {}
    args['safe'] = safe

    if size:
        args['imgsz'] = size
    elif sizeW or sizeH:
        if not sizeW or not sizeH:
            print 'Both X and Y dimensions are required'
            return -1
        args['imgw'] = sizeW
        args['imgh'] = sizeH

    if install:
        installCron(cronMins)
        setCronArgs(queryList, args, maxCount)
#        runCron()
        return 0

    randomSetWallpaper(queryList, args, maxCount)
    return 0

#==============================================================================
if __name__ == '__main__' or __name__ == sys.argv[0]:

    sys.exit(main(sys.argv))

#==============================================================================
# end
