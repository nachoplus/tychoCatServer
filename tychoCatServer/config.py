#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#tychoSuit

import os, sys
import configparser


#Common configuration file

#Logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


#General paths
binpath=os.path.dirname(os.path.realpath(sys.argv[0]))
pkgpath=os.path.dirname(__file__)


#Read values from main.cfg
config = configparser.ConfigParser()
homeconfig=os.path.join(os.path.expanduser('~'), '.config/tychoCatServer')
_configs_files=[f'{x}/tychoCatServer.cfg' for x in ['/etc/tychoCatServer',homeconfig,'./config','.']]
configs_files=[x  for x in _configs_files if os.path.exists(x)]
if len(configs_files)>1:
    print(f'SEVERAL CONFIG FILES FOUND:{configs_files}. Using the last one:{configs_files[-1]}')
elif len(configs_files)==1:
    print(f'CONFIG FILE FOUND:{configs_files[-1]}')
else:
    print(f'ERROR: NO CONFIG FILE WAS FOUND')
    os.popen(f'cp {pkgpath}/tychoCatServer.cfg tychoCatServer.cfg') 
    print(f"Default config:tychoCatServer.cfg was created in current path. Edit and put in one of this locations following your preferences:\n{_configs_files}")
    exit(1)
config.read(configs_files[-1])
cfg_general=config._defaults

def TodayDir():
    return getToday()

def getToday():

    import datetime

    # Get a date object
    today = datetime.datetime.now()

    #For ours propouse we change the day at noon
    today=today-datetime.timedelta(hours=float(cfg_general['day_change_at']))

    # Formatted date
    if len(cfg_general['force_day'])==0:
        return today.strftime("%y-%m-%d")
    else:
        print("Forcing Date",cfg_general['force_day'])
        return cfg_general['force_day']

def writeCfg(directory):
    filename=directory+"/main_"+TodayDir()+".cfg"
    fi=open(filename,'w')
    config.write(fi)
    fi.close()

def printCfg():
    for section in config.sections():
        print()
        print("================ "+section+" ================")
        for item in config.items(section):
            print(item)

if __name__ == '__main__':
     print(os.environ)
     printCfg()
