from hashlib import sha256
import json


class Block:
    def __init__(self, index, info, timestamp, previous_hash, previous_idx_hash=0):
        """
        Constructor for the `Block` class.
        :param index:         Unique ID of the block.
        :param info:  List of transactions.
        :param timestamp:     Time of generation of the block.
        :param previous_hash: Hash of the previous block in the chain which this block is part of.
        :param previous_idx_hash: Hash of the index file (latest version)
        """
        self.__index = index
        self.__info = info
        self.__timestamp = timestamp
        self.__previous_hash = previous_hash  # Adding the previous hash field
        self.nonce = 0
        self.__previous_idx_hash = previous_idx_hash

    def compute_hash(self):
        """
        Returns the hash of the block instance by first converting it
        into JSON string.
        """
        block_string = json.dumps(self.__dict__, sort_keys=True)
        # The string equivalent also considers the previous_hash field now
        return sha256(block_string.encode()).hexdigest()

    @property
    def info(self):
        return self.__info

    @property
    def previous_hash(self):
        return self.__previous_hash

    @property
    def index(self):
        return self.__index

    @property
    def previous_idx_hash(self):
        return self.__previous_idx_hash

    @previous_idx_hash.setter
    def previous_idx_hash(self, previous_idx_hash):
        self.__previous_idx_hash = previous_idx_hash
