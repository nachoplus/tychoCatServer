#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
.. module::
   :platform: Unix, Windows
   :synopsis:

.. moduleauthor:: Nacho Mas <mas.ignacio@gmail.com>

"""
import time
import http.server as BaseHTTPServer
import os
#from urlparse import parse_qs,urlparse
from urllib.parse import urlparse
from urllib.parse import parse_qs

from socketserver import ThreadingMixIn
import threading
import datetime
from math import sqrt
import astropy.io.fits as pyfits
import re

import ucac4server
import satellite
import asteroids
import staticcat

import xlsxwriter
from io import BytesIO
import pickle



from config import *
from helper import *

import logging

# Create a custom logger
logger = logging.getLogger('catserver')

cfg=dict(config.items("DEFAULT"))


#HOST_NAME = cfg['server_address'] 
#To use include server_address=<IP> line in your main.cfg

#By default listen all adapters
HOST_NAME = '0.0.0.0'

PORT_NUMBER = int(cfg['server_port']) # Maybe set this to 9000.

def last_flagged(seq):
    seq = iter(seq)
    a = next(seq)
    for b in seq:
        yield a, False
        a = b
    yield a, True 

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    mpcEngine=asteroids.MPCEphem()

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        """Respond to a GET request."""
        services_cmd={'ucac4':self.ucac4,'sat':self.sat,'mpc':self.mpc,'mpcsearch':self.mpcsearch,'help':self.help,'viz-bin/aserver.cgi':self.ucac4scamp,'hyperleda':self.hyperleda,'hip2':self.hip2,'ngc':self.ngc,'favicon.ico':self.favicon}
        service=urlparse(self.path).path[1:]
        #print service
        qs = parse_qs(urlparse(self.path).query)
        services=list(services_cmd.keys())
        #print services
        if service not in services:
            services_cmd['help'](qs)
            '''
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write('<h1>Service:'+service+' NOT FOUND</h1>')
            self.wfile.write('Services available:'+str(list(services_cmd.keys())))
            ''' 
            return
        if service=='viz-bin/aserver.cgi':
                #Special handler to mimic UCAC4 vizier server import re
                logger.info("VIZ:%s",urlparse(self.path).query)
                response=services_cmd[service](urlparse(self.path).query)
        else:
                response=services_cmd[service](qs)

    def help(self,params):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(binpath+'/helptext.txt','r') as f:
            data=f.read()
        self.wfile.write(data.encode('ascii'))

    def favicon(self,params):
        self.send_response(200)
        self.send_header("Content-type", "image/x-icon")
        self.end_headers()
        with open('favicon.ico','rb') as f:
            data=f.read()
        self.wfile.write(data)

    def static(self,params,catalog):
        formatType,date,ra,dec,r,Type =self.standardParams(params)
        s=staticcat.staticCat(catalog)
        data=s.get(ra,dec,r)
        self.sendOutput(data,formatType)

    def hyperleda(self,params):
        self.static(params,'hyperleda')

    def hip2(self,params):
        self.static(params,'hip2')

    def ngc(self,params):
        self.static(params,'ngc')

    def ucac4(self,params):
        formatType,date,ra,dec,r,Type =self.standardParams(params)
        s=ucac4server.ucac4server()
        #limit area to 10º to avoid overheads
        if r>10:
                r=10
        data=s.get(ra,dec,r)
        self.sendOutput(data,formatType)

    def ucac4scamp(self,params):
        #SCAMP 1.7.0 %s %s%s ucac4 -c %s %s -r %16g -lm %f,%f -m 10000000
        #SCAMP 2.0.4 %s %s%s ucac4 -c %s %s -r %16g  -m 10000000
        SCAMP="2.0.4"

        params=params.split('&')
        logger.info("ucac4scamp params:%s",params)

        
        if params[2].find('%2b')>=0 or params[2].find('+') >=0:
                sep='%2b|%2b|\+'
                sig=1
        elif params[2].find('%2d') >=0 or params[2].find('-') >=0:
                sep='%2d|%2D|\-'
                sig=-1
        elif params[2].find('%20')>=0 or params[2].find(' ') >=0:
                sep='%20| '
                sig=1

        #ra=float(params[2].split(sep)[0])
        #dec=sig*float(params[2].split(sep)[1])

        #radec=re.split(sep,params[2].strip())
        radec=params[2].strip().split(',')
        ra=float(radec[0])
        #dec=sig*float(radec[1])
        dec=float(radec[1])

        r=float(params[4])/60.

        s=ucac4server.ucac4server()
        data=s.load(ra,dec,r)

        if SCAMP=="2.0.4":
                maxstars=int(params[6])
                logger.info("ucac4scamp: RA=%s DEC=%s r=%s MAXSTARS=%s",ra,dec,r,maxstars)
                self.sendOutput(data,'scamp')
        else:
                limits=params[6].split(',')
                magmin=int(float(limits[1]))
                magmax=int(float(limits[0]))
                maxstars=int(params[8])
                logger.info("ucac4scamp: RA=%s DEC=%s r=%s MAGmin=%s MAGmax=%s, MAXSTARS=%s",ra,dec,r,magmin,magmax,maxstars)
                flt=(data['MAG1']<=magmin) & (data['MAG1']>=magmax)
                data=data[flt]
                self.sendOutput(data,'scamp')


    def sat(self,params):
        formatType,date,ra,dec,r,Type =self.standardParams(params)
        satEngine=satellite.satEphem()
        data=satEngine.filterSat(date,ra,dec,r)
        #flt=(data['SPEED']>=20000) 
        #data=data[flt]
        self.sendOutput(data,formatType)

    def mpc(self,params):
        formatType,date,ra,dec,r,astType =self.standardParams(params)
        data=self.mpcEngine.filterMPC(date,ra,dec,r,astType)
        self.sendOutput(data,formatType)



    def mpcsearch(self,params):
        formatType,date,ra,dec,r,astType =self.standardParams(params)
        keys=params.get('key',[''])
        keys=map(lambda x:x.ljust(7),keys)
        logger.info("MPC SEARCH:%s",keys)
        data=self.mpcEngine.search(keys,date,r)
        self.sendOutput(data,formatType)


    def htmlOutput(self,data):
        out='<html>'
        out +='<head><style>'
        css=open(binpath+"/lasagra.css",'r')
        out +=css.read()
        out +='</style></head>'
        out +="<div class='lasagrastyle'><table>"
        out +='<tr>'
        out += '<td>DATE</td><td>RA</td><td>DEC</td><td>R</td><td>TYPE</td>'
        out +='<tr>'
        for t in self.par[1:]:
            out += '<td>'+str(t)+'</td>'
        out +='</tr>'
        out +='</tr>'
        out +='</table></div>'
        out +="<div class='lasagrastyle'><table>"
        out +='<tr>'
        for t in data.dtype.names:
            out += '<td>'+t+'</td>'
        out +='</tr>'
        for d in data:
            out += '<tr>'
            for f in d:
                out += '<td>'+str(f)+'</td>'
            out +='</tr>'
        out +='</table></div></html>'
        return out

    def csvOutput(self,data):
        out=''
        for t in data.dtype.names:
            out += t+','
        out=out[:-1]
        out +='\n'
        for d in data:
            for f,is_last in last_flagged(d):
                if is_last:
                        out += str(f)+'\n'
                else:
                        out += str(f)+','
        return out

# FIXED. Something is wrong with this pyfits version and StringIO
    def fitsOutput(self,data):
        from astropy.table import Table
        #out = BytesIO()
        out = open(cfg['base_dir']+'/tmp.fit','wb')
        t=Table(data)
        t.write(out,format='fits')
        out.close()
        out = open(cfg['base_dir']+'/tmp.fit','rb')
        the_stream = out.read()   # here is your file content
        out.close()
        return the_stream



        columns=[]


        for i,t in enumerate(data.dtype.names):
                #print(data.dtype[i],data.dtype[i].char)
                #numpy to fits type casting
                if np.issubdtype(data.dtype[i], float):
                        f='D'
                elif data.dtype[i].char == 'S' or data.dtype[i].char == 'a' or data.dtype[i].char == 'U':
                        f='A'+str(data.dtype[i].itemsize)
                elif data.dtype[i].char == 'i' or data.dtype[i].char == 'u' or data.dtype[i].char == 'h':
                        f='I'
                elif data.dtype[i].char == '?':
                        f='L'
                columns.append(pyfits.Column(name=t,format=f))

        tbhdu = pyfits.BinTableHDU.from_columns(columns)
        tbhdu.data= np.array(data).view(tbhdu._data_type)
        tbhdu.writeto(out, overwrite=True)
        out.close()
        out = open(cfg['base_dir']+'/tmp.fit','rb')
        the_stream = out.read()   # here is your file content
        out.close()
        return the_stream


        #tbhdu=pyfits.new_table(columns)
        #print columns
        tbhdu.data= np.array(data).view(tbhdu._data_type)

        hdu = pyfits.PrimaryHDU()
        thdulist = pyfits.HDUList([])
        thdulist.append(tbhdu)
        thdulist.writeto(out, clobber=True)
        out.close()
        out = open(cfg['base_dir']+'/tmp.fit','rb')
        the_stream = out.read()   # here is your file content
        out.close()
        return the_stream



    def mpcOutput(self,data):
        #TODO adapt data prior to invoke.
        import ephem
        out=''
        for d in data:
            fecha=d['DATETIME'][0:10].replace('-',' ')
            hh=float(d['DATETIME'][11:13])
            mm=float(d['DATETIME'][14:16])
            ss=float(d['DATETIME'][17:19])
            #print d['KEY'],fecha,hh,mm,ss,ephem.hours(ephem.degrees(str(d['RA']))),ephem.degrees(str(d['DEC']))
            hhdec=round((hh*3600.+mm*60.+ss)/(24*3600)*100000,0)
            fecha=fecha+'.'+"%05.0f" % (hhdec)+" "
            id=d['KEY']

            ra_hh,ra_mm,ra_ss=("%11s" % ephem.hours(ephem.degrees(str(d['RA'])))).split(':')
            #print ra_hh,ra_mm,ra_ss
            ra="%02d %02d %04.1f" % (float(ra_hh),float(ra_mm),float(ra_ss))

            dec_dd,dec_mm,dec_ss=("%11s" % ephem.degrees(str(d['DEC']))).split(':')
            #print dec_dd,dec_mm,dec_ss
            dec="%+03d %02d %05.2f" % (float(dec_dd),float(dec_mm),float(dec_ss))
            #print ra,"/",dec
            #rastr="%11s" % (ephem.degrees(str(d['DEC'])))
            #decstr="%11s" % (ephem.degrees(str(d['DEC'])))
            #ra=rastr.replace(':',' ')
            #dec=decstr.replace(':',' ')
            #id=d['INT_NUMBER'][-7:]

            #[MPnumber,Provisional,Discovery,Note1,Note2,Date,RA,DEC,Mag,Band,Observatory]
            #     492A002  C2014 09 03.13366 03 57 53.26 +05 44 22.9          18.6 V      J75
            #     K07VF3N  C2014 09 14.83670  0 53 58.89   0 07 53.1          20.2 V      J75

            obs=('',id,'','','C',fecha,ra,dec,d['MAG'],'V','J75')
            out+='%5s%7s%1s%1s%1s%16s%-12s%-12s        %5.1f %1s      %3s\n' % obs
        return out

    def excelOutput(self,data):
        out = BytesIO()
        workbook = xlsxwriter.Workbook(out)
        worksheet = workbook.add_worksheet()
        Headerformat = workbook.add_format()
        Headerformat.set_bold()
        Headerformat.set_bg_color('green')
        Headerformat.set_align('center')
        for col,t in enumerate(data.dtype.names):
            worksheet.write_string(0, col,t,Headerformat)

        for row,d in enumerate(data):
            for col,item in enumerate(d):
                worksheet.write(row+1, col,item)

        workbook.close()

        out.seek(0)
        the_stream = out.read()   # here is your file content
        out.close()
        return the_stream

    def scampOutput(self,data):
        '''
        Special output to mimic CDS Strasbourg server output
        as need by scamp refcatlog.
        Not finished but enough to work with scamp
        '''
        out="#======== UCAC4 server (2014-09-25, V0.01) ======== LA SAGRA mimic CDS, Strasbourg ========\n"
        out+="#Center: dummy dummy\n"
        out+='#UCAC4    |    RA  (ICRS) Dec     +/- +/-  mas  EpRA    EpDE  | f.mag  a.mag  +/- |of db| Na  Nu  Cu| pmRA(mas/yr)pmDE  +/-  +/-|MPOS1      UCAC2      Tycho-2    |     2Mkey   Jmag  +/-:cq   Hmag  +/-:cq   Kmag  +/-:cq|  Bmag:1s.   Vmag:1s.   gmag:1s.   rmag:1s.   imag:1s.|gc.HAbhZBLNS|LED 2MX|;     r(")\n'
        for d in data:
            mas=sqrt(d['RA_ERR']*d['RA_ERR']+d['DEC_ERR']*d['DEC_ERR'])
            out +="%10s|%011.7f%+011.7f%4s%4s%5s%8.2f%8.2f|" % (d['UCAC4'],d['RA'],d['DEC'],int(d['RA_ERR']),int(d['DEC_ERR']),int(mas),d['RA_EPOCH'],d['DEC_EPOCH'])
            out +="%6.3f %6.3f %4.2f |%2s%3s|" % (d['MAG1'],d['MAG2'],d['MAG_ERR']/100,int(d['OBJECT_TYPE']),int(d['DOUBLE_STAR']))
            out +="%3s %3s %3s|" % (int(d['nt']),int(d['nu']),int(d['nc']))
            out +="%8.1f %8.1f %4.1f %4.1f|" % (d['pmRA']/10,d['pmDEC']/10,d['pmRAsigma']/10,d['pmDECsigma']/10)
            out +="%9s %s             |" % (d['2MXID'],d['UCAC2ID'].strip())
            out +="%10s" % (d['2MASSID'])
            out +="\n"

        return out

    def pickleOutput(self,data):
        return pickle.dumps(data)

    def sendOutput(self,data,formatType):
        self.send_response(200)

        if formatType.startswith('html'):
            output=self.htmlOutput(data)
            size=len(output)
            contentType="text/html"

        if formatType.startswith('csv'):
            output=self.csvOutput(data)
            contentType="text/csv"
            size=len(output)
            self.send_header("Content-Length",str(size))
            self.send_header("Content-Disposition", 'attachment;filename=output.csv')

        if formatType.startswith('fits'):
            output=self.fitsOutput(data)
            size=len(output)
            self.send_header("Content-Length",str(size))
            self.send_header("Content-Disposition", 'attachment;filename=output.fits')
            contentType="application/fits"

        if formatType.startswith('scamp'):
            output=self.scampOutput(data)
            size=len(output)
            self.send_header("Content-Length",str(size))
            contentType="text/text"


        if formatType.startswith('mpc'):
            output=self.mpcOutput(data)
            size=len(output)
            self.send_header("Content-Length",str(size))
            contentType="text/text"


        if formatType.startswith('excel'):
            output=self.excelOutput(data)
            size=len(output)
            self.send_header("Content-Length",str(size))
            contentType="application/xlsx"
            self.send_header("Content-Disposition", 'attachment;filename=output.xlsx')

        if formatType.startswith('pickle'):
            output=self.pickleOutput(data)
            size=len(output)
            self.send_header("Content-Length",str(size))
            contentType="application/python-pickle"

        self.send_header("Content-type",contentType)
        self.end_headers()
        logger.info("START SENDING %s bytes",size)
        try:
                self.wfile.write(output.encode('ascii'))
                logger.debug("ASCII mode")
        except:
                self.wfile.write(output)
                logger.debug("Binary mode")
        logger.info("END SENDING")

    def standardParams(self,params):
        formatType=params.get('format',['html'])[0]
        '''
        if cfg['fix_date']=='True':
                cfgMPCORB=dict(config.items("MPCORB"))
                date0JD=float(cfgMPCORB['date0'])
                unixT0=(date0JD-2440587.5) * 86400
                date=datetime.datetime.fromtimestamp(unixT0).strftime("%Y-%m-%d %H:%M:%S")
                print "Force date:",date
        else:
                now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                date=params.get('date',[now])[0]
        '''
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        date=params.get('date',[now])[0]
        ra=float(params.get('ra',[0])[0])
        dec=float(params.get('dec',[0])[0])
        r=float(params.get('r',[1])[0])
        astType=params.get('type',[''])
        self.par=(formatType,date,ra,dec,r,astType)
        return (formatType,date,ra,dec,r,astType)





class ThreadedHTTPServer(ThreadingMixIn,BaseHTTPServer.HTTPServer):
    """Handle requests in a separate thread."""
    pass

if __name__ == '__main__':
    #server_class = BaseHTTPServer.HTTPServer
    server_class = ThreadedHTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    httpd.daemon=True
    logger.info("Server Starts on  %s:%s" ,HOST_NAME, PORT_NUMBER)
    if cfg['use_fix_mpcorb']=='True':
        logger.warning("use_fix_mpcorb='True' is set")
        logger.warning("All calculation will be done for a FIX_MPCORB.DAT")
        logger.warning("Calculation for distant dates may be inacurate.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logger.info("Server Stops - %s:%s" ,HOST_NAME, PORT_NUMBER)
