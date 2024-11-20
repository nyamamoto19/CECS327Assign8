import socket
import time

maxPacketSize = 1024 #set arbitrary max packet size to 1024 bits
serverIP = input("Enter server IP: ") #user inputs an ip
#serverIP = ipaddress.IPv4Address(IP)
TCPPort = int(input("Enter port number: ")) #user inputs the port number
TCPSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #AF_INET specifies that it will use ipv4 addresses, SOCK_STREAM specifies that it will use TCP
TCPSocket.bind((serverIP,TCPPort))  # this will bind the ip and the port to the socket
TCPSocket.listen(5) #this will allow 5 connection requests to be queued before we accept. If there are 6 requests before we accept, one will get dropped
incomingSocket, incomingAddress = TCPSocket.accept() #accepts a connection and creates a socket object
print("Connection from",incomingAddress)
while True: #will infinitely run
    packetData = incomingSocket.recv(maxPacketSize) #recieves message from client
    print("Message received:",packetData.decode())
    someData = packetData.upper() #changes the recieved message to all uppercase
    print("Message sending back:", someData.decode())
    incomingSocket.send(bytearray(str(someData.decode()), encoding="utf-8")) #sends message back to the sender as a byte array with the utf-8 encoding
    time.sleep(2)