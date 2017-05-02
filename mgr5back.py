#!/usr/bin/env python
# Copyright (c) 2017 Ruslan Variushkin,  ruslan@host4.biz
# Version 0.4.5
# mgr5back.py is an open-source software to backup virtual machines on the
# ISP VMmanager version 5
import sys
import os
import xmltodict
import time
import configparser
import datetime
pid = str(os.getpid())
import ftplib
from ftplib import FTP

def Conf():
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))
    global NodeID
    global NoBackupID
    global ftp_conn
    global pidfile
    global BackDir
    global FileDB
    global Gzip
    global SaveDate
    global checkdate
    global check
    global Zabbix_Mark_File
    global Zabbix_LVM_File
    global Zabbix_FTP_File
    global Zabbix_Error_File
    global checkdate_after_delete
    NodeID = config['main']['NodeID']
    NoBackupID = config['main']['NoBackupID']
    ftp_conn = config['main']['ftp_conn']
    pidfile = config['main']['pidfile']
    BackDir = config['main']['BackDir']
    FileDB = config['main']['FileDB']
    Gzip = config['main']['Gzip']
    SaveDate = config['main']['SaveDate']
    SaveDate = int(SaveDate)
    checkdate = config['main']['checkdate']
    checkdate = int(checkdate)
    check=set()
    Zabbix_Mark_File = config['main']['ZabbixMarkFile']
    Zabbix_LVM_File = config['main']['ZabbixLVMFile']
    Zabbix_FTP_File = config['main']['ZabbixFTPFile']
    Zabbix_Error_File = config['main']['ZabbixErrorFile']
    checkdate_after_delete = config['main']['CheckDateAfterDelete']

def Check():
    if os.path.isfile(pidfile):
        if  sys.argv[1] == "chfull":
            check.add("1")
        else:
            print "%s already exists, exiting" % pidfile
            sys.exit()
    else:
        if sys.argv[1] == "start" or sys.argv[1] == "id":
            file(pidfile, 'w').write(pid) 
            file(Zabbix_Mark_File, "w").write("1")


def Mysqlget(SQL):
    VarMysql = {}
    St = ['DBHost', 'DBUser', 'DBPassword', 'DBName']
    for line in open(FileDB, 'r').readlines():
        parts = line.split()  # split line into parts
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
        Servs = list(cur.fetchall())
        cnx.close()
    return Servs


def Search():
    sql = "select id from vm where hostnode=\'%s\' and id not in (%s);" % (
        NodeID, NoBackupID)
    Servs = Mysqlget(sql)
    for R in Servs:
        StartBackup(R[0])


def StartBackup(ServerID):
    date = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    print "Start backup-VM ID %s "% (ServerID)
    sql = "select vm,name,pool,size from volume where vm=\'%s\' and hostnode=\'%s\' and pool is not NULL;" % (
        ServerID, NodeID)
    Serv = Mysqlget(sql)
    if not Serv:
        print "Virtual machine does not exist"
        return
    print "Start backup: " + Serv[0][1]
    print "Start sync"
    cmd = "virsh send-key %s KEY_LEFTALT KEY_SYSRQ KEY_S" % (Serv[0][1])
    import time
    time.sleep(3)
    os.system(cmd)
    for R in Serv:
        # print "Start backup storage: "+R[1]
        W = work(R[0], R[1], R[2], date)
        W.CreateLVM(R[3])
    for R in Serv:
        W = work(R[0], R[1], R[2], date)
        if Gzip.lower() == 'yes':
            W.CreateGzip()
        W.PutFtp()
        W.RemoveLVM()
        if Gzip.lower() == 'yes':
            W.RmFile()
        Clean(R[0])


class work:
    def __init__(self, id,  Name, Pool, date):
        self.id = str(id)
        self.date = date
        self.Name = Name
        self.Pool = Pool
        self.PoolName = '/dev/' + Pool + "/" + Name
        self.filez = BackDir + "/" + Name + "_" + date
        self.NameImgFtp = Name + "_" + date
        self.dftp = self.Name + "/" + date
        if Gzip.lower() == 'yes':
            self.filez = BackDir + "/" + Name + "_" + date
        else:
            self.filez = self.PoolName

    def CreateLVM(self, Size):
        print "Start creating LVM Snapshote " + self.Name
        cmd = "lvcreate -L%sM -s -n %s-snapshot %s" % (
            Size, self.Name, self.PoolName)
        os.system(cmd)

    def RemoveLVM(self):
        print "Remove LVM Snapshote " + self.PoolName
        cmd = "lvremove -f %s-snapshot" % (self.PoolName)
        os.system(cmd)

    def RmFile(self):
        print "Remove file or directory:" + self.filez
        cmd = "rm %s" % (self.filez)
        os.system(cmd)

    def CreateGzip(self):
        print "Create gzip file, pool: " + self.Pool + " backup file: " + self.filez
        cmdDD = "dd if=%s-snapshot | gzip -c > %s " % (
            self.PoolName, self.filez)
        os.system(cmdDD)  # start dd

    def PutFtp(self):
        # print self.Name
        DIR = NodeID + "/" + self.id + "/" + self.date
        w = workftp()
        w.Path(NodeID)
        w.Path(self.id)
        w.Path(self.date)
        print "Upload to " + DIR
        w.Put(self.NameImgFtp, self.filez)


class workftp():
    def __init__(self):
        # print "Connect to FTP server"
        with open(ftp_conn) as fd:
            doc = xmltodict.parse(fd.read())
            nameb = doc['doc']['name']
            self.passftp = doc['doc']['settings']['password']
            self.url = doc['doc']['settings']['url']
            self.user = doc['doc']['settings']['username']
        self.ftp = FTP(self.url)
        self.ftp.login(self.user, self.passftp)

    def Path(self, path):
        try:
            self.ftp.cwd(path)
        except ftplib.error_perm:
            self.ftp.mkd(path)
            self.ftp.cwd(path)

    def Put(self,  NameFile, File):
        try:
            self.ftp.storbinary("STOR %s" % (NameFile), open(File))
        except IOError:
            Error()
        self.ftp.quit()
        
    def List(self):
        files = self.ftp.nlst()
        return files

    def FtpRmT(self, path):
        Fpath = "~/" + NodeID
        self.ftp.cwd(Fpath)
        wd = self.ftp.pwd()
        # print wd
        try:
            names = self.ftp.nlst(path)
        except ftplib.all_errors:
            return
        for name in names:
            if os.path.split(name)[1] in ('.', '..'):
                continue
            w = workftp()
            try:
                self.ftp.cwd(name)  # if we can cwd to it, it's a folder
                self.ftp.cwd(wd)  # don't try a nuke a folder we're in
                w.FtpRmT(name)
            except ftplib.all_errors:
                self.ftp.delete(name)
        try:
            self.ftp.rmd(path)
        except ftplib.all_errors:
            return


def Clean(id):
    print "Start clean ftp server, older then:", SaveDate, "days"
    w = workftp()
    path = NodeID + "/%s/" % (id)
    w.ftp.cwd(path)
    ListDirs = w.List()
    import datetime
    date = datetime.datetime.now() - datetime.timedelta(days=SaveDate)
    date2 = date.strftime("%Y%m%d000000")
    print "Check date: " + date2
    for R in ListDirs:
        if date2 > R:
            w.ftp.cwd(R)
            ListFile = w.List()
            for F in ListFile:
                print "Delete file:" + F
                w.ftp.delete(F)
            print "Detele Dir: " + R
            w.ftp.cwd("~/" + path)
            w.ftp.rmd(R)    # Delete old dir
    w.ftp.quit()
    
    
def DateCheck(checkdate):
    date0 = datetime.datetime.now() - datetime.timedelta(days=checkdate)
    date = date0.strftime("%Y-%m-%d")
    date = date0.strftime("%Y%m%d")
    dateCh = "%s000000" % (date)
    return dateCh
        
        
def checkandrm(dir):
    DateCh=DateCheck(checkdate_after_delete)
    w = workftp()
    try:
        w.ftp.cwd(NodeID+"/"+dir)
        ListDirs = w.List()
        resultDir = filter(lambda x: DateCh <= x, ListDirs)
        if resultDir != []:
            print "good"
        else:
            print "Remove the directory %s" % (dir)
            #w.FtpRmT(dir)
    except:
        print "Not Dir, start remove"
        #w.FtpRmT(dir)
        return

def CleanDirs(remove=True):
    sql = "select vm.id from volume join vm on vm.id=volume.vm where volume.hostnode=\'%s\' and volume.pool is not NULL and volume.vm not in (%s);" % (
        NodeID, NoBackupID)
    Servs = Mysqlget(sql)
    w = workftp()
    Sset = set()
    Lset = set()
    print "Start remove old or excess directories in the Node ID directory of the ftp server"
    for S in Servs:
        import string
        S = str(S).replace("(", "")
        S = S.replace(")", "")
        S = S.replace(",", "")
        Sset.add(S)
    try:
        w.ftp.cwd(NodeID)
        ListDirs = w.List()
        Res = set(ListDirs) - Sset
        for dir in Res:
            if remove:
                checkandrm(dir)
                #print ""+ dir
    except:
        from colorama import Fore
        print (Fore.RED + "\nError !!!" + Fore.RESET +
               " You have an error on the ftp server. Check directory name as the node id#%s,permissions etc") % (NodeID)
    if Res and remove == "True":
        print "Old or excess data have been cleaned on the FTP server,bye!"
    else:
        print "Nothing have been cleaned"
        

def ftpdel(path):
    w = workftp()
    print "Remove the directory %s" % (path)
    w.FtpRmT(path)

def chlvm():
    print "Start check the logical volumes"
    cmd = "lvs | grep snapshot"
    Ch = os.system(cmd)
    if Ch:
        print "LVM OK"
    else:
        print "LVM Error"
        check.add("2")

    
def chftp():
    print "Start checking the ftp server\n"
    dateCh = DateCheck(checkdate)
    # print date
    sql = "select vm.id, volume.name from volume join vm on vm.id=volume.vm where volume.hostnode=\'%s\' and volume.pool is not NULL and volume.vm not in (%s);" % (
        NodeID, NoBackupID)
    Servs = Mysqlget(sql)
    w = workftp()
    for R in Servs:
        resultDir = []
        resultDir0 = []
        CheckFile = []
        ChF = []
        # print "Start check host %s"%(R[0])
        path = "%s/%s/" % (NodeID, R[0])
    #   NodeID + "/",hostid,"/"
        # print path
        w.ftp.cwd("~/")
        try:
            w.ftp.cwd(path)
            ListDirs = w.List()
            resultDir = filter(lambda x: dateCh <= x, ListDirs)
            if resultDir != []:
                for ts in resultDir:
                    file = "~/%s/%s/%s/" % (NodeID, R[0], ts)
                    w.ftp.cwd(file)
                    ChF = "%s_%s" % (R[1], ts)
                    try:
                        FileR = w.List()
                        if filter(lambda E: ChF == E,  FileR):
                            # print "Check file %s is OK "%(ChF)
                            CheckFile = "0"
                        else:
                            pass
                    except:
                        pass
        except:
            resultDir0 = "NonDir"
        from colorama import Fore
        print (Fore.YELLOW + "Check the volume %s, the virtual machine ID %s" %
               (R[1], R[0]) + Fore.RESET)
        if resultDir:
            print "Check DIR %s is Ok" % (R[0])
            #CheckftpFiles(R[0], Dir, R[1])
            if CheckFile == "0":
                print "Check a file %s is OK " % (ChF)
            else:
                print (Fore.RED + "Check a file %s is ERROR" %
                       (ChF) + Fore.RESET)
                check.add("3")
        elif resultDir0 == "NonDir":
            print (Fore.RED + "The virtual machine ID %s, have not the directory name like %s, it's ERROR" %
                   (R[0], R[0]) + Fore.RESET)
            check.add("3")
        else:
            print  (Fore.RED +"The virtual machine ID %s is Error. You have to check it." % (R[0])+ Fore.RESET)
            check.add("3")
        print "\n"

    print "Check period of date %s" % (dateCh)


def listF():
    print " VM storage ".center(112, "#")
    sql = "select vm.id,volume.name,vm.ip, vm.mem, vm.vcpu, vm.vsize, volume.pool  from vm  join volume on volume.vm=vm.id and volume.pool is not NULL;"
    Servs = Mysqlget(sql)
    for R in Servs:
        print "VM ID: ", R[0], " Name Store:", R[1], " IP:", R[2], " Memory:", R[3], "M CPU:", R[4], " VSize:", R[5], "M Pool Name: ", R[6]
    print "Note: not backup ID: ", NoBackupID


def stat():
    if os.path.isfile(pidfile):
        pid = open(pidfile,  'r')
        print "mgr5backup.py is running as pid %s" % pid.read()
        pid.close()
    else:
        print "mgr5backup.py is not running\n"

def Chfull():
    if "1" in check:
        pid = open(pidfile,  'r')
        print "mgr5backup.py now is running as pid %s" % pid.read()
    if "2" in check:
        print "LVM Error"
    if "3" in check:
        print "FTP Server ERROR"

def Zabbix():
    chlvm()
    chftp()
    ZF = open(Zabbix_Mark_File,  'w')
    ZLF = open(Zabbix_LVM_File,  'w')
    ZFF = open(Zabbix_FTP_File,  'w')
    if "2" in check:
        ZLF.write("1")
    else:
        ZLF.write("0")
    if "3" in check:
        ZFF.write("1")
    else:
        ZFF.write("0")
    ZF.write("0")
    ZLF.close()
    ZFF.close()
    ZF.close()


def Error():
    print "Error !"
    file=open(Zabbix_Error_File,  "w")
    file.write("1")
    file.close()
    os.remove(pidfile)
    Zabbix()

def Error0():
    file=open(Zabbix_Error_File,  "w")
    file.write("0")
    file.close()

def help():
    return """Help function: Basic Usage:\n
    \tstart      - Start full backup
    \tid         - Start backup only one VM, using by id number, example: ./mgr5backup.py id 15
    \tlist       - Display the virtual machine list
    \tstatus     - Status of process
    \tchftp      - Check data into your ftp server
    \tchlvm      - Start check the logical volumes
    \tchfull     - Full check
    \tftpold     - Show old or excess directories in the Node ID directory of the ftp server
    \tftpdel     - Remove some file or directory on the FTP server
    \tclean      - Remove old or excess directories in the Node ID directory of the ftp server
    \tzabbix-marks - Create all zabbix marks
    \thelp       - Print help\n"""


def Main():
    try:
        if sys.argv[1] == 'id':
            Check()
            StartBackup(sys.argv[2])
            os.remove(pidfile)
            ZF = open(Zabbix_Mark_File,  'w')
            ZF.write("0")
            ZF.close()
        elif sys.argv[1] == 'start':
            Error0()
            Check()
            Search()
            os.remove(pidfile)
            Zabbix()
        elif sys.argv[1] == 'chlvm':
            chlvm()
        elif sys.argv[1] == 'list':
            listF()
        elif sys.argv[1] == "status":
            stat()
        elif sys.argv[1] == "chftp":
            chftp()
        elif sys.argv[1] == "clean":
            CleanDirs()
        elif sys.argv[1] == "ftpold":
            CleanDirs(remove=None)
        elif sys.argv[1] == "ftpdel":
            ftpdel(sys.argv[2])
        elif sys.argv[1] == "chfull":
            chlvm()
            chftp()
            Chfull()
        elif sys.argv[1] == "zabbix-marks":
            Error0()
            Check()
            Zabbix()
        else:
          print help()
    except IndexError:
        print help()


if __name__ == '__main__':
    Conf()
    Main()
