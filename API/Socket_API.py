import errno
import socket
from config import config
import json
import requests


class Adsdk_Socket:
    sock = None
    comm = config.commProtocol()
    ip = config.Config_machine_ip()


    @staticmethod
    def httpsRequest(url, request):
        request = json.loads(request)
        response = requests.post(url, json=request, verify=False, headers={"Content-Type": "application/json"}).text
        return response

    @staticmethod
    def sendRequest(request):
        Adsdk_Socket.sock.sendall(request.encode('utf-8'))


    @staticmethod
    def receiveResponseFromSocket():
        buf = bytearray()
        while True:
            chunk = Adsdk_Socket.sock.recv(12288)
            if not chunk:
                break
            buf.extend(chunk)
            return buf.decode('utf-8')


    @staticmethod
    def receiveResponseFromSocketwithinTime():
        try:
            data = Adsdk_Socket.sock.recv(12000)  # Buffer size is 1024 bytes
            if data:
                return data.decode('utf-8')
            else:
                print("No data received.")
        except socket.timeout:
            print("Timed out waiting for a response.")

    @staticmethod
    def closeSocket(): Adsdk_Socket.sock.close()

    @staticmethod
    def openSocket(port):
        server_address = (Adsdk_Socket.ip, int(port))
        try:
            Adsdk_Socket.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            Adsdk_Socket.sock.connect(server_address)
        except socket.error as e:
            print("Socket is already connected") if e.errno == errno.EISCONN else print("Error connecting:", e)


    @staticmethod
    def getHostName(): return socket.gethostname()
