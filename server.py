import socket 
import select
import multiprocessing
import sys

HOST = "127.0.0.1"
PORT = 10000
MAX_CLIENTS = 5

inputs = [sys.stdin]
users = dict()
chats = dict() # contém tuples de host e port dos chats disponíveis

def main():

    sock = start_server(HOST, PORT)
    clients = []

    while True:
        read, write, execute = select.select(inputs,[],[])
        for command in read:

            if command == sock:
                print("[DEBUG] New connection detected")
                new_sock, addr = new_connection(command)
                inputs.append(new_sock)
                new_sock.send(bytes(show_available_chats(addr),encoding='utf-8'))
                
            elif command == sys.stdin:
                print("[DEBUG] admin command detected")
                adm_command = input()

                if adm_command == "close":
                    for c in clients:
                        c.join()
                    sock.close()
                    sys.exit()
                    
                elif adm_command == 'chats_online':
                    for chat in chats:
                        print(chats[chat])

            else:
                print("[DEBUG] new connection command detected")
                handle_request(command,users[command])

def start_server(host, port):
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock.bind((host,port))
    sock.listen(MAX_CLIENTS)
    sock.setblocking(False)
    inputs.append(sock)
    return sock

def new_connection(sock):
    new_sock, addr = sock.accept()
    users[new_sock] = addr
    return new_sock, addr

# Aqui a pessoa seta o username dela
def setup_connection(sock):
    print("TODO implement me")

def handle_request(sock, addr):
    print("[DEBUG] request function called")
    message = sock.recv(1024)
    if not message:
        inputs.remove(sock)
        sock.close()
    else:
        print("[DEBUG] message received and being processed")
        message = str(message, encoding='utf-8')
        message = message.split()
        execute_command(sock, message)

def show_available_chats(addr):
    available_chats = "AVAILABLE CHATS:\n"
    for chat in chats:
        available_chats += str(chats[chat][0] + ' ' + str(chats[chat][1]) + '\n')
    return available_chats
#    addr.send(bytes(available_chats,encoding='utf-8'))

def execute_command(sock,message):
    print("[DEBUG] Command is being executed")
    # Usuário que roda o comando vira um dono de chat
    if message[0] == "create_chat":
        create_new_chat(sock,users[sock])
    # Usuário se conecta ao chat que está disponível
    elif message[0] == "connect":
        print("TODO implement me")

    elif message[0] == "template":
        print("TODO implement me")

def create_new_chat(sock,addr):
    # Se o usuário tem um tuple diferente, eu insiro ele
    addr_id = addr[1]
    is_server = sock.getsockname() == (HOST,PORT)

    if sock.getsockname() not in chats.values() and not is_server:
        print("[DEBUG] Chat w new IP being created")
        chat_data = sock.getsockname()
        chats[addr_id] = chat_data

    # Se não tiver, usamos um port diferente e adicionamos
    else:
        print("[DEBUG] Chat w new port being created")
        chat_data = sock.getsockname()
        while addr_id not in chats.keys():
            chat_data = (chat_data[0],chat_data[1] + 1)
            print(chat_data)
            is_server = chat_data == (HOST,PORT)
            if not chat_data in chats.values() and not is_server:
                chats[addr_id] = chat_data

    # No final, retornamos o tuple para ele poder mudar suas configs e virar um servidor
    sock.send(bytes(chat_data[0] + ' ' + str(chat_data[1]), encoding='utf-8'))

main()
