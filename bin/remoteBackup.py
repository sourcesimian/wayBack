#!/usr/bin/env python

"""\
RemoteBackup
- Send files away by SMTP (TLS) to a predefined mailbox as attachments.

Usage: RemoteBackup [files ...]

Switches: --help, -h
          --recursive, -R
          --verbose, -v
          --dryrun
          --comment,-c=
          --lt,--gt=<size>   size in bytes or with a k or M suffix
          --acceptTypes=<type list>   eg: --acceptTypes=png,gif,jpg
          --ignoreTypes=<type list>   eg: --ignoreTypes=bin,dat
          --ignoreDirs=<dir list>     eg: --ignoreDirs=.cache,Temp
          --password=<password>
          --user=<username>
Experimental:
          --zip,-z  Zips up recursive directories - but leaves seperate files
                    (the trouble is windows drive letters ...)
          --zipPass=<password> (though ZIP encryption is not yet supported)

Notes: This tool is configured by 'RemoteBackp_config.py' found in the same
       location as the RemoteBackup utility (thus it is terribly portable)
"""


import remoteBackup_config

import sys
import os

import smtplib
import mimetypes
from email import Encoders
#from email.Message import Message
from email.MIMEAudio import MIMEAudio
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.MIMEImage import MIMEImage
from email.MIMEText import MIMEText

import time
import glob
import zipfile

googleIllegalExts = ['.com', '.exe', '.bat', '.cpl', '.scr', '.sys', '.vxd', '.zip']  # zip inside zip appears to be a no-no
googleRemovableExt = '.RemoveThisExt'

#------------------------------------------------------------------------------
outLog = ''

def writeStdErr(msg):
    global outLog    
    outLog += '! ' + msg
    sys.stderr.write('! ' + msg)

def writeStdOut(msg):
    global outLog    
    outLog += msg
    sys.stdout.write(msg)

#------------------------------------------------------------------------------
def sendMail(server, fromAddr, toAddrs, subject, parts):
    """
    sendMessage(server, fromAddr, toAddrs, subject, parts)
    
    eg:
        server = {
            'addr': 'smtp.address.com',
            'user': 'username',
            'pass': 'password'
        }
        
        fromAddr = 'Joe Bloggs <joe.b@nowhere.com>'
        
        toAddrs = [
            'Katy Cat <k.cat@outthere.com>',
            ...
        ]
        
        subject = 'The Subject of this Message'
        
        parts = [
            {'type': maintype, 'subtype': subtype, 'filename': 'att.zip', 'content': content },
            ...
        ]
    """

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['To'] = ", ".join(toAddrs)
    msg['From'] = fromAddr
    msg.preamble = 'This is a multi-part MIME message.\n'
    # To guarantee the message ends with a newline
    msg.epilogue = ''  # To guarantee the message ends with a newline

    for p in parts:
        if p['type'] == 'text':
            # Note: we should handle calculating the charset
            part = MIMEText(p['content'], p['subtype'])
        elif p['type'] == 'image':
            part = MIMEImage(p['content'], p['subtype'])
        elif p['type'] == 'audio':
            part = MIMEAudio(p['content'], p['subtype'])
        else:
            part = MIMEBase(p['type'], p['subtype'])
            part.set_payload(p['content'])
            # Encode the payload using Base64
            Encoders.encode_base64(part)  # Encode the payload using Base64

        if p != parts[0]:
            part.add_header('Content-Disposition', 'attachment', filename=p['filename'])
        msg.attach(part)

    smtp = smtplib.SMTP(server['addr'], server['port'])

    smtp.set_debuglevel(0)

    smtp.ehlo()
    smtp.starttls()
    smtp.ehlo()    
    try:    
        smtp.login(server['user'], server['pass'])
    except smtplib.SMTPAuthenticationError:
        writeStdErr("Authentication error for '%s' [%s]\n" % (server['user'], server['addr']))
        return 1
    
    writeStdOut("Sending message ...\n")

    smtp.sendmail(fromAddr, toAddrs, msg.as_string())
    smtp.quit()

    writeStdOut('Success\n')
    return 0

#------------------------------------------------------------------------------
def main(argv):
    global outLog
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S %z (%Z)")

    outLog = timestamp + '\n'

    if len(argv) == 1:
        print __doc__
        return -1
    
    try:
        import getopt
        optList, optRemainder = getopt.gnu_getopt(argv[1:], 'hRvc:z', ['help', 'recursive',
                                                                      'verbose', 'dryrun',
                                                                      'comment=', 'lt=', 'gt=',
                                                                      'zip', 'zipPass='
                                                                      'acceptTypes=', 'ignoreTypes=',
                                                                      'ignoreDirs=',
                                                                      'noinfo',
                                                                      'user=', 'password=',
                                                                      'to='])
    except getopt.GetoptError, e:
        print __doc__
        print "! Syntax error: ",e
        return -1

    fromAddr = None
    toAddrs = None
    server = {}
    
    doRecursive = False
    doVerbose = False
    doDryRun = False
    comment = None
    ltSize = None
    gtSize = None
    doZip = False
    zipPass = None
    acceptTypeList = []
    ignoreTypeList = []
    ignoreDirList = []
    inputPassword = None
    inputUserName = None
    noInfo = False
    inputToAddrs = []
 
    def resolveSize(size):
        if size[-1] == 'k': 
            mul = 1024
            sz = size[:-1]
        elif size[-1] == 'M':
            mul = (1024 * 1024)
            sz = size[:-1]
        else:
            sz = size
            mul = 1
        try:        
            s = int(sz) * mul
        except:
            writeStdErr('Could not interpret \'size\' argument "%s"\n' % size)
            sys.exit(-4)
        return s

    for n,v in optList:
        if n == '--help' or n == '-h':
            print __doc__
            return 0
        if n == '--recursive' or n == '-R':
            doRecursive = True
        if n == '--verbose' or n == '-v':
            doVerbose = True
        if n == '--dryrun':
            doDryRun = True
        if n == '--comment' or n == '-c':
            comment = v
        if n == '--lt':
            ltSize = resolveSize(v)
        if n == '--gt':
            gtSize = resolveSize(v)
        if n == '--zip' or n == '-z':
            doZip = True
        if n == '--zipPass':
            zipPass = vgetopt.GetoptError
        if n == '-acceptTypes':
            acceptTypeList = v.split(',')
        if n == '--ignoreTypes':
            ignoreTypeList = v.split(',')
        if n == '--ignoreDirs':
            ignoreDirList = v.split(',')
        if n == '--password':
            inputPassword = v
        if n == '--user':
            inputUserName = v
        if n == '--noinfo':
            noInfo = True
        if n == '--to':
            inputToAddrs.append(v)

    if len(optRemainder) > 0:
        argFiles = optRemainder

    # * Do this now - to allow for any user prompting if necessary
    if not doDryRun:    
        fromAddr = remoteBackup_config.getFromAddr()
        if inputToAddrs:
            toAddrs = inputToAddrs
        else:
            toAddrs  = remoteBackup_config.getToAddrs()
        
        server = {}
        if inputUserName:
            server['user'] = inputUserName
            if not inputToAddrs:
                if not '@' in inputUserName:
                    print "! require --user as an email address or at least one --to"
                    return -1
                toAddrs = [inputUserName]
        if inputPassword:
            server['pass'] = inputPassword
        server = remoteBackup_config.getServer(server)

    # * Generate file and zip lists    
    fileList = []
    zipLists = []
    totalSize = 0

    def addFile(fileList, file, acceptTypeList, ignoreTypeList):
        try:        
            if not os.path.isfile(file):
                writeStdErr('Skip (can\'t open): %s\n' % file)
                return 0            
            size = os.path.getsize(file)
            ext = os.path.splitext(file)[1][1:].lower()
            if acceptTypeList and not ext in acceptTypeList:
                return 0
            if ignoreTypeList and ext in ignoreTypeList:
                return 0
            if ltSize and size >= ltSize:
                writeStdErr('Skip (too big): %s\n' % file)
                return 0
            if gtSize and size <= gtSize:
                writeStdErr('Skip (too small): %s\n' % file)
                return 0
            fh = open(file, 'rb')
            fh.close()
            fileList.append(file)
            return size
        except:
            writeStdErr('Skip (can\'t open): %s\n' % file)
            return 0


    ignoredDirs = []
    def ignoreDir(base, fileName, ignoreDirList, ignoredDirs):
        for ignoreDirName in ignoreDirList:
            ignoreDirFullName = os.path.join(globFile, ignoreDirName)                         
            if fileName.startswith(ignoreDirFullName):
                if not ignoreDirFullName in ignoredDirs:
                    ignoredDirs.append(ignoreDirFullName)
                    writeStdErr('Ignoring dir: %s\n' % ignoreDirFullName)
                return True
        return False        
    

    for argFile in argFiles:
        globList = glob.glob(argFile)
        for globFile in globList:
            if os.path.isdir(globFile):
                if doRecursive:
                    zipList = []
                    for root, dirs, files in os.walk(globFile, topdown=False):
                        for name in files:
                            if ignoreDir(globFile, os.path.join(root, name), ignoreDirList, ignoredDirs):
                                continue
                            if doZip:
                                totalSize += addFile(zipList, os.path.join(root, name), acceptTypeList, ignoreTypeList)
                            else:
                                totalSize += addFile(fileList, os.path.join(root, name), acceptTypeList, ignoreTypeList)
                    if zipList:
                        zipLists.append(zipList)
                else:
                    writeStdErr('Ignoring "%s" as it is a DIR and -R not specified\n' % globFile)
            if os.path.isfile(globFile):
                totalSize += addFile(fileList, globFile, acceptTypeList, ignoreTypeList)

    if not fileList and not zipLists:
        writeStdErr('No files to backup\n')
        return -3

    # * Generate message subject and body text
    subject = 'BACKUP: %s' % (timestamp)

    bodyText =  "Remote backup:\n"
    if not noInfo:
    #    bodyText += " IP   - %s\n"
        bodyText += " OS   - %s\n" % sys.platform
        import socket
        bodyText += " Host - %s\n" % socket.gethostname()
        bodyText += " Time - %s\n" % timestamp
        bodyText += " Pwd  - %s\n" % os.getcwd()
        bodyText += " Cli  - %s\n" % ' '.join(argv)

    if comment:
        bodyText += "\nComment:\n" + comment + "\n"

    bodyText += "\nFile list:\n"

    for file in fileList:
        bodyText += ' [att] %s\n' % (os.path.abspath(file))
    if fileList:
        bodyText += '\n'

    for i in xrange(len(zipLists)):
        for file in zipLists[i]:
            bodyText += ' [z%d] %s\n' % (i, os.path.abspath(file))
        bodyText += '\n'

    if doVerbose:
        writeStdOut('\n')    
        writeStdOut(subject+'\n')
        writeStdOut('\n')    
        writeStdOut(bodyText+'\n')

    writeStdOut('Maximum Attachment Size: %d\n' % totalSize )

    if doDryRun:
        writeStdOut('This is a dryrun - so all done!\n')    
        return 0    


    if totalSize >  remoteBackup_config.totalSizeLimit:
        writeStdErr('Total attachment size is greater than limit of %d\n' % remoteBackup_config.totalSizeLimit)
        writeStdErr('Use --verbose --dryrun to see a list of files included\n')
        return -2


    def modifyAttachmentFileName(name):
        if server['addr'] == 'smtp.gmail.com':
            if os.path.splitext(name)[1].lower() in googleIllegalExts:
                return name+googleRemovableExt
        return name


    # * Generate message parts
    parts = []

    # * Add body text    
    parts.append({ 'type': 'text',
                   'subtype': 'plain',
                   'filename': None,
                   'content': bodyText
                 })

    # * Add normal attachments as parts - auto detect MIME types
    if fileList: writeStdOut('Adding attachments ...\n')    
    for file in fileList:
        ctype, encoding = mimetypes.guess_type(file)
        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed), so
            # use a generic bag-of-bits type.
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)

        fp = open(file, 'rb')
        content = fp.read()
        fp.close()

        attFilename = os.path.split(file)[1]
        attFilename = modifyAttachmentFileName(attFilename)

        parts.append({ 'type': maintype,
                       'subtype': subtype,
                       'filename': attFilename,
                       'content': content
                       })

    # * Add zip attachments as parts    
    if zipLists: writeStdOut('Zipping and Adding attachments ...\n')    
    for i in xrange(len(zipLists)):
        tmpZip = os.tmpfile()
        zipFile = zipfile.ZipFile(tmpZip, 'w')

        for file in zipLists[i]:
            arcName = modifyAttachmentFileName(file)
            zipFile.write(file, arcName)
        if zipPass:        
            zipFile.setpassword(zipPass)
        zipFile.close()
        
        tmpZip.flush()            
        tmpZip.seek(0)        
        content = tmpZip.read()
        tmpZip.close()

        parts.append({ 'type': 'application',
                       'subtype': 'zip',
                       'filename': 'z%d.zip' % i,
                       'content': content
                       })

    # * Add session log
    writeStdOut('Preparing to send ...\n')    
    parts.append({ 'type': 'text',
                   'subtype': 'plain',
                   'filename': 'RemoteBackup_log.txt',
                   'content': outLog
                 })

    # * Send the mail for all its parts    
    return sendMail(server,
        fromAddr,
        toAddrs,
        subject,
        parts)

#-------------------------------------------------------------------------------
if __name__ == '__main__' or __name__ == sys.argv[0]:

    sys.exit(main(sys.argv))

#-------------------------------------------------------------------------------
# end
