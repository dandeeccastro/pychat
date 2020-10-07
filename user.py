import socket 
import select 
import sys 

from messager import Messager

class User:

    # Inicializa o User (se não tiver sock ele gera para uso no CLI, mas se ele receber sock 
    # é porque está sendo usado no CentralServer)
    def __init__(self,username=None,messager=None):
        self.username = username
        self.chat_info = None
        self.messager = Messager() if messager == None else messager

    # Conecta o usuário no CentralServer e mantém o loop de conexão (input() é a chamada bloqueante)
    def connect_to_central_server(self,host,port):
        self.messager.connect(host,port)
        self.register_username()

        while True:
            inputs = [sys.stdin, self.messager.get_sock()]
            read, write, execute = select.select(inputs,[],[])
            for command in read:
                if command == sys.stdin:
                    message = input()
                    self.handle_command(message)
                elif command == self.messager.sock:
                    server_message = self.messager.receive()
                    print(server_message)
    
    # Mantém o usuário escolhendo o username dele até que seja um que não 
    # exista no servidor central em questão 
    def register_username(self):
        response = "USERNAME ALREADY EXISTS"
        while response != "REGISTERED":
            username = input("Insira seu username: ") 
            response = self.messager.send_and_receive('NEW ' + username)
            print(response)
        self.username = username

    # Reconecta o usuário, enviando a mensagem de retorno dele 
    # "OLD <username>" e pegando os chats disponíveis
    def reconnect_to_central_server(self):
        chats = self.messager.send_and_receive('OLD ' + self.username)
        print(chats)

    # Lida com comandos enviados para o CentralServer
    def handle_command(self,command):
        command = command.split()
        full_command = ' '.join(command)

        if command[0] == "close":
            print("> [user::handle_command] sending close command")
            self.messager.send_and_receive(command[0] + ' ' + self.username)
            self.messager.close()
            sys.exit()

        elif command[0] == "connect":
            chat_id = self.messager.send_and_receive(full_command)
            if chat_id != 'DENIED':
                inputs = self.connect_to_chat(chat_id)
                self.handle_chat_messaging(inputs)
                self.return_to_server()

        elif command[0] == "create_chat":
            inputs, users = self.generate_host_chat_info(full_command)
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

        self.messager.reconnect(chat_info[0],chat_info[1])
        self.messager.set_blocking_connections(False)
        self.messager.send('('+self.username+' has checked in)')

        inputs = [sys.stdin, self.messager.get_sock()]
        return inputs 

    # Lida com o loop para mensagens, recebendo elas com sockets e enviando as inseridas via stdin.
    # Quando a mensagem é enviada com um / antes, é interpretada como comando
    def handle_chat_messaging(self,inputs):
        while True:
            read, write, execute = select.select(inputs,[],[])
            closed_connection = 0

            for command in read:
                if command == self.messager.get_sock():
                    message = self.messager.receive()
                    if not message:
                        inputs.remove(command)
                    else:
                        print(message)
                elif command == sys.stdin:
                    message = input()
                    if message[0] != '/':
                        self.messager.send('(' + self.username + ') ' + message)
                    else:
                        closed_connection = self.execute_client_side_command(message.split())

            if closed_connection:
                return None

    # Quando não se é host no sistema, o comando é executado por essa função. Ela só tem close por enquanto
    def execute_client_side_command(self,message):
        if message[0] == '/close' or message[0] == '/quit':
            self.messager.send('(' + self.username + ' checked out for today)')
            self.messager.close()
            return 1
        return 0
    
    # Envia o comando de criação de chat, recebe o par host port e configura 
    # suas estruturas internas para hostear o chat
    def generate_host_chat_info(self,command_blob):
        chat_data = self.messager.send_and_receive(command_blob)

        chat_data = tuple(chat_data.split(' '))
        chat_data = (chat_data[0], int(chat_data[1]))
        self.chat_info = chat_data
        inputs, users = self.configure_chat_hosting()

        return inputs, users

    # Reinicia o socket com informações do par host port e gera as estruturas de dados de 
    # manutenção do host do chat
    def configure_chat_hosting(self):
        self.messager.close()
        self.messager.host_connection(self.chat_info[0], self.chat_info[1], 5)
        self.messager.set_blocking_connections(False)
        
        inputs = [self.messager.get_sock(), sys.stdin]
        users = []

        return inputs, users

    # Lida com as conexões de outros usuários e mensagens / comandos do host
    def host_chat(self,inputs,users):
        while True:
            read,write,execute = select.select(inputs,[],[])
            chat_offline = 0
            for command in read:
                # Conecta o novo usuário e atualiza as estruturas de dados
                if command == self.messager.get_sock():
                    new_messager = self.messager.accept() # TODO mudar lógica para lidar com messagers
                    users.append(new_messager)
                    inputs.append(new_messager.get_sock())

                # Ou envia a mensagem ou executa o comando
                elif command == sys.stdin:
                    message = input()
                    if message[0] != '/':
                        message = '(' + self.username + ') ' + message
                        self.messager.emit_message(message, users)
                    else:
                        users, inputs, chat_offline = self.execute_host_side_command(users,inputs,message.split())

                # Passa para a função que lida com mensagens de terceiros
                else:
                    users, inputs, chat_offline = self.handle_incoming_message(users,inputs,command)

            if chat_offline:
                return None

    # Remove o usuário quando não vem mensagem (socket fechado) e faz broadcast da mensagem quando ela existe
    def handle_incoming_message(self,users,inputs,sock):
        message = sock.recv(1024)
        # Usuário está desconectado
        if not message:
            inputs.remove(sock)
            for messager in users:
                if messager.sock == sock:
                    users.remove(messager)
                    break
            return users, inputs, 0
        # Printa mensagem para si mesmo e broadcasta para os outros
        else:
            message = str(message,encoding='utf-8') 
            print(message)
            self.messager.emit_message(message,users)
            return users, inputs, 0

    # Executa comandos no lado do host do chat (aqui teriamos /ban e /kick)
    def execute_host_side_command(self,users,inputs,message):
        if message[0] == '/close' or message[0] == '/quit':
            if not len(users):
                return users, inputs, 1
            print("> [user::execute_host_side_command] There are still people online")
            return users, inputs, 0
        return users, inputs, 0

    # Reconecta o usuário no servidor central (par host port está hardcoded ainda)
    def return_to_server(self):
        self.messager.reconnect("127.0.0.1",10000)
        self.reconnect_to_central_server()

if __name__ == '__main__':
    user = User()
    user.connect_to_central_server("127.0.0.1",10000)
