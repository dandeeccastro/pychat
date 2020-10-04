import socket
import time

def client():
    sock = socket.socket()
    sock.connect(("127.0.0.1",4200))
    time.sleep(1)
    msg = sock.recv(1024)
    print(str(msg, encoding='utf-8'))

def server():
    sock = socket.socket()
    sock.bind(("127.0.0.1",4200))
    sock.listen(1)
    sock.setblocking(False)
    while True:
        new_sock, addr = sock.accept()
        new_sock.send(bytes("This message was sent instantaneously",encoding='utf-8'))

if __name__ == '__main__':
    x = input()
    if x == 'client':
        client()
    elif x == 'server':
        server()
