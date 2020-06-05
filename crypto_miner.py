# Made by Leo

from comms import comms
from RSA import RSA_encrypt
import global_vars as g_var

from datetime import datetime
from threading import Thread
from time import sleep

import ast
import random
import hashlib

# Only multiples of 4
NUMZEROS = 20
MAXNUM = 10000000000000
NUMBER_OF_THREADS = 8
REWARD = 5

MSGRELOAD = 0.5
TASKRELOAD = 30
TRANSGENFREQ = 15
FORKBLOCKBACK = 3
START = '0000'

FILENAME = 'Blockchain.txt'
ID = 'Gunship 1' # ID of the machine

# Number of connections
CONNECTIONS = 2

# IP addresses for the other nodes 
CLIENT = ['192.168.1.31', '192.1681.1.12']
# Recieving data ports
R_PORT = [7000, 8000]
# Sending ports
S_PORT = [6000, 6001]

# --------------------------- Crypto miner class --------------------------- #

class crypto_miner():
    def __init__(self):

        # Initiate the constructor of the parent comms class
        self.channels = [comms(S_PORT[i]) for i in range(CONNECTIONS)]
        
        # Instantiate the RSA signature/verification object
        self.RSA = RSA_encrypt()

        # Select the jobs that will be run when instantiated
        self.start_jobs = [{'func':self.clear_transactions, 'args':None,
                            'info':'New transaction sheet'},

                           {'func':self.mine, 'args':None,
                            'info':'Start the mining program'},

                           {'func':self.message_receiver, 'args':None,
                            'info':'Pull the messages from the in data queue'},
                                                      
                           {'func':self.transaction_gen, 'args':None,
                            'info':'Randomly generate transactions'}]
        
        # Add the inititate server tasks to the start jobs
        for i in range(CONNECTIONS):
            init = {'func':self.channels[i].init_server, 'args': None,
                    'info':'Start the broadcast server worker'}
            start = {'func':self.channels[i].start_client, 'args': (CLIENT[i],R_PORT[i]),
                     'info':'Start the client worker'}
            
            self.start_jobs.insert(0, start)
            self.start_jobs.insert(0, init)
        

        # Make the worker threads
        self.create_workers()
        self.create_jobs()

# -------------------------- Main thread function -------------------------- #

    def main_thread(self):
        while True:
            # Send a message
            test_msg = str({'time': str(datetime.now()),
                            'type':'print_msg',
                            'info':'Routine message sent from ' + ID,
                            'ID':ID})
            send_msg = {'func': self.broadcast, 'args':test_msg,
                        'info':'Message from task issuer'}
            g_var.task_queue.put(send_msg)
            
            # Send a message - update the ID status
            ID_msg = str({'time': str(datetime.now()),
                            'type':'ID',
                            'info':{'pk_e':self.RSA.pk_e,'pk_n':self.RSA.pk_n},
                            'ID':ID})
            send_msg = {'func': self.broadcast, 'args':ID_msg,
                        'info':'Message from task issuer'}
            g_var.task_queue.put(send_msg)
            
            # Wait before starting the loop again
            sleep(TASKRELOAD)

# -------------------------- Receive msg functions ------------------------- #

    def message_receiver(self):
        while True:
            msg = g_var.input_data_queue.get()
            if msg['type'] == 'print_msg':
                print(msg['info'])
                
            elif msg['type'] == 'transaction':
                print('Recieved a transaction: ' + msg['trans'] + '  signed: ' 
                  + str(msg['signature'] != None))
                if self.verify_transaction(msg['trans'], msg['signature'],
                                           msg['ID']):
                     self.add_transaction(msg['trans'], msg['signature'])
            
            elif msg['type'] == 'ID':
                g_var.IDS.update({msg['ID']:{'n': msg['info']['pk_n'], 
                                  'e':msg['info']['pk_e']}})
                print('Updated ID for ' + msg['ID'])
                
            elif msg['type'] == 'new_block':
                block_dict = ast.literal_eval(msg['block'])
                if self.block_verification(block_dict):
                    self.add_new_block(block_dict)

            sleep(MSGRELOAD)

# -------------------------- Receive msg functions ------------------------- #

    def transaction_gen(self):
        while True:
            num = random.randint(1,100)
            trans = 'A -> B ' + str(num)
            signature = self.RSA.sign(self.sha256_hash(trans))
            msg = {'time': str(datetime.now()),'type':'transaction',
                   'info':'Random transaction','ID':ID,'trans':trans,
                   'signature':signature}
            send_trans = {'func': self.broadcast, 'args':msg,
                         'info':'Random transaction'}
            
            print('New transaction: ' + msg['trans'] + '  signed: ' 
                  + str(msg['signature'] != None))
            self.add_transaction(msg['trans'], msg['signature'])
            g_var.task_queue.put(send_trans)
            
            sleep(random.randint(1,TRANSGENFREQ))
            
# -------------------------- Block chain organier -------------------------- #

    def push_block(self, header):
        block = self.build_new_block(header) 
        block_msg = {'time': str(datetime.now()),'type':'new_block',
                     'info':'New block','ID':ID,'block':str(block)} 
        
        self.broadcast(str(block_msg))
        self.add_new_block(block)

    def build_new_block(self, header):
        block = {}
        block['header'] = header
        block['transactions'] = g_var.current_trans
        
        return block
    
    def get_current_header(self):
        header = {}
        header['info'] = 'Version 5, Creator: ' + ID
        header['prev_block_hash'] = self.sha256_hash(g_var.blockchain[-1]['header'])
        header['merkle_root'] = self.merkle_root(g_var.current_trans)
        header['time'] = str(datetime.now())
        header['difficulty'] = NUMZEROS
        
        return header
    
    def block_verification(self, block):
        # Check that the proof of work is valid
        if not self.right_key(str(block['header'])):
            print('Invalid proof of work - block rejected')
            return False
        
        # Check that the previous block hash is correct
  #      print( block['header']['prev_block_hash'],
  #            self.sha256_hash(g_var.blockchain[-1]['header']))
        

        if not block['header']['prev_block_hash'] ==  \
            self.sha256_hash(g_var.blockchain[-1]['header']):
            print('Different previous hash - fork created')
            
            # Check where this block attaches to the established blockchain
            for i in range(2,min(len(g_var.blockchain),FORKBLOCKBACK)):
                if not block['header']['prev_block_hash'] == \
                    self.sha256_hash(g_var.blockchain[-i]['header']):
                    print(f'Fork created, {i} blocks ago')
                    
                    for fork in g_var.fork:
                        if block['header']['prev_block_hash'] == \
                            self.sha256_hash(fork['block'][-1]['header']):
                            fork['block'].append(block)
                    else:     
                        g_var.fork.append({'block':[block], 'root':i-1})
                    
                    break
            
            # Check to see if we should take on this fork
            try:
                dels = []
                for i in range(len(g_var.fork)):
                    if len(g_var.fork[i]['block']) > g_var.fork[i]['root']:
                        self.replace_blockchain(g_var.fork[i])
                        dels.append(i)
                
                # Delete this fork
                dels.reverse()
                for i in dels:
                    g_var.fork.pop(i)
            except Exception as error:
                print('Error: ' + str(error))
                        
            return False
        
        print('Block verification successful...\n')
        return True        

    def add_new_block(self, block):
        print(' ----------------------------- New block added ----------------------------- ')
        g_var.blockchain.append(block)
        self.update_fork_roots()
        self.write_to_file()
        self.clear_transactions()

    def add_transaction(self, transaction, signature):
        g_var.current_trans.append((transaction, signature))
    
    def verify_transaction(self, trans, signature, ID):
        try:
            n = g_var.IDS[ID]['n']
            e = g_var.IDS[ID]['e']
            plaintext = self.RSA.verify(signature, e, n)
            trans_hash = self.sha256_hash(trans)
            if plaintext == trans_hash:
                print('Transaction verified...')
                return True
            else:
                print('Invalid signature...')
                print(plaintext, trans_hash)
                return False
        except:
            print('Do not have the ID to verify transaction - allowing')
            return True
            
            
    def clear_transactions(self):
        g_var.current_trans = []
        
        # Reward to the miner
        g_var.current_trans.append(f'Miner {ID} gets {REWARD}')
    
    def replace_blockchain(self, fork):
        print('Accepting blockchain fork - ' + str(len(fork['block'])) 
              + ' replaced \n')
        print(' ----------------------------- New block added ----------------------------- ')
        for i in range(1, fork['root'] + 1):
            g_var.blockchain[-i] = fork['block'][-i]
            
    def update_fork_roots(self):
        dels = []
        for i in range(len(g_var.fork)):
            g_var.fork[i]['root'] += 1
    
            # See if we can remove the fork by checking its length
            if g_var.fork[i]['root'] > len(g_var.fork[i]['block']):
                dels.append(i)
        
        # Delete the required forks
        dels.reverse()
        for i in dels:
            g_var.fork.pop(i)
                
    def write_to_file(self):
        with open(FILENAME, 'w') as file:
            file.write(str(g_var.blockchain))        

# ---------------------------- Broadcast program --------------------------- #

    # Wrapper function to broadcast to all clients sequentially
    
    def broadcast(self, msg):
        for i in range(CONNECTIONS):
            self.channels[i].broadcast_msg(msg)        
            
# ------------------------------ Miner program ----------------------------- #

    def mine(self):        
        while True:
            header = self.get_current_header()
            nonce = {'nonce':random.randint(1,MAXNUM)}
            header.update(nonce)
            
            if self.right_key(str(header)):

                # Put a task on the task queue
                task = {'func': self.push_block, 'args':header,
                        'info': 'New key found'}
                g_var.task_queue.put(task)

    def right_key(self, key):
        key = str.encode(key)
        result = hashlib.sha256(key)

        if result.hexdigest().startswith(START):
            return True
        else:
            return False
    
    def sha256_hash(self, string):
        string = str.encode(str(string))
        return str(hashlib.sha256(string).hexdigest())
    
    def merkle_root(self, trans):
  #      print(trans)
        if len(trans) > 1 and type(trans) == list:
  #          print(trans, trans[:int(len(trans)/2)], trans[int(len(trans)/2):])
            trans =  self.merkle_root(trans[:int(len(trans)/2)])        \
            + self.merkle_root(trans[int(len(trans)/2):])
            return self.sha256_hash(trans)
        else:
            if type(trans) == list:
                return self.sha256_hash(trans[0])
            else:
                return self.sha256_hash(trans)



# -------------------------- Thread worker setup -------------------------- #

    # Create worker threads
    def create_workers(self):
        for _ in range(NUMBER_OF_THREADS):
            t = worker(self)
            t.daemon = True
            t.start()

    def create_jobs(self):
        for x in self.start_jobs:
            g_var.task_queue.put(x)
            sleep(0.5)

# ------------------------- Inherited worker class ------------------------- #

class worker(Thread):
    def __init__(self, crypto_self):
        Thread.__init__(self)

    def run(self):
        while True:
            task = g_var.task_queue.get()
            args = task['args']

            if not args == None:
                task['func'](args)
            else:
                task['func']()

if __name__ == '__main__':
    crypto = crypto_miner()
    crypto.main_thread()
