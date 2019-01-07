import socket
import threading
import sys
import queue
import random
import time
import vlc
import os

# Fila para utilizar na thread de transmissão
queue_sender = queue.Queue(1)

# Fila para usar na thread de vídeo
queue_video = queue.Queue(1)

# Fila para armazenar todos os nomes de arquivos que foram armazenados em disco
file_names_stored = queue.Queue(0)

#fila para armazenar os videos que serão removidos pela thread de remoção
queue_video_remove = queue.Queue(0)

# Lista com os ips e portas dos clientes. 
# Os dados são armazenados no formato de tuplas ("", "")
clients = []

# Quantidade máxima de clientes conectados
QTD_CLIENTS = 1

# Quantidade atual de clientes conectados
qtd_clients_connected = 0

# Número da porta da comunicação entre cliente e servidor
CLIENT_SERVER_PORT = 9091

# Número da porta da comunicação entre cliente e cliente - mensagens
CLIENT_CLIENT_PORT_M = 9092
# Número da porta da comunicação entre cliente e cliente - servidor de espera para as respostas
CLIENT_CLIENT_PORT_S = 9093
# Número da porta da comunicação entre cliente e cliente - vídeo
CLIENT_CLIENT_PORT_V = 9094

# Nome do diretório dos vídeos
DIR_PATH = "./Movie/"


class ClientReseiver(threading.Thread):
    """Classe que recebe dados dos clientes, porta 9092"""

    def __init__(self, buffer_size):
        threading.Thread.__init__(self)
        self.BUFFER_SIZE = buffer_size

    def verifyClient(self, dest):
        '''Verifica se o cliente já está inserido no canal'''
        global clients
        for info in clients:
            if info[0] == dest[0]:
                return True
        return False

    def removeClient(self, ip):
        '''Remove um cliente de um canal'''
        global clients
        for info in clients:
            if info[0] == ip:
                clients.remove(info)
                print("O cliente ", info ," foi removido!")
                return True
        return False

    def addClient(self, dest):
        '''Insere um cliente'''
        global clients
        if not self.verifyClient(dest):
            # Insere o cliente
            clients.append(dest)
            print("Um novo cliente foi adicionado: ", dest)
            return True
        else:
            print("O cliente ", dest, " foi reposicionado.")
            return True

        return False

    def run(self):
        self._stopped = False
        global clients
        global qtd_clients_connected
        global QTD_CLIENTS
        global CLIENT_CLIENT_PORT_M
        global CLIENT_CLIENT_PORT_S

        print("Thread de captura de dados dos clientes iniciada!")

        # Recebe o dado de um cliente
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
            tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            tcp.bind(('', CLIENT_CLIENT_PORT_M))
            tcp.listen(1)

            file_num = 0

            while not self._stopped:
                content, address = tcp.accept()
                received_msg = content.recvmsg(self.BUFFER_SIZE)
                message = str(received_msg[0], 'utf-8')
                
                print(message)
                
                # Conectar no canal
                if message[0:2] == "10":
                    # IP e Porta do cliente - vídeo
                    dest = (address[0], CLIENT_CLIENT_PORT_V)
                    # IP e Porta do cliente - mensagem
                    destResp = (address[0], CLIENT_CLIENT_PORT_S)

                    print("Solicitação de conexão com o cliente: ", str(dest))
                    
                    if qtd_clients_connected < QTD_CLIENTS:
                        if self.addClient(dest):
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_cl:
                                tcp_cl.connect(destResp)

                                # Envia a confirmação da operação: Sucesso
                                tcp_cl.send(bytes("01", encoding='utf-8'))

                                tcp_cl.close()
                            qtd_clients_connected += 1
                        else:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_cl:
                                tcp_cl.connect(destResp)
                                
                                # Envia a confirmação da operação: Fracasso
                                tcp.send(bytes("00", encoding='utf-8'))

                                tcp_cl.close()

                # Listar Conexões
                if message == "11":
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_cl:
                        tcp_cl.connect(destResp)
                        # Envia a string de IPs
                        print("Listagem de IPs solicitada! Cliente: ", dest)
                        IP = socket.gethostbyname(socket.getfqdn())
                        tcp_cl.send(bytes(str((IP, 9092)) + str(clients), encoding='utf-8'))
                        tcp_cl.close()

                content.close()

    def stop(self):
        self._stopped = True


class ServerReceptor(threading.Thread):
    """Classe que recebe os dados do canal - Servidor, porta CLIENT_SERVER_PORT

    """

    def __init__(self, buffer_size):
        threading.Thread.__init__(self)
        self.BUFFER_SIZE = buffer_size
        self.producerVideo = ClientProducerVideo()
        self.send_video =  ClientSender()
        self.player_video = PlayerAuto()
        self.garbage_collector = GarbageCollector()
        self._stopped = False

    def run(self):
        self._stopped = False
        global file_names_stored
        global CLIENT_SERVER_PORT

        self.producerVideo.start()
        self.send_video.start()
        self.player_video.start()
        self.garbage_collector.start()

        print("Thread de captura de dados iniciada (vídeos)!")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk_server:
            sk_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            sk_server.bind(('', CLIENT_SERVER_PORT))
            sk_server.listen(1)

            file_num = 0

            while not self._stopped:
                content, address = sk_server.accept()

                # Recebe o nome do arquivo
                nome0 = "./Movie/{}.mkv".format(file_num)
                nome1 = "{}.mkv".format(file_num)
                #sys.stdout.write("Recebendo '{}' de {}.\n".format(nome, address[0]))
                sys.stdout.flush()

                # Recebe o arquivo
                with open(nome0, 'wb') as down_file:
                    recv_read = content.recv(self.BUFFER_SIZE)
                    while recv_read:
                        down_file.write(recv_read)
                        recv_read = content.recv(self.BUFFER_SIZE)
                
                # Armazena o nome do arquivo salvo na fila
                file_names_stored.put(nome1)

                content.close()
                file_num += 1

        print("Thread de captura de dados interrompida, cliente/servidor (vídeos)!")

    def stop(self):
        self._stopped = True
        print(self._stopped)


class ClientReceptor(threading.Thread):
    """Classe que recebe os dados do canal - Cliente, porta 9094

    """

    def __init__(self, buffer_size):
        threading.Thread.__init__(self)
        self.BUFFER_SIZE = buffer_size
        self.producerVideo = ClientProducerVideo()
        self.send_video =  ClientSender()
        self.player_video = PlayerAuto()
        self.garbage_collector = GarbageCollector()

    def run(self):
        self._stopped = False
        global file_names_stored
        global CLIENT_SERVER_PORT_V

        self.producerVideo.start()
        self.send_video.start()
        self.player_video.start()
        self.garbage_collector.start()

        print("Thread de captura de dados iniciada (vídeos)!")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk_server:
            sk_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            sk_server.bind(('', CLIENT_CLIENT_PORT_V))
            sk_server.listen()

            file_num = 0

            while not self._stopped:
                content, address = sk_server.accept()

                # Recebe o nome do arquivo
                nome = "./Movie/{}.mkv".format(file_num)
                nome1 = "{}.mkv".format(file_num)
                sys.stdout.write("Recebendo '{}' de {}.\n".format(nome, address[0]))
                sys.stdout.flush()

                # Recebe o arquivo
                with open(nome, 'wb') as down_file:
                    recv_read = content.recv(self.BUFFER_SIZE)
                    while recv_read:
                        down_file.write(recv_read)
                        recv_read = content.recv(self.BUFFER_SIZE)
                        # Armazena o nome do arquivo salvo na fila
                        file_names_stored.put(nome1)

                content.close()
                file_num += 1

            sk_server.close()
        print("Thread de captura de dados interrompida, cliente/cliente (vídeos)!")

    def stop(self):
        self._stopped = True


class ClientProducerVideo(threading.Thread):
    """Classe que pega os nomes dos arquivos armazenados e coloca em um fila - Produtor

    """

    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        self._stopped = False
        global queue_sender
        global queue_video
        global file_names_stored

        print("Thread de monitoramento de pasta iniciada!")

        while not self._stopped:
            if not file_names_stored.empty():
                file_name_used = file_names_stored.get()
                if queue_sender.full():
                    queue_sender.get()
                if queue_video.full():
                    queue_video_remove.put(queue_video.get())
                    
                queue_sender.put(file_name_used)
                queue_video.put(file_name_used)


                
    def stop(self):
        self._stopped = True


class ClientSender(threading.Thread):
    """Classe que envia os pacotes de stream de video - Consumidor, porta CLIENT_CLIENT_PORT

    """

    def __init__(self):
        threading.Thread.__init__(self)
        self.BUFFER_SIZE = 1024
        
    def run(self):
        self._stopped = False
        global queue_sender
        global file_names_stored
        global qtd_clients_connected
        global DIR_PATH

        print("Thread de envio dos pacotes de stream para os clientes iniciada!")

        while True:
            if not queue_sender.empty():
                file_name = queue_sender.get()
                cont = 0
                while cont < qtd_clients_connected:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk_client:
                        sk_client.connect(clients[cont])
                        print("Tranmitindo vídeo para: ", clients[cont])
                        # Envia o arquivo
                        with open(DIR_PATH + file_name, 'rb') as up_file:
                            send_read = up_file.read(self.BUFFER_SIZE)
                            while send_read:
                                sk_client.send(send_read)
                                send_read = up_file.read(self.BUFFER_SIZE)
                                cont+=1
            
                time.sleep(random.random())

    def stop(self):
        self._stopped = True


class Player:
    """Classe que trabalha com o player vlc

    """


    def __init__(self, path):
        self.vlc_instance = vlc.Instance('--quiet')
        self.player = self.vlc_instance.media_player_new()
        self.path = path

    def play(self, file):
        '''file = nome do arquivo. ex: '_000040.mkv'''
        media = self.vlc_instance.media_new(self.path+file)
        self.player.set_media(media)
        self.player.play()


class PlayerAuto(threading.Thread, Player):
    """Classe que vai executar os videos no VLC - Consumidor

    """

    def __init__(self):
        threading.Thread.__init__(self)
        Player.__init__(self, "./Movie/")
    
    def run(self):
        self._stopped = False

        print("Thread de execução de vídeos iniciada!")

        while not self._stopped:
            if not queue_video.empty():
                video_name = queue_video.get()
                
                Player.play(self, video_name)
                time.sleep(2)
                queue_video_remove.put(video_name)


    def stop(self):
        self._stopped = True


class GarbageCollector(threading.Thread, Player):
    """Classe que apaga os arquivos já executados

    """

    def __init__(self):
        threading.Thread.__init__(self)


    def remove_video(self, file_name):
        '''remove o video arquivo como parâmetro'''

        os.remove("./Movie/" + file_name)

    def run(self):
        self.stopped = False

        print('Thread de remoção de videos iniciada!')

        while not self.stopped:
            if not queue_video_remove.empty():
                if not queue_sender.empty():
                    if (queue_sender.queue[0] != queue_video_remove.queue[0]):
                        video_name = queue_video_remove.get()
                        self.remove_video(video_name)
                else:
                    video_name = queue_video_remove.get()
                    self.remove_video(video_name)
            time.sleep(random.random())
    
    def stop(self):
        self.stopped = True