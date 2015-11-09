#!/usr/bin/env python

import os

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

