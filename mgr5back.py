#!/usr/bin/python -t

import sys
import os

pid = str(os.getpid())
pidfile = '/tmp/vdsback.pid'
BackDir='/tmp'

def Check():
    if os.path.isfile(pidfile):
        print "%s already exists, exiting" % pidfile
        sys.exit()
    else:
        file(pidfile, 'w').write(pid)

def MysqlGet():
    global VarMysql
    VarMysql={}
    FileDB="/usr/local/mgr5/etc/vmmgr.conf.d/db.conf"
    St=['DBHost','DBUser','DBPassword','DBName']
    for line in open(FileDB,'r').readlines():
        parts = line.split() # split line into parts
        if len(parts) > 1: 
            VarMysql[parts[0]] = parts[1]

def LvmBackup(Name, Size):
    print Name
    print Size
    print "#######################"



def MysqlConn():
    import mysql.connector
    from mysql.connector import errorcode
    try:
        cnx = mysql.connector.connect(user=VarMysql['DBUser'], password=VarMysql['DBPassword'],
                                 host=VarMysql['DBHost'],
                                database=VarMysql['DBName'])
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else:
        cur = cnx.cursor()
        Res=cur.execute("SELECT name,vsize FROM vm")
        Servs=list(cur.fetchall())
        for R in Servs:
            LvmBackup(R[0],R[1])
        cnx.close()

def conftp(nameb,user,url,password ):
    from ftplib import FTP
    ftp = FTP(url)
    ftp.login(user, password)
    #print ftp.mkd(nameb)
    if nameb in ftp.nlst('') :
        pass
    else :
        print 'NO Dir, Start create'
        ftp.mkd(nameb)
        
    file = 'README.md'
    ftp.cwd(nameb)
    ftp.storbinary('STOR '+file, open(file, 'rb'))
    ftp.quit() 

def ftpget():
    import xmltodict
    with open('/usr/local/mgr5/etc/.vmmgr-backup/storages/st_1') as fd:
        doc = xmltodict.parse(fd.read())
        nameb=doc['doc']['name']
        passftp=doc['doc']['settings']['password']
        urlftp=doc['doc']['settings']['url']
        userftp=doc['doc']['settings']['username']
    conftp(nameb,userftp,urlftp,passftp)
    
    
    
def Main(): 
    #Check()
   # print "good"
    #import time
    #time.sleep(10)
    #MysqlGet()
    #MysqlConn()
    #print VarMysql['DBHost']
    #os.remove(pidfile)
    ftpget()
Main()


