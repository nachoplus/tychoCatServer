#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
.. module:: ucac4server
   :platform: Unix, Windows
   :synopsis:

.. moduleauthor:: Nacho Mas <mas.ignacio@gmail.com>

"""
import pyfits
import numpy as np
import os
from config import *
cfg=dict(config.items("STATIC_CATS"))

class staticCat():

    def __init__(self,catalog):
	self.catalogFile=catalog
	pass

    def get(self,ra,dec,r):
	w=r*2
	h=r*2
        catalog=self.catalogFile
	f=pyfits.open(cfg[catalog])
	data=f[1].data

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

	


if __name__ == '__main__':
    s=hyperleda()
    print s.get(50,-16.3,2.0)
