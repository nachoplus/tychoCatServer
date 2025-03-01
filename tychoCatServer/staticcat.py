#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
.. module:: staticcat
   :platform: Unix, Windows
   :synopsis:

.. moduleauthor:: Nacho Mas <mas.ignacio@gmail.com>

"""
import astropy.io.fits as pyfits
import numpy as np
import os
from .config import *
import logging

# Create a custom logger
logger = logging.getLogger(__name__)

catalogs={
    'hyperleda':f'{pkgpath}/STATIC_CATS/HYPERLEDA_6.cat',
    'hip2':f'{pkgpath}/STATIC_CATS/HIP2.cat',
    'ngc':f'{pkgpath}/STATIC_CATS/NGC.cat',
}

class staticCat():

    def __init__(self,catalog):
        logger.info("INIT module")
        logger.info("Catalog:%s",catalog)
        self.catalogFile=catalog
        pass

    def get(self,ra,dec,r):
        w=r*2
        h=r*2
        catalog=self.catalogFile
        f=pyfits.open(catalogs[catalog])
        olddata=np.array(f[1].data)

        newtypes=[]
        for i,name in enumerate(olddata.dtype.names):
                if olddata[name].dtype.str.startswith('|S'):
                        _newtype=olddata[name].dtype.str.replace('|S','|U')
                        logger.debug("COL: %s dtype:%s need to be changed to unicode type %s. Doing",name,olddata[name].dtype.str,_newtype)
                        newtypes.append((name,_newtype))
                        logger.debug("New dtype:%s",np.dtype([(name,_newtype)]))
                else:
                        newtypes.append((name,olddata[name].dtype.str))

        _dtypes=np.dtype(newtypes)
        data=olddata.astype(_dtypes)
        logger.debug("size:%s final dtype:%s",data.shape,data.dtype)
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
    s=staticCat('hyperleda')
    print(s.get(50,-16.3,2.0))
