import socket
import threading
import sys
from client import Receptor

# IP e porta do servidor
TCP_HOST    = 'localhost'  # IP
TCP_PORT    = 6060         #porta
BUFFER_SIZE = 1024 # Normally 1024
QTD_CLIENTS = 1
opt = ""

dest = (TCP_HOST, TCP_PORT)

msg = None

recep = Receptor()
# recep.daemon = True
QTD_CLIENTS = int(input("Digite o número de clientes máximo: "), 10)

while True:
    #Leitura da entrada de dados
    opt = ""
    print("Opções:\n"
          "1 - Para contatar o servidor\n"
          "2 - Para contatar o cliente")

    opt = input()

    if opt == "1":
        msg = input("Digite a mensagem enviada para o servidor (XXC): ")

    elif opt == "2":
        print("Opções:\n"
              "1 - Para listar conexões\n"
              "2 - Para listar arquivos")
        msg = input()

    #tcp.connect(dest)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp:

        tcp.connect(dest)
        tcp.send(bytes(msg, encoding='utf-8'))

        print("Mensagem Enviada: ", msg)

        # Sair do canal
        if msg[0:2] == '12':
            recep.stop()
            recep.join()
            recep = Receptor()


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

        # quantidade de clientes conectados
        if msg[0:2] == '13':
            print(str(tcp.recv(BUFFER_SIZE), 'utf-8'))

        tcp.shutdown(socket.SHUT_RDWR)
