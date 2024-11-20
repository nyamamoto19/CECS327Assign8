import socket
import time
from pymongo import MongoClient
'''
maxPacketSize = 1024 #set arbitrary max packet size to 1024 bits
serverIP = input("Enter server IP: ") #user inputs an ip
TCPPort = int(input("Enter port number: ")) #user inputs the port number
TCPSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #AF_INET specifies that it will use ipv4 addresses, SOCK_STREAM specifies that it will use TCP
TCPSocket.bind((serverIP,TCPPort))  # this will bind the ip and the port to the socket
TCPSocket.listen(5) #this will allow 5 connection requests to be queued before we accept. If there are 6 requests before we accept, one will get dropped
incomingSocket, incomingAddress = TCPSocket.accept() #accepts a connection and creates a socket object
print("Connection from",incomingAddress)
'''
def get_database():
    url = "mongodb+srv://user1:user1Password@cluster0.0f9ks.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    client = MongoClient(url)
    return client

mongoDB = get_database()
result = mongoDB.test.mongodb_virtual.find() #test is within mongoDB, mongodb_virtual is table name
for res in result:
    print(res)


'''
query = incomingSocket.recv(maxPacketSize) #recieves query from client
if query == 1:
    #What is the average moisture inside my kitchen fridge in the past three hours?
    pass
elif query == 2:
    #What is the average water consumption per cycle in my smart dishwasher?
    pass
elif query ==3:
    #Which device consumed more electricity among my three IoT devices (two refrigerators and a dishwasher)?
    pass
else:
    incomingSocket.send(bytearray("Invalid query"), encoding="utf-8")
    '''
