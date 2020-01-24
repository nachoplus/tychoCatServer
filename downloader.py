#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

from subprocess import Popen,call
import subprocess,os, sys,shutil
from urllib.request import urlretrieve

from config import *

import logging

# Create a custom logger
logger = logging.getLogger('dowloader')


def exe(cmd):
        logger.debug("EXE CMD:%s",cmd)
        res=subprocess.getoutput(cmd)
        logger.debug("CMD RESULTS:%s",res)
        return res


def ucac4files():
        logger.info("Step 1. ==============================")
        logger.info("Downloading UCAC4 catalog files:")
        logger.info("visit http://cdsarc.u-strasbg.fr/viz-bin/Cat?I/322A for catalog description")
        cfg=dict(config.items("UCAC4"))
        path=cfg['datadir']
        if not os.path.exists(path+"/UCAC4.finished"):
                if not os.path.exists(path):
                    logger.info("Creating UCAC4 catalog dir:%s",path)
                    os.makedirs(path)
                logger.info("Downloading UCAC4 files to:%s",path)
                call_list=["wget","-cr","-nH","--cut-dirs=5","ftp://cdsarc.u-strasbg.fr/pub/cats/I/322A/UCAC4/*","-P",path]
                p=call(call_list)
                logger.info("%s",exe("touch "+path+"/UCAC4.finished"))
        else:
                logger.info("UCAC4 files already download")


def jplEph():
        pkg='ftp://ssd.jpl.nasa.gov/pub/eph/planets/Linux/de430/linux_p1550p2650.430'
        cfg=dict(config.items("MPCORB"))
        path=os.path.dirname(os.path.abspath(cfg['de_jpl']))
        file_name = pkg.split('/')[-1]
        logger.info("Installing JPL ephem file:%s",file_name)
        if not os.path.exists(path):
                logger.info("Creating JPL Ephem dir:%s",path)
                os.makedirs(path)
        if not os.path.isfile(path+'/'+file_name):
                logger.info("Dowloading:%s",pkg)
                urlretrieve(pkg,path+'/'+file_name)
        else:
                logger.info("%s allready downloaded",file_name)


if __name__ == '__main__':
        logger.warning("================================================")
        logger.warning("First time run. Only need to run one time.Setting up")
        logger.warning("It could be take very-very long time")
        logger.warning("CHECK your data_dir in config/main.cfg file!!!")
        logger.warning("================================================")
        logger.warning("")
        ucac4files()
        jplEph()
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
