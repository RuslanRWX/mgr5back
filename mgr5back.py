#!/usr/bin/python 

import sys
import os

ftp_conn='/usr/local/mgr5/etc/.vmmgr-backup/storages/st_1'
pidfile = '/tmp/vdsback.pid'
#BackDir='/tmp'
#FileDB="/usr/local/mgr5/etc/vmmgr.conf.d/db.conf"
FileDB='/home/ruslan/db.conf'
pid = str(os.getpid())



def Check():
    if os.path.isfile(pidfile):
        print "%s already exists, exiting" % pidfile
        sys.exit()
    else:
        file(pidfile, 'w').write(pid)

def MysqlGet():
    global VarMysql
    VarMysql={}
    St=['DBHost','DBUser','DBPassword','DBName']
    for line in open(FileDB,'r').readlines():
        parts = line.split() # split line into parts
        if len(parts) > 1: 
            VarMysql[parts[0]] = parts[1]

def LvmBackup(Name, Size, Pool):
    import datetime
    date=datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    PoolName='/dev/'+Pool+"/"+Name
    NameImgFtp=Name+"_"+date
    print "Start creating LVM Snapshote "+Name
    #print FileBack
    cmdCreateLVM="lvcreate -L%sG -s -n %s-snapshot %s"%(Size,Name,PoolName )
    cmdRmLVM="lvremove -f %s"%(PoolName)
    os.system(cmdCreateLVM)  # create LVM snapeshot 
    ftpput(PoolName, NameImgFtp)   # put to ftp 
    os.system(cmdRmLVM)  # remove LVM snapeshot
    #print "#########",date,"##############"



def Start():
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


def ftpput(file, NameImg):
    print "Start put file to backup server"+file
    import xmltodict
    with open(ftp_conn) as fd:
        doc = xmltodict.parse(fd.read())
        nameb=doc['doc']['name']
        passftp=doc['doc']['settings']['password']
        url=doc['doc']['settings']['url']
        user=doc['doc']['settings']['username']
    from ftplib import FTP
    ftp = FTP(url)
    ftp.login(user, passftp)
    #print ftp.mkd(nameb)
    if nameb in ftp.nlst('') :
        pass
    else :
        print 'NO Dir, Start create'
        ftp.mkd(nameb)
    ftp.cwd(nameb)
    pipe="/tmp/%s"%(NameImg)
    mkpipe="mkfifo %s"%(pipe)
    os.system(mkpipe)
    cmdDD="dd if=%s-snapshot | gzip -c > %s &"%(file, pipe)
    os.system(cmdDD) 
    ftp.storbinary("STOR %s"%(NameImg), open(pipe))
    rmpipe="rm %s"%(pipe)
    ftp.quit() 

    
 # Need create LVM to file with date
 # Need clean file and clean ftp store 
 
 
def Main(): 
    #Check()
   # print "good"
    #import time
    #time.sleep(10)
    #MysqlGet()
    Start()
    #print VarMysql['DBHost']
    #os.remove(pidfile)
    #ftpget()

if __name__ == '__main__':
    Main()

