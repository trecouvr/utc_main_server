# -*- coding: utf-8 -*-
"""
@author Thomas
"""
import threading
from queue import Queue, Empty
import colorConsol


class Sender(threading.Thread):
	"""
	Cette class est une boucle infinie threadé qui a pour rôle d'envoyer
	les messages aux clients. Le server se contente de lui donner un message
	à envoyer via {@link #addMsg addMsg}. La {@link #run boucle} du thread
	observe à chaque tour si il y a un message à envoyer, si c'est le cas
	elle appelle la {@link #_send fonction pour envoyer}.
	"""
	def __init__(self, server):
		threading.Thread.__init__(self,None, None, "Sender")
		self.daemon = True # ce thread est un daemon, il s'arretera quand tous les threads non daemon s'arreteront
		self._server = server
		self._queue = Queue()
	
	def addMsg(self, mask_from, to, msg):
		"""
		Ajouter un message à la liste des messages à envoyer

		@param mask_from (bitmask/int) si le client est auth ce paramètre correpond
		au bitmask 0001000 avec le nième bit set (n=id du client), sinon
		il correspond tout simplement à l'id du client
		@param to (int) l'id du client à qui ce message est destiné
		@param msg (str) le message
		"""
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
		"""
		@param mask_from (bitmask/int) voir {@link #addMsg addMsg}
		@param to (int) l'id du client à qui ce message est destiné
		@param msg (str) le message
		"""
		self._server.write("send : '%s'"%msg)
		if mask_from >= 0 or to == 0:
			c = self._server.clients[to]
			threading.Thread(None, c.send, "Sender send to %s"%c.id, (mask_from, msg)).start()
		else:
			self._server.write("%s is not auth, he can speak only to the server"%self._server.clients[mask_from], colorConsol.FAIL)
			
		
		
		
		
		
		
		
		
		
		
		
		
		
