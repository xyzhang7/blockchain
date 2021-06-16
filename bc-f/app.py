import requests
from flask import Flask, request
# import requests
import NFT
from Blockchain import Blockchain
from Block import Block
import time
import json
import Users
import Transactions

app = Flask(__name__)

tx = Blockchain()
users = Blockchain()
nfts = Blockchain()
peers = set()

CONNECTED_NODE_ADDRESS = "http://127.0.0.1:5000"
posts = []


def verify_author():
    # TODO
    return True


# User API
@app.route('/users/new_user', methods=['POST'])
def new_user():
    if not verify_author():
        return "Forbidden", 403

    data = Users.new_users(users, request)

    response = app.response_class(
        response=json.dumps(data[0]),
        status=data[1],
        mimetype='application/json'
    )
    return response


@app.route('/users/chain', methods=['GET'])
def get_users_chain():
    return Users.get_users(users)


@app.route('/users/pending_user', methods=['GET'])
def get_pending_user():
    return json.dumps(users.unconfirmed_info)


@app.route('/users/mine', methods=['GET'])
def mine_unconfirmed_users():
    return Users.mine_unconfirmed_users(users, peers)


@app.route('/users/add_block', methods=['POST'])
def users_add_block():
    return Users.users_add_block(users, request)


# Transaction API
@app.route('/tx/new_transaction', methods=['POST'])
def new_transaction():
    data = Transactions.new_transaction(tx, request)
    response = app.response_class(
        response=json.dumps(data[0]),
        status=data[1],
        mimetype='application/json'
    )
    return response


@app.route('/tx/chain', methods=['GET'])
def get_chain():
    return Transactions.get_chain(tx)


@app.route('/tx/pending_tx', methods=['GET'])
def get_pending_tx():
    return json.dumps(tx.unconfirmed_info)


@app.route('/tx/mine', methods=['GET'])
def mine_unconfirmed_tx():
    return Transactions.mine_unconfirmed_tx(tx, peers)


@app.route('/tx/add_block', methods=['POST'])
def tx_add_block():
    return Transactions.tx_add_block(tx, request)


# NFT API
@app.route('/nfts/new_file', methods=['POST'])
def new_nft_file():
    data = NFT.new_file(nfts, request)
    response = app.response_class(
        response=json.dumps(data[0]),
        status=data[1],
        mimetype='application/json'
    )
    return response


@app.route('/nfts/transfer', methods=['POST'])
def transfer():
    data = NFT.transfer(nfts, request)
    response = app.response_class(
        response=json.dumps(data[0]),
        status=data[1],
        mimetype='application/json'
    )
    return response


@app.route('/nfts/chain', methods=['GET'])
def get_nft_chain():
    return NFT.get_chain(nfts)


@app.route('/nfts/pending_nfts')
def get_pending_nfts():
    print(nfts.unconfirmed_info)
    return json.dumps(nfts.unconfirmed_info)


@app.route('/nfts/mine', methods=['GET'])
def mine_unconfirmed_nfts():
    return NFT.mine_unconfirmed_nfts(nfts, peers)


@app.route('/nfts/add_block', methods=['POST'])
def nft_add_block():
    return NFT.nft_add_block(nfts, request)


# Endpoint to add new peers to the network
@app.route('/register_node', methods=['POST'])
def register_new_peers():
    # The host address to the peer node
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    # Add the node to the peer list
    peers.add(node_address)

    # Return the blockchain to the newly registered node so that it can sync
    return get_chain()


# 创立新的节点
@app.route('/register_with', methods=['POST'])
def register_with_existing_node():
    """
    Internally calls the `register_node` endpoint to
    register current node with the remote node specified in the
    request, and sync the blockchain as well with the remote node.
    """
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    data = {"node_address": request.host_url}
    headers = {'Content-Type': "application/json"}

    # Make a request to register with remote node and obtain information 放入节点名单
    response = requests.post(node_address + "/register_node",
                             data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        global blockchain
        global peers
        # update chain and the peers
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)
        peers.update(response.json()['peers'])
        return "Registration successful", 200
    else:
        # if something goes wrong, pass it on to the API response
        return response.content, response.status_code


def create_chain_from_dump(chain_dump):
    blockchain = Blockchain()
    for idx, block_data in enumerate(chain_dump):
        block = Block(block_data["_Block__index"],
                      block_data["_Block__info"],
                      block_data["_Block__timestamp"],
                      block_data["_Block__previous_hash"])
        block.nonce = block_data["nonce"]
        proof = block.compute_hash()

        if idx > 0:
            added = blockchain.add_block(block, proof)
            if not added:
                raise Exception("The chain dump is tampered!!")
        else:  # the block is a genesis block, no verification needed
            blockchain.chain.append(block)
    return blockchain


def check_chain_validity(cls, chain):
    """
    A helper method to check if the entire blockchain is valid.
    """
    result = True
    previous_hash = "0"

    # Iterate through every block
    for block in chain:
        block_hash = block.compute_hash()
        # remove the hash field to recompute the hash again
        # using `compute_hash` method.
        # delattr(block, "hash")

        if not cls.is_valid_proof(block, block.hash) or \
                previous_hash != block.previous_hash:
            result = False
            break

        # block.hash, previous_hash = block_hash, block_hash
        previous_hash = block_hash

    return result


def consensus():
    """
    Our simple consensus algorithm. If a longer valid chain is
    found, our chain is replaced with it.
    """
    global blockchain

    longest_chain = None
    current_len = len(blockchain.chain)

    for node in peers:
        response = requests.get('{}/chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and blockchain.check_chain_validity(chain):
            # Longer valid chain found!
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain  # 选择最长链
        return True

    return False


# endpoint to add a block mined by someone else to
# the node's chain. The node first verifies the block
# and then adds it to the chain.
@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["_Block__index"],
                  block_data["_Block__info"],
                  block_data["_Block__timestamp"],
                  block_data["_Block__previous_hash"])
    block.nonce = block_data["nonce"]

    proof = block.compute_hash()
    added = blockchain.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201


def announce_new_block(block):
    """
    A function to announce to the network once a block has been mined.
    Other blocks can simply verify the proof of work and add it to their
    respective chains.
    """
    headers = {'Content-Type': "application/json"}
    for peer in peers:
        url = "{}add_block".format(peer)
        requests.post(url, data=json.dumps(block.__dict__, sort_keys=True), headers=headers)


@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result:
        return "No transactions to mine"
    else:
        # Making sure we have the longest chain before announcing to the network
        chain_length = len(blockchain.chain)
        consensus()

        if chain_length == len(blockchain.chain):
            # announce the recently mined block to the network
            announce_new_block(blockchain.last_block)
            return "Block #{} is mined.".format(blockchain.last_block.index)

        return "Current Chain is not the latest version. New chain is updated."


if __name__ == '__main__':
    app.run()
