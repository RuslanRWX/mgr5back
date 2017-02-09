#!/usr/bin/python -t

import sys
import os

pid = str(os.getpid())
pidfile = "/tmp/vdsback.pid"


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



def Main(): 
    #Check()
   # print "good"
    #import time
    #time.sleep(10)
    MysqlGet()
    MysqlConn()
    print VarMysql['DBHost']
    #os.remove(pidfile)
Main()


