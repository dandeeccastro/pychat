import socket 

class MSI:

    def __init__(self,sock):
        self.sock = sock
        self.send_buf = None
        self.recv_buf = None

    def show_new_messages(self):
        messages = self.recv_buf
        self.recv_buf = None
        return messages

    def get_new_messages_from_host(self):
        print("> [msi] TODO implement me")
        self.__recv()
        return self.show_new_messages()

    def send_message(self,msg):
        print("> [msi] TODO implement me")
        
    def __bsend(self,msg):
        self.send_buf += bytes(self.uid + ' ' + msg + '\n', encoding='utf-8')

    def __sendrecv(self,msg=None):
        self.__send(msg)
        self.__recv()

    def __send(self,msg=None):
        if msg:
            self.bsend(msg)
        self.sock.send(self.send_buf)
        self.send_buf = None

    def __recv(self):
        self.recv_buf += self.sock.recv(1024)
