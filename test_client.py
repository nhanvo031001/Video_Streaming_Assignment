import socket
from tkinter import Message
while True:
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = str(input())
    udp_socket.sendto(message.encode('utf-8'), ('localhost', 3000))
    if message == 'exit':
        udp_socket.close()
        break
while True:
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = str(input())
    udp_socket.sendto(message.encode('utf-8'), ('localhost', 3000))
    if message == 'exit':
        udp_socket.close()
        break