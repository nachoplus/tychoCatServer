__CatServer__
========
Introduction
------------
CatServer is a http ephemerids server. Its aim is provide a collection of objects present in a sky region at given time. CatServer was development for LSSS (http://www.lasagraskysurvey.es/) NEO hutting project.

At this time its provide ephemerids for:
* satellites in NORAD database. (More than 15000 objects)
* know asteroids in Minor Planet Center (MPC). (More than 650000 asteroids)
* UCAC4 star catalog.(over 113 million objects)

In the near future its wil be provide also:
* Planets and natural satellite (to be done)
* Hiperleda galaxies (to be done)

The output format will be html,csv,excel,fits or mpc 

Due to the large MPC asteroid database some speed up are needed. Basically a preliminar calculation is done for all the objects at daily basic. This results are used to prefilter asteroids in a given region and then precise position are calculated for them.

This cache mechanish has two modes of operation:

1. Fix MPCORB.DAT: Is the user responsability to download a recent MPCORB.DAT from http://www.minorplanetcenter.net/iau/MPCORB.html . Then cache position are calculate for a given day the first time that is needed. As osculating orbital elements change over the time this mode of operation only works well for dates near (+-50 days) the MPCORB.DAT file. This mode of operation is oriented to Observatory ephemerids server. (use_fix_mpcorb='True') 

2. MPCORB.DAT is only valid for a dates near (+-100days) its epoch. To overhelm this limitation the elements in MPCORB.DAT are propagated to diferents epoch using 'integrat', thus acurate calculation will be done. In this mode updateMPCORB.py script must be running all the time in order to update the database with new asteroids. This mode of operation is oriented to precoveries and general ephemerids server for far dates.(use_fix_mpcorb='False') 


This software is heavily base on pyephem for calculations https://github.com/brandon-rhodes/pyephem . Also use a Bill Gray integrat from project pluto http://www.projectpluto.com/pluto/integrat.htm .

__Installing__
----------
Edit config/config.cfg and adapt to your needs some parameters.
Mandatory changes are:
```python
use_fix_mpcorb='True'
home_dir=/home/nacho/work/CatServer [HOME of scrips]
base_dir=%(home_dir)s/../DATA [all DATA home]
```
for use_fix_mpcorb='False' the following setting are also relevant:
```python
date0=2457022.500000 [ Julian Date center date]
datefrom=2457016.500000  [ Julian Date min. It must be date0-Delta ->symetric from date0]
dateto=2457028.500000 [ Julian Date max. It must be date0+Delta -> symetric from date0]
eachdays=50 [propagate MPCORB file every 50 days]
```

Then run `bootstrap.py` . This executable compile and download all needed files.
This are the steps that bootstrap.py performs:

1. Compile ucac4 C rutines using swig.

2. Download (3.2Gb) UCAC4 from ftp://cdsarc.u-strasbg.fr/pub/cats/I/322A/UCAC4

3. Compile integrat from Project Pluto (http://www.projectpluto.com/pluto/integrat.htm). Is the Bill Gray original lunar rutines except I introduce a line in linlunar.mak in order to compile integrat.

4. Download (109Mb) JPL ephem  from: ftp://ssd.jpl.nasa.gov/pub/eph/planets/Linux/de430/linux_p1550p2650.430 needed by integrat.

5. Compile pyephem pkg. 

It take some time (more than 3.3Gb of downloads)

Now, depending of the setting of 'use_fix_mpcorb':
* use_fix_mpcorb='True' => Download MCPORB.DAT rename to FIX_MPCORB.DAT and put in the 'datempcorb' dir
* use_fix_mpcorb='False'=> Run updaterCatServer.py to create the firts cache. The run take very very very long time depending of your dateto/datefrom may be several days!!

__Run the server__
----------

Go to the CatServer home_dir and execute ./CatServer.py
When use_fix_mpcorb='False' execute also ./updateMPCORB.py . This script must be running all the time in order to update the database with new asteroids.


__Using__
----------
CatServer is a regular http server. You visit it below url with your favorite browser. The aim of this server is provide a collection of objects present ina  sky region at given time. Thus date, ra, dec and r (search radio) are mandatory (but they have defaults).

At the present times you can get stars from UCAC4 catalog, satellites 
or know asteroids.

####**URL syntax:**

####Help (this file):
`http://host:port/help`

####Stars in UCAC4 catalog:
`http://host:port/ucac4?format={format}&ra={RA degrees}&dec={DEC degrees}&r={degrees}`
`http://host:port/viz-bin/aserver.cgi?format={output format}&ra={RA degrees}&dec={DEC degrees}&r={degrees}`

####Satellites:
`http://host:port/sat?format={format}&date={YYYY-MM-DD HH:MM:SS}&ra={RA degrees}&dec={DEC degrees}&r={degrees}`

####Asteroids:
`http://host:port/mpc?format={format}&date={YYYY-MM-DD HH:MM:SS}&ra={RA degrees}&dec={DEC degrees}&r={degrees}`
`http://host:port/mpcsearch?format={format}&date={YYYY-MM-DD HH:MM:SS}&key={asteroid key}`

Implemented {format} can take this values: html,csv,excel,fits or mpc  

###NOTES:
Aditional url:

`{server basename}/viz-bin/aserver.cgi`

This URL is used to mimic CDS a server output as needed by SCAMP astroref catalog

