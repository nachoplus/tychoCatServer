#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
.. module:: ucac4server
   :platform: Unix, Windows
   :synopsis:

.. moduleauthor:: Nacho Mas <mas.ignacio@gmail.com>

"""
import numpy as np
import os
import logging

from .ucac4 import *
from .config import *



# Create a custom logger
logger = logging.getLogger(__name__)


class ucac4server():

    def __init__(self):
            usual_header = "UCAC4 RA DEC MAG1 MAG2 MAG_ERR OBJECT_TYPE DOUBLE_STAR \
                RA_EPOCH DEC_EPOCH RA_ERR DEC_ERR nt nu nc   pmRA  pmDEC pmRAsigma pmDECsigma \
                2MASSID mag_j mag_h mag_k e2mphos0 e2mphos1 e2mphos2 icq_flag0 icq_flag1 icq_flag2 Bmag Vmag gmag rmag \
                imag sig_B sig_V sig_g sig_r sig_i catflags Ya Leda 2MXFLAGS 2MXID UCAC2ID"
            headers=" ".join(usual_header.split()).split()
            #logger.info("Headers:%s",headers)
            logger.info("INIT module")
            headers_units=['|U25','f8','f8','f8','f8','f8','u2','u2','f8','f8','f8','f8','u2','u2','u2','f8','f8','f8','f8','u4','f8',\
                     'f8','f8','f8','f8','f8','f8','f8','f8','f8','f8','f8','f8','f8','f8','f8','f8','f8','f8','u4','u1','u1','u1','u4','|S25']
            strType=[]
            for i,header in enumerate(headers):
                strType.append((header,headers_units[i]))
            #print strType
            self.dt=np.dtype(strType)
            #print dt

    def load(self,ra,dec,r):
        w=r*2
        h=r*2
        path=f'{ucac4data_dir}/u4b'
        filename=f"{storage_dir}/tmp.stars"
        starsfile=fopen(filename, 'wr')
        f=0
        logger.info("retriving %s stars",extract_ucac4_stars(starsfile,ra,dec,w,h,path,f))
        fclose(starsfile)
        with open(filename, 'r') as stars:
                lines=[line.strip() for line in stars]
        os.remove(filename)
        l=[tuple(line.split(',')) for line in lines]
        s=np.array(l,dtype=self.dt)
        return s
        
    def get(self,ra,dec,r):
         s=self.load(ra,dec,r)
         return s[['UCAC4','RA','DEC','MAG1','MAG2','pmRA','pmDEC','RA_ERR','DEC_ERR','MAG_ERR','pmRAsigma','pmDECsigma']]

if __name__ == '__main__':
    s=ucac4server()
    print(s.get(50,-16.3,2.0))
