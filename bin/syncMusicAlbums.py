#!/usr/bin/env python

"""\
SyncMusicAlbums
  Synchronise music alums to a portable device

Usage: syncMusicAlbums <mediaDir> 

Switches: --help, -h
          --to <destDir>
          --playlists <destDir>

"""

import os
import sys
import glob
import shutil

_MAX_ROWS = 30

try:
    import Tkinter as tk


    #===============================================================================
    class TkPathSelector(tk.Entry):
        
        def __init__(self, master, *kw, **options):
            self._bgColour = '#FFFFFF'
            self._mandatory = False
            self._filetypes = [('All Files', '*.*')]
            self._title = None
            text = None
            
            keys = options.keys()
            for o in keys:
                
                if o == 'mandatory':
                    self._mandatory = options[o]
                    if self._mandatory:
                        self._bgColour = '#DDFFFF'
                    del options[o]
                    
                if o == 'mode':
                    self._mode = options[o]
                    del options[o]

                if o == 'title':
                    self._title = options[o]
                    del options[o]

                if o == 'filetypes':
                    self._filetypes = options[o]
                    del options[o]
                    
                if o == 'text':
                    text = options[o]
                    del options[o]
                    
            self._frame = tk.Frame(master)
            self._textVar =  tk.StringVar(self._frame)
            tk.Entry.__init__(self, self._frame, textvariable=self._textVar, *kw, **options)
            
            self._textVar.trace('w', self._onChange)
            
            if text:
                self._textVar.set(text)
            else:
                self._onChange()

            self._button = tk.Button(self._frame, text=' ... ', command=self._onButton)
            self._button.grid(row=0, column=1, sticky=tk.E+tk.N+tk.S)
            
            tk.Entry.grid(self, row=0, column=0, sticky=tk.W+tk.E)

            #---------------------------------------------------------------------------
        def grid(self, *kw, **options):
            self._frame.grid(*kw, **options)
            
        #---------------------------------------------------------------------------
        def isValid(self):
            return self._testValue()
            
        #---------------------------------------------------------------------------
        def setPath(self, path):
            return self._textVar.set(path)
            
        #---------------------------------------------------------------------------
        def getPath(self):
            return self._textVar.get()
            
        #---------------------------------------------------------------------------
        def _onChange(self, a=None, b=None, c=None):
            if not self._testValue():
                self.config(background='#FFDDFF')
            else:
                self.config(background=self._bgColour)

        #---------------------------------------------------------------------------
        def _onButton(self):
            path =  self._textVar.get()
            #path = os.path.abspath(path)
            
            if self._mode == 'FileSelect':
                ret = self.tkSelectFileName(path, self._filetypes)
            elif self._mode == 'FileSaveAs':
                #base,file = os.path.split(path)
                ret = self.tkSaveFileName(path, self._filetypes)
            elif self._mode == 'DirSelect':
                ret = self.tkSelectDirName(path)
            else:
                return
                
            if not ret:
                return
                
            ret = os.path.normpath(ret)
            
            ret  = TkPathSelector.getRelativePath(ret)
            self._textVar.set(ret)

        #---------------------------------------------------------------------------
        def _testValue(self):
            
            path = self._textVar.get()
            if not path:
                return not self._mandatory
            
            if self._mode == 'FileSelect':
                return os.path.isfile(path)
                
            elif self._mode == 'FileSaveAs':
                base,file = os.path.split(path)
                if not base:
                    return True
                return os.path.isdir(base)
                
            elif self._mode == 'DirSelect':
                return os.path.isdir(path)
                
            else:
                return False

        #---------------------------------------------------------------------------
        def tkSelectFileName(self, initialdir, filetypes):
            import tkFileDialog

            filename = tkFileDialog.askopenfilename(parent=self, title=self._title, initialdir=initialdir, filetypes=filetypes)
            
            if os.name == 'nt':
                filename = filename.replace('/', '\\')
            return filename

        #---------------------------------------------------------------------------
        def tkSaveFileName(self, initialdir, filetypes):
            import tkFileDialog
            
            filename = tkFileDialog.asksaveasfilename(parent=self, filetypes=filetypes, title=self._title)

            p,ext = os.path.splitext(filename)
            if filename and not ext:
                filename += os.path.splitext(filetypes[0][1])[1]
            
            return filename
        
        #---------------------------------------------------------------------------
        def tkSelectDirName(self, initialdir):
            import tkFileDialog
            dirname = tkFileDialog.askdirectory(parent=self, initialdir=initialdir, title=self._title)
            return dirname
            
        #---------------------------------------------------------------------------
        @staticmethod
        def getRelativePath(path, cwd=os.getcwd()):

            path = os.path.realpath( os.path.abspath(path) )
            cwd = os.path.realpath( os.path.abspath(cwd) )
            
            pathList = path.split(os.sep)
            cwdList  = cwd.split(os.sep)
            
            # On different drive ?
            if os.name == 'nt'and pathList[0] != cwdList[0]:
                return path

            # Ignore common base
            i = 0
            while 1:
                if pathList[i] != cwdList[i]:
                    break
                i += 1
                if len(pathList) == i or len(cwdList) == i:
                    break
            if os.name == 'nt' and i == 1  or  os.name != 'nt' and i == 0:
                    return path
            pathList = pathList[i:]
            cwdList  = cwdList[i:]
            
            rel = []
            for c in cwdList:
                rel.append('..')
            rel += pathList
            
            return os.path.join(*rel)
except:
    pass

#===============================================================================
class AlbumSelect:
    def __init__(self):
        self._albumDict = {}
        self._albumState = {}
    
        self._m = tk.Tk()
        self._m.title('Album Sync')
        #self._m.attributes('-topmost', 1)
        self._m.geometry('+0+0')
        #self._m.resizable(width=tk.NO, height=tk.NO)
    
        self._m.bind('<Escape>', self._onEsc)

        self._m.protocol('WM_DELETE_WINDOW', self._onClose)
        
        self._inp = tk.Frame(self._m)
        self._inp.grid(row=0, column=0, columnspan=2, sticky=tk.N+tk.S+tk.E+tk.W)

        self._src = TkPathSelector(self._inp, width=45, mode='DirSelect', mandatory=True)
        self._src.grid(row=0, column=0, sticky=tk.E+tk.W)
        self._dst = TkPathSelector(self._inp, width=45, mode='DirSelect', mandatory=True)
        self._dst.grid(row=1, column=0, sticky=tk.E+tk.W)
        self._sync = tk.Button(self._inp, width=10, text='Sync', command=self._onSync)
        self._sync.grid(row=0, column=1, rowspan=2, padx=3, sticky=tk.E+tk.W+tk.N+tk.S)

        self._text = tk.Text(self._m, relief=tk.FLAT, width=70, height=_MAX_ROWS)
        self._text.grid(row=1, column=0, sticky=tk.N+tk.S+tk.E+tk.W)

        self._text.tag_config('artist', background='#D0E0FF', foreground='#000080', lmargin1=5)

        self._text.tag_config('state:toSync', background='#00E000', foreground='white', lmargin1=15)
        self._text.tag_config('state:synced', background='#80C080', foreground='white', lmargin1=15)
        self._text.tag_config('state:toRemove', background='#D00000', foreground='white', lmargin1=15)
        self._text.tag_config('state:default', background='#FFFFFF', foreground='black', lmargin1=15)

        def show_hand_cursor(event):
            event.widget.configure(cursor="hand1")
        def show_arrow_cursor(event):
            event.widget.configure(cursor="")

        self._text.tag_bind("a", "<Enter>", show_hand_cursor)
        self._text.tag_bind("a", "<Leave>", show_arrow_cursor)
        self._text.tag_bind("a", "<Button-1>", self._onTextClick)
        self._text.tag_bind("a", "<Button-3>", self._onTextContext)
        self._text.config(cursor="arrow")
        
        self._textScroll = tk.Scrollbar(self._m)
        self._textScroll.grid(row=1, column=1, sticky=tk.N+tk.S)
        self._textScroll.grid_remove()

        self._text.config(yscrollcommand=self._textScroll.set)
        self._textScroll.config(command=self._text.yview)

        self._popup = tk.Menu(self._m, tearoff=0)
        self._popup.add_command(label="Info", command=self._popupInfo)
        #self._popup.add_separator()
        #self._popup.add_command(label="Home")
        
        self._status = tk.StringVar()
        self._statusWidget = tk.Label(self._m, relief=tk.FLAT, textvariable=self._status)
        self._statusWidget.grid(row=2, column=0, sticky=tk.W+tk.E)

    #---------------------------------------------------------------------------
    def run(self, baseDir, syncToDir, albumDict, albumState):

        self._exitCode = False
        self._src.setPath(baseDir)
        self._dst.setPath(syncToDir)
        
        self._albumDict = albumDict
        self._albumState = albumState

        self._updateList()
        self._updateStatus()
        tk.mainloop()
        
        return self._exitCode

    #---------------------------------------------------------------------------
    def _updateList(self):

        artistAlbumList = self._albumDict.keys()
        def sort(a, b):
            return AlbumInfo.sort(self._albumDict[a], self._albumDict[b])
        artistAlbumList.sort(sort)
        
        scrollPos = self._textScroll.get()
        self._text.delete(1.0, tk.END)

        rowCount = 0
        
        currentArtist = None
        for artistAlbum in artistAlbumList:
            artist = self._albumDict[artistAlbum]['artist']
            album = self._albumDict[artistAlbum]['album']
            state = self._albumState[artistAlbum]['state']
            
            if currentArtist != artist:
                currentArtist = artist
                self._text.insert(tk.INSERT, '%s\n' % (artist), ('artist'))
                rowCount += 1
            nl = '\n'
            self._text.insert(tk.INSERT, '- %s%s' % (album, nl), ('state:%s'%(state), 'a', 'album:%s'%(artistAlbum)) )
            rowCount += 1
            
        self._text.yview('moveto', scrollPos[0])
        self._text.focus()

        if rowCount > _MAX_ROWS:
            self._textScroll.grid()
        else:
            self._textScroll.grid_remove()

    #---------------------------------------------------------------------------
    def _onEsc(self, event):
        self._onClose()
    
    #---------------------------------------------------------------------------
    def _onClose(self):
        self._m.destroy()
        
    #---------------------------------------------------------------------------
    def _onSync(self):
        #print '_onSync'
        self._exitCode = True
        self._onClose()

    #---------------------------------------------------------------------------
    def _getListItemId(self, event):
        self._currentAlbum = None
        
        w = event.widget
        x, y = event.x, event.y
        tags = w.tag_names("@%d,%d" % (x, y))

        for t in tags:
            if t.startswith('id:'):
                id = t[3:]
                if id in self.AlbumDict:
                    self._currentAlbum
                return id

    #---------------------------------------------------------------------------
    def _setCurrentAlbum(self, event):
        self._currentAlbum = None
    
        w = event.widget
        x, y = event.x, event.y
        tags = w.tag_names("@%d,%d" % (x, y))

        tagPrefix = 'album:'
        for t in tags:
            if t.startswith(tagPrefix):
                self._currentAlbum = t[len(tagPrefix):]
                return True
        return False

    #---------------------------------------------------------------------------
    def _onTextClick(self, event):
        self._setCurrentAlbum(event)
        #print 'Click',self._currentAlbum
        
        currentState = self._albumState[self._currentAlbum]
        
        if currentState['state'] == 'default':
            currentState['state'] = 'toSync'
        elif currentState['state'] == 'toSync':
            currentState['state'] = 'default'
        elif currentState['state'] == 'synced':
            currentState['state'] = 'toRemove'
        elif currentState['state'] == 'toRemove':
            currentState['state'] = 'synced'
            
        self._updateList()
        self._updateStatus()

    #---------------------------------------------------------------------------
    def _onTextContext(self, event):
        self._setCurrentAlbum(event)

        try:
            self._popup.tk_popup(event.x_root, event.y_root, 0)
        finally:
            # make sure to release the grab (Tk 8.0a1 only)
            self._popup.grab_release()

        return
    #---------------------------------------------------------------------------
    def _updateStatus(self):

        dstDir = self._dst.getPath()
        s = os.statvfs(dstDir)
        freeSpace = s.f_bsize * s.f_bavail

        toSync = 0
        toRemove = 0
        for artistAlbum in self._albumDict:
            if self._albumState[artistAlbum]['state'] == 'toSync':
                toSync += self._albumDict[artistAlbum].getAlbumSize()
            if self._albumState[artistAlbum]['state'] == 'toRemove':
                toRemove += self._albumDict[artistAlbum].getAlbumSize()

        self._status.set("%d MiB - %d MiB = %d MiB  ->  %d MiB" % (toSync / (1024 * 1024), toRemove / (1024 * 1024), (toSync - toRemove) / (1024 * 1024), freeSpace / (1024 * 1024)))

    #---------------------------------------------------------------------------
    def _popupInfo(self):
        print
        print self._albumDict[self._currentAlbum]
        print self._albumDict[self._currentAlbum].getAlbumSize()
        
#===============================================================================
class AlbumInfo(dict):
    def __init__(self):
        dict.__init__(self)
        self._musicFileExts = ['.mp3', '.mpc', '.wma', 'wav']

    #--------------------------------------------------------------------------
    def load(self, baseDir):
        self._info = {}
        albumFileName = os.path.join(baseDir, '.album')

        if not os.path.isfile(albumFileName):
            return False

        self['baseDir'] = baseDir

        albumFile = open(albumFileName, 'rt')
        for line in albumFile:
            line = line.split('#', 1)[0]
            line = line.rstrip()
            if not line:
                continue
            s = line.split('=', 2)
            name = s[0].rstrip()
            value = None
            if len(s) > 1:
                value = s[1].strip()
            self[name] = value

        s = baseDir.split(os.sep)
        if not 'artist' in self:
            self['artist'] = s[-2]
        if not 'album' in self:
            self['album'] = s[-1]
            
            if self['album'].lower().startswith(self['artist'].lower()) and len(self['album']) > len(self['artist']):
                self['album'] = self['album'][len(self['artist']):]
                self['album'] = self['album'].lstrip('-._ ')

        self._loadMusicFiles()
        return True

    #--------------------------------------------------------------------------
    def _loadMusicFiles(self):

        musicFiles = []
        for root, dirs, files in os.walk(self['baseDir'], topdown=False):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in self._musicFileExts:
                    musicFiles.append(os.path.join(root, file))
            musicFiles.sort()
            self['musicFiles'] = musicFiles

    #--------------------------------------------------------------------------
    def getAlbumSize(self):
        totalSize = 0
        for musicFile in self['musicFiles']:
            totalSize += os.path.getsize(musicFile)
        return totalSize

    #--------------------------------------------------------------------------
    def __getitem__(self, key):
        if dict.has_key(self, key):
            return dict.__getitem__(self, key)
        return ''

    #--------------------------------------------------------------------------
    @staticmethod
    def sort(a, b):
        if a['artist'] == b['artist']:
            return cmp(a['album'], b['album'])
        return cmp(a['artist'], b['artist'])
        
#===============================================================================
def getAlbumDict(baseDir):

    albumDict = {}

    for root, dirs, files in os.walk(baseDir, topdown=False):
        if '.album' in files:
            albumInfo = AlbumInfo()
            albumInfo.load(root)

            if albumInfo['artist']:
                albumName = '%s - %s' % (albumInfo['artist'], albumInfo['album'])
            else:
                albumName = '%s' % (albumInfo['album'])

            if not len(albumInfo['musicFiles']):
                print 'Empty Album: %s' % (albumName)
                print '             %s' % (albumInfo['baseDir'])
                continue
            if albumName in albumDict:
                print 'Duplicate albums @ "%s", "%s"' % (albumDict[albumName]['baseDir'][len(baseDir):], root[len(baseDir):])
                continue
            albumDict[albumName] = albumInfo

    return albumDict


#===============================================================================
def readConfigFile(albumConfigFile):

    actionDict = {}
    if not os.path.isfile(albumConfigFile):
        return actionDict

    for line in open(albumConfigFile, 'rt'):
        line = line.split('#')[0]
        line = line.rstrip()
        if not line:
            continue

        if line.startswith('+ '):
            actionDict[line[2:]] = 'toSync'
        if line.startswith('- '):
            actionDict[line[2:]] = 'toRemove'

    return actionDict

#===============================================================================
def writeConfigFile(albumConfigFile, albumState):
    f = open(albumConfigFile, 'wt')
    
    albumStateKeys = albumState.keys()
    albumStateKeys.sort()
    
    for artistAlbum in albumStateKeys:
        if albumState[artistAlbum]['state'] == 'toSync':
            f.write('+ %s\n' % artistAlbum)
        elif albumState[artistAlbum]['state'] == 'toRemove':
            f.write('- %s\n' % artistAlbum)
        else:
            pass
    f.close()

#===============================================================================
def getActionDict(baseDir, syncToDir, albumDict, GUI):
    albumConfigFile = os.path.join(syncToDir, '.sync.config')
    configuredActionDict = readConfigFile(albumConfigFile)

    if not GUI:
        return configuredActionDict
    
    dirList = glob.glob(os.path.join(syncToDir,'*'))
    syncedAlbumList = []
    for entry in dirList:
        if os.path.isdir(entry):
            syncedAlbumList.append(os.path.split(entry)[-1])

    if GUI:
        albumState = {}
        for album in albumDict:
            albumState[album] = {'state': 'default'}

            if album in syncedAlbumList:
                albumState[album]['state'] = 'synced'
#            elif album in configuredActionDict:
#                albumState[album]['state'] = configuredActionDict[album]

        albumSelect = AlbumSelect()
        if not albumSelect.run(baseDir, syncToDir, albumDict, albumState):
            return {}

        writeConfigFile(albumConfigFile, albumState)

    return readConfigFile(albumConfigFile)

#===============================================================================
def syncAlbumFiles(baseDir, syncToDir, GUI=True):

    albumDict = getAlbumDict(baseDir)

    if not os.path.isdir(syncToDir):
        os.makedirs(syncToDir)

    actionDict = getActionDict(baseDir, syncToDir, albumDict, GUI)
    
    for albumName in actionDict:
        if not actionDict[albumName] == 'toRemove':
            continue

        destAlbumDir = os.path.join(syncToDir, albumName)
        print ' - Del: %s' % albumName
        shutil.rmtree(destAlbumDir)

    for albumName in actionDict:
        if not actionDict[albumName] == 'toSync':
            continue

        destAlbumDir = os.path.join(syncToDir, albumName)
        if not albumName in albumDict:
            print 'Can\'t find "%s" in source albums' % albumName
            continue

        if not os.path.isdir(destAlbumDir):
            os.makedirs(destAlbumDir)

        mediaFileList = albumDict[albumName]['musicFiles']

        def genDiscAndFilePath(fileList):
            discNo = 1
            basePath = None
            for filePath in fileList:
                p,f = os.path.split(filePath)
                if basePath == None:
                    basePath = p
                else:
                    if basePath != p:
                        discNo += 1
                        basePath = p
                yield discNo, filePath

        multiDisc = False
        for discNo, filePath in genDiscAndFilePath(mediaFileList):
            if discNo > 1:
                multiDisc = True
                break

        playlistFileName = os.path.join(destAlbumDir, '000.m3u')
        playlistFile = open(playlistFileName, 'wt')

        for discNo, filePath in genDiscAndFilePath(mediaFileList):
            fileName = os.path.split(filePath)[1]

            if multiDisc:
                fileName = '%02d.%s' % (discNo, fileName)

            src = os.path.join(albumDict[albumName]['baseDir'], filePath)
            dst = os.path.join(destAlbumDir, fileName)

            if os.path.exists(dst):
                dstStat = os.stat(dst)
                srcStat = os.stat(src)
                if srcStat.st_size == dstStat.st_size:
                    print " - Skip:  %s / %s" % (albumName, fileName)
                    continue              

            if not os.path.isfile(dst):
                print " - Sync:  %s / %s" % (albumName, fileName)
                #print '  ::s', src
                #print '  ::d', dst
                shutil.copy(src, dst)
            playlistFile.write('%s\n' % (fileName))
        playlistFile.close()

    print 'Done'


#==============================================================================
def syncPlayListFiles(baseDir, playListsDir):

    albumDict = getAlbumDict(baseDir)

    # Write playlist Files
    for albumName in albumDict:

        playListDir = playListsDir
        if albumDict[albumName]['artist']:
            playListDir = os.path.join(playListsDir, albumDict[albumName]['artist'])
        if not os.path.isdir(playListDir):
            os.makedirs(playListDir)
        playlistFileName = os.path.join(playListDir, albumName+'.m3u')

        f = open(playlistFileName, 'wt')
        f.write('# Autogenerated: %s\n' % (albumDict[albumName]['baseDir']))
        for musicFile in albumDict[albumName]['musicFiles']:
            f.write('%s\n' % (os.path.relpath(musicFile, playListDir)))
        f.close()

#==============================================================================
def main(argv):

    baseDir = os.getcwd()
    musicFileExts = ['.mp3', '.mpc', '.wma', 'wav']

    try:
        import getopt
        optList, optRemainder = getopt.gnu_getopt(argv[1:], 'h', ['help', 'to=', 'playlists=', 'gui'])
    except getopt.GetoptError, e:
        print __doc__
        print "! Syntax error: ",e
        return -1

    gui = False
    albumDir = None
    syncToDir = None
    playListsDir = None
 
    for n,v in optList:
        if n in ('--help', '-h'):
            print __doc__
            return 0
        if n in ('--to'):
            syncToDir = v
        if n in ('--playlists'):
            playListsDir = v
        if n in ('--gui'):
            gui = True

    if len (optRemainder):
        baseDir = optRemainder[0]

    if not os.path.isdir(baseDir):
        print __doc__
        return -1

    if playListsDir:
        syncPlayListFiles(baseDir, playListsDir)
        return 0

    if syncToDir:
        syncAlbumFiles(baseDir, syncToDir, gui)
        return 0

    print __doc__
    return -1

#-------------------------------------------------------------------------------
if __name__ == '__main__' or __name__ == sys.argv[0]:

    sys.exit(main(sys.argv))

#-------------------------------------------------------------------------------
# end
