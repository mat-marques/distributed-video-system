import socket
import threading
import sys

# Classe que recebe dados dos clientes
class ClientReseiver(threading.Thread):
    def __init__(self, qtdClientsMax):
        threading.Thread.__init__(self)
        self.qtdClients = 0
        self.qtdClientsMax = qtdClientsMax
        self.clients = []

    # Verifica se o cliente já está inserido no canal
    def verifyClient(self, dest):
        for self.clients in info:
            if info[0] == dest[0]:
                return True
        return False

    # Remove um cliente de um canal
    def removeClient(self, ip):
        for self.clients in info:
            if info[0] == ip:
                self.clients.remove(info)
                print("O cliente ", dest ," foi removido!")
                return True
        return False

    # Insere um cliente
    def addClient(self, dest):
        if not self.verifyClient(dest):
            # Insere o cliente
            self.clients.append(dest)
            print("Um novo cliente foi adicionado: ", dest)
            return True
        return False

    def run(self):
        self._stopped = False

        print("Thread de captura de dados dos clientes iniciada!")

        # Recebe o dado de um cliente
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
            tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            tcp.bind(('', 9092))
            tcp.listen(1)

            file_num = 0

            while not self._stopped:
                content, address = tcp.accept()
                received_msg = content.recvmsg(BUFFER_SIZE)
                message = str(received_msg[0], 'utf-8')
                
                print(message)
                
                # Conectar no canal
                if message[0:2] == "10":
                    # IP e Porta do cliente que fez a requisição
                    dest = (address[0], message[3:7])
                    if self.qtdClients < self.qtdClientsMax:
                        if self.addClient(dest):
                            
                            # Envia a confirmação da operação: Sucesso
                            tcp.send(bytes("01", encoding='utf-8'))

                            self.qtdClients += 1
                    else:
                        # Envia a confirmação da operação: Fracasso
                        tcp.send(bytes("00", encoding='utf-8'))

                # Listar Conexões
                if message == "11":
                    # Envia a string de IPs
                    tcp.send(bytes(str(self.clients), encoding='utf-8'))

                # Sair do canal
                if message == "12":
                    # Remove cliente
                    self.removeClient(address[0])

                    self.qtdClients -= 1

                    # Envia a confirmação da operação: Sucesso
                    tcp.send(bytes("01", encoding='utf-8'))
                    

            
    def stop(self):
        self._stopped = True


