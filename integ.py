"""Perforce Integration utility

Author: Aravind Thangavelu
Date: October 10, 2008

Usage:

Functions:

"""
import sys, os, string, re, getopt, stat, subprocess, pipes
from optparse import OptionParser
from subprocess import Popen
from p4dir import findBranch

# grabs relevant changelist fields
class Changelist:
    def __init__(self, change, client=""):
        self.user = ""
        self.client = ""
        self.files = []
        self.job = []
        self.comment = ""
        self.num = change
        
        #print "In Changelist init"
        findJob = re.compile("^job(\d+) ")
        findUser = re.compile("^Change " + str(change) + " by (\S+)@(\S+) ")
        findFile = re.compile("^\.\.\.\s*(.+)\#(\d+) (\S+)")

        firstLine=True
        startComment=False
        
        #print "Before popen"
        try:
            #print "Before Popen " + str(change)
            chg = Popen(["p4", "describe", str(change)], stdout=subprocess.PIPE)
            #print "After Popen"
            #chg.wait()
            #print "after wait"
        except:
            sys.exit("Unable to find matching changelist " + str(change))
        for line in chg.stdout.readlines():
            #print line
            if line.find("Jobs fixed ...") != -1:
                #print "end comment"
                startComment = False
                #print "*" * 30
                #print self.comment
                #print "*" * 30
            if startComment:
                #print "adding comment"
                testline = line
                if testline.strip():
                    self.comment = self.comment + line
            sr = findUser.search(line)
            if sr:
                #print "found user"
                (self.user, self.client) = sr.groups()
            sr = findJob.search(line)
            if sr:
                #print "found job"
                self.job.append("job" + sr.group(1))
            sr = findFile.search(line)
            if sr:
                #print "before p4 where $$" + sr.group(1) + "$$ sr.grouup(1) " + sr.group(1)
                #where = Popen(["p4", "where", sr.group(1)], stdout=subprocess.PIPE)
                #where.wait()
                #clientLine = where.stdout.readline()
                #print "clientLine " + clientLine
                #clientFile = clientLine.split()[2]
                #print "clientFile " + clientFile
                #self.files.append((sr.group(1), clientFile, sr.group(2), sr.group(3)))
                self.files.append((sr.group(1), "", sr.group(2), sr.group(3)))
            if firstLine:
                #print "first line"
                firstLine = False
                startComment = True
        chg.wait()
        #print "After popen"
        
    def getJob(self):
        return self.job
    def getUser(self):
        return self.user
    def getClient(self):
        return self.client
    def getFiles(self):
        return self.files
    def getComment(self):
        return self.comment
    def getNum(self):
        return self.num
        
#check the list of checked in changelists
def p4changes(root, begin, end, xList, sxList):
    changes = []
    foundEnd = False
    
    #print "In p4changes: begin " + str(begin) + " end " + str(end)
    findChangelist = re.compile("^Change (\d+) ")
    root = root + "/..."
    print "Root: " + root
    try:
        src = Popen(["p4", "changes", root], stdout=subprocess.PIPE)
        #src.wait()
    except:
        sys.exit("Unable to get the changes in directory " + root)
    for line in src.stdout.readlines():
        #print line
        sr = findChangelist.search(line)
        if sr:
            curChange = sr.group(1);
            #print "Changelist: " + str(curChange)
            if foundEnd:
                if int(curChange) not in xList:
                    changes.append(int(curChange))
                else:
                    sxList.append(int(curChange))
            if (int(curChange) == end):
                #print "Found ending changelist " + str(end)
                foundEnd = True
                changes.append(int(curChange))
            if (int(curChange) == begin):
                #print "Found beginning changelist " + str(begin)
                #print changes
                #changes.sort()
                return changes
            if (int(curChange) < begin):
                print "Unable to find matching changelists"
                changes = []
                return changes
    src.wait()
                
def p4fixjob(change, curChangelist):
    jobs = curChangelist.getJob()
    for job in jobs:
        subprocess.call(["p4", "fix", "-c" + str(change), job])

def p4printjob(jobs):
    jobs.sort()
    jobsUnique = []
    for job in jobs:
        if job not in jobsUnique:
            jobsUnique.append(job)
            
    for job in jobsUnique:
        #print "job#" + job
        try:
            jobinfo = Popen(["p4", "job", "-o", job], stdout=subprocess.PIPE)
        except:
            sys.exit("Unable to get info for job " + job)
        
        startSummary = False
        jobSummary = ""
        for line in jobinfo.stdout.readlines():
            #print line
            if line.startswith("Description:"):
                #print "jobsummary " + jobSummary
                break
            elif startSummary:
                testline = line
                jobSummary = jobSummary + testline.strip()
            elif line.startswith("Summary:"):
                startSummary = True
        print str(job) + "\t" + jobSummary
        jobinfo.wait()

def p4addcommenthdr(change, destBranch):
    descStr = ""
    findDesc = re.compile("^Description:")
    desc = Popen(["p4", "change", "-o", str(change)], stdout=subprocess.PIPE)
    for line in desc.stdout.readlines():
        if not line.startswith("\tx\r\n") and not line.endswith("\tx\r\n"):
            descStr = descStr + line
        if findDesc.search(line):
            descStr = descStr + "\t" + destBranch + ": "
    desc.wait()

    desc = Popen(["p4", "change", "-i"], stdin=subprocess.PIPE)
    desc.communicate(descStr)
    desc.wait()
    
def p4addcomment(change, fromBranch, curChangelist, fullComment):
    descStr = ""
    findDesc = re.compile("^Description:")
    desc = Popen(["p4", "change", "-o", str(change)], stdout=subprocess.PIPE)
    #desc.wait()
    for line in desc.stdout.readlines():
        if not line.startswith("\tx\r\n") and not line.endswith("\tx\r\n"):
            descStr = descStr + line
        if findDesc.search(line):
            curChange = curChangelist.getNum()
            if fullComment:
                descStr = descStr + "\t" + "Integrating from " + fromBranch + " Changelist " + str(curChange) + " by " + curChangelist.getUser() + ":\n"
                comment = curChangelist.getComment()
                comment = comment.replace("\n", "\n\t")
                if comment[-1] == '\t':
                    comment = comment[:-1]
                descStr = descStr + "\t" + comment + "\n\n"
            else:
                descStr = descStr + "\t" + "Changelist " + str(curChange) + " by " + curChangelist.getUser() + "\n"
    desc.wait()
    #print "Changelist Description"
    #print descStr
    desc = Popen(["p4", "change", "-i"], stdin=subprocess.PIPE)
    #desc.wait()
    desc.communicate(descStr)
    desc.wait()
    #desc.wait()
    
def p4rangecomment(change, fromBranch, begin, end, xList):
    descStr = ""
    findDesc = re.compile("^Description:")
    desc = Popen(["p4", "change", "-o", str(change)], stdout=subprocess.PIPE)
    #desc.wait()
    for line in desc.stdout.readlines():
        descStr = descStr + line
        if findDesc.search(line):
            descStr = descStr + "\t" + "Integrating from " + fromBranch + " Changelist " + str(begin) + " to Changelist " + str(end) + "\n"
            if len(xList) > 0:
                descStr = descStr + "\t" + "Except"
                for x in xList:
                    descStr = descStr + " Changelist " + str(x)
                descStr = descStr + "\n"
            descStr = descStr + "\n"
    desc.wait()
    
    #print "Changelist Description"
    #print descStr
    desc = Popen(["p4", "change", "-i"], stdin=subprocess.PIPE)
    #desc.wait()
    desc.communicate(descStr)
    #desc.wait()
    desc.wait()
    
def p4integrate(change, curChangelist, sourceDepot, destDepot, acceptTheirs, previewOnly, forceInteg):
    #print "In p4integrate"
    resolveFiles =[]
    files = curChangelist.getFiles()
    for file in files:
        #print "file: " + str(file)
        if file[0].startswith(sourceDepot):
            #print "Valid File"
            srcFile = file[0] + "#" + file[2] + "," + file[2]
            destFile = file[0].replace(sourceDepot, destDepot)
            addToResolveFile = True
            #print "srcFile: " + srcFile
            #print "destFile: " + destFile
            #print "Starting integrate"
            if previewOnly:
                integ = Popen(["p4", "integrate", "-n", srcFile, destFile], stderr=subprocess.PIPE)
            elif forceInteg:
                integ = Popen(["p4", "integrate", "-c" + str(change), "-Dt", "-Ds", "-Di", "-f", "-i", srcFile, destFile], stderr=subprocess.PIPE)
            else:
                integ = Popen(["p4", "integrate", "-c" + str(change), srcFile, destFile], stderr=subprocess.PIPE)
            #integ.wait()
            integ.wait()
            for line in integ.stderr.readlines():
                print "line: " + line
                if line.find("already integrated") != -1:
                    #print "File: " + file[0] + " already integrated"
                    addToResolveFile = False
            if addToResolveFile:
                resolveFiles.append(destFile)
        else:
            print "File " + file[0] + "is not part of source depot " + sourceDepot
    
    if len(resolveFiles) == 0:
        return True
    
    if previewOnly:
        return False
        
    resolveFailed = False
    #print "Resolve Files: " + str(resolveFiles)
    #print "Starting resolve"
    if acceptTheirs:
        mergeType = "-at"
    else:
        mergeType = "-am"
    for file in resolveFiles:
        resolve = Popen(["p4", "resolve", mergeType, file], stdout=subprocess.PIPE)
        #resolve.wait()
        for line in resolve.stdout.readlines():
            if line.find("resolve ") != -1:
                print "Resolve failed for file: " + file
                resolveFailed = True
        resolve.wait()
        
    if resolveFailed:
        return False
    else:
        #print "Successfully resolved all files"
        return True
    
def p4newchange(client, user):
    findChange = re.compile("^Change (\d+)")
    changeStr = ""
    changeStr = changeStr + "\nChange:\tnew\n\n"
    changeStr = changeStr + "Client:\t" + client + "\n\n"
    changeStr = changeStr + "User:\t" + user + "\n\n"
    changeStr = changeStr + "Status:\tnew\n\n"
    changeStr = changeStr + "Description:\n\tx\n\n"
    changeStr = changeStr + "Files:\n\n"
    changelist = Popen(["p4", "change", "-i"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    #changelist.wait()
    (newchange, dontcare) = changelist.communicate(changeStr)
    #changelist.wait()
    changelist.wait()
    return findChange.search(newchange).group(1)
    
class ClientSpec:
    def __init__(self, client):
        self.view = ""
        self.rootDir = ""
        foundView = False
        cspec = Popen(["p4", "client", "-o", client], stdout=subprocess.PIPE)
        #cspec.wait()
        for line in cspec.stdout.readlines():
            if foundView and line.startswith("\t//depot/"):
                #print line
                sr = re.compile("^\t(\S+) (\S+)").search(line)
                if sr:
                    #print "View: " + sr.group(1)
                    self.view = sr.group(1).rstrip(".")
                    rootDir = sr.group(2)
                    rootDir = rootDir.rstrip(".")
                    findIndex = rootDir.find("/", 2)
                    findIndex = findIndex + 1
                    self.rootDir = rootDir[findIndex:]
                    #print "rootDir: " + self.rootDir
                    #print "view: " + self.view
                    break
            sr = re.compile("^View:").search(line)
            if sr:
                foundView = True
        cspec.wait()

    def getView(self):
        return self.view
    def getRootDir(self):
        return self.rootDir

def findCommonRoot(change):
    #print "In findCommonRoot"
    commonRoot = ""
    commonLength = 0
    changelist = Changelist(change)
    fileList = changelist.getFiles()
    for files in fileList:
        file = files[0]
        if commonLength == 0:
            commonRoot = file
            commonLength = len(commonRoot)
        elif len(file) < commonLength:
            commonRoot = file
            commonLength = len(commonRoot)
    
    print "commonRoot : " + commonRoot
    commonMatch = commonRoot.rfind("/")
    print "commonMatch : " + str(commonMatch)
    if commonMatch != -1:
        commonRoot = commonRoot[:commonMatch]
        commonLength = len(commonRoot)
        print "new commonRoot: " + commonRoot
    lenList = range(1, commonLength + 1)
    lenList.sort(reverse=True)
    for i in lenList:
        matchFound = True
        for files in fileList:
            file = files[0]
            matchStr = commonRoot[:i]
            if file.find(matchStr) != 0:
                matchFound = False
                break
        if matchFound:
            print str(i)
            print commonRoot[:i]
            return commonRoot[:i]
    return ""
    
def findSourceBranch(change, view, rootDir):
    print "View: " + view
    #print "In findSourceBranch"
    changelist = Changelist(change)
    #print "After Changelist"
    fileList = changelist.getFiles()
    file = fileList[0][0]
    print "File: " + file
    prefixList = []
    prefixList.append("//depot/Firmware/NG/SonicOS")
    prefixList.append("//depot/Firmware/SuperMassive/SonicOS/WorkSet")
    prefixList.append("//depot/Firmware/SuperMassive/SonicOS")
    prefixList.append("//depot/Firmware/Octeon/WorkSet")
    prefixList.append("//depot/Firmware/Octeon")
    prefixList.append("//depot/Firmware/ENH/WorkSet")
    prefixList.append("//depot/Firmware/ENH")
    prefixList.append("//depot/Firmware/STD/WorkSet")
    prefixList.append("//depot/Firmware/STD")
    
    prefix = "//depot/Firmware/NG/SonicOS/WorkSet/"
    if file.startswith(prefix):
        prefixLen = len(prefix) + 1
        fileMatch = file.find("/", prefixLen)
        if fileMatch != -1:
            fileMatch = file.find("/", fileMatch + 1)
            if fileMatch != -1:
                branch = file[:fileMatch]
                return branch
            else:
                print "Invalid file name " + file
        else:
            print "Invalid file name " + file
            
    for prefix in prefixList:
        if file.startswith(prefix):
            prefixLen = len(prefix) + 1
            fileMatch = file.find("/", prefixLen)
            if fileMatch != -1:
                #print "fileMatch: " + str(fileMatch)
                branch = file[:fileMatch]
                return branch
            else:
                print "Invalid file name " + file
                return ""
    print "Filename did not match any of the well know branches: " + str(prefixList)
    return ""
    
def p4getfiles(change, curChangelist, sourceDepot, destDepot, resolveFilelist):
    #print "In p4integrate"
    files = curChangelist.getFiles()
    for file in files:
        #print "file: " + str(file)
        if file[0].startswith(sourceDepot):
            #print "Valid File"
            foundMatch = False
            destFile = file[0].replace(sourceDepot, destDepot)
            for resolveFile in resolveFilelist:
                if resolveFile[0] == file[0] and int(resolveFile[2]) + 1 == int(file[2]):
                    #print "Found match: " + str(resolveFile)
                    resolveFile[2] = file[2]
                    #print "New version: " + str(resolveFile)
                    foundMatch = True
                    break
            if not foundMatch:
                #print "Adding file: " + file[0]
                resolveFilelist.append([file[0], file[2], file[2], destFile])
            #print "srcFile: " + srcFile
            #print "destFile: " + destFile
            #print "Starting integrate"
        else:
            print "File " + file[0] + "is not part of source depot " + sourceDepot

def p4resolve(change, resolveFilelist, acceptTheirs):
    for resolveFile in resolveFilelist:
        srcFile = resolveFile[0] + "#" + resolveFile[1] + "," + resolveFile[2]
        integ = Popen(["p4", "integrate", "-c" + str(change), srcFile, resolveFile[3]])
        #integ.wait()
        integ.wait()
    if acceptTheirs:
        mergeType = "-at"
    else:
        mergeType = "-am"
    for resolveFile in resolveFilelist:
        #print "Resolving file : " + resolveFile[3]
        resolve = Popen(["p4", "resolve", mergeType, resolveFile[3]], stdout=subprocess.PIPE)
        #print "After Popen"
        #resolve.wait()
        #print "After wait"
        for line in resolve.stdout.readlines():
            if line.find("resolve ") != -1:
                print "Resolve failed for file: " + str(resolveFile[3])
        resolve.wait()
    
def printDup(resolveFilelist):
    print "Duplicate file entries:"
    for i in range(len(resolveFilelist)):
        for j in range(len(resolveFilelist)):
            if i != j and resolveFilelist[i][0] == resolveFilelist[j][0]:
                print str(resolveFilelist[i])
                print str(resolveFilelist[j])
                

def main():
    #print "Main"
    usage = "usage: %prog [options] Changelist"
    parser = OptionParser(usage)
    parser.add_option("-b", type="int", dest="begin", help="Begining Changelist", default=0)
    parser.add_option("-c", type="string", dest="client", help="Client", default="")
    parser.add_option("-d", type="string", dest="destin", help="Destination Branch", default="")
    parser.add_option("-e", type="int", dest="end", help="Ending Changelist", default=0)
    parser.add_option("-f", action="store_true", dest="fullCom", default=False, help="Full Comment")
    parser.add_option("-i", action="store_true", dest="forceInteg", default=False, help="Force Integration")
    parser.add_option("-j", action="store_true", dest="jobs", default=False, help="List Jobs")
    parser.add_option("-l", action="store_true", dest="lineCom", default=False, help="Line Comment")
    parser.add_option("-n", action="store_true", dest="new", default=False, help="New Changelist")
    parser.add_option("-p", action="store_true", dest="preview", default=False, help="Preview Only")
    parser.add_option("-r", type="string", dest="root", help="Root", default="")
    parser.add_option("-s", type="string", dest="source", help="Source Branch", default="")
    parser.add_option("-t", action="store_true", dest="acceptTheirs", default=False, help="Accept Theirs")
    parser.add_option("-u", type="string", dest="user", help="User", default="")
    parser.add_option("-v", action="store_true", dest="verbose", default=False, help="Verbose")
    parser.add_option("-x", action="append", type="int", dest="xList", help="Exception List", default=[])
    (options, args) = parser.parse_args()
    #print "Begin: " + str(options.begin)
    #print "End: " + str(options.end)
    range = False
    print "Destination Branch: $" + options.destin + "$"
    if options.new:
        print "New Changelist"
    else:
        print "Existing Changelist"
        
    if options.client == "":
        parser.error("Clientspec not specified")
    cspec = ClientSpec(options.client)

    if len(args) != 1 and not options.new and not options.preview and not options.jobs:
        parser.error("Incorrect number of arguments")
    if options.begin == 0:
        parser.error("Beginning changelist not specified")
    if options.source == "":
        srcBranch = findSourceBranch(options.begin, cspec.getView(), cspec.getRootDir())
        if srcBranch == "":
            parser.error("Source branch not specified")
    else:
        srcBranch = options.source
    if options.destin == "" and not options.jobs:
        parser.error("Destination branch not specified")
        
    print "User: " + options.user
    print "Client: " + options.client
    print "Root: " + options.root
    print "Source Branch: " + srcBranch
    print "Dest Branch: " + options.destin
    print "Root Dir: " + cspec.getRootDir()
    
    if options.begin != 0 and options.end == 0:
        print "Changelist: " + str(options.begin)
    else:
        range = True
        print "Beginning Changelist: " + str(options.begin)
        print "Ending Changelist: " + str(options.end)
        
    if len(options.xList) > 0:
        print "Skip Changelists: " + str(options.xList)

    srcMatch = srcBranch.rfind("/")
    if srcMatch != -1:
        srcMatch = srcMatch + 1
        fromBranch = srcBranch[srcMatch:]
    else:
        fromBranch = srcBranch
        
    destBranch = options.destin
    dest = findBranch(options.destin, options.root)
        
    print "Destin branch: " + destBranch
    
    #print "Souce: " + srcBranch
    #print "Dest: " + dest
    destDepot = ""

    if not options.jobs:
        try:
            os.chdir(dest)
        except:
            sys.exit("Error: Directory " + dest + " not present")
                    
        where = Popen(["p4", "where"], stdout=subprocess.PIPE)
        #where.wait()
        p4Where = where.stdout.readline().split(" ")
        #print p4Where
        destDepot = p4Where[0].rstrip(".")
        #print "Dest Depot: " + destDepot
        where.wait()
    
    sourceDepot = srcBranch + "/"
    
    print "Source Depot: " + sourceDepot
    print "Dest Depot: " + destDepot
    jobList = []
    jobs = []
    
    #p4Where = os.popen("p4 where", "r").readline().split(" ")
    #print "p4Where: ",
    #print p4Where
    #root = p4Where[-1]
    #if root[-1] == '\n':
        #root = root[:-1]
    #print "Root: " + root

    if options.begin != 0 and options.end == 0:
        options.end = options.begin
    if options.begin != 0 and options.end != 0:
        #print "Beginning Changelist: " + str(options.begin)
        #print "Ending Changelist: " + str(options.end)
        sxList = []
        changes = p4changes(srcBranch, options.begin, options.end, options.xList, sxList)
        print "Matching Changelists: ",
        print changes
        if len(options.xList) > 0:
            print "Skipped Changelists: " + str(sxList)
            if len(options.xList) != len(sxList):
                print "Not all changelists in skip list were skipped"
                sys.exit("Skip changelists failed")
                
        if changes == []:
            print "Unable to find matching changelist for begin " + str(options.begin) + " and end " + str(options.end) + " in branch " + srcBranch
        else:
            if not options.new and not options.preview and not options.jobs:
                change = int(args[0])
                print "Merge Changelist: " + str(change)
            elif not options.preview and not options.jobs:
                change = p4newchange(options.client, options.user)
                if change == 0:
                    sys.exit("Unable to create new changelist")
                print "New Merge Changelist: " + str(change)
            else:
                change = ""
            
            changes.sort()
            resolveFilelist = []
            fullComment = True
            if not range and options.lineCom:
                fullComment = False
            elif range and not options.fullCom:
                fullComment = False
            
            for curChange in changes:
                curChangelist = Changelist(curChange)
                if options.jobs:
                    jobs += curChangelist.getJob()
                else:
                    if not options.preview:
                        print "Adding DTS from Changelist " + str(curChange)
                        p4fixjob(change, curChangelist)
                        print "Adding comments from Changelist " + str(curChange)
                        p4addcomment(change, srcBranch, curChangelist, fullComment)
                    if options.preview or not range:
                        if not options.preview:
                            p4addcommenthdr(change, destBranch)
                        #print "Integrating files from Changelist " + str(curChange)
                        if not p4integrate(change, curChangelist, sourceDepot, destDepot, options.acceptTheirs, options.preview, options.forceInteg):
                            if options.preview:
                                print "Changelist " + str(curChange) + " NOT integrated"
                            else:
                                print "Resolve Failed for changelist " + str(curChange)
                                sys.exit("Resolve Failed")
                        elif options.preview:
                            print "Changelist " + str(curChange) + " already integrated"
                    else:
                        print "Getting files from Changelist " + str(curChange)
                        p4getfiles(change, curChangelist, sourceDepot, destDepot, resolveFilelist)
            if range:
                if not options.preview and not options.jobs:
                    p4rangecomment(change, srcBranch, options.begin, options.end, sxList)
                    p4addcommenthdr(change, destBranch)
                    #print "Resolve File List"
                    #for files in resolveFilelist:
                    #print str(files)
                    p4resolve(change, resolveFilelist, options.acceptTheirs)
                    #printDup(resolveFilelist)
                elif options.jobs:
                    #print str(jobs)
                    p4printjob(jobs)

if __name__ == '__main__':
    main()

