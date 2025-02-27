#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

from subprocess import Popen,call
import subprocess,os, sys,shutil


from .config import *

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
        logger.info("%s",exe(cmd))
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

def bootstrap():
        logger.warning("================================================")
        logger.warning("Bootstraping... compiling and installing code   ")
        logger.warning("================================================")
        logger.warning("Step1")
        ucac4src()
        logger.warning("Step2")
        lunar()
        logger.warning("================================================")
        logger.warning("                        READY!")
        logger.warning("================================================")

if __name__ == '__main__':
        bootstrap()


