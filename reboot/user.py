import socket 
import select 
import sys 

from msi import MSI

class User:

    # Inicializa o User (se não tiver sock ele gera para uso no CLI, mas se ele receber sock é porque está sendo usado no CentralServer)
    def __init__(self,username=None,sock=None):
        self.username = username
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) if sock == None else sock
        self.chat_info = None

    # Conecta o usuário no CentralServer e mantém o loop de conexão (input() é a chamada bloqueante)
    def connect_to_central_server(self,host,port):
        self.sock.connect((host,port))
        self.register_username()
        while True:
            command = input()
            self.handle_command(command)
    
    def register_username(self):
        response = "USERNAME ALREADY EXISTS"
        while response != "REGISTERED":
            username = input("Insira seu username: ") 
            self.sock.send(bytes('NEW ' + username,encoding='utf-8'))
            response = str(self.sock.recv(1024),encoding='utf-8')
            print(response)
        self.username = username
        self.get_available_chats()

    def reconnect_to_central_server(self):
        self.sock.send(bytes('OLD ' + self.username,encoding='utf-8'))
        self.get_available_chats()

    # Pega e printa os chats disponíveis no CentralServer
    def get_available_chats(self):
        chats = self.sock.recv(1024)
        print(str(chats,encoding='utf-8'))

    # Lida com comandos enviados para o CentralServer
    def handle_command(self,command):
        command = command.split()
        command_blob = bytes(' '.join(command),encoding='utf-8')

        if command[0] == "close":
            self.sock.send(bytes(command[0] + ' ' + self.username,encoding='utf-8'))
            self.sock.close()
            sys.exit()

        elif command[0] == "connect":
            chat_id = self.get_chat_id(command_blob)
            if chat_id != 'DENIED':
                inputs = self.connect_to_chat(chat_id)
                self.handle_chat_messaging(inputs)
                self.return_to_server()

        elif command[0] == "create_chat":
            inputs, users = self.generate_host_chat_info(command_blob)
            self.host_chat(inputs, users)
            self.return_to_server()

    # Envia comando de conectar para o server e recebe 
    # informações do chat que você quer se conectar
    def get_chat_id(self,command_blob):
        self.sock.send(command_blob)
        chat_id = self.sock.recv(1024)
        chat_id = str(chat_id,encoding='utf-8')
        return chat_id

    # Abre o novo socket, conecta com o chat_info e lida com as mensagens
    # a serem enviadas e recebidas
    def connect_to_chat(self, chat_info):
        chat_info = tuple(chat_info.split(' '))
        chat_info = (chat_info[0],int(chat_info[1]))

        self.sock.close()
        self.sock = socket.socket()
        self.sock.connect(chat_info)
        self.sock.setblocking(False)
        self.sock.send(bytes('('+self.username+' has checked in)',encoding='utf-8'))

        inputs = [sys.stdin, self.sock]
        return inputs 

    def handle_chat_messaging(self,inputs):
        while True:
            read, write, execute = select.select(inputs,[],[])
            closed_connection = 0

            for command in read:
                if command == self.sock:
                    message = self.sock.recv(1024)
                    if not message:
                        inputs.remove(command)
                    else:
                        message = str(message, encoding='utf-8')
                        print(message)
                elif command == sys.stdin:
                    message = input()
                    if message[0] != '/':
                        self.send_message(message)
                    else:
                        closed_connection = self.execute_client_side_command(message.split())

            if closed_connection:
                return None

    def send_message(self,message):
        message = '(' + self.username + ') ' + message
        self.sock.send(bytes(message, encoding='utf-8'))

    def execute_client_side_command(self,message):
        if message[0] == '/close' or message[0] == '/quit':
            message = '(' + self.username + ' checked out for today)'
            self.sock.send(bytes(message, encoding='utf-8'))
            self.sock.close()
            return 1
        return 0
    
    def generate_host_chat_info(self,command_blob):
        self.sock.send(command_blob)

        chat_data = self.sock.recv(1024)
        chat_data = str(chat_data,encoding='utf-8')
        chat_data = tuple(chat_data.split(' '))
        chat_data = (chat_data[0], int(chat_data[1]))
        self.chat_info = chat_data
        inputs, users = self.configure_chat_hosting()

        return inputs, users

    def configure_chat_hosting(self):
        self.sock.close()
        self.sock = socket.socket()
        # print("> [user] " + str(self.chat_info))
        self.sock.bind(self.chat_info)
        self.sock.listen(5) #TODO remove magic number from logic
        self.sock.setblocking(False)
        
        inputs = [self.sock, sys.stdin]
        users = []

        return inputs, users

    def host_chat(self,inputs,users):
        while True:
            read,write,execute = select.select(inputs,[],[])
            chat_offline = 0
            for command in read:
                if command == self.sock:
                    new_sock, addr = self.sock.accept()
                    users.append(new_sock)
                    inputs.append(new_sock)

                elif command == sys.stdin:
                    message = input()
                    if message[0] != '/':
                        message = '(' + self.username + ') ' + message
                        self.broadcast_message(users,self.sock,message)
                    else:
                        users, inputs, chat_offline = self.execute_host_side_command(users,inputs,message.split())
                else:
                    users, inputs, chat_offline = self.handle_incoming_message(users,inputs,command)

            if chat_offline:
                return None

    def handle_incoming_message(self,users,inputs,sock):
        message = sock.recv(1024)
        # Usuário está desconectado
        if not message:
            print("> [user] Message was null ")
            users.remove(sock)
            inputs.remove(sock)
            return users, inputs, 0
        # Printa mensagem para si mesmo e broadcasta para os outros
        else:
            message = str(message,encoding='utf-8') 
            print(message)
            self.broadcast_message(users,sock,message)
            return users, inputs, 0

    def broadcast_message(self,users,sock,message):
        for user in users:
            if user is not sock:
                user.send(bytes(message, encoding='utf-8')) 

    def execute_host_side_command(self,users,inputs,message):
        if message[0] == '/close' or message[0] == '/quit':
            if not len(users):
                return users, inputs, 1
            print("> [user] There are still people online")
            return users, inputs, 0
        return users, inputs, 0

    def return_to_server(self):
        self.sock.close()
        self.sock = socket.socket()
        self.sock.connect(("127.0.0.1",10000))
        self.reconnect_to_central_server()

if __name__ == '__main__':
    user = User()
    user.connect_to_central_server("127.0.0.1",10000)
