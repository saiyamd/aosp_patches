#!/usr/bin/python

"""
Script to generate patches from AOSP source.

This script compares base commit from manifest.xml of each project
against head commit. If head commit is different from the
manifest.xml, it generates the patches, create directory in provided
output patch directory and moves those patches.

Test it on your repo and suggest edit.

XXX: Beware of "rmtree"
"""

import os
import git
import xml.etree.ElementTree as ET
import shutil
import sys
import getopt
import time
import logging

sys.tracebacklimit = 0
logfile=os.getcwd()+'/patch_logfile.log'

g_argv=''
g_abs_patch_dir_path=''
g_abs_aosp_caf_path=''
g_loglevel=logging.INFO

# Add custom project path and base commit id
# Also enable block of code dealing with custom_project below
#custom_project = {
#	"device/oem/dev_name": "--root",
#}

def config_logfile():
	# generate log file with provided filename
	logging.basicConfig(level=g_loglevel, filename=logfile, filemode="a", \
	format="%(asctime)-15s %(levelname)-8s %(message)s")

	# relay log messages on stdout as well
	stdoutlog = logging.getLogger()
	stdoutlog.setLevel(g_loglevel)
	handler = logging.StreamHandler(sys.stdout)
	handler.setLevel(g_loglevel)
	formatter = logging.Formatter("%(asctime)-15s %(levelname)-8s %(message)s")
	handler.setFormatter(formatter)
	stdoutlog.addHandler(handler)

def os_system_cmd(cmd):
	logging.info("cmd: %s"%(cmd))
	#os.system(cmd)
	os.system(cmd+' > /dev/null')

def git_format_patch(project_dir, commit_id, cwdpath):
	#print "git format-path in " + project_dir
	cmd = 'git format-patch '+ commit_id
	os_system_cmd(cmd)

def generate_patch_files(project_dir, project_commit_id):
	#print project_dir, project_commit_id
	project_name = os.path.join(g_abs_aosp_caf_path, project_dir)
	os.chdir(project_name)

	repo = git.Repo('./')
	head_commit = str(repo.head.commit.hexsha)

	#print head_commit
	#print project_commit_id

	if (head_commit == project_commit_id) :
		logging.info("No change in %s"%(project_name))
	else:
		logging.info("%s updated!!"%(project_name))
		git_format_patch(project_name, project_commit_id, os.getcwd())
		create_proj_dir_in_patch_dir = os.path.join(g_abs_patch_dir_path, project_dir)

		#if output patch directory exist, delete it
		if(os.path.isdir(create_proj_dir_in_patch_dir)):
			shutil.rmtree(create_proj_dir_in_patch_dir, ignore_errors=True)

		os.makedirs(create_proj_dir_in_patch_dir, 0775)

		cmd = 'mv '+project_name+'/*.patch '+create_proj_dir_in_patch_dir
		os_system_cmd(cmd)
		
	logging.info("")

def create_patches(aosp_caf_path, out_patch_dir):
	global g_abs_aosp_caf_path
	g_abs_aosp_caf_path = os.path.abspath(aosp_caf_path)
	global g_abs_patch_dir_path
	g_abs_patch_dir_path = os.path.abspath(out_patch_dir)
	abs_exec_path = os.path.abspath(os.getcwd())

	logging.info("== AOSP CAF: " + g_abs_aosp_caf_path)
	logging.info("== Patch out path: " + g_abs_patch_dir_path)
	logging.info("== Script execution path: " + abs_exec_path)

	#print g_abs_aosp_caf_path,g_abs_patch_dir_path, abs_exec_path

	manifest_path = os.path.join(g_abs_aosp_caf_path, '.repo/manifest.xml')

	isPathValid(manifest_path, 'M')
	logging.info("== Using: " + manifest_path)

	# Parse manifest.xml
	root = ET.parse(manifest_path)
	for type_tag in root.findall('project'):
		project_commit_id = type_tag.get('revision')
		project_dir = type_tag.get('name')

		logging.info("---------------------------------------------------------")
		#print os.path.isdir(os.path.join(g_abs_aosp_caf_path, project_dir))
		if not (os.path.isdir(os.path.join(g_abs_aosp_caf_path,project_dir))):
			logging.info("Project directory %s doesn't exist"%(project_dir))
			logging.info("Checking for relative path from manifest.xml")
			project_dir = type_tag.get('path')
			#print os.path.isdir(os.path.join(g_abs_aosp_caf_path, project_dir))
			if not (os.path.isdir(os.path.join(g_abs_aosp_caf_path,project_dir))):
				logging.info("Project at relative path %s doesn't exist"%(project_dir))
				continue

		logging.debug("project dir:%s, commit_id in manifest.xml:%s"%(project_dir,project_commit_id))
		project_name = os.path.join(g_abs_aosp_caf_path, project_dir)
		generate_patch_files(project_dir, project_commit_id)
		logging.info("---------------------------------------------------------")
		os.chdir(abs_exec_path)

	# Parse custom projects
	#for project_name, commit_id in custom_project.items():
	#	logging.info("---------------------------------------------------------")
	#	#print project_name
	#	#print commit_id
	#	generate_patch_files(project_name, commit_id)
	#	logging.info("---------------------------------------------------------")
	#	os.chdir(abs_exec_path)

def usage(argv):
    buf = '\nUsage:' + argv[0]+ '\n' + \
    '[OPTIONS] :\n'\
    '\t -C \t<AOSP source path>\n' + \
    '\t -P \t<Output patch directory>\n'
    '\t -h --help display this help and exit\n'
    print buf
    sys.exit(0)

def isPathValid(path, arg):
	try:
		os.stat(path)
	except:
		if (arg == 'P') :
			os.mkdir(path)
			return path

		if (arg == 'M') :
			print "manifest.xml is not found at %s"%(path)
			sys.exit(1)

		print "Invalid path %s"%(path)
		usage(g_argv)

	return path

def parseCmdLine(argv):
	aosp_caf_path = ''
	out_path_dir = ''

	try:
		opts, args = getopt.getopt(argv[1:],"hC:P:", ["help"])
	except getopt.GetoptError:
		usage(argv)

	for opt, arg in opts:
		#print opt, arg
		if((opt == "-h") or (opt == "--help")):
			usage(argv)
		elif(opt == "-C"):
			aosp_caf_path = isPathValid(arg.strip(), 'C')
		elif(opt == "-P"):
			out_path_dir = isPathValid(arg.strip(), 'P')

	if aosp_caf_path == '' or out_path_dir == '':
		print "Argument missing"
		usage(argv)

	return aosp_caf_path, out_path_dir

def main(argv):
	global g_argv
	g_argv = argv
	if len(sys.argv) > 1 :

		# Config logfile/loglevel
		config_logfile()

		# Parse cmdline
		aosp_caf_path, out_patch_dir = parseCmdLine(argv)
		
		logging.info("== Start Time: %s =="%(time.asctime(time.localtime(time.time()))))
		create_patches(aosp_caf_path, out_patch_dir)
		logging.info("== End Time: %s =="%(time.asctime(time.localtime(time.time()))))
		sys.exit(0)
	else :
		usage(argv)

# Entry Point
if __name__ == '__main__':
	main(sys.argv)
