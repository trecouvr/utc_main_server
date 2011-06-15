# -*- coding: utf-8 -*

import serial
from socket import *
import subprocess
import re
import sys

host = "";
port = int(sys.argv[1]) if len(sys.argv)>1 else 5555

p = subprocess.Popen("ifconfig", shell=True, stdout=subprocess.PIPE)
result = p.communicate()[0].strip().split("\n\n")

interfaces = list()
for bloc in result:
	r = re.search('^(\S+)\s', bloc)
	name = r.group(1)
	r = re.search('inet add?r:(\S+) ', bloc)
	ip = r.group(1) if r else ""
	r = re.search('(\d+.\d+) [KMG]?B', bloc)
	debit = float(r.group(1)) if r else 0.0
	interfaces.append((name,ip,debit))

# les wifi en premier
def fn_cmp(x,y):
	namex, ipx, debitx = x
	namey, ipy, debity = y
	if 'wlan' in namex:
		poidsx = 0
	else:
		poidsx = 1
	if 'wlan' in namey:
		poidsy = 0
	else:
		poidsy = 1

	return poidsx - poidsy
	
interfaces = sorted(interfaces, cmp=lambda x,y: fn_cmp(x,y))

for name,ip,debit in interfaces:
	#print name, ip, debit
	if name != 'lo' and ip and debit > 0.0:
		print "found :",name, ip, port
		host = ip
		break

if not host:
	host = raw_input("host : ")


usbdev = "/dev/ttyACM0"
#ser = serial.Serial(usbdev, 115200)


bufsize = 1024
addr = (host,port)


UDPSock = socket(AF_INET,SOCK_DGRAM)
UDPSock.bind(addr)

print "Standby ready !"

while 1:
    data,addr = UDPSock.recvfrom(bufsize)
    print data
    #ser.write(buf)

UDPSock.close()
#ser.close()


