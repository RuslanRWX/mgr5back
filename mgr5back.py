#!/usr/bin/python 

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
    #FileDB="/usr/local/mgr5/etc/vmmgr.conf.d/db.conf"
    FileDB='/home/ruslan/db.conf'
    St=['DBHost','DBUser','DBPassword','DBName']
    for line in open(FileDB,'r').readlines():
        parts = line.split() # split line into parts
        if len(parts) > 1: 
            VarMysql[parts[0]] = parts[1]

def LvmBackup(Name, Size, Pool):
    import datetime
    date=datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    PoolName='/dev/'+Pool+"/"+Name
    FileImg=BackDir+"/"+Name+"_"+date
    print "Start creating LVM Snapshote "+Name
    #print FileBack
    cmdCreateLVM="lvcreate -L%sG -s -n %s-snapshot %s"%(Size,Name,PoolName )
    cmdRmLVM="lvremove -f %s"%(PoolName)
    cmdDD="dd if=%s-snapshot | gzip -c > %s"%(PoolName, FileImg)
    os.system(cmdCreateLVM)  # create LVM snapeshot 
    os.system(cmdDD)          # start dd
    os.system(cmdRmLVM)  # remove LVM snapeshot
    ftpput(FileImg)               # put file 
    #print "#########",date,"##############"



def MysqlConn():
    MysqlGet()
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
        Res=cur.execute("select vm.name, vm.vsize, volume.pool from volume  join vm on vm.name =volume.name;")
        Servs=list(cur.fetchall())
        for R in Servs:
            LvmBackup(R[0],R[1], R[2])
        cnx.close()

def conftpput(nameb,user,url,password, file ):
    from ftplib import FTP
    ftp = FTP(url)
    ftp.login(user, password)
    #print ftp.mkd(nameb)
    if nameb in ftp.nlst('') :
        pass
    else :
        print 'NO Dir, Start create'
        ftp.mkd(nameb)
    ftp.cwd(nameb)
    ftp.storbinary('STOR '+file, open(file, 'rb'))
    ftp.quit() 

def ftpput(file):
    print "Start put file to backup server"+file
    import xmltodict
    with open('/usr/local/mgr5/etc/.vmmgr-backup/storages/st_1') as fd:
        doc = xmltodict.parse(fd.read())
        nameb=doc['doc']['name']
        passftp=doc['doc']['settings']['password']
        urlftp=doc['doc']['settings']['url']
        userftp=doc['doc']['settings']['username']
    conftpput(nameb,userftp,urlftp,passftp, file)
    
 # Need create LVM to file with date
 # Need clean file and clean ftp store 
 
 
def Main(): 
    #Check()
   # print "good"
    #import time
    #time.sleep(10)
    #MysqlGet()
    MysqlConn()
    #print VarMysql['DBHost']
    #os.remove(pidfile)
    #ftpget()
Main()


