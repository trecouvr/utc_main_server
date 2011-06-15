#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author Thomas

Création du server
ajout des ports serials
identification et réarrangement
"""
import os
import sys
SERVER_ROOT_DIR  = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
sys.path.append(SERVER_ROOT_DIR)

import subprocess
import time

from server import *

server = Server()
server.start()

#server.addSubprocessClient(os.path.join(SERVER_ROOT_DIR,"clients","C++","a.out"))


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




