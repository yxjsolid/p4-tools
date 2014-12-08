import os
import sys
import subprocess
import pipes
from subprocess import Popen

def findBranchNg(branch, rootpath):
	branchpath = ''
	finddir = '//depot/Firmware/NG/SonicOS/*'
	#print finddir
	p4dirs = Popen(['p4', 'dirs', finddir], stdout=subprocess.PIPE, cwd=rootpath)
	dirs = p4dirs.stdout.read()
	p4dirs.wait()
	dirlist = dirs.split()

	foundBranch = False
	for dir in dirlist:
		#print dir
		index = dir.rfind('/')
		if branch == dir[index + 1 :]:
			foundBranch = True
			branchpath = rootpath + dir[19:]
			#print 'Found branch: ' + dir
			#print 'Branch path: ' + branchpath
			break

	if not foundBranch:
		finddir = '//depot/Firmware/NG/SonicOS/WorkSet/*/*'
		#print finddir
		p4dirs = Popen(['p4', 'dirs', finddir], stdout=subprocess.PIPE, cwd=rootpath)
		dirs = p4dirs.stdout.read()
		p4dirs.wait()
		dirlist = dirs.split()
	
		for dir in dirlist:
			#print dir
			index = dir.rfind('/')
			if branch == dir[index + 1 :]:
				foundBranch = True
				branchpath = rootpath + dir[19:]
				#print 'Found branch: ' + dir
				#print 'Branch path: ' + branchpath
				break
		
	return branchpath

def findBranchSuperMassive(branch, rootpath):
	branchpath = ''
	finddir = '//depot/Firmware/SuperMassive/SonicOS/*'
	#print finddir
	p4dirs = Popen(['p4', 'dirs', finddir], stdout=subprocess.PIPE, cwd=rootpath)
	dirs = p4dirs.stdout.read()
	p4dirs.wait()
	dirlist = dirs.split()
	
	foundBranch = False
	for dir in dirlist:
		#print dir
		index = dir.rfind('/')
		if branch == dir[index + 1 :]:
			foundBranch = True
			branchpath = rootpath + dir[29:]
			#print 'Found branch: ' + dir
			#print 'Branch path: ' + branchpath
			break

	if not foundBranch:
		finddir = '//depot/Firmware/SuperMassive/SonicOS/WorkSet/*'
		#print finddir
		p4dirs = Popen(['p4', 'dirs', finddir], stdout=subprocess.PIPE, cwd=rootpath)
		dirs = p4dirs.stdout.read()
		p4dirs.wait()
		dirlist = dirs.split()
	
		for dir in dirlist:
			#print dir
			index = dir.rfind('/')
			if branch == dir[index + 1 :]:
				foundBranch = True
				branchpath = rootpath + dir[29:]
				#print 'Found branch: ' + dir
				#print 'Branch path: ' + branchpath
				break
		
	return branchpath

def findBranchOcteon(branch, rootpath):
	branchpath = ''
	finddir = '//depot/Firmware/Octeon/*'
	#print finddir
	p4dirs = Popen(['p4', 'dirs', finddir], stdout=subprocess.PIPE, cwd=rootpath)
	dirs = p4dirs.stdout.read()
	p4dirs.wait()
	dirlist = dirs.split()
	
	foundBranch = False
	for dir in dirlist:
		#print dir
		index = dir.rfind('/')
		if branch == dir[index + 1 :]:
			foundBranch = True
			branchpath = rootpath + dir[23:]
			#print 'Found branch: ' + dir
			#print 'Branch path: ' + branchpath
			break

	if not foundBranch:
		finddir = '//depot/Firmware/Octeon/WorkSet/*'
		p4dirs = Popen(['p4', 'dirs', finddir], stdout=subprocess.PIPE, cwd=rootpath)
		dirs = p4dirs.stdout.read()
		p4dirs.wait()
		dirlist = dirs.split()

		for dir in dirlist:
			#print dir
			index = dir.rfind('/')
			if branch == dir[index + 1 :]:
				foundBranch = True
				branchpath = rootpath + dir[23:]
				#print 'Found branch: ' + dir
				#print 'Branch path: ' + branchpath
				break
		
	return branchpath

def findBranch(branch, rootdir):
	#print 'rootdir ' + rootdir
	branchpath = ''
	finddir = rootdir + '/*'
	p4dirs = Popen(['p4', 'dirs', finddir], stdout=subprocess.PIPE, cwd=rootdir)
	dirs = p4dirs.stdout.read()
	p4dirs.wait()
	#p4dirs.close()
	dirlist = dirs.split()
	rootpath = rootdir 
	#print dirs

	for dir in dirlist:
		if dir == '//depot':
			finddir = rootdir + '/depot/Firmware/*'
			p4dirs = Popen(['p4', 'dirs', finddir], stdout=subprocess.PIPE, cwd=rootdir)
			dirs = p4dirs.stdout.read()
			p4dirs.wait()
			#print p4dirs
			rootpath = rootpath + '/depot/Firmware'
		elif dir == '//depot/Firmware':
			finddir = rootdir + '/Firmware/*'
			p4dirs = Popen(['p4', 'dirs', finddir], stdout=subprocess.PIPE, cwd=rootdir)
			dirs = p4dirs.stdout.read()
			p4dirs.wait()
			#print p4dirs
			rootpath = rootpath + '/Firmware'

	dirlist = dirs.split()
	#print dirlist
	for dir in dirlist:
		#print 'Dir: ' + dir
		if (dir == '//depot/Firmware/NG') or (dir == '//depot/Firmware/Octeon') or (dir == '//depot/Firmware/SuperMassive'):
			if os.path.exists(rootpath + '/NG'):
				branchpath = findBranchNg(branch, rootpath + '/NG')
			if branchpath == '' and os.path.exists(rootpath + '/SuperMassive'):
				branchpath = findBranchSuperMassive(branch, rootpath + '/SuperMassive')
			if branchpath == '' and os.path.exists(rootpath + '/Octeon'):
				branchpath = findBranchOcteon(branch, rootpath + '/Octeon')
		elif dir.startswith('//depot/Firmware/NG/'):
			branchpath = findBranchNg(branch, rootpath)
		elif dir.startswith('//depot/Firmware/SuperMassive/'):
			branchpath = findBranchSuperMassive(branch, rootpath)
		elif dir.startswith('//depot/Firmware/Octeon/'):
			branchpath = findBranchOcteon(branch, rootpath)

		if branchpath != '':
			break

	return branchpath

