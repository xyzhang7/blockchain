"""
TRANSACTION_INDEX:
        {(<donator1 public key, recipient1 public key>):
            {"value": <value1>, "description": <description1>},
         (<donator2 public key, recipient2 public key>):
            {"value": <value2>, "description": <description2>},
        ...}
"""

from Blockchain import Blockchain
import time
import json
from Block import Block
import requests
import random
import hashlib


def new_transaction(tx: Blockchain, request):
    tx_data = request.get_json()
    required_fields = ["from", "to", "value", "private_key", "description"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404

    # check key pair
    if tx_data['from'] != hashlib.sha256(tx_data["private_key"].encode('utf-8')).hexdigest():
        return "Forbidden", 403

    del tx_data["private_key"]
    tx_data["timestamp"] = time.time()

    # Update index
    tx.bc_idx[(tx_data["from"], tx_data["to"])].append((tx_data["value"], tx_data["description"]))

    tx.add_new_info(tx_data)
    return "Success", 201


def get_chain(tx: Blockchain):
    chain_data = []
    length = 0
    for block in tx.chain:
        chain_data.append(block.__dict__)
        length = block.index
    return json.dumps({"length": length,
                       "chain": chain_data})


def consensus(tx: Blockchain, peers):
    longest_chain = None
    current_len = len(tx.chain)

    for node in peers:
        response = requests.get('{}/tx/chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and tx.check_chain_validity(chain):
            # Longer valid chain found!
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain  # 选择最长链
        return True
    return False


def announce_new_block(block, peers):
    headers = {'Content-Type': "application/json"}
    for peer in peers:
        url = "{}/tx/add_block".format(peer)
        requests.post(url, data=json.dumps(block.__dict__, sort_keys=True), headers=headers)


def mine_unconfirmed_tx(tx: Blockchain, peers):
    result = tx.mine()
    if not result:
        return "No transactions to mine", 400
    else:
        # Making sure we have the longest chain before announcing to the network
        chain_length = len(tx.chain)
        consensus(tx, peers)

        if chain_length == len(tx.chain):
            # announce the recently mined block to the network
            announce_new_block(tx.last_block, peers)
            return "Transaction Block #{} is mined.".format(tx.last_block.index), 201

        return "Current Chain is not the latest version. New chain is updated.", 200


def tx_add_block(tx: Blockchain, request):
    block_data = request.get_json()
    block = Block(block_data["_Block__index"],
                  block_data["_Block__info"],
                  block_data["_Block__timestamp"],
                  block_data["_Block__previous_hash"],
                  block_data["_Block__previous_idx_hash"])
    block.nonce = block_data["nonce"]

    proof = block.compute_hash()
    added = tx.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400

    return "User Block added to the chain", 201
