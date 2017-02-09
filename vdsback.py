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
            #print parts[0]   # print column 2
            VarMysql[parts[0]] = parts[1]
           # print VarMysql['DBHost']

def Main(): 
    #Check()
   # print "good"
    #import time
    #time.sleep(10)
    MysqlGet()
    print VarMysql['DBHost']
    #os.remove(pidfile)
Main()


