import socket
import ast

from Client import *

# IP e porta do servidor
TCP_HOST    = 'localhost'  # IP
TCP_PORT    = 6060         #porta
BUFFER_SIZE = 1024 # Normally 1024
opt = ""

# 1 para servidor e 2 para cliente
CONNECTION = 1
msg = None
CLIENT_CONNECTED = None
CANAL = 0

# Thread que vai receber os vídeos do servidor
recep_server = ServerReceptor(BUFFER_SIZE)

# Thread que vai receber os vídeos do cliente
recep_client = ClientReceptor(BUFFER_SIZE)

list_clients = []

# Leitura da quantidade de clientes que podem se conectar neste cliente
QTD_CLIENTS = int(input("Digite o número de clientes máximo: "), 10)

#Thread para receber mensagens dos clientes
#CLIENT_PORT = int(input("Digite o número da porta de acesso para os clientes poderem se comunicar: "), 10)
#thread_client_reseiver = ClientReseiver(CLIENT_PORT)

# Thread que monitora mensagens de possíveis clientes
thread_client_reseiver = ClientReseiver(BUFFER_SIZE)
thread_client_reseiver.start()

# Leitura do IP do servidor
TCP_HOST = input("Digite o IP do servidor: ")

# Define a tupla com o ip e porta do servidor
dest = (TCP_HOST, TCP_PORT)

# Leitura do canal
CANAL = input("Digite o canal desejado: ")

def convertStringList(list_cl):
    list_c = ast.literal_eval(list_cl)
    return list_c

connected = False

print("Iniciando a conexão com o servidor!")

msg = str("10")

while True:
    # Comunicação com o servidor
    if msg != "0":
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
            tcp.connect(dest)
                
            tcp.send(bytes(msg+CANAL, encoding='utf-8'))

            # Entrou em um canal
            if msg[0:2] == '10':

                # Recebe a mensagem de resposta
                #   "10" -> conectcou
                #   "00" -> nao conectou
                message = ""
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk_server:
                    sk_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                    sk_server.bind(('', CLIENT_SERVER_PORT))
                    sk_server.listen(1)

                    content, address = sk_server.accept()

                    received_msg = content.recvmsg(BUFFER_SIZE)
                    message = str(received_msg[0], 'utf-8')

                    if message == "00":
                        print("Limite de canais conectados excedidos.")
                        msg = "11"
                        continue
                    elif not recep_server.is_alive():
                        recep_server.start()
                        msg = "0"
                        connected = True 
                        continue

            # lista de clientes conectados
            if msg[0:2] == '11':
                list_cl = str(tcp.recv(BUFFER_SIZE), 'utf-8')
                print(list_cl)
                list_clients = convertStringList(list_cl)
                msg = "0"

            tcp.close()
    
    if msg != "0":
        continue

    print("Estalecendo conexão com um dos possíveis clientes ...")
    msg = "10"
    #Tenta se comunicar com um dos clientes. Se conecta no cliente que aceitar primeiro a conexão.
    if not connected:
        for cl in list_clients:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
                print("Estabelecendo conexão com o cliente: ", cl, " ...")
                tcp.connect((cl, CLIENT_CLIENT_PORT_M))
                print("Conexão estabelecida.")

                print("Enviando solicitação de entrada no canal do cliente ...")
                tcp.send(bytes(msg, encoding='utf-8'))
                print("Mensagem enviada.")
                
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk_server:
                    sk_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                    sk_server.bind(('', CLIENT_CLIENT_PORT_S))
                    sk_server.listen(1)
                    
                    print("Aguardando resposta do cliente ...")
                    content, address = sk_server.accept()

                    received_msg = content.recvmsg(BUFFER_SIZE)
                    message = str(received_msg[0], 'utf-8')
                    print("Resposta recebida.")

                    if message == "00":
                        print("Limite de clientes conectados excedidos.")
                        print("Solicitação rejeitada!")
                    elif not recep_client.is_alive():
                        print("Solicitação de entrada no canal aceita.")
                        recep_client.start()
                        connected = True
                    
                    sk_server.close()
                tcp.close()
    
    msg = ""
    if connected:
        while True:
            print("- Digite L para listar os nomes dos arquivos de vídeos.")
            print("- Digite E para fechar a aplicação.")
            msg = input("Opção: ")

            if msg == "E":
                print("Iniciando processo de fechamento da aplicação")
                recep_client.stop()
                recep_server.stop()
                thread_client_reseiver.stop()
                break
            
            if msg == "L":
                print(list(file_names_stored.queue))

        if msg == "E":
            if recep_client.is_alive:
                recep_client.join()

            if recep_server.is_alive:
                recep_server.join()
            
            print("Aplicação finalizada!")
            break
    else:
        print("Não foi possível se conectar no canal solicitado!")
        print("Tanto Cliente quanto Servidor estão lotados!")
        print("Tente novamente mais tarde!")
        print("Aplicação encerrada!")
        break