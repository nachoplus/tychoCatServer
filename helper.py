#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#tychoSuit


import numpy as np
import ephem

pi=np.pi

dubliJDoffset= 2415020
MJDoffset=2400000.5

def group(lst, n):
  for i in range(0, len(lst), n):
    val = lst[i:i+n]
    if len(val) == n:
      yield tuple(val)

def distance(ra0,dec0,ra1,dec1):
        #arg in degrees
        #return degrees
        deltaDE=dec1-dec0
        deltaRA=ra1-ra0
        cosfactor=np.cos(dec0*np.pi/180)
        return np.sqrt(deltaDE*deltaDE+deltaRA*deltaRA*cosfactor*cosfactor)


def speed(t,ra0,dec0,ra1,dec1):
        #arg in degrees, days
        #return arcsec per min
        return (distance(ra0,dec0,ra1,dec1)/t)*3600/(24*60)

def PA(ra0,dec0,ra1,dec1):
        deltaDE=dec1-dec0
        deltaRA=ra1-ra0
        cosfactor=np.cos(dec0*np.pi/180)
        pa=np.arctan2(deltaRA*cosfactor,deltaDE)
        if pa<0:
                pa=2*np.pi+pa
        return pa*180/np.pi



def give_number(letter):

    try:
        int(letter)
        return letter
    except ValueError:
        if letter.isupper():
            return str(ord(letter) - ord('A') + 10)
        if letter.islower():
            return str(ord(letter) - ord('a') + 36)

def convert_design(packed):

    '''
      Convert the packed designation format to formal designation.
    '''

    isdigit = str.isdigit

    try:
        packed = packed.strip()
    except ValueError:
        print("ValueError: Input is not convertable to string.")

    if isdigit(packed) == True: desig = packed.lstrip('0') # ex: 00123

    if isdigit(packed[0]) == False: # ex: A7659 = 107659

        if isdigit(packed[1:]) == True: # ex: A7659
            desig = give_number(packed[0]) + packed[1:]

        elif isdigit(packed[1:3]) == True:  # ex: J98SG2S = 1998 SS162

            if isdigit(packed[4:6]) == True and packed[4:6] != '00':
                desig = give_number(packed[0]) + packed[1:3] + ' ' + packed[3] + packed[-1] + packed[4:6].lstrip("0")

            if isdigit(packed[4:6]) == True and packed[4:6] == '00':
                desig = give_number(packed[0]) + packed[1:3] + ' ' + packed[3] + packed[-1]

            if isdigit(packed[4:6]) == False:
                desig = give_number(packed[0]) + packed[1:3] + ' ' + packed[3] + packed[-1] + give_number(packed[4]) + packed[5]

        elif packed[2] == 'S': # ex: T1S3138 = 3138 T-1
            desig = packed[3:] + ' ' + packed[0] + '-' + packed[1]

    return desig

def date_from_designation(packed):
        isdigit = str.isdigit
        if isdigit(packed[0]) == False and  isdigit(packed[1:3]) == True and (packed[0] in ['I','J','K']) and len(packed.strip())==7: 
                try:
                        packdt = str(packed).strip()
                except ValueError:
                        print("ValueError: Input is not convertable to string.")
                
                year=give_number(packdt[0]) + packdt[1:3]
                halfmonth=float(give_number(packdt[3]))-9
                if halfmonth>9:
                        halfmonth-=1
                month=str(np.ceil(halfmonth/2))
                #print "HALFMONTH:",packdt[3],halfmonth,month,halfmonth % 2
                if (halfmonth % 2)==1:
                        day='01'
                else:
                        day='15'
                d=year+'/'+month+'/'+day
                dd=ephem.date(d+" 00:00:00")

                #print packdt[4:]
                #print packed,d,dd
        else:
                dd=ephem.date(0)
        return dd

        


def convert_date(packdt):

    '''
      Convert the packed year format to standard year.
    '''
    try:
        packdt = str(packdt).strip()
    except ValueError:
        print("ValueError: Input is not convertable to string.")

    '''
       Month     Day      Character         Day      Character
                       in Col 4 or 5              in Col 4 or 5
     Jan.       1           1             17           H
     Feb.       2           2             18           I
     Mar.       3           3             19           J
     Apr.       4           4             20           K
     May        5           5             21           L
     June       6           6             22           M
     July       7           7             23           N
     Aug.       8           8             24           O
     Sept.      9           9             25           P
     Oct.      10           A             26           Q
     Nov.      11           B             27           R
     Dec.      12           C             28           S
               13           D             29           T
               14           E             30           U
               15           F             31           V
               16           G

     Examples:

     1996 Jan. 1    = J9611
     1996 Jan. 10   = J961A
     1996 Sept.30   = J969U
     1996 Oct. 1    = J96A1
     2001 Oct. 22   = K01AM
    '''

    return '/'.join([give_number(packdt[0]) + packdt[1:3],give_number(packdt[3]),give_number(packdt[4])])


def asteroid_type(a,e,i):
        #http://en.wikipedia.org/wiki/Near-Earth_object
        Qt=1.017
        qt=0.983
        at=1
        neo=1.3
        Q=a*(1+e)
        q=a*(1-e)
        t=[]

        if q<=neo:
                t.append("NEO")

        if a<=at: 
                if Q>qt:
                        t.append("Athen")
                else:
                        t.append("Atira")
        else:
                if q<Qt:
                        t.append("Apollo")
                #Amors (1.0167 < q < 1.3 AU) 
                elif Qt < q < neo:
                        t.append("Amor")

        #Mars crossers (1.3 < q < 1.6660 AU)
        if neo < q < 1.6660:
                t.append("MarsCrosser")

        #HUNGARIAN Semi-major axis between 1.78 and 2.00 AU. Orbital period of approximately 2.5 years.
        #Low eccentricity of below 0.18. An inclination of 16° to 34°
        if 1.78<=a<=2.0 and e<=0.18 and 16<=i<=34:
                t.append("Hungaria")

        #MB:Zona I (2,06-2,5 UA), Zona II (2,5-2,82 UA) y Zona III (2,82-3,28 UA).
        if 2.06<=a<=2.5:
                #main belter I
                t.append("MB I")

        if 2.5<=a<=2.82:
                #main belter II
                t.append("MB II")

        if 2.82<=a<=3.28:
                #main belter II
                t.append("MB III")

        # HILDA: semi-major axis between 3.7 AU and 4.2 AU, an eccentricity less than 0.3, and an inclination less than 20°
        if 3.7<=a<=4.2 and e<=0.3 and i<=20:
                t.append("Hilda")

        #TNOs 30,103
        if a>=30.103:
                t.append("TNO")

        #print a,Q,q,t
        t_=';'.join(t)
        return t_
        


'''
def distance(ra0,dec0,ra1,dec1):
    #arg in degrees
    dis=Haversine((ra1*np.pi/180,dec1*np.pi/180),(ra0*np.pi/180,dec0*np.pi/180))*180/np.pi
    return dis

def PA(ra0,dec0,ra1,dec1):
    #arg in degrees
    deltaDE=dec1-dec0
    deltaRA=ra1-ra0 
    if deltaRA!=0: 
            pendiente=deltaDE/deltaRA
            np.cosfactor=np.cos(((dec0+dec1)/2)*np.pi/180)
            if (np.cosfactor==0):
                np.cosfactor=0.000000000001
            PA=np.arctan(pendiente/np.cosfactor)*180/np.pi
    else:
            if deltaDE>0:
                PA=0
            else:
                PA=180

    if PA>=0:
        PA_ASTROMETRICA=PA
    else:
        PA_ASTROMETRICA=PA+360
    return PA_ASTROMETRICA

def speed(t,ra0,dec0,ra1,dec1):
    #arg in degrees,time in days and fractions
    #result in arcsec/min
    dis=distance(ra0,dec0,ra1,dec1)
    if t==0:
        speed=0
    else:
        speed=(dis*3600*180/np.pi)/(t*24*60)
    return speed

def Haversine((ra1,dec1),(ra2,dec2)):
    #arg in radians
    #return also in radians
    dra = ra2 - ra1
    ddec = dec2 - dec1
    a = np.sin(ddec/2)*np.sin(ddec/2) + np.cos(dec1) * np.cos(dec2) * np.sin(dra/2) * np.sin(dra/2)
    c = 2 * np.arcsin(min(1,sqrt(a)))
    return c
'''
