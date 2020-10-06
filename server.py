import socket 
import select
import sys

from user import User

MAX_CLIENTS = 5

class CentralServer:

    # Inicialização do servidor com estruturas de manutenção de usuários
    def __init__(self,host,port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.users = dict() # username => User object
        self.chats = [] # array de usernames
        self.inputs = [sys.stdin]
        self.start_server()

    # Iniciando socket e ouvindo usuários
    def start_server(self):
        print("> [server::start_server] starting server")
        self.sock.bind((self.host,self.port))
        self.sock.listen(MAX_CLIENTS)
        self.sock.setblocking(False)
        self.inputs.append(self.sock)
        print("> [server::start_server] started server")

    # Rodando servidor e lidando com as conexões 
    def run(self):
        while True:
            read, write, execute = select.select(self.inputs,[],[])
            for command in read:
                if command == self.sock:

                    new_sock, addr = self.sock.accept()
                    login_message = str(new_sock.recv(1024),encoding='utf-8').split() # Pego a mensagem inicial de conexão
                    print('> [server::run] new user ' + login_message[1] + ' detected')

                    if login_message[0] == 'NEW': # Usuário novo no sistema
                        while login_message[1] in self.users.keys():
                            new_sock.send(bytes("USERNAME ALREADY EXISTS",encoding='utf-8'))
                            login_message = str(new_sock.recv(1024),encoding='utf-8').split()
                        new_sock.send(bytes("REGISTERED",encoding='utf-8'))
                        self.new_connection(login_message[1],new_sock)

                    elif login_message[0] == 'OLD': # Usuário retornando de um chat
                        print("> [server::run] user " + login_message[1] + " is returning")
                        self.returning_connection(login_message[1],new_sock)

                elif command == sys.stdin:
                    adm_command = input()
                    adm_command = adm_command.split()[0]
                    self.handle_admin_command(adm_command)

                else:
                    self.handle_request(command)
    
    # Lida com os comandos inseridos via standard input
    def handle_admin_command(self,adm_command):
        if adm_command == 'close':
            if not len(self.users.values()):
                self.sock.close()
                sys.exit()
            print("> [server::handle_admin_command] There are still users online")
        elif adm_command == 'chats_online':
            if len(self.chats):
                for chat in self.chats:
                    print("> [server::handle_admin_command.chats_online()] " + chat)
            else:
                print("> [server::handle_admin_command.chats_online()] There are no chats online")
        elif adm_command == 'users_online':
            for user in self.users.values():
                print("> [server::handle_admin_command.users_online()] " + user.username)

    # Lida com novos usuários entrando no servidor
    def new_connection(self,username,sock):
        print("> [server::new_connection] new connection detected")
        self.users[username] = User(username,sock)
        self.inputs.append(sock)
        sock.send(bytes(self.show_available_chats(),encoding='utf-8'))
        print("> [server::new_connection] new connection solved")

    # Lida com usuários reconectando de chats
    def returning_connection(self,username,sock):
        if username in self.chats:
            self.chats.remove(username)        
        self.users[username] = User(username,sock)
        self.inputs.append(sock)
        sock.send(bytes(self.show_available_chats(),encoding='utf-8'))

    # Gera a string com os chats existentes
    def show_available_chats(self):
        available_chats = "AVAILABLE CHATS:\n"
        for chat in self.chats:
            available_chats += chat + '\n'
        return available_chats

    # Emite a string de chats disponíveis para todos os usuários conectados no servidor central
    def emit_available_chats(self):
        available_chats = self.show_available_chats()
        for user in self.users.values():
            if user.username not in self.chats:
                user.sock.send(bytes(available_chats,encoding='utf-8'))

    # Lida com mensagens de socks conectados. Se não há mensagem, removemos dos inputs, mas se há, 
    # lidamos com ela usando execute_command
    def handle_request(self,sock):
        message = sock.recv(1024)
        if not message:
            self.inputs.remove(sock)
            sock.close()
        else:
            message = str(message, encoding='utf-8')
            message = message.split()
            self.execute_command(sock,message)

    # Dependendo da mensagem, essa função encaminha para a função responsável pela resolução do comando
    def execute_command(self,sock,message):
        if message[0] == 'create_chat':
            self.create_new_chat(sock)
        elif message[0] == 'connect':
            self.connect_to_chat(sock,message[1])
        elif message[0] == 'close':
            print("> [server::execute_command] conexão vai ser fechada")
            self.close_connection(sock,message[1])

    # Adiciona o usuário na lista de chats, passa para ele o par host port no qual ele hosteara seu chat 
    # e atualiza as estruturas de dados para que o servidor não espere conexões vindas do soquete dele
    def create_new_chat(self,sock):
        used_locations = [(self.host,self.port)]
        # Seleciono o usuário igualando via sock
        for user in self.users.values():
            if user.username in self.chats:
                used_locations.append(user.chat_info) # armazeno par de host e port já utilizado pelo sistema
            if user.sock == sock:
                request_user = user

        self.chats.append(request_user.username)
        chat_location = request_user.sock.getsockname()
        while chat_location in used_locations:
            chat_location = (chat_location[0], chat_location[1] + 1)
            if chat_location not in used_locations:
                used_locations.append(chat_location)
                break

        self.users[request_user.username].chat_info = chat_location
        sock.send(bytes(chat_location[0] + ' ' + str(chat_location[1]), encoding='utf-8'))
        self.emit_available_chats()

    # Envia a dupla host port do chat, se existir. Senão, envia DENIED
    def connect_to_chat(self,sock,username):
        if username in self.chats:
            target = self.users[username].chat_info
            sock.send(bytes(target[0] + ' ' + str(target[1]), encoding='utf-8'))
        else:
            sock.send(bytes('DENIED',encoding='utf-8'))

    # Remove o usuário das estruturas de dados
    def close_connection(self,sock,username):
        print("> [server::close_connection] " + username + " is logging out")
        sock.send(bytes("Goodbye",encoding='utf-8'))
        for uid in self.users.keys():
            if uid == username:
                self.users.pop(uid)
                break

if __name__ == '__main__':
    hostname = socket.gethostname()
    IP = socket.gethostbyname(hostname)
    print(hostname, IP)
    srv = CentralServer("127.0.0.1",10000)
    srv.run()
