#!/usr/bin/python 

import sys
import os
import xmltodict
import time

NodeID='2'
NoBackupID='151'
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
        

def Mysqlget(SQL):
    VarMysql={}
    St=['DBHost','DBUser','DBPassword','DBName']
    for line in open(FileDB,'r').readlines():
        parts = line.split() # split line into parts
        if len(parts) > 1: 
            VarMysql[parts[0]] = parts[1]
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
        cur.execute(SQL)
        Servs=list(cur.fetchall())
        cnx.close()
    return Servs

def Search():
   sql="select id from vm where hostnode=\'%s\' and id not in (%s);"%(NodeID, NoBackupID)
   Servs=Mysqlget(sql)
   for R in Servs:
       StartBackup(R[0])

def StartBackup(ServerID):
    #print ServerID
    sql="select vm,name,pool,size from volume where vm=\'%s\' and hostnode=\'%s\' and pool is not NULL;"%(ServerID,NodeID)
    Serv=Mysqlget(sql)
    #print Serv
    for R in Serv:
        W=work(R[1], R[2])
        W.CreateLVM(R[3])
    for R in Serv:
        W=work(R[1], R[2])
        W.CreateGzip()
        W.PutFtp()


class work:
    def __init__(self, Name, Pool):
        import datetime
        self.date=datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.Name=Name
        self.Pool=Pool
        PoolName='/dev/'+Pool+"/"+Name
        self.filez=BackDir+"/"+Name+"_"+self.date
        NameImgFtp=Name+"_"+self.date
        self.dftp=self.Name+"/"+self.date
        #print PoolName
    def CreateLVM(self, Size):
     #   print "Name: ", self.Name," Size:  ", Size," Pool: "+ self.Pool
        print "Start creating LVM Snapshote "+Name
        cmdCreateLVM="lvcreate -L%sM -s -n %s-snapshot %s"%(Size,Name,PoolName )
        os.system(cmdCreateLVM)
    def CreateGzip(self):
        print "Create gzip file, pool: "+self.Pool+" backup file: "+self.filez
        cmdDD="dd if=%s-snapshot | gzip -c > %s "%(PoolName, filez)
        os.system(cmdDD)  # start dd
    def PutFtp(self):
        print "Upload a file via FTP :"+self.filez
        with open(ftp_conn) as fd:
            doc = xmltodict.parse(fd.read())
            nameb=doc['doc']['name']
            passftp=doc['doc']['settings']['password']
            url=doc['doc']['settings']['url']
            user=doc['doc']['settings']['username']
        import ftplib
        from ftplib import FTP
        print self.Name
        DIR=NodeID+"/"+nameb+"/"+self.Name+"/"+self.date
        ftp = FTP(url)
        ftp.login(user, passftp)
        #print ftp.mkd(nameb)
        try:
            ftp.cwd(NodeID)
        except ftplib.error_perm:
            ftp.mkd(NodeID)
        try:
            ftp.cwd(nameb)
        except ftplib.error_perm:
            ftp.mkd(nameb)
        try:
            ftp.cwd(self.Name)
        except:
            ftp.mkd(self.Name)
        try:
            ftp.cwd(self.date)
        except ftplib.error_perm:
            ftp.mkd(self.date)
        ftp.cwd(DIR)
        print "Upload to "+DIR
        ftp.storbinary("STOR %s"%(self.NameImgFtp), open(self.filez))
        ftp.quit()
       
      
      
def Main(): 
    if len(sys.argv) > 1:
         Startbackup(sys.argv[1])
    else:
        Search()
    #sql="select name,pool,size from volume where hostnode=\'%s\' and vm not in (%s) and pool is not NULL;"%(NodeID, NoBackupID)
    #res=Mysqlget(sql)
    #print res
    
    
if __name__ == '__main__':
    Main()

