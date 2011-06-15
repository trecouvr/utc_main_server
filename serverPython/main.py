#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author Thomas

Création du server
ajout des ports serials
identification et réarrangement
"""

import os
ROOT_DIR  = os.path.split(os.path.split(os.path.dirname(os.path.abspath(__file__)))[0])[0]
#print ROOT_DIR

import subprocess
import time

#subprocess.Popen([os.path.join(ROOT_DIR,"com","serverPython","kill_socket.sh"),"50000"]).wait()
#time.sleep(2)

from server import *

server = Server()
server.start()

#server.addSubprocessClient("clients/python/UDPClient/main.py")
#server.addSubprocessClient(os.path.join(ROOT_DIR,"Visio","UTCamera","bin","UTCamera"))
server.addSubprocessClient(os.path.join(ROOT_DIR,"pinceControl","AX12","scriptPince.py"))
#server.addSubprocessClient(os.path.join(ROOT_DIR,"clients","soutenance_quentin","main.py"))
#server.addSubprocessClient(["../../../IA/main.py","1","0"])
#p = subprocess.Popen(os.path.join(ROOT_DIR,"smartphone.py"))


import glob

def scanSerials():
	pathname = '/dev/ttyACM*'
	return glob.iglob(pathname)


for serial in scanSerials():
	server.addSerialClient(serial,115200)

server.parseMsg(ID_SERVER, "ls")


print 'fin thread principal'




