# Made by Leo
# Contains the global variables

# Made by Leo

from multiprocessing import Queue

task_queue = Queue()
input_data_queue = Queue()

current_trans = []
prev_key = 0

fork = []

IDS = {}

# Starts with the genesis block
blockchain = [{'header':{'prev_block_hash':1513515}}]