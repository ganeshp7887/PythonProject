import socket
from config import config


class SimpleSocket:

    def __init__(self):
        self.host = config.Config_machine_ip()

    def openSocket(self, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, int(port)))

    def sendRequest(self, data):
        raise Exception("Socket not connected. Call connect() first.") if self.sock is None else self.sock.sendall(data.encode('utf-8'))

    def receiveResponseFromSocket(self, buffer_size=12588):
        return self.sock.recv(buffer_size).decode('utf-8') if self.sock else (_ for _ in ()).throw(Exception("Socket not connected. Call connect() first."))

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None