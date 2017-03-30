#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

from subprocess import Popen,call
import commands,os, sys,shutil
import urllib

from config import *

def exe(cmd):
	print cmd
	res=commands.getoutput(cmd)
	#print res
	return res

def dependens():
	exe("sudo apt-get install python-pip python-dev python-numpy python-xlsxwriter python-simplejson swig unzip")
	exe("sudo pip install pyfits")

def ucac4files():
	print "Step 1. =============================="
	print "First download UCAC4 catalog files:"
	print "visit http://cdsarc.u-strasbg.fr/viz-bin/Cat?I/322A for catalog description"
	cfg=dict(config.items("UCAC4"))
        path=cfg['datadir']
	tmppath=path+"/tmp"
	if not os.path.exists(path):
	       	print "Creating UCAC4 catalog dir",path
		os.makedirs(path)
		os.makedirs(tmppath)
		print "Downloading UCAC4 files to:",path
		call_list=["wget","-cr","ftp://cdsarc.u-strasbg.fr/pub/cats/I/322A/UCAC4/*","-P",tmppath]
        	p=call(call_list)
		exe('mv '+tmppath+"/cdsarc.u-strasbg.fr/pub/cats/I/322A/UCAC4/* "+path)
		shutil.rmtree(tmppath)
	else:
		print "UCAC4 files already download"

def ucac4src():
	org_path=os.getcwd()
	os.chdir('ucac4.src')
	print "Installing ucac4 swig rutines"
	cmd='./mkswig.sh'
	exe(cmd)
	os.chdir(org_path)

def lunar():
	print "Installing integrat from project pluto:"
	org_path=os.getcwd()
	os.chdir('lunar')
	print "Installing"
	cmd='./configure'
	exe(cmd)
	cmd='make -f linlunar.mak clean'
	exe(cmd)
	cmd='make  -f linlunar.mak'
	exe(cmd)
	exe('chmod a+x integrat')
	exe('cp integrat ..')
	os.chdir(org_path)

def jplEph():
	pkg='ftp://ssd.jpl.nasa.gov/pub/eph/planets/Linux/de430/linux_p1550p2650.430'
	cfg=dict(config.items("MPCORB"))
        path=os.path.dirname(os.path.abspath(cfg['de_jpl']))
       	file_name = pkg.split('/')[-1]
	print "Installing JPL ephem file:",file_name
	if not os.path.exists(path):
	       	print "Creating JPL Ephem dir",path
		os.makedirs(path)
	if not os.path.isfile(path+'/'+file_name):
		print "Dowloading:",pkg
		urllib.urlretrieve(pkg,path+'/'+file_name)
	else:
		print file_name,"Allready downloaded"

def pyephem():
	print "Installing modified version of pyephem"
	org_path=os.getcwd()
	os.chdir('pyephem/pyephem-3.7.5.1')
	cmd='sudo python setup.py install'
	exe(cmd)
	os.chdir(org_path)

if __name__ == '__main__':
	print "================================================"
	print "First time run. Only need to run one time.Setting up"
	print "It could be take very-very long time"
	print "CHECK your data_dir in config/main.cfg file!!!"
	print "================================================"
	print
	dependens()
	ucac4src()
	ucac4files()
	lunar()
	jplEph()
	pyephem()
	cfg=dict(config.items("MPCORB"))
        path=cfg['base_dir']
	print "================================================"
	print "			READY!"
	print "================================================"
	print "All the data was put on:"
	print path
	print "Now, depending of the setting og 'use_fix_mpcorb':"
	print
	print "use_fix_mpcorb='True'"
	print "\tDownload MCPORB.DAT rename to FIX_MPCORB.DAT and"
	print "\tput in the 'datempcorb' dir:"
	print "\t"+cfg['datempcorb']
	print
	print "use_fix_mpcorb='False'"
	print "\tRun updaterCatServer.py to create the cache."
	print "\tThe first run take very very very long time"
	print "\tDepending of your dateto/datefrom may be several days!!"
	print
	print "Actual value of use_fix_mpcorb=",cfg['use_fix_mpcorb']
	print "================================================"

