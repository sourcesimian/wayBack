#!/usr/bin/env python

import Tkinter as tk
import os

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

#===============================================================================

