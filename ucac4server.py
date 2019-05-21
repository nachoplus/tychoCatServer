#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
.. module:: ucac4server
   :platform: Unix, Windows
   :synopsis:

.. moduleauthor:: Nacho Mas <mas.ignacio@gmail.com>

"""
import ucac4
import numpy as np
import os
from config import *
cfg=dict(config.items("UCAC4"))

class ucac4server():

    def __init__(self):
	    usual_header = "UCAC4 RA DEC MAG1 MAG2 MAG_ERR OBJECT_TYPE DOUBLE_STAR \
		RA_EPOCH DEC_EPOCH RA_ERR DEC_ERR nt nu nc   pmRA  pmDEC pmRAsigma pmDECsigma \
		2MASSID mag_j mag_h mag_k e2mphos0 e2mphos1 e2mphos2 icq_flag0 icq_flag1 icq_flag2 Bmag Vmag gmag rmag \
		imag sig_B sig_V sig_g sig_r sig_i catflags Ya Leda 2MXFLAGS 2MXID UCAC2ID"
	    headers=" ".join(usual_header.split()).split()
	    print(len(headers))
	    headers_units=['|S25','f8','f8','f8','f8','f8','u2','u2','f8','f8','f8','f8','u2','u2','u2','f8','f8','f8','f8','u4','f8',\
	             'f8','f8','f8','f8','f8','f8','f8','f8','f8','f8','f8','f8','f8','f8','f8','f8','f8','f8','u4','u1','u1','u1','u4','|S25']
	    print(len(headers_units))
	    strType=[]
	    for i,header in enumerate(headers):
        	strType.append((header,headers_units[i]))
	    #print strType
	    self.dt=np.dtype(strType)
	    #print dt

    def load(self,ra,dec,r):
	w=r*2
	h=r*2
        path=cfg['datadir']+'/u4b'
	filename=cfg['base_dir']+"/tmp.stars"
        starsfile=ucac4.fopen(filename, 'wr')
        f=0
        print(ucac4.extract_ucac4_stars(starsfile,ra,dec,w,h,path,f))
        ucac4.fclose(starsfile)
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
