#!/usr/bin/python
# -*- coding: iso-8859-15 -*-


import ephem
import os
from threading import Thread
import multiprocessing
import astropy.io.fits as pyfits
import numpy as np
import pickle
import datetime




from .config import *
from .helper import *

import logging

# Create a custom logger
logger = logging.getLogger(__name__)

cfg=dict(config.items("MPCORB"))
cfgOBS=dict(config.items("OBSERVATORY"))



class MPCEphem:
    asteroids=dict()
    filter_asteroid=dict()
    sun = ephem.Sun()
    guestDate=''
    loadedMPCORB=''
    result_queue = multiprocessing.Queue()

    def init(self,date):
        logger.info("INIT module")
        if  self.initGuestPos(date):
                self.getMPCORB(date)
                self.guestPos=pickle.load(open( self.guestDB, "rb" ) )
                self.guestDate=ephem.date(date)
                logger.info("Load guestDB: %s",self.guestDB)
                logger.info("self.guestDate: %s",self.guestDate)
                logger.info("ASTEROID INIT: Above the horizont: %s",len(self.guestPos))
        else:
                self.guestPos=np.asarray([])
                logger.critical("FAIL TO LOAD ASTEROID GUESTDB.")
                exit(1)


    def loadMPCorb(self,filename):
        if filename==self.loadedMPCORB:
                logger.info("MPCORB %s already load", filename)
                return

        asteroid=dict()
        logger.info("Reading:%s",filename)
        MPC = open(filename, "r", encoding="latin-1")
        content=MPC.readlines()
        #skip headers comments
        try:
                i=0
                while content[i].find('----------'):
                    i += 1
                content=content[i+1:]
        except:
                pass
        n = 0
        for ast in content:
            n += 1
            if True:
                try:
                    designation=ast[:7]
                    try:
                        H=float(ast[8:12]),
                        G=float(ast[15:19]),
                        asteroid[designation] = tuple(ast[8:104].split())
                    except:
                        #print "Not H,G magnitudes. Setting to standard values 0.0 0.15:",designation
                        if len(ast)>80:
                                asteroid[designation] = tuple([0e0,0.15]+ast[20:104].split())
                except:
                    logger.exception("Error loading line")
                    pass

        logger.info("MPC catalogue has been read. Total readed asteroids %s of %s",len(asteroid),n)

        self.asteroids = asteroid
        self.loadedMPCORB=filename


    def setObserver(self,lat,lon,elev,hor="10:00:00"):
        logger.info("LON:%s LAT:%s ELEV:%s",lon,lat,elev)
        here = ephem.Observer()
        here.lat, here.lon, here.horizon  = str(lat), str(lon), str(hor)
        here.elev = float(elev)
        here.temp = 25e0
        #here.compute_pressure()
        #P=0 to disable reflection calculation
        here.pressure=0
        #print "Observer info: \n", here

        # setting in self
        self.here = here

    def setDate(self,date):
        self.here.date=ephem.date(date)
        logger.info("OBSERVER DATE SET TO:%s",ephem.localtime(self.here.date))

        #print("Observer info: \n", self.here)
        self.sun.compute(self.here)


    def loadObject(self,des):

        '''
           Input: asteroid Designation (des).
           Output: Return pyephem class with asteroid ephemeris for any date or observer.
        '''


        ast = ephem.EllipticalBody()

        '''
        EllipticalBody elements:

         _inc — Inclination (°)
         _Om — Longitude of ascending node (°)
         _om — Argument of perihelion (°)
         _a — Mean distance from sun (AU)
         _M — Mean anomaly from the perihelion (°)
         _epoch_M — Date for measurement _M
         _size — Angular size (arcseconds at 1 AU)
         _e — Eccentricity
         _epoch — Epoch for _inc, _Om, and _om
         _H, _G — Parameters for the H/G magnitude model
         _g, _k — Parameters for the g/k magnitude model
        '''

        # Reading
        H, G, epoch_M, M, argper, node, i, e, n, a = self.asteroids[des]

        # Asteroid Parameters
        ast._H, ast._G, ast._M, ast._om, ast._Om, ast._inc, ast._e, ast._a = map(float,[H,G,M,argper,node,i,e,a])
        ast._epoch_M = str(convert_date(epoch_M))
        #print ast._H, ast._G, ast._M, ast._om, ast._Om, ast._inc, ast._e, ast._a
        #print convert_date(epoch_M)

        # Constants
        ast._epoch = str("2000/1/1 12:00:00")

        t=asteroid_type(ast._a,ast._e,ast._inc)

        return (ast,t)

    def phase_angle(self,elongation, earthd, sund):

        r = self.sun.earth_distance
        ratio = (earthd**2 + sund**2 - r**2)/(2e0*earthd*sund)
        ph_rad = np.arccos(round(ratio,5))
        return ph_rad*180/pi



    def vmag(self,H,G,phang,delta,r):

        phang = phang*pi/180e0

        # Constants
        A1 = 3.332; A2 = 1.862
        B1 = 0.631; B2 = 1.218
        #C1 = 0.986; C2 = 0.238

        # phase functions
        f = lambda A, B, ph: np.exp((-A)*np.tan(5e-1*ph)**B) + 1e-10

        # reduced magnitude
        rmag =  H - 2.5*np.log10((1 - G)*f(A1,B1,phang) + G*f(A2,B2,phang))

        # apparent visual magnitude
        return rmag + 5*np.log10(r*delta)


    def compute(self,mylist,delta=0):
        '''
        Compute positions and other values for asteroids in mylist. Do twice (if delta <>0) to compute PA and SPEED
        '''
        dtypes=np.dtype([("KEY","|U7"),("PRECOVERY",np.int16),("TYPE","|U30"),("DATETIME","|U25"),("MJD",np.float64),("EPOCH","|U10"),\
        ("RA",np.float64),("DEC",np.float64),("MAG",np.float64),("SPEED",np.float64),("PA",np.float64),("PHASE",np.float64),("EARTH_DIS",np.float64),\
                ("SUN_DIS",np.float64),("ELONG",np.float64),("SUN_SEPARATION",np.float64)])
        astPos=[]
        for key, value in mylist.items() :
            try:
                obs_date=str(convert_date(value[2]))
                discover_Date=date_from_designation(key)
                if discover_Date>=self.here.date:
                        precovery=1
                        #print key,discover_Date
                else:
                        precovery=0
                (a,type_)=self.loadObject(key)
                #first compute actual position at datetime
                a.compute(self.here)
                ra  =a.a_ra*180/(pi)
                dec =a.a_dec*180/pi
                #print key,value
                #print ra,dec
                phang=self.phase_angle(a.elong,a.earth_distance,a.sun_distance)
                vmag=self.vmag(a._H,a._G,phang,a.earth_distance,a.sun_distance)
                sun_separation=ephem.separation(self.sun,a)
                ldate=self.here.date.datetime().strftime('%Y-%m-%d %H:%M:%S')
                ddate="{:18.11f}".format(self.here.date+dubliJDoffset-MJDoffset)

                #then compute for datetime+delta if delta!=0
                #to calculate SPEED and PA
                if delta !=0:
                        self.here.date+=delta
                        a.compute(self.here)
                        ra_  =a.a_ra*180/(pi)
                        dec_ =a.a_dec*180/pi
                        pa=PA(ra,dec,ra_,dec_)
                        sp=speed(delta,ra,dec,ra_,dec_)
                        self.here.date-=delta
                else:
                        pa=np.nan
                        sp=np.nan

                astPos.append((key,precovery,type_,ldate,ddate,obs_date,ra,dec,vmag,sp,pa,phang,a.earth_distance,a.sun_distance,a.elong,sun_separation))
                
            except:
                logger.exception("Fail to compute %s %s",key,value)

        nrec=len(astPos)
        Pos=np.asarray(astPos,dtype=dtypes)
        logger.debug("Adding thread:%s results (%d) to the result queue.",multiprocessing.current_process().name,nrec)
        if len(Pos)>0:
                logger.debug("Added %s",multiprocessing.current_process().name)
                self.result_queue.put(Pos)
        else:
                logger.debug("%s has zero results. Skiping",multiprocessing.current_process().name)
        logger.debug("Threath:%s end. Returning to main",multiprocessing.current_process().name)
        return Pos

    def setNames(self,date='',sufix=".MPCORB.DAT"):
        dir_dest=cfg["datempcorb"]
        dir_guestDB=cfg["guestdbdir"]
        datestart=float(cfg['date0'])
        datefrom=float(cfg['datefrom'])
        dateto=float(cfg['dateto'])
        eachdays=float(cfg['eachdays'])

        if len(date)==0:
            d = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        else:
            d = datetime.datetime.strptime(date,"%Y-%m-%d %H:%M:%S")

        d=d.strftime("%Y-%m-%d")
        jd=ephem.date(d)+dubliJDoffset
        logger.info("DATE=%s -> Julian Date:%s",date,jd)
        if not cfg['use_fix_mpcorb']=='True':
          if jd>=dateto:
            logger.error("date %s is outside off orbital DB range.DATETO %s" ,jd,dateto)
            self.mpcorbfile=dir_dest+'/kk.p'
            self.guestDB=dir_guestDB+'/kk.p'
            return


          if jd<=datefrom:
            logger.error("date %s is outside off orbital DB range. DATEFROM %s" ,jd,datefrom)
            self.mpcorbfile=dir_dest+'/kk.p'
            self.guestDB=dir_guestDB+'/kk.p'
            return

        jd=int(jd)
        dateDistance=round((jd-datestart)/eachdays)
        mpcorbprefix="%0d" % (datestart+dateDistance*eachdays)
        logger.info("Datestar=%s DateDistnace=%s MPCORBprefix=%s",datestart,dateDistance,mpcorbprefix)

        if cfg['use_fix_mpcorb']=='True':
                self.mpcorbfile=dir_dest+'/FIX_MPCORB.DAT'
                #self.guestDB=dir_guestDB+'/FIX_guest_'+getToday()+".p"
                dayPrefix=d[:10]
                self.guestDB=dir_guestDB+'/FIX_guest_'+dayPrefix+".p"
        else:
                self.mpcorbfile=dir_dest+'/'+mpcorbprefix+sufix
                self.guestDB=dir_guestDB+'/guest_'+str(jd)+".p"

        logger.info("Setname. MPCORB FILE:%s",self.mpcorbfile)
        logger.info("Setname. GUEST FILE:%s",self.guestDB)
        return jd

    def getMPCORB(self,date=''):
        self.setNames(date)
        logger.info("Looking for MPCORB file:%s",self.mpcorbfile)
        if not os.path.isfile(self.mpcorbfile):
            logger.error("MPCORB file not found.")
            return
        else:
            logger.info("MPCORB file found.")

        self.loadMPCorb(self.mpcorbfile)






    def windowMPC(self,ra,dec,r,astType=[]):
        #Asteroids with speed above this are always taken into acount
        speed_=3.
        #margin is to asure all posibles asteroids are computed
        #include 1º for parallax errors (max at moon distant)
        #and speed_*24*60 arcsec to take into acount asteroids displacement
        margin=1+speed_*24.*60./3600.
        logger.info("Windows filter. Margin:%s",margin)
        r=r+margin
        
        #data=self.guestPos.copy()
        data=self.guestPos
        decmin=dec-r
        if decmin<-90:
            decmin=-90

        decmax=dec+r
        if decmax>90:
            decmax=90

        ramin=(360+ra-r) % 360
        ramax=(360+ra+r) % 360

        if r*2>360:
                ramin=0
                ramax=360


        logger.info("Windows filter. RAmin=%s,RAmax=%s,DECmin=%s,DECmax=%s,RA=%s,DEC=%s,r=%s",ramin,ramax,decmin,decmax,ra,dec,r)

        mask=[]
        for dat in data['TYPE']:
                s1=set(dat.split(';'))
                #print s1
                if len(astType)==1 and (astType[0]=='' or astType[0]=='All'):
                        s2=set([])
                else:
                        s2=set(astType)

                if len(s2)==0:
                        mask.append(True)
                elif len(s1.intersection(s2))!=0:
                        mask.append(True)
                else:
                        mask.append(False)                ,self.mpcorbfile
        mask=np.array(mask)
        if len(mask)!=0:
                data=data[mask]
        else:
                logger.warning("AREA WITHOUT ASTEROIDS. RAmin=%s,RAmax=%s,DECmin=%s,DECmax=%s,RA=%s,DEC=%s,r=%s",ramin,ramax,decmin,decmax,ra,dec,r)
                filter_asteroid ={}
                return filter_asteroid

        if ramin<ramax:
            flt=(data['RA']<=ramax) & (data['RA']>=ramin) & (data['DEC']<=decmax) & (data['DEC']>=decmin) | (data['SPEED']>=speed_)
        else:
            #p.e. ra=0 r=10 => ramin=-10 => ramin=350;ramax=10 => ra>350 | ra <10
            flt=((data['RA']<=ramax) | (data['RA']>=ramin)) & (data['DEC']<=decmax) & (data['DEC']>=decmin) | (data['SPEED']>=speed_)


        #filterkeys=map(lambda x:x[0],data[flt])
        filterkeys=data[flt]['KEY']
        filter_asteroid ={}
        for key in filterkeys:
                try:
                        filter_asteroid[key]=self.asteroids[key]
                except:
                        logger.exception("KEY %s DOES NOT FOUND IN mpcorb.dat. It should not ocurre",key)



        #print filterkeys
        return filter_asteroid




    def filterMPC(self,date,ra,dec,r,astType=[]):
        logger.info("Filtering by: Date:%s,RA=%s DEC=%s,r=%s",date,ra,dec,r)
        #Check if is need to switch MPCORB.DAT & guestDB
        if ephem.date(date)!=self.guestDate:
            self.init(date)

        mylist=self.windowMPC(ra,dec,r,astType)
        self.setDate(date)
        #
        data=self.threadCompute(mylist,delta=ephem.minute)


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
        s=data[flt]

        return s

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
        identify posible asteroids in the FOV.
        Return True if ready to use False otherwise.
        '''

        self.setObserver(lon=cfgOBS["lon"],lat=cfgOBS["lat"],elev=cfgOBS["elev"])
        self.setNames(date)

        dir_dest=os.path.dirname(self.guestDB)
        if not os.path.exists(dir_dest):
            os.makedirs(dir_dest)

        #Check if someone is doing now
        #(not locked)
        lockfile=self.guestDB+'.lock'
        if  os.path.isfile(lockfile):
            return False

        #Check if allready exist
        if  os.path.isfile(self.guestDB):
            return True

        self.getMPCORB(date)


        logger.info("INIT DB FOR DATE:%s",date)
        #lock while computing...
        with open(lockfile,'w') as f:
                f.write('lock')

        #Call compute
        self.setDate(date)
        dummy=self.threadCompute(self.asteroids,ephem.hour*12)

        #pick only relevant variables and mag filter
        guestPos=dummy[['KEY','RA','DEC','MAG','SPEED','TYPE']]
        flt=(guestPos['MAG']<=float(cfg['maxmag']))
        guestPos=guestPos[flt]
        pickle.dump(guestPos, open( self.guestDB, "wb" ),2 )

        #unlock
        os.remove(lockfile)
        return True




    def threadCompute(self,asteroids,delta=0):
        '''
        Speed up. Make a chunk of asteroids dict and process in
        one thread per CPU core.
        asteroids is a dict contain elements
        delta is the time to compute PA,SPEED
        '''
        ncores=multiprocessing.cpu_count()
        if len(asteroids)<=ncores*10:
            logger.info("Not to much asteroids(%d). Going single thread", len(asteroids))
            return self.compute(asteroids,delta)

        chunk_size=int(len(asteroids)/ncores)

        asteroids_chunks=[dict(list(asteroids.items())[x:x+chunk_size]) for x in range(0, chunk_size*ncores,chunk_size)]
        if len(asteroids) % ncores !=0:
                asteroids_chunks.append(dict(list(asteroids.items())[chunk_size*ncores:]))
        logger.info("CORES:%s #ASTEROIDS:%s CHUNK_SIZE:%s #CHUNKS:%s",ncores,len(asteroids),chunk_size,len(asteroids_chunks))

        try:
            logger.info("Creating Threads ...")
            threadsPool=[]
            #define threads

            for i,chunk in enumerate(asteroids_chunks):
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

            #print "Threads got..."
            # Wait for all of them to finish
            [x.join() for x in threadsPool]
            #print "Threads close..."
            for i,r in enumerate(result):
                if i==0:
                    final_result=r
                    continue
                final_result=np.hstack((final_result,r))
            total_asteroids=len(final_result)
            n_chunks=len(asteroids_chunks)
            rest=total_asteroids-ncores*chunk_size
            logger.info("Processed  %d  asteroids on %d cores. %d chuncks x %d each + 1 chunk x %d ",total_asteroids,ncores ,n_chunks-1,chunk_size,rest)
            return final_result
        except Exception as e:
            logger.exception("Main loop exception:")






if __name__ == '__main__':
    '''
        Test
    '''
    mpc=MPCEphem()

    print(mpc.filterMPC("2018-09-13 12:31:38",30.2,12,.2))
    #print(mpc.filterMPC("1971-09-14 22:23:09",41.2,-13,1))
    #print(mpc.filterMPC("2026-03-14 02:23:09",4.2,-13,1))

