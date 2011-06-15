# -*- coding: utf-8 -*-
"""
@author Thomas

Thread servant à envoyer les messages daux clients
"""
import threading
from Queue import Queue, Empty
import colorConsol


class Sender(threading.Thread):
	def __init__(self, server):
		threading.Thread.__init__(self,None, None, "Sender")
		self.daemon = True # ce thread est un daemon, il s'arretera quand tous les threads non daemon s'arreteront
		self._server = server
		self._queue = Queue()
	
	def addMsg(self, mask_from, to, msg):
		self._queue.put((mask_from,to,msg))
	
	def run(self):
		self._server.write("Sender loop start", colorConsol.OKGREEN)
		while not self._server.e_shutdown.is_set():
			try:
				mask_from, to, msg = self._queue.get(True, 2)
			except Empty:
				pass
			else:
				self._send(mask_from, to, msg)
				self._queue.task_done()
		self._server.write("Sender loop stop", colorConsol.WARNING)
	
	def _send(self, mask_from, to, msg):
		self._server.write("send : '%s'"%msg)
		for c in self._server.clients:
			if to & (1 << c.id):
				#self._server.write("to : '%s'"%c.id)
				threading.Thread(None, c.send, "Sender send to %s"%c.id, (mask_from, msg)).start()
		
		
		
		
		
		
		
		
		
		
		
		
		
