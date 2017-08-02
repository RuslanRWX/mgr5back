# mgr5back
mgr5back - программка для бэкапирования виртуальных машин программного продукта ISP VMmanager 5 


# install pip on CentOS
yum -y install python-pip

# install php on Debian/Ubuntu
apt-get update && apt-get install python-pip


#then install additional modules

pip install mysql-connector  
or
centos: yum install mysql-connector-python
debian: apt-get install python-mysql.connector

pip install xmltodict 

pip install configparser

pip install colorama


##########

# Развертывание 
<br>git clone https://github.com/ruslansvs2/mgr5back.git
<br>Описание содержимого в каталоге 
<br>
# Add Jobs To cron

0 23  *  * *   root /root/scripts/mgr5back/mgr5back.py start >> /var/log/mgr5back.log 2>&1
<br>0 0  1  * *   root /root/scripts/mgr5back/mgr5back.py clean >> /var/log/mgr5back.clean.log 2>&1


<br>2.1 cd mgr5backup; ls -al 
<br>2.2 файлы
      config.ini  - конфигурационный файл 
      mgr5backup.py - скрипт бекапа 
      README.md - файл readme 
<br>Установка модулей 
<br>3.1 Актуальная установка модулей описана в файле README.md 
<br>Конфигурация config.ini 
<br>4.1 cat config.ini

##############################################
<br><b3>Main configuration file config.ini<b3>
<br>[main]
<br>#ID vmmanager of your node
<br>NodeID: 2
<br>#exclude the virtual machines which should not be backup.
<br># example NoBackupID='51,12' - ids are separeted by commas. 0 - all virtual machines to backup 
<br>NoBackupID: 0
<br># Connect to ftp server via the vmmgr-backup storage.
<br>ftp_conn: /usr/local/mgr5/etc/.vmmgr-backup/storages/st_3
<br># Pidfile
<br>pidfile: /tmp/mgr5back.pid
<br># Backup directory
<br>BackDir: /backup
<br># Connect to database via the vmmgr config file
<br>#FileDB: /usr/local/mgr5/etc/vmmgr.conf.d/db.conf
<br>FileDB: /usr/local/mgr5/etc/vmmgr.conf.d/db.conf
<br># You can use script with gzip and without zipping, YES or NO
<br>Gzip: YES
<br># How many days keep the backup files
<br>SaveDate: 30
<br># Approximate period of time the backing up process, min 1 day
<br>checkdate: 8
<br># The mark file of zabbix
<br>ZabbixMarkFile: /tmp/ZabbixMark.log 
<br># The LVM mark file of zabbix 
<br>ZabbixLVMFile: /tmp/ZabbixLVM.log
<br># The FTP mark file of zabbix 
<br>ZabbixFTPFile: /tmp/ZabbixFTP.log

#######################################################
<br>Help функция
<br>start - Start full backup
<br>id - Start backup only one VM, using by id number, example: ./mgr5backup.py id 15
<br>list - Display the virtual machine list
<br>status - Status of process
<br>chftp - Check data into your ftp server
<br>chlvm - Start check the logical volumes
<br>chfull - Full check
<br>ftpold - Show old or excess directories in the Node ID directory of the ftp server
<br>ftpdel - Remove some file or directory on the FTP server
<br>clean - Remove old or excess directories in the Node ID directory of the ftp server
<br>zabbix-marks - Create all zabbix marks
<br>help - Print help

<br>Запуск бекапа 
<br>6.1 ./mgr5back.py start   – запустит полный бекап всех виртуальных машин кроме  NoBackupID 
<br>6.2 ./mgr5back.py id  151  – запуск бекапа виртуальной машины с id 151
<br>Вывод всех виртуальных машин 

<br>7.1 ./mgr5back.py list 
<br>Статус 
<br>8.1 ./mgr5back.py status  – вывод статуса программки

<br>Проверка бекапов 
<br>9.1 Проверка LVM
<br>9.1.1  ./mgr5back.py chlvm   – проверит ошибки на уровни LVM 
<br>вывод:  
<br>LVM OK  – все без ошибок 
<br>LVM Error  - ошибка, выполните lvs, возможно после бекапа не удалось удалить логический раздел   

<br>9.2 Проверка наличия бекапа на FTP сервере 
<br>9.2.1  ./mgr5back.py chftp  
<br>вывод 
<br>Start checking the ftp server
<br>Check the volume vm13798, the virtual machine ID 134
<br>Check DIR 134 is Ok
<br>Check a file vm13798_20170404020002 is OK  
<br>Check the volume vm14913, the virtual machine ID 176
<br>The virtual machine ID 176, have not the directory name like 176, it's ERROR
<br>Check period of date 20170404000000
<br>FTP Server ERROR 

<br>тут происходит проверка на наличия папок и файлов на стороне ftp сервера.
<br>  ./mgr5back.py chfull  – объединяет проверку chlvm и chftp 

<br>Удаление лишних файлов и папок на бекап сервере. 
<br>11.1  ./mgr5back.py clean 
<br>11.1.a Вывод при удаление, на бекап сервере лишней или старой директории бекапа VM c ID 600 
<br>Start remove old or excess directories in the Node ID directory of the ftp server
<br>Remove a directory 600
<br>FTP server has been cleaned,bye! 
<br>11.1.b  вывод без удаления, файлы  консинстентны
<br>Start remove old or excess directories in the Node ID directory of the ftp server
<br>Nothing have been cleaned  
<br>11.1с - Вывод при ошибке 
<br>Start remove old or excess directories in the Node ID directory of the ftp server
<br>Remove a directory 600
<br>Error !!! You have an error on the ftp server. Check directory name as the node id#2,permissions etc
<br>FTP server have cleaned,bye! 

<br>12. ftpold  - отобразит старые или лишние файлы и папки на фтп-сервере (в отношении к Ноде)
<br>пример: ./mgr5back.py ftpold
<br>Start remove old or excess directories in the Node ID directory of the ftp server
<br>Old or excess file or directory 999
<br>Old or excess file or directory 161

<br>13.  ftpdel     - удалить папку или файл на фтп сервере вручную
<br>пример: ./mgr5back.py ftpdel 999
<br>Remove the directory 999

<br>14. zabbix-marks - Create all zabbix marks  
<br>14.1 Можно запускать при стартовой установке или после дебага ошибки, в противном случаи в заббиксе
<br>будет висеть ошибка до следующего запуска бекапа. 


<br><br>Восстановление 
<br>Заходим на бекап сервер 
<br>1.1 Смотрим куда бекапится:
<br> grep name `grep ftp_conn /root/scripts/mgr5back/config.ini | awk '{print $2}'`
<br>1.2 На бекап сервере: cd number_of_node/vm-id/date
<br>example: cd /2/229/20170611191737
<br>Разархивировать 
<br>2.1 mv vds vds.gz
<br>example: mv vm15497_20170611191737  vm15497_20170611191737.gz
<br>2.2 Копирование на ноду где будем восстанавливать 
<br> На ноде 
<br>3.1 Запуск gunzip vds.gz
<br>example: gunzip vm15497_20170611191737.gz 
<br>Заливаем бекап на img c виртуальной машинной: dd if=vds of=/IMG 
<br>Note: Виртуальная машина должна быть выключена, размер образа нового диска должен соответствовать или быть больше бекапа. 
 

