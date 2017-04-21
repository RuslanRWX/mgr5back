# mgr5back


# install pip on CentOS
yum -y install python-pip

# install php on Debian/Ubuntu
apt-get update && apt-get install python-pip


#then install additional modules

pip install mysql-connector

pip install xmltodict 

pip install configparser

pip install colorama


# Add Jobs To cron

0 23  *  * *   root /root/scripts/mgr5back/mgr5back.py start >> /var/log/mgr5back.log 2>1&
0 0  1  * *   root /root/scripts/mgr5back/mgr5back.py clean >> /var/log/mgr5back.clean.log 2>1&



