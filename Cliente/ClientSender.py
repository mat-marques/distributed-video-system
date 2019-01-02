import socket
import threading
import sys

# Classe que envia os pacote de stream de video
class ClientSender(threading.Thread):
    def __init__(self, qtdClientsMax):
        threading.Thread.__init__(self)

    def run(self):
        self._stopped = False

        print("Thread de envio dos pacotes de stream para os clientes iniciada!")

                
    def stop(self):
        self._stopped = True


