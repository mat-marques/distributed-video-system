import socket

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

# Thread que vai receber os vídeos do servidor
recep_server = ServerReceptor(BUFFER_SIZE)

# Thread que vai receber os vídeos do cliente
recep_client = ClientReceptor(BUFFER_SIZE)

# Leitura da quantidade de clientes que podem se conectar neste cliente
QTD_CLIENTS = int(input("Digite o número de clientes máximo: "), 10)

#Thread para receber mensagens dos clientes
#CLIENT_PORT = int(input("Digite o número da porta de acesso para os clientes poderem se comunicar: "), 10)
#thread_client_reseiver = ClientReseiver(CLIENT_PORT)

# Thread que monitora mensagens de possíveis clientes
thread_client_reseiver = ClientReseiver(BUFFER_SIZE)
thread_client_reseiver.start()

while True:
    print("\n\n\n##################################################")
    print("Opções para estabelecimento de conexão:")
    print("Digite 1 para se conectar em um servidor;")
    print("Digite 2 para se conectar em um cliente;")
    print("Digite 0 para sair da aplicação;")

    CONNECTION = input()
    print("\n")
    # Define a tupla com o ip e porta do servidor
    if CONNECTION == "1":
        TCP_HOST = input("Digite o IP do servidor: ")
        dest = (TCP_HOST, TCP_PORT)
    
    # Define a tupla com o ip e porta do cliente
    elif CONNECTION == "2":
        TCP_HOST = input("Digite o IP do cliente: ")
        #CLIENT_PORT = input("Digite o número da porta do cliente: ")
        dest = (TCP_HOST, CLIENT_CLIENT_PORT_M)

    elif CONNECTION == "0":
        print("Aplicação finalizada!")
        break
    else:
        print("Opção incorreta! Tente novamente")
        continue

    # Comunicação com o servidor
    if CONNECTION == "1":
        while True:
            print("\n\n\n##################################################")
            print("- Para entrar em uma canal XXC, XX=10 e C = um número de 0 a 9;")
            print("- Para listar os cliente de um canal XXC, XX=11 e C = um número de 0 a 9;")
            print("- Para sair de um canal XXC, XX=12 e C = um número de 0 a 9;")
            print("- Para verificar o número de cliente de um canal XXC, XX=13 e C = um número de 0 a 9;")
            print("- Digite 0 para finalizar a aplicação;")
            msg = input("Digite a mensagem que será enviada ao servidor (XXC, sem espaço): ")

            # Finaliza a aplicação
            if msg[0:1] == '0':
                if recep_server._stopped:
                    recep_server.stop()
                    recep_server.join()
                break
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:

                tcp.connect(dest)

                print("Enviado:", msg)

                # Sair do canal
                if msg[0:2] == '12':
                    recep_server.stop()
                    recep_server.join()
                    recep_server = ServerReceptor(BUFFER_SIZE)
                    
                tcp.send(bytes(msg, encoding='utf-8'))

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
                    elif not recep_server.is_alive():
                        recep_server.start()

                # lista de clientes conectados
                if msg[0:2] == '11':
                    print(str(tcp.recv(BUFFER_SIZE), 'utf-8'))

                # quantidade de clientes conectados
                if msg[0:2] == '13':
                    print(str(tcp.recv(BUFFER_SIZE), 'utf-8'))

                tcp.shutdown(socket.SHUT_RDWR)

    # Comunicação com o cliente
    elif CONNECTION == "2":
        is_connected = False
        while True:

            # Se conecta no cliente
            if not is_connected:
                #tcp.connect(dest)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
                    print(dest)
                    tcp.connect(dest)
                    tcp.send(bytes("10", encoding='utf-8'))

                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_cl:
                        tcp_cl.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                        tcp_cl.bind(('', CLIENT_CLIENT_PORT_S))
                        tcp_cl.listen(1)
                        content, address = tcp_cl.accept()
                        received_msg = content.recvmsg(BUFFER_SIZE)
                        message = str(received_msg[0], 'utf-8')

                        print(message)

                        if message == "00":
                            print("Limite de clientes excedido!")
                            break

                        elif message == "01":
                            print("Operação realizada com sucesso!")
                            is_connected = True

                            if not recep_client.is_alive():
                                recep_client.start()

                            break

                        content.close()

                        tcp_cl.close()
                        
                    tcp.close()
            
        while is_connected:
            print("\n\n\n##################################################")
            print("Opções:")
            print("1 - Para listar conexões")
            print("2 - Para listar arquivos")
            print("0 - Finalizar aplicação")
            msg = input()
            
            if msg == "1":
                #tcp.connect(dest)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
                    tcp.connect(dest)
                    tcp.send(bytes("11", encoding='utf-8'))

                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_cl:
                        tcp_cl.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                        tcp_cl.bind(('', CLIENT_CLIENT_PORT_S))
                        tcp_cl.listen(1)
                        content, address = tcp_cl.accept()
                        received_msg = content.recvmsg(BUFFER_SIZE)
                        message = str(received_msg[0], 'utf-8')

                        print(message)

                        tcp_cl.shutdown(socket.SHUT_RDWR)

                    tcp.shutdown(socket.SHUT_RDWR)

            if msg == "2":
                print(list(file_names_stored.queue))

            if msg == "0":
                print("Aplicação encerrada!")
                recep_client.stop()
                recep_client.join()
                break