Introduction
============
tychoCatServer is a ephemerids server. Its aim is to get a collection of objects present in a sky region at given time. 

At this time tychoCatServer provide ephemerids for:
* satellites in NORAD database. 
* know asteroids in Minor Planet Center (MPC).
* UCAC4 star catalog.(over 113 million objects)
* Hipparcos 2 start catalog
* NGC catalog
* Hyperleda galaxies catalog
* Planets and natural satellite (to be done)


The output format will be html,csv,excel,fits,pickle,json or mpc 

This software is heavily base on pyephem for calculations https://github.com/brandon-rhodes/pyephem.
Also use a Bill Gray **integrat** from project pluto http://www.projectpluto.com/pluto/integrat.htm to propagate asteroids orbital element to differents dates.

Installation
============
Its recomended install under a python virtual enviroment to do not mesh the host's  python ecosystem.

```console
python3 -m venv venv
source venv/bin/activate
git clone https://github.com/nachoplus/tychoCatServer.git
cd tychoCatServer
pip install .
```
Alternative you can install directly from github:
```console
python3 -m venv venv
source venv/bin/activate
pip install git+https://github.com/nachoplus/tychoCatServer.git@new_updater
```

>Do not forget to create a config file (see next section)


Config file tychoCatServer.cfg
==============================

This file is mandatory and could be in the following locations:
* /etc/tychoCatServer/tychoCatServer.cfg
* $HOME/.config/tychoCatServer/tychoCatServer.cfg
* ./config/tychoCatServer.cfg
* . (current dir)

The lattest take precent over the others.

In this file are all the relevant variables. Please edit to reflect your setup.



Asteroids
=========

Due to the large MPC asteroid database some speed up are needed. Basically a preliminar calculation is done for all the objects at daily basic. This results are used to prefilter asteroids in a given region and then precise position are calculated for them.

This cache mechanish has two modes of operation:

1. Fix MPCORB.DAT: Is the user responsability to download a recent MPCORB.DAT from http://www.minorplanetcenter.net/iau/MPCORB.html . Then cache position are calculate for a given day the first time that is needed. As osculating orbital elements change over the time this mode of operation only works well for dates near (+-50 days) the MPCORB.DAT file. This mode of operation is oriented to Observatory ephemerids server. (use_fix_mpcorb='True') 

2. MPCORB.DAT is only valid for a dates near (+-100days) its epoch. To overhelm this limitation the elements in MPCORB.DAT are propagated to diferents epoch using 'integrat', thus acurate calculation will be done. In this mode updateMPCORB.py script must be running all the time in order to update the database with new asteroids. This mode of operation is oriented to precoveries and general ephemerids server for far dates.(use_fix_mpcorb='False') 




__Installing__
----------
Edit config/config.cfg and adapt to your needs some parameters.
Mandatory changes are:
```python
#MPC operation mode
use_fix_mpcorb='True'
#HOME of scrips
home_dir=/home/nacho/work/tychoCatServer
#Home of  cache and catalog data
base_dir=%(home_dir)s/../var/catserver 
```
for use_fix_mpcorb='False' the following setting are also relevant:
```python
#center epoch Julian Date
date0=2457022.500000 
#Min epoch Julian Date. It must be date0-Delta ->symetric from date0
datefrom=2457016.500000
#Max epoch Julian Date. It must be date0+Delta ->symetric from date0
dateto=2457028.500000
#propagate stepsize for MPCORB file
eachdays=50
```

Then run `bootstrap.py` . This executable compile and download all needed files.
This are the steps that bootstrap.py performs:

1. Compile ucac4 C rutines using swig.

2. Download (3.2Gb) UCAC4 from ftp://cdsarc.u-strasbg.fr/pub/cats/I/322A/UCAC4

3. Compile integrat from Project Pluto (http://www.projectpluto.com/pluto/integrat.htm). Is the Bill Gray original lunar rutines except I introduce a line in linlunar.mak in order to compile integrat.

4. Download (109Mb) JPL ephem  from: ftp://ssd.jpl.nasa.gov/pub/eph/planets/Linux/de430/linux_p1550p2650.430 needed by integrat.


It take some time (more than 3.3Gb of downloads)

Now, depending of the setting of 'use_fix_mpcorb':
* use_fix_mpcorb='True' => Download MCPORB.DAT rename to FIX_MPCORB.DAT and put in the 'datempcorb' dir
* use_fix_mpcorb='False'=> Run updaterCatServer.py to create the firts cache. The run take very very very long time depending of your dateto/datefrom may be several days!!

__TODO__
* Accept observatory code or coords in the url. At this time observatory is fixed in tychoCatServer.cfg
* Create information page telling what database is using


__Run the server__
----------

Go to the tychoCatServer home_dir and execute ./tychoCatServer.py
When use_fix_mpcorb='False' execute also ./updateMPCORB.py . This script must be running all the time in order to update the database with new asteroids.


__Use__
----------
tychoCatServer is a regular http server. You visit below url with your favorite browser. The aim of this server is provide a collection of objects present in a sky region at given time. Thus date, ra (degrees), dec(degrees) and r (search radio in degrees) are mandatory.

At the present times you can get stars from UCAC4 catalog, satellites or know asteroids. Output file format {format} can take this values: html,csv,excel,fits,json,pickle or mpc

####**URL syntax:**

####Help:
`http://host:port/`
`http://host:port/help`

####Stars in UCAC4 catalog:
`http://host:port/ucac4?format={format}&ra={RA}&dec={DEC}&r={degrees}`

####Satellites:
`http://host:port/sat?format={format}&date={YYYY-MM-DD HH:MM:SS}&ra={RA}&dec={DEC}&r={degrees}`

####Asteroids:
`http://host:port/mpc?format={format}&date={YYYY-MM-DD HH:MM:SS}&ra={RA}&dec={DEC}&r={degrees}`
`http://host:port/mpcsearch?format={format}&date={YYYY-MM-DD HH:MM:SS}&key={key}`

####HIPPARCOS2 start catalog:
`http://host:port/hip2?format={format}&ra={RA}&dec={DEC}&r={degrees}`

####Hyperleda galaxies catalog:
`http://host:port/hyperleda?format={format}&ra={RA}&dec={DEC}&r={degrees}`

####NGC catalog:
`http://host:port/ngc?format={format}&ra={RA}&dec={DEC}&r={degrees}`

###NOTES:
Default values:
>date={present time}
>ra=0
>dec=0
>r=1
>format=html

Aditional url:

>`http://host:port/viz-bin/aserver.cgi`

>This URL is used to mimic CDS a server output as needed by SCAMP astroref catalog


