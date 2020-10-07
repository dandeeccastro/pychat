import socket 
import select
import sys

from user import User
from messager import Messager

MAX_CLIENTS = 5

class CentralServer:

    # Inicialização do servidor com estruturas de manutenção de usuários
    def __init__(self,host,port):
        self.host = host
        self.port = port
        self.messager = Messager()
        self.users = dict() # username => User object
        self.chats = [] # array de usernames
        self.messagers = []
        self.inputs = [sys.stdin]
        self.start_server()

    # Iniciando socket e ouvindo usuários
    def start_server(self):
        print("> [server::start_server] starting server")
        self.messager.host_connection(self.host,self.port,5)
        self.messager.set_blocking_connections(False)
        self.inputs.append(self.messager.get_sock())
        print("> [server::start_server] started server")

    # Rodando servidor e lidando com as conexões 
    def run(self):
        while True:
            read, write, execute = select.select(self.inputs,[],[])
            for command in read:
                if command == self.messager.get_sock():

                    new_messager = self.messager.accept()
                    login_message = new_messager.receive()
                    login_message = login_message.split()
                    print('> [server::run] new user ' + login_message[1] + ' detected')

                    if login_message[0] == 'NEW': # Usuário novo no sistema
                        while login_message[1] in self.users.keys():
                            login_message = new_messager.send_and_receive("USERNAME ALREADY EXISTS")
                            login_message = login_message.split()
                        new_messager.send("REGISTERED")

                        self.new_connection(login_message[1],new_messager) 

                    elif login_message[0] == 'OLD': # Usuário retornando de um chat
                        print("> [server::run] user " + login_message[1] + " is returning")
                        self.returning_connection(login_message[1],new_messager)

                    self.update_messagers()

                elif command == sys.stdin:
                    adm_command = input()
                    adm_command = adm_command.split()[0]
                    self.handle_admin_command(adm_command)

                else:
                    self.handle_request(self.get_messager_by_sock(command))
    
    def update_messagers(self):
        self.messagers = [user.messager for user in self.users.values()]

    def get_messager_by_sock(self,sock):
        for user in self.users.values():
            if user.messager.sock == sock:
                return user.messager

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
    def new_connection(self,username,messager):
        print("> [server::new_connection] new connection detected")
        self.users[username] = User(username,messager)
        self.inputs.append(messager.get_sock())
        # messager.send(bytes(self.show_available_chats(),encoding='utf-8'))
        print("> [server::new_connection] new connection solved")

    # Lida com usuários reconectando de chats
    def returning_connection(self,username,messager):
        if username in self.chats:
            self.chats.remove(username)        
        self.users[username] = User(username,messager)
        self.inputs.append(messager.get_sock())
        messager.send(self.show_available_chats())

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
    def handle_request(self,messager):
        message = messager.receive()
        if not message:
            self.inputs.remove(messager.get_sock())
            messager.close()
        else:
            message = message.split()
            self.execute_command(messager,message)

    # Dependendo da mensagem, essa função encaminha para a função responsável pela resolução do comando
    def execute_command(self,messager,message):
        if message[0] == 'create_chat':
            self.create_new_chat(messager)
        elif message[0] == 'connect':
            self.connect_to_chat(messager,message[1])
        elif message[0] == 'close':
            print("> [server::execute_command] conexão vai ser fechada")
            self.close_connection(messager,message[1])

    # Adiciona o usuário na lista de chats, passa para ele o par host port no qual ele hosteara seu chat 
    # e atualiza as estruturas de dados para que o servidor não espere conexões vindas do soquete dele
    def create_new_chat(self,messager):
        used_locations = [(self.host,self.port)]
        # Seleciono o usuário igualando via sock
        for user in self.users.values():
            if user.username in self.chats:
                used_locations.append(user.chat_info) # armazeno par de host e port já utilizado pelo sistema
            if user.messager == messager:
                request_user = user

        self.chats.append(request_user.username)
        chat_location = request_user.messager.get_pair_host_port()
        while chat_location in used_locations:
            chat_location = (chat_location[0], chat_location[1] + 1)
            if chat_location not in used_locations:
                used_locations.append(chat_location)
                break

        self.users[request_user.username].chat_info = chat_location
        messager.send(chat_location[0] + ' ' + str(chat_location[1]))

        self.messager.emit_message(self.show_available_chats(),[user.messager for user in self.users.values()])

    # Envia a dupla host port do chat, se existir. Senão, envia DENIED
    def connect_to_chat(self,messager,username):
        if username in self.chats:
            target = self.users[username].chat_info
            messager.send(target[0] + ' ' + str(target[1]))
        else:
            messager.send('DENIED')

    # Remove o usuário das estruturas de dados
    def close_connection(self,messager,username):
        print("> [server::close_connection] " + username + " is logging out")
        messager.send("Goodbye")
        for uid in self.users.keys():
            if uid == username:
                self.users.pop(uid)
                self.update_messagers()
                break

if __name__ == '__main__':
    hostname = socket.gethostname()
    IP = socket.gethostbyname(hostname)
    print(hostname, IP)
    srv = CentralServer("127.0.0.1",10000)
    srv.run()
