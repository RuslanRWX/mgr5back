#!/usr/bin/python 

import sys
import os

ftp_conn='/usr/local/mgr5/etc/.vmmgr-backup/storages/st_1'
pidfile = '/tmp/vdsback.pid'
BackDir='/backup'
#FileDB="/usr/local/mgr5/etc/vmmgr.conf.d/db.conf"
FileDB='/home/ruslan/db.conf'
# You can use script with gzip and without zipping, 
Gzip="YES"   # YES or NO 

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
    filez=BackDir+"/"+Name+"_"+date
    NameImgFtp=Name+"_"+date
    print "Start creating LVM Snapshote "+Name
    cmdCreateLVM="lvcreate -L%sG -s -n %s-snapshot %s"%(Size,Name,PoolName )
    cmdRmLVM="kpartx -d %s; lvremove -f %s"%(PoolName, PoolName)
    os.system(cmdCreateLVM)  # create LVM snapeshot 
    if Gzip is "YES":
        cmdDD="dd if=%s-snapshot | gzip -c > %s "%(PoolName, filez)
        os.system(cmdDD)  # start dd
    else:
        filez=PoolName
    ftpput(filez,NameImgFtp)   # put to ftp
    os.system(cmdRmLVM)  # remove LVM snapeshot
    if Gzip is not "YES":
        rmf="rm %s"%(filez)
        os.system(rmf)              # remove gzip file 
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
    ftp.storbinary("STOR %s"%(NameImg), open(file))
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

