"""
A implementation of NFTs which provides basic functionality
to track and transfer NFTs.
NFTs represent ownership over digital assets.
NFTs are distinguished by `tokenId`.
"""

import json
import hashlib
import os
from io import StringIO

import requests
import time

from werkzeug.utils import secure_filename

import config
from Block import Block
from Blockchain import Blockchain


def hash_data(data):
    if not isinstance(data, bytes):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def new_file(nfts: Blockchain, request):
    """
    Create an NFT if `from` == 0
    Throws if public key `to` is not verified.
    Throws if `file` is not a attached.
    """
    upload_folder = config.UPLOAD_FOLDER
    print(request)
    nft_data = {}
    required_fields = ["from", "to", "private_key"]
    for field in required_fields:
        if not request.form.get(field):
            return "Invalid NFT data", 404

    file = request.files["file"]

    # If user does not select file, browser also
    # submit a empty part without filename
    if file.filename == "":
        return "Empty NFT file", 404

    nft_data["from"] = request.form["from"]
    nft_data["to"] = request.form["to"]
    nft_data["private_key"] = request.form["private_key"]

    # TODO: check if an NFT is original
    # TODO: chunk large file

    # Verify ownership
    print("to: ", nft_data["to"])
    print("hash data: ", hash_data(nft_data["private_key"]))
    if nft_data["to"] != hash_data(nft_data["private_key"]):
        return "Forbidden", 403
    del nft_data["private_key"]

    filename = secure_filename(file.filename)
    file.save(os.path.join(upload_folder, filename))
    file.seek(0)
    file_binary_data = file.read()

    nft_data["timestamp"] = time.time()
    nft_data["tokenId"] = hash_data(file_binary_data)

    nfts.add_new_info(nft_data)
    return "Success", 201


def balanceOf(owner):
    """
    Get all NFTs assigned to `owner`
    """
    # TODO: check if valid owner ID
    # TODO: retrieve all NFTs of the owner
    pass


def ownerOf(nfts: Blockchain, tokenId):
    """
    Return the owner of NFT
    """
    owner = None
    for block in nfts.chain[::-1]:
        info = block.info
        for inf in info[::-1]:
            if inf["tokenId"] == tokenId:
                owner = inf["to"]
                return owner
    # for inf in nfts.unconfirmed_info[::-1]:
    #     if inf["tokenId"] == tokenId:
    #         owner = inf["to"]
    #         return owner
    return owner


def transfer(nfts: Blockchain, request):
    """
    Transfer ownership of an NFT.
    Throws if `from` is not the current owner.
    Throws if `to` is the zero. (NFT is not deletable)
    Throws if public key `from` is not verified.
    Throws if `tokenId` is not a valid NFT
    """
    nft_data = request.get_json()
    required_fields = ["from", "to", "private_key", "tokenId"]

    for field in required_fields:
        if not nft_data.get(field):
            return "Invalid NFT data", 404

    owner = ownerOf(nfts, nft_data["tokenId"])
    print("tokenId", nft_data["tokenId"])
    print("owner", owner)

    # verify if the owner authorize the transaction
    print("from", nft_data["from"])
    print("hash", hash_data(nft_data["private_key"]))
    if nft_data["from"] != hash_data(nft_data["private_key"]) or \
            owner != nft_data["from"]:
        return "Forbidden", 403
    del nft_data["private_key"]

    nft_data["timestamp"] = time.time()

    nfts.add_new_info(nft_data)
    return "Success", 201


def mine_unconfirmed_nfts(nfts: Blockchain, peers):
    result = nfts.mine()
    if not result:
        return "No new nfts to mine", 400
    else:
        chain_length = len(nfts.chain)
        consensus(nfts, peers)
        if chain_length == len(nfts.chain):
            announce_new_block(nfts.last_block, peers)
            return "NFT Block #{} is mined.".format(nfts.last_block.index), 201
        return "Current Chain is not the latest version. New chain is updated.", 200


def get_chain(nfts: Blockchain):
    chain_data = []
    chain_len = 0
    for block in nfts.chain:
        chain_data.append(block.__dict__)
        chain_len = block.index
    return json.dumps({"length": chain_len,
                       "chain": chain_data})


def announce_new_block(block, peers):
    headers = {"Content-Type": "application/json"}
    for peer in peers:
        url = "{}/nfts/add_block".format(peer)
        requests.post(url, data=json.dumps(block.__dict__, sort_keys=True), headers=headers)


def consensus(nfts: Blockchain, peers):
    longest_chain = None
    current_len = len(nfts.chain)

    for node in peers:
        response = requests.get('{}/nfts/chain'.format(node))
        length = response.json()["length"]
        chain = response.json()["chain"]
        if length > current_len and nfts.check_chain_validity(chain):
            current_len = length
            longest_chain = chain
    if longest_chain:
        config.nfts = longest_chain
        return True
    return False


def nft_add_block(nfts: Blockchain, request):
    block_data = request.get_json()
    block = Block(block_data["_Block__index"],
                  block_data["_Block__info"],
                  block_data["_Block__timestamp"],
                  block_data["_Block__previous_hash"])
    block.nonce = block_data["nonce"]
    proof = block.compute_hash()
    added = nfts.add_block(block, proof)
    if not added:
        return "The block was discarded by the node", 400
    return "User Block added to the chain", 201
