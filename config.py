#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#tychoSuit

import os, sys
import configparser


#Common configuration file

#Logging
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


#General paths
binpath=os.path.realpath(sys.argv[0])
configpath=os.path.dirname(binpath)+"/config"


#Read values from main.cfg
config = configparser.ConfigParser()
config.read(configpath+"/main.cfg")
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
	printCfg()
