# Made by Leo

import ast
import socket
import global_vars as g_var

RECVBUFFER = 204807

all_connections = []
all_address = []

class comms:
    def __init__(self, port, host = ''): 
        self.port = port
        self.host = host
        self.all_connections = []
        self.all_address = []        

# ------------------------ Server acceptance thread ------------------------ #

    # Handling connection from multiple clients and saving to a list
    # Closing previous connections when server.py file is restarted

    def accepting_connections(self):
        for c in self.all_connections:
            c.close()
        del all_connections[:]
        del all_address[:]
        
        print('Broadcasting on: ' + str(self.port))
                
        while True:
            try:
                conn, address = self.s.accept()
                self.s.setblocking(1)  # prevents timeout
                
                all_connections.append(conn)
                all_address.append(address)

                print("Connection has been established: " + address[0])

            except Exception as error:
                print("Error accepting connections: " + str(error))

# ----------------------------- Client thread ----------------------------- #
    
    def start_client(self, params): # The host is the IP
        host = params[0]
        port = params[1]
        s_c = socket.socket()
        
        print('Trying to connnect to the server')
        print(host, port)
        s_c.connect((host, port))
        
        while True:
  #          print('Waiting to recieve data')
            data = s_c.recv(RECVBUFFER)
        
            if len(data) > 0:
                dict_str = data.decode("utf-8")
                
                try:
                    in_dict = ast.literal_eval(dict_str)
                 #   print('I have recieved: ' + in_dict['info'])
                except:
                     print('Could not decode the message - possibly due to message overload')
                
                # Add it to the input data queue
                g_var.input_data_queue.put(in_dict)
            
# ------------------------------ Worker tasks ------------------------------ #
        
    # Send commands to client/victim or a friend
    def broadcast_msg(self, msg):
        try:
            for conn in all_connections:
                print('Broadcasting message: ', end = '')
                if len(msg) > 0:
                    conn.send(str.encode(str(msg)))
                print('Sent')
        except Exception as error:
            print("Error sending commands: " + str(error))

# ------------------------------ Socket setup ------------------------------ #
    
    def init_server(self):
        self.create_socket()
        self.bind_socket()
        self.accepting_connections()
        
    # Create a Socket ( connect two computers)
    def create_socket(self):
        try:
            self.s = socket.socket()
        except socket.error as msg:
            print("Socket creation error: " + str(msg))

    # Binding the socket and listening for connections
    def bind_socket(self):
        try:
            print("Binding the Port: " + str(self.port))
            self.s.bind((self.host, self.port))
            self.s.listen(10)
        except socket.error as msg:
            print("Socket Binding error" + str(msg) + "\n" + "Retrying...")
            self.bind_socket()
