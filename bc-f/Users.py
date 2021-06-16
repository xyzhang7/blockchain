from Blockchain import Blockchain
import time
import json
from Block import Block
import requests
import random
import hashlib


def new_users(users: Blockchain, request):
    user_data = request.get_json()
    required_fields = ["access_key", "name", "description"]

    for field in required_fields:
        if not user_data.get(field):
            return "Invalid User Info", 404

    # check access key
    if user_data['access_key'] != "PASSWORD":
        return "Forbidden", 403
    del user_data["access_key"]

    # generate key pair
    res = [random.randrange(1, 16, 1) for i in range(64)]

    # private key
    private_key = hashlib.sha256(str(res).encode('utf-8')).hexdigest()
    # public key
    public_key = hashlib.sha256(private_key.encode('utf-8')).hexdigest()

    response = {}
    response['public_key'] = str(public_key)
    response['private_key'] = str(private_key)

    user_data['public_key'] = str(public_key)
    user_data["timestamp"] = time.time()
    users.add_new_info(user_data)

    return response, 201


def get_users(users: Blockchain):
    chain_data = []
    length = 0
    for block in users.chain:
        chain_data.append(block.__dict__)
        length = block.index
    return json.dumps({"length": length,
                       "chain": chain_data})


def consensus(users: Blockchain, peers):
    longest_chain = None
    current_len = len(users.chain)

    for node in peers:
        response = requests.get('{}/users/chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and users.check_chain_validity(chain):
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
        url = "{}/users/add_block".format(peer)
        requests.post(url, data=json.dumps(block.__dict__, sort_keys=True), headers=headers)


def mine_unconfirmed_users(users: Blockchain, peers):
    result = users.mine()
    if not result:
        return "No New Users", 400
    else:
        # Making sure we have the longest chain before announcing to the network
        chain_length = len(users.chain)
        consensus(users, peers)

        if chain_length == len(users.chain):
            # announce the recently mined block to the network
            announce_new_block(users.last_block, peers)
            return "User Block #{} is mined.".format(users.last_block.index), 201

        return "Current Chain is not the latest version. New chain is updated.", 200


def users_add_block(users: Blockchain, request):
    block_data = request.get_json()
    block = Block(block_data["_Block__index"],
                  block_data["_Block__info"],
                  block_data["_Block__timestamp"],
                  block_data["_Block__previous_hash"])
    block.nonce = block_data["nonce"]

    proof = block.compute_hash()
    added = users.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400

    return "User Block added to the chain", 201
