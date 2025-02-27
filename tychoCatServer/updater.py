#!/usr/bin/python
# -*- coding: iso-8859-15 -*-


import ephem
import subprocess,os, sys
from subprocess import Popen,call
from threading import Thread
import multiprocessing
import simplejson
import astropy.io.fits as pyfits
import numpy as np
import pickle
import datetime

from .satellite import satEphem
from .asteroids import MPCEphem

import filecmp
import time

from .config import *
from .helper import *

# Create a custom logger
logger = logging.getLogger('updater')

cfg=dict(config.items("MPCORB"))
cfgOBS=dict(config.items("OBSERVATORY"))

def exe(cmd):
        logger.debug("EXE CMD:%s",cmd)
        res=subprocess.getoutput(cmd)
        logger.debug("CMD RESULTS:%s",res)
        return res


class propagateMPCorb:
    '''
    Class to download mpcfiles, propagate to diferents epoch and update 
    mpcorb and guestDBs.
    '''
    datedmpcorb=cfg["datempcorb"]
    date0=float(cfg['date0'])
    datefrom=float(cfg['datefrom'])
    dateto=float(cfg['dateto'])
    eachdays=float(cfg['eachdays'])

    logger.info('%s %s %s %s',datefrom,date0,dateto,eachdays)
    jd_range_plus=list(np.arange(date0,dateto,eachdays))
    jd_range_minus=list(np.arange(date0,datefrom,-eachdays))
    jd_range=set(jd_range_minus+jd_range_plus)
    logger.info("jd_range_plus:%s",jd_range_plus)
    logger.info("jd_range_minus:%s",jd_range_minus)
    logger.info("jd_range:%s",jd_range)

    def downloadMPCORBfile(self):
        '''
        Download mpcorb.dat file form MPC,
        decompresse and change name to reflect 
        the date
        '''
        cfg=dict(config.items("MPCORB"))
        dir_dest=cfg["datempcorb"]
        if not os.path.exists(dir_dest):
            os.makedirs(dir_dest)
        fileD='MPCORB.DAT'
        mpcorbfile=dir_dest+'/'+fileD
        datedmpcorbfile=dir_dest+'/'+getToday()+'.'+fileD
        logger.info("Checking for updated MPCORB.DAT:"+datedmpcorbfile)
        if not os.path.isfile(datedmpcorbfile):
            logger.info("MPCORB file not exists:%s",datedmpcorbfile)
            logger.info("Downloading")
            filename=os.path.basename(cfg["mpcorburl"])
            logger.info(filename)
            cmd="wget -c "+cfg["mpcorburl"]+" -O "+dir_dest+"/"+filename
            logger.info(cmd)
            res=exe(cmd)
            logger.info(res)
            res=exe("gunzip -f "+dir_dest+"/"+filename)
            logger.info(res)
            logger.info("Renaming "+mpcorbfile+ " to "+datedmpcorbfile)
            res=exe("mv  "+mpcorbfile+ " "+datedmpcorbfile)
            logger.info(res)
            logger.info("Cleaning FIX_guest_* cache files")
            res=exe("rm "+cfg["guestdbdir"]+"/FIX_guest_????-??-??.p")
            logger.info(res)                  

        else:
            logger.info("%s EXIST. Using" % datedmpcorbfile)

        logger.info("Creating symbolic link from "+getToday()+'.'+fileD+ " to "+ dir_dest+ "/MPCORB.DAT")
        res=exe("ln -s -f "+getToday()+'.'+fileD+" "+ dir_dest+ "/MPCORB.DAT")
        logger.info(res)

        return "MPCORB.DAT"

    def downloadDAILYfile(self):
        '''
        Download mpcorb.dat file form MPC,
        decompresse and change name to reflect 
        the last asteroid key in the list.
        Return False if already downloaded
        '''
        dir_dest=cfg["datempcorb"]
        if not os.path.exists(dir_dest):
            os.makedirs(dir_dest)
        logger.info("Downloading")
        filename=os.path.basename(cfg["dailyurl"])
        mpcorbfile=dir_dest+'/'+filename
        logger.info(mpcorbfile)
        if  os.path.isfile(mpcorbfile):
                os.remove(mpcorbfile)
        cmd="wget -c "+cfg["dailyurl"]+" -O "+mpcorbfile
        logger.info(cmd)
        res=exe(cmd)
        logger.info(res)

        fileD=self.getLastKeyDate(filename)+'.mpcorb'
        
        if  os.path.isfile(dir_dest+"/"+fileD):
            logger.info("File "+fileD+" already exist. Delete before proceed.\nQuitting")
            return(False)

        res=exe("mv  "+mpcorbfile+ " "+dir_dest+"/"+fileD)
        logger.info(res)
        #make a copy to trace
        if not os.path.exists(dir_dest+"/kernels"):
           os.makedirs(dir_dest+"/kernels")
        res=exe("cp  "+dir_dest+"/"+fileD+ " "+dir_dest+"/kernels/"+getToday()+'.'+fileD)
        logger.info(res)
        logger.info(fileD)

        return fileD

    def getLastKeyDate(self,mpcfile):
        '''
        Search for the last key in a mpcorb file
        '''
        #load elements
        content=self.readFile(mpcfile)
        contentA=np.asarray(content)
        content_keys_list=np.asarray([x[:7] for x in content ])
        nrecords=len(content_keys_list)
        discover_date=ephem.date(0)
        k=''
        for key in content_keys_list:
                date_ = date_from_designation(key)
                #logger.info date_
                if discover_date <= date_ :
                        discover_date = date_
                        k=key
        logger.info("%s %s",k,discover_date)
        return k


        


    def timeShift(self,mpcorb_from,mpcorb_to,newdate):
        '''
        update osculating elements to a new epoch
        using Bill Gray integrat soft
        '''
        de_jpl=cfg["de_jpl"]
        call_list=[f"{pkgpath}/integrat",mpcorb_from,mpcorb_to,newdate,"-f"+de_jpl]
        logger.info(call_list)
        p=call(call_list)
        logger.info(p)

    def propagate_thread(self,jd_range,mpcfile):
      '''
      update osculating elements to a new epoch. 
      for a dates in jd_range
      '''
      for i,jd in enumerate(jd_range):
        newdate=str(jd)
        if i==0:
           continue

        mpcorb_from="%s/%d.%s" % (self.datedmpcorb,jd_range[i-1],mpcfile)
        mpcorb_to="%s/%d.%s" % (self.datedmpcorb,jd,mpcfile)

        if  not os.path.isfile(mpcorb_from):
            logger.info("File %s does not exist. Quitting",mpcorb_from)
            return

        if  os.path.isfile(mpcorb_to):
            logger.info("File %s already exist. Skipping",mpcorb_to)
            continue
        
        #Check if lock
        lockfile=mpcorb_to+'.lock'
        if  os.path.isfile(lockfile):
            logger.info("File %s is locked",mpcorb_to)
            return

        #lock while computing...
        with open(lockfile,'w') as f:
                f.write('lock')

        self.timeShift(mpcorb_from,mpcorb_to,newdate)
        #unlock
        os.remove(lockfile)


    def propagate(self,mpcfile):
        '''
        Integrat the mpcfile over the whole timespan.
        Two threads UP/DOWN to speed up
        '''
        logger.info(self.jd_range_plus)
        newdate=str(self.date0)
        mpcorb_from="%s/%s" % (self.datedmpcorb,mpcfile)
        mpcorb_to="%s/%d.%s" % (self.datedmpcorb,self.date0,mpcfile)
        if  not os.path.isfile(mpcorb_to):
            self.timeShift(mpcorb_from,mpcorb_to,newdate)
        else:
            logger.info("File %s already exist. Continue",mpcorb_to)


        try:
            logger.info("Creating Threads ...")
            tUP = Thread(None,self.propagate_thread,None, (self.jd_range_plus, mpcfile, ))
            tDOWN = Thread(None,self.propagate_thread,None, (self.jd_range_minus, mpcfile, ))
            tDOWN.start()
            tUP.start()
            tDOWN.join()
            tUP.join()
            logger.info("UP/DOWN Threads created...")
        except Exception as e:
            logger.info("Thread error...")
            logger.info(e)

    def initMPC(self):
            mpcfile=self.downloadMPCORBfile()
            if len(mpcfile)!=0:
                self.propagate(mpcfile)

    def populateGuestDB(self):
            datefrom=self.datefrom-dubliJDoffset
            dateto=self.dateto-dubliJDoffset
            mpc=MPCEphem()
            for d in np.arange(datefrom+1,dateto-1):
                fecha=ephem.date(d)
                dt_fecha=fecha.datetime()
                f=dt_fecha.strftime("%Y-%m-%d %H:%M:%S")
                if mpc.initGuestPos(f):
                        logger.info("guestDB form date %s done (Exist or Created)",f)
                else:
                        logger.info("guestDB form date %s FAIL!",f)

    def updateGuest_DAILY(self,mpcfile):
            datefrom=self.datefrom-dubliJDoffset
            dateto=self.dateto-dubliJDoffset
            mpc=MPCEphem()
            for d in np.arange(datefrom+1,dateto-1):
                fecha=ephem.date(d)
                dt_fecha=fecha.datetime()
                f=dt_fecha.strftime("%Y-%m-%d %H:%M:%S")
                logger.info("Updating guest DB")
                self.updateGuestDB(f,mpcfile)



    def updateGuestDB(self,date,mpcfile):
        #add or update date_guestDB ussing new records in orbfile
        mpcEngine=MPCEphem()
        mpcEngine.setNames(date,sufix='.'+mpcfile)
        if not os.path.isfile(mpcEngine.guestDB):
                logger.info("GuestDB:"+ mpcEngine.guestDB+" DOES NOT EXIST. ")
                return
        mpcEngine.loadMPCorb(mpcEngine.mpcorbfile)
        #Call compute
        mpcEngine.setObserver(lon=cfgOBS["lon"],lat=cfgOBS["lat"],elev=cfgOBS["elev"])
        mpcEngine.setDate(date)
        logger.info("Going multithreading..")
        dummy=mpcEngine.threadCompute(mpcEngine.asteroids,ephem.hour*12)
        if len(dummy)==0:
                return
        #pick only relevant variables and mag filter
        newGuestPos=dummy[['KEY','RA','DEC','MAG','SPEED','TYPE']]
        flt=(newGuestPos['MAG']<=float(cfg['maxmag']))
        #get the new records
        newGuestPos=newGuestPos[flt]
        if len(newGuestPos)==0:
                logger.info("Not new coords")
                return

        #retrive the old DB
        logger.info("Updating guestDB:%s",mpcEngine.guestDB)
        GuestPos=pickle.load(open( mpcEngine.guestDB, "rb" ) )


        #keep records not changed

        mask = np.in1d(GuestPos[['KEY']].astype('a7'),newGuestPos[['KEY']].astype('a7'))

        NotChanged=GuestPos[np.logical_not(mask)]

        #then add the new ones or updated

        n_notchange=len(NotChanged)
        n_update=len(newGuestPos)
        n_orginal=len(GuestPos)
        logger.info(date)
        logger.info("Num records in old DB:",n_orginal)
        logger.info("Num of records in update:",n_update)
        logger.info("Num records not changed:",n_notchange)
        logger.info("Num records TO changed:",n_orginal-n_notchange)
        logger.info("Num records TO add:",n_update-(n_orginal-n_notchange))
        guestPos=np.hstack((NotChanged,newGuestPos))
        n_total_new=len(guestPos)
        logger.info("Num record in the new DB:&s",n_total_new)

        '''
        #first update old records
        for r in newGuestPos:
                 guestPos[(guestPos['KEY']==r['KEY'])]=r
        newsrecords=newGuestPos[(newGuestPos['KEY']!=guestPos['KEY'])]
        #then add the new ones
        guestPos=np.hstack((guestPos,newsrecords))
        '''

        pickle.dump(guestPos, open( mpcEngine.guestDB, "wb" ),2 )




    def updateMPC_DAILY(self,mpcdaily):
        #Update MPCORB.file with the new DAILY.DAT
        #Download and propagate elements 

        logger.info("propagating DAILY.DAT")
        self.propagate(mpcdaily)
        dd=mpcdaily.split('.')[0]
        logger.info("%s %s",dd,mpcdaily.split('.'))
        #The update
        for d in self.jd_range:
                logger.info(d)
                mpcorb_org="%d.MPCORB.DAT" % (d)
                update_records="%d.%s.mpcorb" % (d,dd)
                logger.info("Updating %s with the records in %s" ,mpcorb_org,update_records)
                if not self.updateMPC(mpcorb_org,update_records):
                        logger.info("Fail to update!")

        return 



    def readFile(self,filename):
        dir_dest=cfg["datempcorb"]
        filename=dir_dest+"/"+filename
        logger.info("Reading:%s",filename)
        MPC = open(filename, "r")
        content=MPC.readlines()
        #skip headers comments
        try:
                i=0
                while content[i].find('----------'):
                    i += 1
                return content[i+1:]
        except:
                return content
        
        
    def updateMPC(self,mpcfile,incfile):

        content=self.readFile(mpcfile)
        contentA=np.asarray(content)
        content_keys_list=np.asarray([x[:7] for x in content ])
        nrecords=len(content_keys_list)

        content_update=self.readFile(incfile)
        content_updateA=np.asarray(content_update)
        content_update_keys_list=np.asarray([x[:7] for x in content_update ])
        nrecords_update=len(content_update_keys_list)

        dir_dest=cfg["datempcorb"]
        mpcfile=dir_dest+"/"+mpcfile
        #This an update so check if allready exist the file
        if  not os.path.isfile(mpcfile):
            logger.info("File ",mpcfile," does not exist. Quitting")
            return True

        #Check if lock
        lockfile=mpcfile+'.lock'
        if  os.path.isfile(lockfile):
            logger.info("File ",mpcfile," is locked. Quitting")
            return False

        #lock while computing...
        with open(lockfile,'w') as f:
                f.write('lock') 


        #First delete records to update using
        #MASK to keep records not to be updated
        mask = np.in1d(content_keys_list.astype('a7'),content_update_keys_list.astype('a7'))
        AA=content_keys_list[mask]

        seen = set()
        uniq = []
        dupli = []
        for x in AA:
            if x not in seen:
                uniq.append(x)
                seen.add(x)
            else:
                dupli.append(x)
        logger.info("UPDATED RECORDS:%u, UNIQUES:%u, DUPLICATE:%u",len(AA),len(uniq),len(dupli))
        contentA=contentA[np.logical_not(mask)]
        nkeep=len(contentA)
        nupdated=len(mask[mask])
        nadded=nrecords_update-nupdated
        #logger.info(mpcfile,"\nRECORDS:%u/%u TO BE UPDATED:%u TO BE ADDED:%u KEEPED:%u CHECK:%u",nrecords,nrecords_update,nupdated,nadded,nkeep,((nkeep+nupdated)==nrecords))

        r=np.hstack((contentA,content_updateA))
        #r=AA

        thefile=open(mpcfile,'w')
        for item in r:
            thefile.write("%s" % item)
        thefile.close()


        #unlock
        os.remove(lockfile)
        return True

    def DailyHousekeep(self,f1,f2):
        with open(self.datedmpcorb+"/"+f1, 'r') as file1:
            with open(self.datedmpcorb+"/"+f2, 'r') as file2:
                same = set(file2).difference(file1)
        same.discard('\n')
        logger.info(list(same))

    def DailyHousekeep(self):
        dir_dest=cfg["datempcorb"]
        filename=dir_dest+"/"+update_records
        os.remove(filename)
        pass

def update():
    '''
        1.- Call initMPC() to download MPCORB.DAT. Only one time. First version of DATEMPCORB set. Long run ...
        2.- Call populateGuestDB() to create firts version of guestDB (Only one time). Very long run ...
        3.- Call updateMPC_DAILY() to download DAILY.DAT and updateGuest_DAILY() to add/update records to MCORB and guestDB files
    '''
    m= propagateMPCorb()
    s= satEphem()
        
    if True:
        m.initMPC()
    if False:
        m.populateGuestDB()


    while True:
        logger.info("download mpcorb DAILY.DAT")
        mpcdaily=m.downloadDAILYfile()
        if mpcdaily:
           m.updateMPC_DAILY(mpcdaily) 
           m.updateGuest_DAILY(mpcdaily)
        logger.info("download TLE..")
        s.downloadTLEfile()
        logger.info("wait for 8 hours")
        time.sleep(8*3600)     

if __name__ == '__main__':
    update()




