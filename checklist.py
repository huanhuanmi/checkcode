#!/usr/bin/env python
# -*- coding: UTF-8 -*-
__author__ = 'huan'
__version__ = 'checklist'
import os
import re
import subprocess
import  sys
import time

#----------------------------------------------General functions-------------------------------------------
def test(v):
    test.result = v
    return  v

def printdvline(num):
    try:
        t = isinstance(num, int)
        if t == False:
            print('\n')
            return
        else:
            if (num == 1):
                print("---------------------------------------------------------" + '\n')
            else:
                print('\n')
    except:
        print('\n')

def check_servicestatus(servername):
    s = servername
    try:
        d = subprocess.Popen(["service "+s+" status"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        out = d.stdout.read()
        runregex = re.compile('is running')
        stopregex = re.compile('stop')
        unregex = re.compile('unrecognized')
        if len(runregex.findall(out)):
            print('service '+servername+' is runing')
            return 'ok'
        elif len(stopregex.findall(out)):
                print('service '+servername+' is stop')
                return 'false'
        else:
            print("can not find servce status")
            return 'non'
    except:
        print("get service status error")
        return 'err'

def check_ping(ip):
    try:
        b = subprocess.Popen(["ping -c 1 -w 1 "+ ip],stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        out = b.stdout.read()
        regex = re.compile('100% packet loss')
        if len(regex.findall(out)) == 0:
            print(ip+':ping is ok')
            return 'ok'
        else:
            print(ip+':ping is false')
            return  'false'
    except:
        print("error")
        return ("err")
# -------------------------------------local network------------------------------------------------------
#check bond status
def check_bound():
    isbond = 'False'
    bondstatus = 'down'
    for line in os.popen('cat /proc/net/bonding/bond0'):
        if test(re.match('^MII Status:\s+(\w+)\n$',line)):
            isbond = 'True'
            m = test.result
            flags = m.group(1).split(',')
            if 'up' in flags:
                bondstatus = 'up'
                continue
            else :
                bondstatus = 'down'
                break
    print("is bond?:"+isbond)
    if (isbond == 'True'):
        print("bond status:"+bondstatus)
    return

def check_lo_neighbor():
    isbgpd = False
    isospf = False
    bgpdstatus = 'up'
    ospfdstatus = 'up'
    ping = False
    for line in os.popen('service bgpd status'):
        if test(re.match('^bgpd.*running.*\n$',line)):
            isbgpd = True
        elif test(re.match('^bgpd/s+is/s+stop...\n$', line)):
            bgpdstatus = 'down'
    if isbgpd:
        print("bgp is:"+bgpdstatus)
        for line in os.popen("cat /etc/quagga/bgpd.conf |grep neighbor |awk '{print $2}' |sort -u"):
            if test(re.match("^\s*\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\s*$",line)):
                pingneighbor = test.result
                print("test ping neighbor:")
                check_ping('pingneighbor')
                time.sleep(1)
            else:
                print("can not find neighbor")
    return
#checknameserver ip
def check_nameserver(serverip1 = '172.16.16.16',serverip2 = '10.16.16.16'):
    serverip1 = serverip1
    serverip2 = serverip2
    nameservercfg = 'False'
    name_servers = list()
    for line in open('/etc/resolv.conf'):
        if test(re.match('^\s*nameserver\s+(\S+)\s*\n$', line)):
            print(serverip1)
            if ((serverip1 == test.result.group(1))or(serverip2 == test.result.group(1))):
                nameservercfg = 'True'
            name_servers.append(test.result.group(1))
    print("nameserver config is:"+nameservercfg)
    print(name_servers)
    return name_servers


#----------------------------------loopbackcheck-----------------------------------------
def check_loopback():
    path = '/etc/sysconfig/network-scripts/ifcfg-lo-range'
    bgppath = '/etc/quagga/bgpd.conf'
    ospfpath ='/etc/quagga/ospfd.conf'
    if check_servicestatus('bgpd') == 'ok':
        filepath2 = bgppath
    elif check_servicestatus('ospfd') == 'ok':
        filepath2 = ospfpath
    else:
        return "not bgp or ospf status"
    os.path.exists(filepath2)
    for i in range(0,6):
        filepath1 = path+str(i)
        if os.path.exists(filepath1):
            with open(filepath1,'r') as f1:
                for line in f1:
                    if line[:13] == 'IPADDR_START=':
                        startip=line[13:]
                        ipstartnum=int(startip.split('.')[-1])
                        print("\nIPADDR_START:"+line[13:])
                    elif line[:11] == 'IPADDR_END=':
                        endip=line[11:]
                        ipendnum=int(endip.split('.')[-1])
                        print("IPEND:"+line[11:])
                    else:
                        continue
        else:
            break
    with open(filepath2,'r') as f2:
        for line in f2:
            args = line.strip().split()
            if args == []:
                break
            if args[0] == 'network':
                if '/' in args[1]:
                    netip = args[1].split('/')
                    quaggastartnum = int(netip[0].split('.')[-1])
                    n = 32-int(netip[1])
                    quaggaendnum = (quaggastartnum+2**n) -1
                    if quaggaendnum >= 255:
                        quaggaendnum = 255
                else:
                    bgpips = list()
                    bgpips.append(args[1])

    if ipstartnum == quaggastartnum and ipendnum == quaggaendnum:
        print("loopback config files is true!")
        f2.close()
        return 'ok'
    else:
        print("loopback config files is not true!")
        f2.close()
        return 'false'




#-----------------------------------servicecheck------------------------------------------
def check_rpmversion(rpmversion,rpm):
    ver = rpmversion
    rpname = rpm
    try:
        d = subprocess.Popen(["rpm -qa "+rpname],stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        out = d.stdout.read()
        regex = re.compile(ver)
        if len(regex.findall(out)):
            print("rpmversion is right: \nsoftversion is "+ver)
            return 'true'
        else:
            print("rpmversion is false: \nsoftversion is not "+ver)
            return 'false'
    except:
        print("err")
        return "error"


if __name__=='__main__':
    print('\n\n---------------------CHECKLIST---------------------------')
    print('\n-----------------neterok checklist-----------------------')

    #network check
    try:
        print("now check bond status:")
        check_bound()
        time.sleep(0.3)
        printdvline(1)
        print("now check nameserver status")
        check_nameserver()
        time.sleep(0.3)
        printdvline(1)
        print("now check the neighbor status")
        check_lo_neighbor()
        printdvline(1)
        check_rpmversion('haproxy-1.5.12-21.x86_64','haproxy')
        printdvline(1)
        print("now check the service status")
        check_servicestatus('bgpd')
        printdvline(1)
        print("now check loopback status:")
        check_loopback()
        time.sleep(0.3)
        printdvline(1)

    except:
        print("checklist is some abnormity interruption")
    #service check
