#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
##TO BE DONE
##Future BaseClass for asteroids and satellites

import ephem
import csv
import commands,os, sys
from subprocess import Popen,call
from threading import Thread
import multiprocessing
import simplejson
import pyfits
import numpy as np
import cPickle as pickle
import datetime

import datetime

from config import *
from helper import *
cfg=dict(config.items("MPCORB"))
cfgOBS=dict(config.items("OBSERVATORY"))

pi=np.pi

def give_number(letter):

    try:
        int(letter)
        return letter
    except ValueError:
        if letter.isupper():
            return str(ord(letter) - ord('A') + 10)
        if letter.islower():
            return str(ord(letter) - ord('a') + 36)

def convert_design(packed):

    '''
      Convert the packed designation format to formal designation.
    '''

    isdigit = str.isdigit

    try:
        packed = packed.strip()
    except ValueError:
        print("ValueError: Input is not convertable to string.")

    if isdigit(packed) == True: desig = packed.lstrip('0') # ex: 00123

    if isdigit(packed[0]) == False: # ex: A7659 = 107659

        if isdigit(packed[1:]) == True: # ex: A7659
            desig = give_number(packed[0]) + packed[1:]

        elif isdigit(packed[1:3]) == True:  # ex: J98SG2S = 1998 SS162

            if isdigit(packed[4:6]) == True and packed[4:6] != '00':
                desig = give_number(packed[0]) + packed[1:3] + ' ' + packed[3] + packed[-1] + packed[4:6].lstrip("0")

            if isdigit(packed[4:6]) == True and packed[4:6] == '00':
                desig = give_number(packed[0]) + packed[1:3] + ' ' + packed[3] + packed[-1]

            if isdigit(packed[4:6]) == False:
                desig = give_number(packed[0]) + packed[1:3] + ' ' + packed[3] + packed[-1] + give_number(packed[4]) + packed[5]

        elif packed[2] == 'S': # ex: T1S3138 = 3138 T-1
            desig = packed[3:] + ' ' + packed[0] + '-' + packed[1]

    return desig

def convert_date(packdt):

    '''
      Convert the packed year format to standard year.
    '''
    try:
        packdt = str(packdt).strip()
    except ValueError:
        print("ValueError: Input is not convertable to string.")

    '''
       Month     Day      Character         Day      Character
                       in Col 4 or 5              in Col 4 or 5
     Jan.       1           1             17           H
     Feb.       2           2             18           I
     Mar.       3           3             19           J
     Apr.       4           4             20           K
     May        5           5             21           L
     June       6           6             22           M
     July       7           7             23           N
     Aug.       8           8             24           O
     Sept.      9           9             25           P
     Oct.      10           A             26           Q
     Nov.      11           B             27           R
     Dec.      12           C             28           S
               13           D             29           T
               14           E             30           U
               15           F             31           V
               16           G

     Examples:

     1996 Jan. 1    = J9611
     1996 Jan. 10   = J961A
     1996 Sept.30   = J969U
     1996 Oct. 1    = J96A1
     2001 Oct. 22   = K01AM
    '''

    return '/'.join([give_number(packdt[0]) + packdt[1:3],give_number(packdt[3]),give_number(packdt[4])])

class epheEngine:
    result_queue = multiprocessing.Queue()


    def loadElements(self,filename):


    def setObserver(self,lat,lon,elev,hor="10:00:00"):

        here = ephem.Observer()
        here.lat, here.lon, here.horizon  = str(lat), str(lon), str(hor)
        here.elev = float(elev)
        here.temp = 25e0
        #here.compute_pressure()
	#P=0 to disable reflection calculation
	here.pressure=0
        print "Observer info: \n", here

        # setting in self
        self.here = here

    def setDate(self,date):
        self.here.date=ephem.date(date)
        print ephem.localtime(self.here.date)
        #print("Observer info: \n", self.here)
        self.sun.compute(self.here)


    def loadObject(self,des):

    def compute(self,mylist,delta=0):
    def windowMPC(self,ra,dec,r):
	#Asteroids with speed above this are always taken into acount
	speed_=1
	#margin is to asure all posibles asteroids are computed
	#include 1º for paralax errors (max at moon distant)
	#and speed_*24*60 arcsec to take into acount asteroids displacement
	margin=1+speed_*24*60/3600
	#r=r+margin

        data=self.guestPos
        decmin=dec-r
        if decmin<-90:
            decmin=-90
        decmax=dec+r
        if decmax>90:
            decmax=90

        ramin=(ra-r) % 360
        ramax=(ra+r) % 360

        if ramin<ramax:
            flt=(data['RA']<=ramax) & (data['RA']>=ramin) & (data['DEC']<=decmax) & (data['DEC']>=decmin) | (data['SPEED']>=speed_)
        else:
            #p.e. ra=0 r=10 => ramin=-10 => ramin=350;ramax=10 => ra>350 | ra <10
            flt=((data['RA']<=ramax) | (data['RA']>=ramin)) & (data['DEC']<=decmax) & (data['DEC']>=decmin) | (data['SPEED']>=speed_)

        filterkeys=map(lambda x:x[0],data[flt])
        filter_asteroid = { key: self.asteroids[key] for key in filterkeys }
        #print filterkeys
        return filter_asteroid




    def filterMPC(self,date,ra,dec,r):
        #Check if is need to switch MPCORB.DAT & guestDB
        if ephem.date(date)!=self.guestDate:
            self.init(date)

        mylist=self.windowMPC(ra,dec,r)
        self.setDate(date)
	#
        data=self.threadCompute(mylist,delta=ephem.minute)
	
	if True:
	        return data

        decmin=dec-r
        if decmin<-90:
            decmin=-90
        decmax=dec+r
        if decmax>90:
            decmax=90

        ramin=(ra-r) % 360
        ramax=(ra+r) % 360

        if ramin<ramax:
            flt=(data['RA']<=ramax) & (data['RA']>=ramin) & (data['DEC']<=decmax) & (data['DEC']>=decmin) 
        else:
            #p.e. ra=0 r=10 => ramin=-10 => ramin=350;ramax=10 => ra>350 | ra <10
            flt=((data['RA']<=ramax) | (data['RA']>=ramin)) & (data['DEC']<=decmax) & (data['DEC']>=decmin)


        return data[flt]

    def search(self,keys,date,r):
        if ephem.date(date)!=self.guestDate:
            self.init(date)

        filter_asteroid = { key: self.asteroids[key] for key in keys }
        #print filter_asteroid
        self.setDate(date)
        data=self.threadCompute(filter_asteroid,delta=ephem.minute)
        return data


    def initGuestPos(self,date):
        '''
        Do init calculation to find out a preliminary
        positions of asteroid in that date.
        The result is store as pickle object and used to
        identify posible asteroids in the FOV
        '''

        self.getMPCORB(date)
        self.setObserver(lon=cfgOBS["lon"],lat=cfgOBS["lat"],elev=cfgOBS["elev"])

	#Check if allready exist
        if  os.path.isfile(self.guestDB):
            return
        print "INIT DB FOR DATE:",date

	#Call compute
        self.setDate(date)
        dummy=self.threadCompute(self.asteroids,ephem.hour*12)

	#pick only relevant variables and mag filter
        guestPos=dummy[['KEY','RA','DEC','MAG','SPEED']]
        flt=(guestPos['MAG']<=float(cfg['maxmag']))
        guestPos=guestPos[flt]
        pickle.dump(guestPos, open( self.guestDB, "wb" ) )

    def threadCompute(self,asteroids,delta=0):
        '''
        Speed up. Make a chunk of asteroids dict and process in
        one thread per CPU core.
        '''
        ncores=8
        if len(asteroids)<=ncores*10:
            print "Not to much asteroids(%d). Going single thread" % len(asteroids)
            return self.compute(asteroids,delta)

        chunk_size=len(asteroids)/ncores

        asteroids_chunks=[dict(asteroids.items()[x:x+chunk_size]) for x in xrange(0, chunk_size*ncores,chunk_size)]
	if len(asteroids) % ncores !=0:
        	asteroids_chunks.append(dict(asteroids.items()[chunk_size*ncores:]))

        print "CORES/AST/CHUNK/cho SIZE:",ncores,len(asteroids),chunk_size,len(asteroids_chunks)

        try:
            print "Creating Threads ..."
            threadsPool=[]
            #define threads

            for i,chunk in enumerate(asteroids_chunks):
                #print chunk
                #t = Thread(None,self.compute,None, (chunk,))
                t=multiprocessing.Process(target=self.compute, args=(chunk,delta,))
                threadsPool.append(t)
            print "Threads created..."
            # Start all threads
            [x.start() for x in threadsPool]
            print "Threads started..."
            result=[]
            for j in threadsPool:
                result.append(self.result_queue.get())
            print "Threads got..."
            # Wait for all of them to finish
            [x.join() for x in threadsPool]
            print "Threads close..."
            for i,r in enumerate(result):
                if i==0:
                    final_result=r
                    continue
                final_result=np.hstack((final_result,r))

            print len(final_result)
            print "%d compute Threads.Processing %d x %d asteroids" % (ncores,ncores,chunk_size)
            return final_result
        except Exception as e:
            print "Thread error..."
            print e





if __name__ == '__main__':

    m=prepareMPCorb()
    #m.populateGuestDB()
    m.propagate('DAILY.DAT')

    '''
    #mpc.getMPCORB('1973-09-29 00:00:00')
    print mpc.filterMPC("2014-09-13 12:31:38",30.2,12,.2)
    print mpc.filterMPC("1971-09-14 22:23:09",41.2,-13,1)
    print mpc.filterMPC("2026-03-14 02:23:09",4.2,-13,1)
    '''
