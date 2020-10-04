import socket 
import select
import sys

from user import User

MAX_CLIENTS = 5

class CentralServer:

    def __init__(self,host,port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.users = dict() # username => User object
        self.chats = [] # array de usernames
        self.inputs = [sys.stdin]
        self.start_server()

    def start_server(self):
        print("> [server] starting server")
        self.sock.bind((self.host,self.port))
        self.sock.listen(MAX_CLIENTS)
        self.sock.setblocking(False)
        self.inputs.append(self.sock)
        print("> [server] started server")

    def run(self):
        while True:
            read, write, execute = select.select(self.inputs,[],[])
            for command in read:
                if command == self.sock:
                    new_sock, addr = self.sock.accept()
                    raw_username = new_sock.recv(1024)
                    username = str(raw_username,encoding='utf-8').split()
                    print('> [server] ' + username[1])

                    if username[0] == 'NEW':
                        while username[1] in self.users.keys():
                            new_sock.send(bytes("USERNAME ALREADY EXISTS",encoding='utf-8'))
                            raw_username = new_sock.recv(1024)
                            username = str(raw_username,encoding='utf-8').split()
                        new_sock.send(bytes("REGISTERED",encoding='utf-8'))
                        self.new_connection(username[1],new_sock)
                    elif username[0] == 'OLD':
                        self.returning_connection(username[1],new_sock)

                elif command == sys.stdin:
                    adm_command = input()
                    adm_command = adm_command.split()[0]
                    self.handle_admin_command(adm_command)
                else:
                    self.handle_request(command)
    
    def handle_admin_command(self,adm_command):
        # TODO: esperar por finalização das conexões
        if adm_command == 'close':
            if not len(self.users.values()):
                self.sock.close()
                sys.exit()
            print("> [server] There are still users online")
        elif adm_command == 'chats_online':
            if len(self.chats):
                for chat in self.chats:
                    print("> [server] " + chat)
            else:
                print("> [server] There are no chats online")
        elif adm_command == 'users_online':
            for user in self.users.keys():
                print(user)

    def new_connection(self,username,sock):
        print("> [server] new connection detected")
        self.users[username] = User(username,sock)
        self.inputs.append(sock)
        sock.send(bytes(self.show_available_chats(),encoding='utf-8'))
        print("> [server] new connection solved")

    def returning_connection(self,username,sock):
        if username in self.chats:
            self.chats.remove(username)        
        self.users[username] = User(username,sock)
        sock.send(bytes(self.show_available_chats(),encoding='utf-8'))

    def show_available_chats(self):
        available_chats = "AVAILABLE CHATS:\n"
        for chat in self.chats:
            available_chats += chat + '\n'
        return available_chats
    
    def handle_request(self,sock):
        message = sock.recv(1024)
        if not message:
            self.inputs.remove(sock)
            sock.close()
        else:
            message = str(message, encoding='utf-8')
            message = message.split()
            self.execute_command(sock,message)

    def execute_command(self,sock,message):
        if message[0] == 'create_chat':
            self.create_new_chat(sock)
        elif message[0] == 'connect':
            self.connect_to_chat(sock,message[1])
        elif message[0] == 'template':
            print("TODO implement me")
        elif message[0] == 'close':
            self.close_connection(message[1])

    def create_new_chat(self,sock):
        used_locations = [(self.host,self.port)]
        print("> [server] " + str(used_locations))
        # Seleciono o usuário igualando via sock
        for user in self.users.values():
            # armazeno par de host e port já utilizado pelo sistema
            used_locations.append(user.chat_info)
            if user.sock == sock:
                request_user = user

        # Se o cara já não é um chat, transformo ele em um
        if request_user.username not in self.chats:
            print("> [server] " + request_user.username + " should be in chats")
            self.chats.append(request_user.username)
            print("> [server] " + str(self.chats))
            chat_location = request_user.sock.getsockname()
            if chat_location == (self.host,self.port):
                chat_location = (chat_location[0], chat_location[1] + 1)
            while chat_location not in used_locations:
                if chat_location not in used_locations:
                    used_locations.append(chat_location)
                    break
                chat_location = (chat_location[0], chat_location[1] + 1)

        self.users[request_user.username].chat_info = chat_location
        sock.send(bytes(chat_location[0] + ' ' + str(chat_location[1]), encoding='utf-8'))

    def connect_to_chat(self,sock,username):
        if username in self.chats:
            target = self.users[username].chat_info
            print("> [server] " + username)
            sock.send(bytes(target[0] + ' ' + str(target[1]), encoding='utf-8'))
        else:
            sock.send(bytes('DENIED',encoding='utf-8'))

    def close_connection(self,username):
        for uid in self.users.keys():
            if uid == username:
                del self.users[uid]
                break

if __name__ == '__main__':
    hostname = socket.gethostname()
    IP = socket.gethostbyname(hostname)
    print(hostname, IP)
    srv = CentralServer("127.0.0.1",10000)
    srv.run()
