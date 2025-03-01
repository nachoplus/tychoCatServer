#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

import sqlite3 as sqlite
import urllib2
import sys
import commands

'''
Concept proof for sqlite DB
'''


def give_number(letter):

    '''
     Convert to number a alphabet letter
    '''    
    try:
     int(letter)
     return letter
    except ValueError:
     if letter.isupper():
      return str(ord(letter) - ord('A') + 10)
     if letter.islower():
      return str(ord(letter) - ord('a') + 36)


def convert_date(packdt):

  '''
    Convert the packed year format to standard year.
  '''
  print packdt
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


class sqliteEngine():

   def decodeMPCorb(self,filename,offset=0):

      '''
      Load a file of MPC formated orbital data to sqlite DB
      '''
      asteroid=dict()
      print "Reading:",filename
      response = urllib2.urlopen(filename)
      mpc = response.read().split('\n')
      mpc=mpc[offset:-1]
      for ast in mpc:
	try:	
		KEY=ast[:7]
		if len(ast)<104:
			continue
		try:
               		H=float(ast[8:12]),
               		G=float(ast[15:19]),
               		dummy= tuple(ast[8:104].split()+[ast[104:]])
	   	except:
	       		#print "Not H,G magnitudes. Setting to standard values 0.0 0.15:",designation	
	       		dummy = tuple([0e0,0.15]+ast[20:104].split()+[ast[104:]])
	except:
		print "Error loading line"
		pass
	#print dummy
	H, G, epoch_M, M, argper, node, i, e, n, a,resto = dummy
	H, G, M, argper, node, i, e, n, a =map(float,[H, G, M, argper, node, i, e, n, a])
        epoch_M = str(convert_date(epoch_M))
	KEY=KEY.ljust(7)
	dummy=(KEY,H, G, epoch_M, M, argper, node, i, e, n, a,resto)
	#print dummy
        asteroid[KEY]=dummy
      print "\nMPC catalogue has been read. The total of asteroids are ",len(asteroid), " of ",len(mpc)
      return asteroid

   def saveMPCorb(self,asteroids):
	con = sqlite.connect('mpc_elements.db')
	tablename='asteroid'
	with con:
    		cur = con.cursor()    
    		cur.execute("CREATE TABLE IF NOT EXISTS "+tablename+" (KEY,H, G, epoch, M, argper, node, i, e, n, a,resto,PRIMARY KEY (KEY, epoch))")
		for k,v in asteroids.iteritems():
			values=list(v)
			#values.insert(0,k)
			#values.insert(0,family)
			#print k,values
			try:
				cur.execute("INSERT INTO "+tablename+" VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)", values)
			except:
				print "ERROR INSERTING:",values

   def getMPCorb(self,date):
	con = sqlite.connect('mpc_elements.db')
	tablename='asteroid'
	with con:
    		cur = con.cursor()    
    		cur.execute("SELECT * FROM "+tablename)
		print [record for record in cur.fetchall()]


   def updated_mpcorb_dir(self):  
	#ast=self.decodeMPCorb('http://www.minorplanetcenter.net/iau/MPCORB/MPCORB.DAT',offset=41)
	#self.saveMPCorb(ast)
	ast=self.decodeMPCorb('http://www.minorplanetcenter.net/iau/MPCORB/DAILY.DAT')
	self.saveMPCorb(ast)

   def timeShiftMPCorb(self,newdate):
	res=commands.getoutput("integrat ")
	print res

if __name__ == '__main__':
	s=sqliteEngine()
	s.getMPCorb("")

