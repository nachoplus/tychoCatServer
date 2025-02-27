#!/usr/bin/python
# -*- coding: iso-8859-15 -*-



import ephem
import numpy as np
import subprocess
import multiprocessing
import glob

from .config import *
from .helper import *

import logging

# Create a custom logger
logger = logging.getLogger(__name__)

cfg=dict(config.items("TLE"))
cfgOBS=dict(config.items("OBSERVATORY"))

pi=np.pi

class satEphem():

    def __init__(self):
        logger.info("INIT module")
        self.result_queue = multiprocessing.Queue()

    def get(self,date):
        logger.info("Loading TLEfile for date:%s",date)
        self.loadTLEfile(date)
        self.setObserver(lon=cfgOBS["lon"],lat=cfgOBS["lat"],elev=cfgOBS["elev"])
        self.setDate(date)
        self.pos=self.threadCompute(self.TLEs,delta=ephem.second)
        return self.pos



    def setObserver(self,lon,lat,elev,hor="00:00:00"):
        logger.info("LON:%s LAT:%s ELEV:%s",lon,lat,elev)
        here = ephem.Observer()
        here.lat, here.lon, here.horizon  = str(lat), str(lon), str(hor)
        here.elev = float(elev)
        here.temp = 25e0
        here.pressure=0

        # setting in self
        self.here = here

    def setDate(self,date):
        self.here.date=ephem.date(date)
        logger.info("OBSERVER DATE SET TO:%s",ephem.localtime(self.here.date))





    def compute(self,satellites,delta=0):

        dtypes=np.dtype([('NAME', "|U24"), ('CAT_NUMBER',"|U6"), ('KEY', "|U6"),('DATETIME',"|U25"), ('MJD', np.float64), ('MAG', np.float64), \
                        ('RA', np.float64), ('DEC', np.float64),("SPEED",np.float64),("PA",np.float64), ('AZ', np.float64), ('ALT', np.float64), ('RANGE', np.float64), \
                        ('ELEVATION', np.float64), ('RANGE_SPEED', np.float64), ('ECLIPSED', np.bool),('EPOCH',"|U12")])


        astPos=[]
        for i,tle in enumerate(satellites):
            #print ("TLE:",tle)
            lines=tle
            try:
                    sat=ephem.readtle(lines[0],lines[1],lines[2])
                    sat.compute(self.here)
                    if sat.range_velocity==0:
                       logger.error("FAIL to compute Sat:%s DATE:%s",sat.name,self.here.date)
                       continue
            except:
                    logger.error("computing %s",lines[0])
                    logger.exception("TLE elements:%s,%s",lines[1],lines[2])
                    continue



            ra  =sat.ra*180/pi
            dec =sat.dec*180/pi
            elements1=" ".join(lines[1].split()).split(' ')
            """
            dummy=elements1[2]
            if int(dummy[:2])>50:
                    year='19'+dummy[:2]
            else:
                    year='20'+dummy[:2]
            int_number=year+'-'+dummy[-4:]
            """
            int_number=elements1[2]
            dummy=elements1[3]
            try:
               yy=dummy[:2] 
               yyy=int(yy)
            except:
               #print("bad year. next sat",yy)
               continue
            if yyy>50:
                year='19'+yy
            else:
                year='20'+yy
            epoch_day=dummy[-12:]
            epoch=year+'/'+epoch_day

            ldate=self.here.date.datetime().strftime('%Y-%m-%d %H:%M:%S')
            ddate="{:18.11f}".format(self.here.date+dubliJDoffset-MJDoffset)

            #then compute for datetime+delta if delta!=0
            if delta !=0:
                self.here.date+=delta
                sat.compute(self.here)
                ra_  =sat.a_ra*180/(pi)
                dec_ =sat.a_dec*180/pi
                pa=PA(ra,dec,ra_,dec_)
                sp=speed(delta,ra,dec,ra_,dec_)
                self.here.date-=delta
            else:
                pa=np.nan
                sp=np.nan
            onePos=(sat.name,sat.catalog_number,int_number,ldate,ddate,sat.mag,ra,dec,sp,pa, \
                            sat.az*180/pi,sat.alt*180/pi,sat.range,sat.elevation,sat.range_velocity,sat.eclipsed,epoch)
            #print(i,len(satellites),onePos)
            astPos.append(onePos)


        nrec=len(astPos)
        Pos=np.asarray(astPos,dtype=dtypes)
        #logger.debug("Result:%s",Pos)
        logger.debug("Adding thread:%s results (%d) to the result queue.",multiprocessing.current_process().name,nrec)
        if nrec>0:
           self.result_queue.put(Pos)
           logger.debug("Added %s",multiprocessing.current_process().name)
        else:
           logger.debug("%s has zero results. Skiping",multiprocessing.current_process().name)
        logger.debug("Threath:%s end. Returning to main",multiprocessing.current_process().name)
        return Pos

    def loadTLEfile(self,date):
        '''
        Chose and load the most apropiate TLE file.
        '''
        self.downloadTLEfile()
        dir_dest=cfg["tledir"]
        d=ephem.date(date)
        dirs = [os.path.basename(x) for x in glob.glob( dir_dest+'/??-??-??.TLE')]
        days=list(map(lambda x:ephem.date('20'+x[:8].replace('-','/')+" 00:00:00"),dirs))
        distance=list(map(lambda x:np.abs(d-x),days))
        minD=np.min(distance)
        minIndex=distance.index(minD)
        BetterDay=dirs[minIndex]
        #print minD,minIndex,dirs[minIndex]
        logger.info("TLE for:%s -> Best available: %s",d,BetterDay)
        self.tlefile=dir_dest+'/'+BetterDay
        nrec=self.readTLEfile(self.tlefile)
        logger.info("TLE from:%s #REG LOADED: %s",self.tlefile,nrec)

    def downloadTLEfile(self):
        '''
        Download TLE file of the day unzip and rename
        '''
        dir_dest=cfg["tledir"]
        if not os.path.exists(dir_dest):
            os.makedirs(dir_dest)
        tlefile=dir_dest+'/'+getToday()+".TLE"

        if not os.path.isfile(tlefile):
            logger.info("TLE %s not exit. Downloading" , os.path.basename(tlefile))
            res=subprocess.getoutput("wget -c "+cfg["tleurl"])
            logger.info("\n%s",res)
            logger.info("Downloaded file: %s",os.path.basename(cfg["tleurl"]))
            import zipfile
            with zipfile.ZipFile(os.path.basename(cfg["tleurl"]),"r") as zip_ref:
                zip_ref.extractall()
            #res=subprocess.getoutput("unzip "+os.path.basename(cfg["tleurl"]))
            #logger.info("Unzip file: %s",res)
            res=subprocess.getoutput("mv ALL_TLE.TXT "+tlefile)
            logger.info("renaming ALL_TLE.TXT to %s",tlefile)
            logger.info("\n%s",res)
            os.remove(os.path.basename(cfg["tleurl"]))
            
            '''
            #Clasif TLE
            #http://www.prismnet.com/~mmccants/tles/classfd.zip
            print "Dowloading CLASIF TLE file:",cfg["tleclasifurl"]
            res=subprocess.getoutput("wget -c "+cfg["tleclasifurl"])
            print res
            print os.path.basename(cfg["tleclasifurl"])
            res=subprocess.getoutput("unzip "+os.path.basename(cfg["tleclasifurl"]))
            print res
            res=subprocess.getoutput("cat classfd.tle >> "+self.tlefile)
            print res
            '''
        else:
            logger.info("TLE %s already downloaded", os.path.basename(tlefile))




    def readTLEfile(self,url):
        '''
        Read the TLE file and group by 3 lines
        '''
        self.TLEs=[]
        f=open(url)
        theList=f.read().split('\n')
        f.close()
        N=3
        #tles = [''.join(theList[n:n+N]) for n in range(0, len(theList), N)]
        tles = list(group(theList,3))
        self.TLEs = tles
        return len(self.TLEs)


    def filterSat(self,date,ra,dec,r):
        data=self.get(date)
        decmin=dec-r
        if decmin<=-90:
            decmin=-90
        decmax=dec+r
        if decmax>=90:
            decmax=90

        ramin=(360+ra-r) % 360
        ramax=(360+ra+r) % 360

        if r*2>=360:
                ramin=0
                ramax=360


        if ramin<ramax:
            flt=(data['RA']<=ramax) & (data['RA']>=ramin) & (data['DEC']<=decmax) & (data['DEC']>=decmin)
        else:
            #p.e. ra=0 r=10 => ramin=-10 => ramin=350;ramax=10 => ra>350 | ra <10
            flt=((data['RA']<=ramax) | (data['RA']>=ramin)) & (data['DEC']<=decmax) & (data['DEC']>=decmin)

        return data[flt]



    def filterTLEs(self):
        '''
        TODO. Filter by orbital characteris
        '''
        pass


    def threadCompute(self,satellites,delta=0):
        '''
        Speed up. Make a chunk of satellites list and process in
        one thread per CPU core.
        '''
        ncores=multiprocessing.cpu_count()

        if len(satellites)<=ncores*10:
            logger.info("Not to much satellites(%d). Going single thread", len(satellites))
            return self.compute(satellites,delta)

        chunk_size=int(len(satellites)/ncores)

        satellites_chunks=[satellites[x:x+chunk_size] for x in range(0, chunk_size*ncores,chunk_size)]
        if len(satellites) % ncores !=0:
                logger.debug("remaining sats:%s",len(satellites)-chunk_size*ncores)
                logger.debug("remaining sats:%s",satellites[chunk_size*ncores:])
                satellites_chunks.append(satellites[chunk_size*ncores:])

        
        total_satellites=len(satellites)
        n_chunks=len(satellites_chunks)
        rest=total_satellites-ncores*chunk_size
        logger.info("CORES:%s #SATELLITES:%s CHUNK_SIZE:%s #CHUNKS:%s",ncores,total_satellites,chunk_size,n_chunks)
        logger.info("Programed %d  satellites on %d cores. %d chuncks x %d each + 1 chunk x %d ",total_satellites,ncores ,n_chunks-1,chunk_size,rest)
        try:
            logger.info("Creating Threads ...")
            threadsPool=[]
            #define threads

            for i,chunk in enumerate(satellites_chunks):
                #print chunk
                #t = Thread(None,self.compute,None, (chunk,))
                t=multiprocessing.Process(target=self.compute, args=(chunk,delta,))
                threadsPool.append(t)

            # Start all threads
            [x.start() for x in threadsPool]
            logger.info("Started %s threads",len(threadsPool))
            
            #to avoid full queue retrive the result while threads are running 
            result=[]
            while 1:
                running = any(p.is_alive() for p in threadsPool)
                while not self.result_queue.empty():
                       result.append(self.result_queue.get())
                if not running:
                       break
            # Wait for all of them to finish
            [x.join() for x in threadsPool]
            logger.info("All threads finished")

            for i,r in enumerate(result):
                if i==0:
                    final_result=r
                    continue
                final_result=np.hstack((final_result,r))
            total_satellites=len(final_result)
            n_chunks=len(satellites_chunks)
            rest=total_satellites-ncores*chunk_size
            logger.info("Processed  %d  satellites on %d cores. %d chuncks x %d each + 1 chunk x %d ",total_satellites,ncores ,n_chunks-1,chunk_size,rest)
            return final_result
        except Exception as e:
            logger.error("Exception in Thread loop...")
            logger.exception("")


if __name__ == '__main__':
    s=satEphem()
    data=s.filterSat("2019-06-01 01:00",25,-6.3,.1)
    print(data)
    #flt=(data['ELEVATION']>=1E8)
    #print data[flt]
