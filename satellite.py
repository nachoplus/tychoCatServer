#!/usr/bin/python
# -*- coding: iso-8859-15 -*-



import ephem
import numpy as np
import subprocess
import multiprocessing


from config import *
from helper import *
cfg=dict(config.items("TLE"))
cfgOBS=dict(config.items("OBSERVATORY"))

pi=np.pi

class satEphem():
    result_queue = multiprocessing.Queue()

    def get(self,date):
        self.loadTLEfile(date)
        self.setObserver(lon=cfgOBS["lon"],lat=cfgOBS["lat"],elev=cfgOBS["elev"])
        print("DATE:",date)
        self.setDate(date)
        self.pos=self.threadCompute(self.TLEs,delta=ephem.second)
        return self.pos



    def setObserver(self,lon,lat,elev,hor="00:00:00"):

        here = ephem.Observer()
        here.lat, here.lon, here.horizon  = str(lat), str(lon), str(hor)
        here.elev = float(elev)
        here.temp = 25e0
        here.pressure=0

        # setting in self
        self.here = here

    def setDate(self,date):
        self.here.date=ephem.date(date)
        print(ephem.localtime(self.here.date))





    def compute(self,satellites,delta=0):

        dtypes=np.dtype([('NAME', "|U24"), ('CAT_NUMBER',"|U6"), ('KEY', "|U6"),('DATETIME',"|U25"), ('MJD', np.float64), ('MAG', np.float64), \
                        ('RA', np.float64), ('DEC', np.float64),("SPEED",np.float64),("PA",np.float64), ('AZ', np.float64), ('ALT', np.float64), ('RANGE', np.float64), \
                        ('ELEVATION', np.float64), ('RANGE_SPEED', np.float64), ('ECLIPSED', np.bool),('EPOCH',"|U12")])


        astPos=[]
        for i,tle in enumerate(satellites):
            print ("TLE:",tle)
            lines=tle.split('\r')[:-1]
            print (lines)
            try:
                    sat=ephem.readtle(lines[0],lines[1],lines[2])
                    sat.compute(self.here)
            except:
                    print("ERROR computing or reading TLE:\n",lines)
                    continue

            if sat.range_velocity==0:
                print("FAIL to compute Sat:",sat.name,self.here.date)
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

            if int(dummy[:2])>50:
                year='19'+dummy[:2]
            else:
                year='20'+dummy[:2]
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

            astPos.append((sat.name,sat.catalog_number,int_number,ldate,ddate,sat.mag,ra,dec,sp,pa, \
                            sat.az*180/pi,sat.alt*180/pi,sat.range,sat.elevation,sat.range_velocity,sat.eclipsed,epoch))


        nrec=len(astPos)
        Pos=np.asarray(astPos,dtype=dtypes)
        if len(Pos)>0:
           self.result_queue.put(Pos)
        return Pos

    def loadTLEfile(self,date):
        '''
        Chose and load the most apropiate TLE file.
        '''
        self.downloadTLEfile()
        dir_dest=cfg["tledir"]
        d=ephem.date(date)
        dirs = os.listdir( dir_dest)
        print(dirs)
        for hh in (list(map(lambda x:'20'+x[:8].replace('-','/')+" 00:00:00",dirs))):
            print(hh)
            print(ephem.date(hh))
        days=list(map(lambda x:ephem.date('20'+x[:8].replace('-','/')+" 00:00:00"),dirs))
        print(days)
        distance=list(map(lambda x:np.abs(d-x),days))
        print(distance)
        minD=np.min(distance)
        minIndex=distance.index(minD)
        BetterDay=dirs[minIndex]
        #print minD,minIndex,dirs[minIndex]
        print("TLE for:",d,"Best available",BetterDay)
        self.tlefile=dir_dest+'/'+BetterDay
        nrec=self.readTLEfile(self.tlefile)
        print("TLE from:",self.tlefile,nrec," REG LOADED")

    def downloadTLEfile(self):
        '''
        Download TLE file of the day and rename
        '''
        dir_dest=cfg["tledir"]
        if not os.path.exists(dir_dest):
            os.makedirs(dir_dest)
        tlefile=dir_dest+'/'+getToday()+".TLE"

        if not os.path.isfile(tlefile):
            print("TLE %s not exit. Downloading" % os.path.basename(tlefile))
            res=subprocess.getoutput("wget -c "+cfg["tleurl"])
            print(res)
            print(os.path.basename(cfg["tleurl"]))
            res=subprocess.getoutput("unzip "+os.path.basename(cfg["tleurl"]))
            print(res)
            res=subprocess.getoutput("mv ALL_TLE.TXT "+tlefile)
            print(res)
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
            print("TLE %s already downloaded" % os.path.basename(tlefile))




    def readTLEfile(self,url):
        '''
        Read the TLE file and group by 3 lines
        '''
        self.TLEs=[]
        f=open(url)
        theList=f.read().split('\n')
        f.close()
        N=3
        tles = [''.join(theList[n:n+N]) for n in range(0, len(theList), N)]
        self.TLEs = tles[:-1]
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
            print("Not to much satellites(%d). Going single thread" % len(satellites))
            return self.compute(satellites,delta)

        chunk_size=int(len(satellites)/ncores)

        satellites_chunks=[satellites[x:x+chunk_size] for x in range(0, chunk_size*ncores,chunk_size)]
        if len(satellites) % ncores !=0:
                satellites_chunks.append(satellites[chunk_size*ncores:])

        print("CORES/AST/CHUNK/cho SIZE:",ncores,len(satellites),chunk_size,len(satellites_chunks))

        try:
            print("Creating Threads ...")
            threadsPool=[]
            #define threads

            for i,chunk in enumerate(satellites_chunks):
                #print chunk
                #t = Thread(None,self.compute,None, (chunk,))
                t=multiprocessing.Process(target=self.compute, args=(chunk,delta,))
                threadsPool.append(t)

            # Start all threads
            [x.start() for x in threadsPool]

            result=[]
            for j in threadsPool:
                result.append(self.result_queue.get())

            # Wait for all of them to finish
            [x.join() for x in threadsPool]

            for i,r in enumerate(result):
                if i==0:
                    final_result=r
                    continue
                final_result=np.hstack((final_result,r))

            print(len(final_result))
            print("%d compute Threads.Processing %d x %d satellites" % (ncores,ncores,chunk_size))
            return final_result
        except Exception as e:
            print("Thread error...")
            print(e)


if __name__ == '__main__':
    s=satEphem()
    data=s.filterSat("2014-09-21 01:00",25,-6.3,2.0)
    print(data)
    #flt=(data['ELEVATION']>=1E8)
    #print data[flt]
