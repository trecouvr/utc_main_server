#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author Thomas

Création du server
ajout des ports serials
identification et réarrangement
"""


import subprocess
import time

#subprocess.Popen([os.path.join(ROOT_DIR,"com","serverPython","kill_socket.sh"),"50000"]).wait()
#time.sleep(2)

from server import *

server = Server()
server.start()

#server.addSubprocessClient("clients/python/UDPClient/main.py")
#server.addSubprocessClient(os.path.join(ROOT_DIR,"Visio","UTCamera","bin","UTCamera"))
#server.addSubprocessClient(os.path.join(ROOT_DIR,"pinceControl","AX12","scriptPince.py"))
#server.addSubprocessClient(os.path.join(ROOT_DIR,"clients","soutenance_quentin","main.py"))
#server.addSubprocessClient(["../../../IA/main.py","1","0"])
#p = subprocess.Popen(os.path.join(ROOT_DIR,"smartphone.py"))


import glob

def scanSerials():
	pathname = '/dev/ttyACM*'
	return glob.iglob(pathname)


for serial in scanSerials():
	server.addSerialClient(serial,115200)

server.parseMsg(ID_SERVER, "ls()")

class KillableInput(threading.Thread):
	def __init__(self):
		super(self.__class__, self).__init__()
		self.daemon = True
		self._queue = Queue.Queue()

	def run(self):
		while not server.e_shutdown.isSet():
			self._queue.put(raw_input())

	def get(self, timeout):
		try:
			c = self._queue.get(True, timeout)
		except Queue.Empty:
			return None
		else:
			self._queue.task_done()
			return c

input = KillableInput()
input.start()

while not server.e_shutdown.isSet():
	msg = input.get(1)
	if msg:
		server.parseMsg(ID_SERVER, msg)

print 'fin thread principal'




