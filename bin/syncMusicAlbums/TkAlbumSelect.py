#!/usr/bin/env python

import Tkinter as tk
from TkPathSelector import *
from AlbumInfo import *

_MAX_ROWS = 30

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

