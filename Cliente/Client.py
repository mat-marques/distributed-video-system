import socket
import threading
import sys
import queue
import random
import time

# Fila para utilizar na thread de transmissão
queue_sender = queue.Queue(1)

# Fila para usar na thread de vídeo
queue_video = queue.Queue(1)

# Fila para armazenar todos os nomes de arquivos que foram armazenados em disco
file_names_stored = queue.Queue(0)

# Armazena o nome do arquivo que vai ser processado no momento
file_name_used = ""

# Lista com os ips e portas dos clientes. 
# Os dados são armazenados no formato de tuplas ("", "")
clients = []

# Quantidade máxima de clientes conectados
QTD_CLIENTS = 1

# Quantidade atual de clientes conectados
qtd_clients_connected = 0

# Classe que recebe dados dos clientes
class ClientReseiver(threading.Thread):
    def __init__(self, buffer_size, port):
        threading.Thread.__init__(self)
        self.port = port
        self.BUFFER_SIZE = buffer_size

    # Verifica se o cliente já está inserido no canal
    def verifyClient(self, dest):
        for clients in info:
            if info[0] == dest[0]:
                return True
        return False

    # Remove um cliente de um canal
    def removeClient(self, ip):
        for clients in info:
            if info[0] == ip:
                clients.remove(info)
                print("O cliente ", info ," foi removido!")
                return True
        return False

    # Insere um cliente
    def addClient(self, dest):
        if not self.verifyClient(dest):
            # Insere o cliente
            clients.append(dest)
            print("Um novo cliente foi adicionado: ", dest)
            return True
        return False

    def run(self):
        self._stopped = False

        print("Thread de captura de dados dos clientes iniciada!")

        # Recebe o dado de um cliente
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
            tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            tcp.bind(('', self.port))
            tcp.listen()

            file_num = 0

            while not self._stopped:
                content, address = tcp.accept()
                received_msg = content.recvmsg(self.BUFFER_SIZE)
                message = str(received_msg[0], 'utf-8')
                
                print(message)
                
                # Conectar no canal
                if message[0:2] == "10":
                    # IP e Porta do cliente que fez a requisição
                    dest = (address[0], message[3:7])
                    if qtd_clients_connected < QTD_CLIENTS:
                        if self.addClient(dest):
                            
                            # Envia a confirmação da operação: Sucesso
                            tcp.send(bytes("01", encoding='utf-8'))

                            qtd_clients_connected += 1
                    else:
                        # Envia a confirmação da operação: Fracasso
                        tcp.send(bytes("00", encoding='utf-8'))

                # Listar Conexões
                if message == "11":
                    # Envia a string de IPs
                    tcp.send(bytes(str(clients), encoding='utf-8'))

                # Sair do canal
                if message == "12":
                    # Remove cliente
                    self.removeClient(address[0])

                    qtd_clients_connected -= 1

                    # Envia a confirmação da operação: Sucesso
                    tcp.send(bytes("01", encoding='utf-8'))
                
                content.close()

            
    def stop(self):
        self._stopped = True


# Classe que recebe os dados do canal - Servidor
class ServerReceptor(threading.Thread):
    def __init__(self, buffer_size):
        threading.Thread.__init__(self)
        self.BUFFER_SIZE = buffer_size

    def run(self):
        self._stopped = False

        print("Thread de captura de dados iniciada (vídeos)!")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk_server:
            sk_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            sk_server.bind(('', 9091))
            sk_server.listen(1)

            file_num = 0

            while not self._stopped:
                content, address = sk_server.accept()

                # Recebe o nome do arquivo
                nome = "./Movie/{}.mkv".format(file_num)
                #sys.stdout.write("Recebendo '{}' de {}.\n".format(nome, address[0]))
                sys.stdout.flush()

                # Recebe o arquivo
                with open(nome, 'wb') as down_file:
                    recv_read = content.recv(self.BUFFER_SIZE)
                    while recv_read:
                        down_file.write(recv_read)
                        recv_read = content.recv(self.BUFFER_SIZE)
                        # Armazena o nome do arquivo salvo na fila
                        #file_names_stored.put(nome)

                content.close()
                file_num += 1

        print("Thread de captura de dados interrompida (vídeos)!")

    def stop(self):
        self._stopped = True
        print(self._stopped)


# Classe que recebe os dados do canal - Cliente
class ClientReceptor(threading.Thread):
    def __init__(self, buffer_size):
        threading.Thread.__init__(self)
        self.BUFFER_SIZE = buffer_size

    def run(self):
        self._stopped = False

        print("Thread de captura de dados iniciada (vídeos)!")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk_server:
            sk_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            sk_server.bind(('', 9092))
            sk_server.listen()

            file_num = 0

            while not self._stopped:
                content, address = sk_server.accept()

                # Recebe o nome do arquivo
                nome = "./Movie/{}.mkv".format(file_num)
                sys.stdout.write("Recebendo '{}' de {}.\n".format(nome, address[0]))
                sys.stdout.flush()

                # Recebe o arquivo
                with open(nome, 'wb') as down_file:
                    recv_read = content.recv(self.BUFFER_SIZE)
                    while recv_read:
                        down_file.write(recv_read)
                        recv_read = content.recv(self.BUFFER_SIZE)
                        # Armazena o nome do arquivo salvo na fila
                        file_names_stored.put(nome)

                content.close()
                file_num += 1

        print("Thread de captura de dados interrompida (vídeos)!")

    def stop(self):
        self._stopped = True


# Classe que pega os nomes dos arquivos armazenados e coloca em um fila - Produtor
class ClientProducerVideo(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        self._stopped = False

        print("Thread de monitoramento de pasta iniciada!")

        while True:
            if not file_names_stored.empty():
                file_name_used = file_names_stored.get()
                if not queue_sender.full():
                    queue_sender.put(file_name_used)
                    time.sleep(random.random())

                
    def stop(self):
        self._stopped = True


# Classe que envia os pacotes de stream de video - Consumidor
class ClientSender(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.BUFFER_SIZE = 1024
        
    def run(self):
        self._stopped = False

        print("Thread de envio dos pacotes de stream para os clientes iniciada!")

        while True:
            if not queue_sender.empty():
                file_name = queue_sender.get()
                cont = 0
                while cont < qtd_clients_connected:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk_client:
                        sk_client.connect(clients[cont])

                        # Envia o arquivo
                        with open(file_name, 'rb') as up_file:
                            send_read = up_file.read(self.BUFFER_SIZE)
                            while send_read:
                                sk_client.send(send_read)
                                send_read = up_file.read(self.BUFFER_SIZE)
                                cont+=1

                time.sleep(random.random())

    def stop(self):
        self._stopped = True