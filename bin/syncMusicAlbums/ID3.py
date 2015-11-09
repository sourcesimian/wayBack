#!/usr/bin/env python

import os
import sys
sys.path.append( os.path.split(__file__)[0] )
sys.path.append( os.path.join(os.path.split(__file__)[0], 'mutagen') )

#===============================================================================
class ID3:

    def __init__(self, filename):
      import mutagen.mp3
      import mutagen.easyid3
      import mutagen.id3
#      from mutagen.mp3 import MP3
#      print EasyID3.valid_keys.keys()

      self.filename = filename
      self.audio = None
        
      self.audio = mutagen.mp3.MP3( filename, ID3=mutagen.easyid3.EasyID3 )

      if self.audio.tags == None:
        self.audio.add_tags(ID3=mutagen.easyid3.EasyID3)
    
    def save(self):
      if self.audio:
        self.audio.save()

    def getTitle(self):
      title = ''
      if 'title' in self.audio:
        title = self.audio['title']
      return title

    def setTitle(self, title):
      self.audio['title'] = title

    def getArtist(self):
      artist = ''
      if 'artist' in self.audio:
        artist = self.audio['artist']
      return artist

    def setArtist(self, artist):
      self.audio['artist'] = artist

    def getAlbum(self):
      album = ''
      if 'album' in self.audio:
        album = self.audio['album']
      return album

    def setAlbum(self, album):
      self.audio['album'] = album

    def getTrackNumber(self):
      trackNo = None
      if 'tracknumber' in self.audio:
        trackNo = int(self.audio['tracknumber'][0].split('/')[0])
      return trackNo

    def setTrackNumber(self, trackNumber, trackTotal):
      self.audio['tracknumber'] = '%d/%d' % (trackNumber, trackTotal)

    def __str__(self):


      s  = 'ID3 TAG: %s\n' % self.filename
      s += " - Artist: %s\n" % self.getArtist()
      s += " - Album : %s\n" % self.getAlbum()
      s += " - Track : %d\n" % self.getTrackNo()
      s += " - Title : %s\n" % self.getTitle()

      return s


#===============================================================================
def test(argv):

    try:
        import getopt
        optList, optRemainder = getopt.gnu_getopt(argv[1:], 'h', ['help', 'artist=', 'album='])
    except getopt.GetoptError, e:
        print __doc__
        print "! Syntax error: ",e
        return -1
 
    filePath = None
    artist = None
    album = None

    if len(optRemainder) > 0:
      filePaths = optRemainder

    for n,v in optList:
        if n in ('--artist'):
          artist = v
        if n in ('--album'):
          album = v

    for filePath in filePaths:
      print '* '+filePath
      if not artist and not album:
       id3 = ID3(filePath)
       print id3

      else:
          id3 = ID3(filePath)
          if album:
            id3.setAlbum(album)
          if artist:
            id3.setArtist(artist)
          id3.save()


    return 0

#-------------------------------------------------------------------------------
if __name__ == '__main__' or __name__ == sys.argv[0]:
    sys.exit(test(sys.argv))

#-------------------------------------------------------------------------------
# end
