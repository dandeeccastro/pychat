import socket 
import select 
import sys 

class Messager:
    def __init__(self,sock=None):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) if sock == None else sock

    def connect(self, host, port):
        self.sock.connect((host,port))

    def host_connection(self, host, port, amount_of_connections):
        self.sock.bind((host,port))
        self.sock.listen(amount_of_connections)

    def set_blocking_connections(self, is_blocking)
        self.sock.setblocking(is_blocking)

    def send(self,message):
        self.sock.send(bytes(message,encoding='utf-8'))

    def send_and_receive(self,message):
        self.sock.send(bytes(message,encoding='utf-8'))
        response = str(self.sock.recv(1024),encoding='utf-8')
        return response

    def emit_message(self,message,receivers):
        for receiver in receivers:
            receiver.send(bytes(message,encoding='utf-8'))

    def reconnect(self,host,port):
        self.sock.close()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host,port))

    def close(self):
        self.sock.close()

    def receive(self):
        response = str(self.sock.recv(1024),encoding='utf-8')
        return response
    
    def get_sock(self):
        return self.sock

    def accept(self):
        new_sock, addr = self.sock.accept()
        return Messager(new_sock)
