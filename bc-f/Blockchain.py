from Block import Block
import time


class Blockchain:
    difficulty = 2

    def __init__(self):
        """
        Constructor for the `Blockchain` class.
        """
        self.unconfirmed_info = []
        self.__chain = []
        self.__create_genesis_block()

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

    def add_block(self, block, proof):
        """
        A function that adds the block to the chain after verification.
        Verification includes:
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of
          a latest block in the chain match.
        """
        previous_hash = self.last_block.compute_hash()

        if previous_hash != block.previous_hash:
            return False

        if not self.is_valid_proof(block, proof):
            return False

        # block.hash = proof
        self.__chain.append(block)
        return True

    def is_valid_proof(self, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    def add_new_info(self, info):
        self.unconfirmed_info.append(info)

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

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)
        self.unconfirmed_info = []
        return new_block.index

    def check_chain_validity(self, chain):
        rt = True
        previous_hash = "0"
        for block in chain:
            block_hash = block.hash
            delattr(block, "hash")
            if not self.is_valid_proof(block, block_hash) or previous_hash != block.previous_hash:
                rt = False
                break
            block.hash, previous_hash = block_hash, block_hash
        return rt

