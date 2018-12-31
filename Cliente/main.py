import socket
import threading
import sys
from receptor import Receptor

# IP e porta do servidor
TCP_HOST    = 'localhost'  # IP
TCP_PORT    = 6060         #porta
BUFFER_SIZE = 1024 # Normally 1024
QTD_CLIENTS = 1
opt = ""

# 1 para servidor e 2 para cliente
CONNECTION = 1

#dest = (TCP_HOST, TCP_PORT)

msg = None
CLIENT_CONNECTED = None

recep = Receptor(BUFFER_SIZE)
# recep.daemon = True
# Leitura da quantidade de clientes que podem se conectar neste cliente
QTD_CLIENTS = int(input("Digite o número de clientes máximo: "), 10)

CLIENT_CONNECTED = [QTD_CLIENTS]

while True:
    print("Opções para estabelecimento de conexão:")
    print("Digite 1 para se conectar em um servidor")
    print("Digite 2 para se conectar em um cliente")

    CONNECTION = input()

    if CONNECTION == "1":
        TCP_HOST = input("Digite o IP do servidor: ")
        dest = (TCP_HOST, TCP_PORT)
        break
    elif CONNECTION == "2":
        TCP_HOST = input("Digite o IP do cliente: ")
        TCP_PORT = input("Digite a porta de acesso para o cliente: ")
        dest = (TCP_HOST, TCP_PORT)
        break
    else:
        print("Opção incorreta! Tente novamente")


if CONNECTION == "1":
    while True:
        print("Para entar em uma canal XXC, XX=10 e C = um número de 0 a 9;")
        print("Para listar os cliente de um canal XXC, XX=11 e C = um número de 0 a 9;")
        print("Para sair de um canal XXC, XX=12 e C = um número de 0 a 9;")
        print("Para verificar o número de cliente de um canal XXC, XX=13 e C = um número de 0 a 9;")
        print("Digite 0 para finalizar a aplicação;")
        msg = input("Digite a mensagem que será enviada ao servidor (XXC, sem espaço): ")

        # Finaliza a aplicação
        if msg[0:1] == '0':
            break

        #tcp.connect(dest)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:

            tcp.connect(dest)
            tcp.send(bytes(msg, encoding='utf-8'))

            print("Mensagem Enviada: ", msg)

            # Entrou em um canal
            if msg[0:2] == '10':

                # Recebe a mensagem de resposta
                #   "10" -> conectou
                #   "00" -> nao conectou
                message = ""
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sk_server:
                    sk_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                    sk_server.bind(('', 9091))
                    sk_server.listen(1)

                    content, address = sk_server.accept()

                    received_msg = content.recvmsg(BUFFER_SIZE)
                    message = str(received_msg[0], 'utf-8')

                if message == "00":
                    print("Limite de canais conectados excedidos.")
                elif not recep.is_alive():
                    recep.start()

            # lista de clientes conectados
            if msg[0:2] == '11':
                print(str(tcp.recv(BUFFER_SIZE), 'utf-8'))

            # Sair do canal
            if msg[0:2] == '12':
                recep.stop()
                recep.join()
                recep = Receptor(BUFFER_SIZE)
                
            # quantidade de clientes conectados
            if msg[0:2] == '13':
                print(str(tcp.recv(BUFFER_SIZE), 'utf-8'))

            tcp.shutdown(socket.SHUT_RDWR)

elif CONNECTION == "2":
    while True:
        #tcp.connect(dest)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:
            tcp.connect(dest)
            tcp.send(bytes("10 " + TCP_PORT, encoding='utf-8'))

            if str(tcp.recv(BUFFER_SIZE), 'utf-8') == "00":
                print("Ocorreu um erro na operação  de inserção do cliente no canal!")
                break

            elif str(tcp.recv(BUFFER_SIZE), 'utf-8') == "01":
                print("Operação realizada com sucesso!")
                
            tcp.shutdown(socket.SHUT_RDWR)

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

                if str(tcp.recv(BUFFER_SIZE), 'utf-8') == "00":
                    print("Ocorreu um erro na operação!")

                elif str(tcp.recv(BUFFER_SIZE), 'utf-8') == "01":
                    print("Operação realizada com sucesso!")

                tcp.shutdown(socket.SHUT_RDWR)

        if msg == "2":
            print("Lista os arquivos ...")

        if msg == "0":
            print("Aplicação encerrada!")
            break







