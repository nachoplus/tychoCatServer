#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

from subprocess import Popen,call
import subprocess,os, sys,shutil
from urllib.request import urlretrieve

from config import *

import logging

# Create a custom logger
logger = logging.getLogger('bootstrap')


def exe(cmd):
        logger.debug("EXE CMD:%s",cmd)
        res=subprocess.getoutput(cmd)
        logger.debug("CMD RESULTS:%s",res)
        return res


def ucac4src():
        org_path=os.getcwd()
        os.chdir(binpath+'/ucac4.src')
        logger.info("Installing ucac4 swig rutines")
        cmd='./mkswig.sh'
        exe(cmd)
        os.chdir(org_path)

def lunar():
        logger.info("Installing integrat from project pluto:")
        org_path=os.getcwd()

        os.chdir(binpath+'/lunar')
        cmd='make  clean'
        logger.info("%s",exe(cmd))
        cmd='make '
        logger.info("%s",exe(cmd))
        cmd='make install'
        logger.info("%s",exe(cmd))
        os.chdir(org_path)

        os.chdir(binpath+'/jpl_eph')
        cmd='make  clean'
        logger.info("%s",exe(cmd))
        cmd='make '
        logger.info("%s",exe(cmd))
        cmd='make install'
        logger.info("%s",exe(cmd))
        os.chdir(org_path)

        os.chdir(binpath+'/lunar')
        cmd='make integrat'
        logger.info("%s",exe(cmd))
        cmd='chmod a+x integrat'
        logger.info("%s",exe(cmd))
        cmd='cp integrat ..'
        logger.info("%s",exe(cmd))
        os.chdir(org_path)


def pyephem():
        #Not needed. Now upstream is fixed.
        logger.info("Installing modified version of pyephem")
        logger.info("Not needed. Now upstream is fixed.")
        return
        org_path=os.getcwd()
        #os.chdir('pyephem/pyephem-3.7.5.1')
        os.chdir('ephem-3.7.6.0')
        cmd='python3 setup.py install'
        logger.info("%s",exe(cmd))
        os.chdir(org_path)

if __name__ == '__main__':
        logger.warning("================================================")
        logger.warning("First time run. Only need to run one time.Setting up")
        logger.warning("It could be take very-very long time")
        logger.warning("CHECK your data_dir in config/main.cfg file!!!")
        logger.warning("================================================")
        logger.warning("")
        ucac4src()
        lunar()
        #Not needed. Now upstream is fixed.
        #pyephem()
        cfg=dict(config.items("MPCORB"))
        path=cfg['base_dir']
        logger.warning("================================================")
        logger.warning("                        READY!")
        logger.warning("================================================")
        logger.warning("All the data was put on:%s",path)
        logger.warning("Now, depending of the setting og 'use_fix_mpcorb':")
        logger.warning("")
        logger.warning("use_fix_mpcorb='True'")
        logger.warning("\tDownload MCPORB.DAT rename to FIX_MPCORB.DAT and")
        logger.warning("\tput in the 'datempcorb' dir:")
        logger.warning("\t%s",cfg['datempcorb'])
        logger.warning("")
        logger.warning("use_fix_mpcorb='False'")
        logger.warning("\tRun updaterCatServer.py to create the cache.")
        logger.warning("\tThe first run take very very very long time")
        logger.warning("\tDepending of your dateto/datefrom may be several days!!")
        logger.warning("")
        logger.warning("Actual value of use_fix_mpcorb=%s",cfg['use_fix_mpcorb'])
        logger.warning("================================================")

