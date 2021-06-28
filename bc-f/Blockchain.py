import collections
import hashlib
import json
import os
import pickle

from Block import Block
import config
import time


class Blockchain:
    """
    :param op: default path of index file (specified in config.py)
    """
    difficulty = 2
    op = None

    def __init__(self):
        """
        Constructor for the `Blockchain` class.
        :param bc_idx[]: index of current blockchain
        """
        self.unconfirmed_info = []
        self.__chain = []
        self.__create_genesis_block()
        self.__bc_idx = None

    def __create_genesis_block(self):
        """
        A function to generate genesis block and appends it to
        the chain. The block has index 0, previous_hash as 0, and
        a valid hash.
        """
        genesis_block = Block(0, [], time.time(), "0")
        self.proof_of_work(genesis_block)
        self.__chain.append(genesis_block)

    @property
    def last_block(self) -> Block:
        """
        A quick pythonic way to retrieve the most recent block in the chain. Note that
        the chain will always consist of at least one block (i.e., genesis block)
        """
        return self.__chain[-1]

    @property
    def chain(self):
        return self.__chain

    def __setattr__(self, name, value):
        """
        NFTS_INDEX: dict(dict)
        {<public key1>:
            {<tokenId1>: <file path1>, <tokenId2>: <file path2>, ...},
         <public key2>:
            {...},
        ...}

        TRANSACTION_INDEX: dict(list)
        {(<donator1 public key>, <recipient1 public key>):
            [(value1, description1), (value2, description2), ...],
         (<donator2 public key>, <recipient2 public key>):
            [...],
        ...}
        """
        super(Blockchain, self).__setattr__(name, value)
        if name == 'op':
            if config.NFT_INDEX in value:
                self.__bc_idx = collections.defaultdict(dict)
            elif config.TRANSACTION_INDEX in value:
                self.__bc_idx = collections.defaultdict(list)
            else:
                raise IOError("config fail")
            self.save_bc_index()

    @property
    def bc_idx(self):
        return self.__bc_idx

    def save_bc_index(self):
        """
        :param op: the index file name defined in config.py
        """
        with open(self.op, "wb") as f:
            pickle.dump(self.__bc_idx, f)
        f.close()

    def load_bc_index(self):
        try:
            f = open(self.op, "rb")
        except OSError:
            print("The index file of current blockchain does not exist")
            return False
        else:
            previous_bc_idx = pickle.load(f)
            f.close()
        return previous_bc_idx

    def compute_hash(self, data):
        if isinstance(data, collections.defaultdict):
            data = json.dumps(data, sort_keys=True)
        if not isinstance(data, bytes):
            data = data.encode('utf-8')
        return hashlib.sha256(data).hexdigest()

    def compute_prev_index(self):
        """
        returns: hash of latest saved index file
        """
        previous_bc_idx = self.load_bc_index()
        return self.compute_hash(previous_bc_idx)

    def add_new_info(self, info):
        self.unconfirmed_info.append(info)

    def proof_of_work(self, block):
        """
        Function that tries different values of the nonce to get a hash
        that satisfies our difficulty criteria.
        """
        block.nonce = 0

        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def mine(self):
        """
        This function serves as an interface to add the pending
        transactions to the blockchain by adding them to the block
        and figuring out proof of work.
        """
        if not self.unconfirmed_info:
            return False

        last_block = self.last_block

        new_block = Block(index=last_block.index + 1,
                          info=self.unconfirmed_info,
                          timestamp=time.time(),
                          previous_hash=last_block.compute_hash())
        if self.bc_idx is not None:
            new_block.previous_idx_hash = self.compute_prev_index()

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)

        if self.bc_idx is not None:
            self.add_bc_index(new_block)

        self.unconfirmed_info = []
        return new_block.index

    def is_valid_proof(self, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    def add_bc_index(self, block):
        previous_idx_hash = self.compute_prev_index()
        if previous_idx_hash != block.previous_idx_hash:
            return False
        self.save_bc_index()

    def add_block(self, block, proof):
        """
        A function that adds the block to the chain after verification.
        Verification includes:
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of
          a latest block in the chain match.
        * The
        """
        previous_hash = self.last_block.compute_hash()

        if previous_hash != block.previous_hash:
            return False

        if not self.is_valid_proof(block, proof):
            return False

        # block.hash = proof
        self.__chain.append(block)
        return True

    def check_chain_validity(self, chain):
        is_valid = True
        previous_hash = "0"
        for block in chain:
            block_hash = block.hash
            delattr(block, "hash")
            if not self.is_valid_proof(block, block_hash) or previous_hash != block.previous_hash:
                is_valid = False
                break
            block.hash, previous_hash = block_hash, block_hash
        # TODO: verify index file
        return is_valid

    def check_index_validity(self, block):
        pass
