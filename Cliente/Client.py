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

# Classe que recebe dados dos clientes
class ClientReseiver(threading.Thread):
    def __init__(self, buffer_size, port):
        threading.Thread.__init__(self)
        self.port = port
        self.BUFFER_SIZE = buffer_size

    # Verifica se o cliente já está inserido no canal
    def verifyClient(self, dest):
        global clients
        for info in clients:
            if info[0] == dest[0]:
                return True
        return False

    # Remove um cliente de um canal
    def removeClient(self, ip):
        global clients
        for info in clients:
            if info[0] == ip:
                clients.remove(info)
                print("O cliente ", info ," foi removido!")
                return True
        return False

    # Insere um cliente
    def addClient(self, dest):
        global clients
        if not self.verifyClient(dest):
            # Insere o cliente
            clients.append(dest)
            print("Um novo cliente foi adicionado: ", dest)
            return True
        return False

    def run(self):
        self._stopped = False
        global clients
        global qtd_clients_connected
        global QTD_CLIENTS

        print("Thread de captura de dados dos clientes iniciada!")

        # Recebe o dado de um cliente
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
            tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            tcp.bind(('', self.port))
            tcp.listen(1)

            file_num = 0

            while not self._stopped:
                content, address = tcp.accept()
                received_msg = content.recvmsg(self.BUFFER_SIZE)
                message = str(received_msg[0], 'utf-8')
                
                print(message)
                
                # Conectar no canal
                if message[0:2] == "10":
                    # IP e Porta do cliente que fez a requisição
                    dest = (address[0], int(message[3:7]))

                    # IP e uma Porta padrão do cliente para comunicação
                    destResp = (address[0], 9091)
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
                        print("Listagem de IPs solicitada! Cliente: ", destResp)
                        tcp_cl.send(bytes(str(clients), encoding='utf-8'))
                        tcp_cl.close()
            
    def stop(self):
        self._stopped = True


# Classe que recebe os dados do canal - Servidor
class ServerReceptor(threading.Thread):
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

        self.producerVideo.start()
        self.send_video.start()
        self.player_video.start()
        self.garbage_collector.start()

        print("Thread de captura de dados iniciada (vídeos)!")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk_server:
            sk_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            sk_server.bind(('', 9091))
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
        global file_names_stored

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


# Classe que envia os pacotes de stream de video - Consumidor
class ClientSender(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.BUFFER_SIZE = 1024
        
    def run(self):
        self._stopped = False
        global queue_sender
        global file_names_stored
        global qtd_clients_connected

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
                        with open(file_name, 'rb') as up_file:
                            send_read = up_file.read(self.BUFFER_SIZE)
                            while send_read:
                                sk_client.send(send_read)
                                send_read = up_file.read(self.BUFFER_SIZE)
                                cont+=1
            
                time.sleep(random.random())

    def stop(self):
        self._stopped = True



# Classe que trabalha com o player vlc
class Player:
    
    #path = caminho dos arquivos. ex: '../videos/'
    def __init__(self, path):
        self.vlc_instance = vlc.Instance('--quiet')
        self.player = self.vlc_instance.media_player_new()
        self.path = path

    #file = nome do arquivo. ex: '_000040.mkv'
    def play(self, file):
        media = self.vlc_instance.media_new(self.path+file)
        self.player.set_media(media)
        self.player.play()
        #time.sleep(0.5)
        #duration = self.player.get_length() / 1000
        #time.sleep(duration-0.5)


# Classe que vai executar os videos no VLC - Consumidor
class PlayerAuto(threading.Thread, Player):
    def __init__(self):
        threading.Thread.__init__(self)
        Player.__init__(self, "./Movie/")
    
    """
    def remove_video(self, file_name):
        os.remove("./Movie/" + file_name)
    """
    
    def run(self):
        self._stopped = False

        print("Thread de execução de vídeos iniciada!")

        while not self._stopped:
            if not queue_video.empty():
                video_name = queue_video.get()
                
                Player.play(self, video_name)
                time.sleep(2)
                queue_video_remove.put(video_name)

                #self.remove_video(video_name)

    def stop(self):
        self._stopped = True


class GarbageCollector(threading.Thread, Player):
    def __init__(self):
        threading.Thread.__init__(self)

    def remove_video(self, file_name):
        os.remove("./Movie/" + file_name)

    def run(self):
        self.stopped = False

        print('Thread de remoção de videos iniciada!')

        while not self.stopped:
            if not queue_video_remove.empty():
                video_name = queue_video_remove.get()
                self.remove_video(video_name)
            time.sleep(random.random())
    
    def stop(self):
        self.stopped = True