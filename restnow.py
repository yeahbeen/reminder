import socket

s = socket.socket()         
host = "localhost"
port = 11233
s.settimeout(10)
s.connect((host, port))