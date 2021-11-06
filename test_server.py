import socket
while True:
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('', 3000))
    message, client_address = udp_socket.recvfrom(2048)
    message = message.decode('utf-8')
    print(message)
    if message == 'exit':
        udp_socket.shutdown(socket.SHUT_RDWR)
        udp_socket.close()
        break
while True:
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(('', 3000))
    message, client_address = udp_socket.recvfrom(2048)
    message = message.decode('utf-8')
    print(message)
    if message == 'exit':
        udp_socket.shutdown(socket.SHUT_RDWR)
        udp_socket.close()
        break