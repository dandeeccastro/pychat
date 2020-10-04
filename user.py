import socket
import select 
import sys

HOST = "127.0.0.1"
PORT = 10000

def main():
    sock = socket.socket()
    sock.connect((HOST,PORT))

    chats = sock.recv(1024)
    print(str(chats, encoding='utf-8'))

    while True:
        command = input()
        handle_command(sock,command)

# Aqui a pessoa seta o username dela
def setup_connection(sock):
    print("TODO implement me")

def handle_command(sock,command):
    command = command.split()
    command_blob = bytes(' '.join(command),encoding='utf-8')

    if command[0] == "close":
        sock.close()
        sys.exit()

    elif command[0] == "connect":
        sock.send(command_blob)
        chat_id = sock.recv(1024)
        chat_id = str(chat_id,encoding='utf-8')
        print (chat_id)

    elif command[0] == "create_chat":
        sock.send(command_blob)

        chat_data = sock.recv(1024)
        chat_data = str(chat_data,encoding='utf-8')
        chat_data = tuple(chat_data.split(' '))
        chat_data = (chat_data[0], int(chat_data[1]))

        host_chat(sock,chat_data)

def host_chat(sock,chat_information):
    inputs = []
    users = []

    sock.close()
    sock = socket.socket()
    sock.bind(chat_information)
    sock.listen(5) #TODO remove magic number from logic
    sock.setblocking(False)
    
    inputs.append(sock)
    inputs.append(sys.stdin)

    while True:
        read,write,execute = select.select(inputs,[],[])
        for command in read:
            if command == sock:
                new_sock, addr = sock.accept()
                users.append(new_sock)
            elif command == sys.stdin:
                message = input()
                handle_chat_request(command,users,message)
            else:
                handle_chat_request(command,users)

def handle_chat_request(sock,users,message=None):

    if not message:
        message = sock.recv(1024)
        message = str(message, encoding='utf-8')

    if message[0] == '/':
        message = message.split()
        if message[0] == '/close':
            print("You can never leave...")

    else:
        # Isso não deve funcionar...
        for user in users:
            user.send(bytes(message, encoding='utf-8'))

    print("TODO implement me")
    
main()
