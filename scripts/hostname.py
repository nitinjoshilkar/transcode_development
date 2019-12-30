import socket
print(socket.gethostname())
hostname=socket.gethostname()
ip_address= socket.gethostnamebyname(hostname)
print(ip_address)


