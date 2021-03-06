from flask import Flask, jsonify, request
from textwrap import dedent
from uuid import uuid4
import requests
import hashlib
import json
from time import time

class Blockchain():
    def __init__(self):
        self.chain: list = []
        self.current_transactions: list = []
        
    def genesis_block(self) -> dict:
        """
        Creates the Genesis Block
        :return : <dict> New Block
        """
        block = { "index": 1, "timestamp": time(), "transactions": self.current_transactions, "proof": 0, "previous_hash": None}

        # Append block to chain array
        self.chain.append(block)

        return block;

    def new_block(self, proof: int, previous_hash: str = None) -> dict:
        """
        Create a new Block in the Blockchain
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of the previous Block
        :return : <dict> New Block
        """
        block = { "index": len(self.chain) + 1, "timestamp": time(), "transactions": self.current_transactions, "proof": proof, "previous_hash": previous_hash or self.hash(self.chain[-1])}

        # Reset the current list of transactions
        self.current_transactions = []

        # Append block to chain array
        self.chain.append(block)

        return block;

    def new_transaction(self, sender: str, recipient: str, amount: float) -> int:
        """
        Creates a new transaction to got into the next mined Block
        :param sender: <str> Address of sender
        :param recipient: <str> Address of the Recipient
        :param amount: <float> Amount 
        :return : <int> The index of the Block that will hold this transaction
        """
        self.current_transactions.append({ "sender": sender,"recipient": recipient,"amount": amount})

        return self.last_block['index'] + 1

    def proof_of_work(self, last_proof: int) -> int:
        """
        Simple Proof of Work Algorithm:
        - Find a number p' such that hash(pp') contains leading 4 zeroes, where p is the previous p'
        - p is the previous proof, and p' is the new proof
        :param last_proof: <int>
        :return : <int>
        """
        proof = 0
        while (self.valid_proof(last_proof, proof) is False):
            proof += 1
        return proof

    @property
    def last_block(self) -> dict: 
        # Returns the last block in the chain
        return self.chain[-1]

    @staticmethod
    def hash(block: dict) -> str:
        """
        Create a SHA-256 hash of a Block
        :param block: <dict> Block
        :return : <str>
        """

        # Make sure dictionary is ordered, or inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @staticmethod
    def valid_proof(last_proof: int, proof: int) -> bool:
        """
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeros?
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :return :<bool> True if correct, False if not.
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

# Instantiate out Node
app = Flask(__name__)

# Generate a globally unique addres for this node
node_identifier = str(uuid4()).replace("-", "")

# Instantiate the Blockchain
blockchain = Blockchain()

@app.route("/", methods=["GET"])
def home():
    # Ignore this its just to test the web server
    text = {"hey": "there", "the": "server", "is": "running!", "test_val" : len("what are you looking at")}
    response = jsonify(text)
    return response, 200

@app.route("/mine", methods=["GET"])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = None
    if(len(blockchain.chain)):
        last_block = blockchain.last_block
    else:
        # Create the genisis block here
        last_block = blockchain.genesis_block()

    last_proof = last_block["proof"]
    proof = blockchain.proof_of_work(last_proof)

    # We must recieve a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin
    blockchain.new_transaction(sender="0", recipient=node_identifier,amount=1.00)

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    # Don't know why its not printed in order but it works!
    message = {"message": "New Block Forged", "index": block["index"], "transactions": block["transactions"],"proof": block["proof"],"previous_hash": block["previous_hash"]}
    response = jsonify(message)
    return response, 200

@app.route("/transactions/new", methods=["POST"])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = ["sender", "recipient", "amount"]
    if not all(k in values for k in required):
        return "Missing values", 400

    # Create a new Transaction
    index = blockchain.new_transaction(values["sender"], values["recipient"], values["amount"])

    message = {"message": f"Transaction will be added to Block {index}"}
    response = jsonify(message)
    return response, 201

@app.route("/chain", methods=["GET"])
def full_chain():
    '''
    response = {
            "chain", blockchain.chain,
            "length", len(blockchain.chain),
            }
    return jsonify(response), 200
    '''
    thingy = {"chain": blockchain.chain, "length": len(blockchain.chain)}
    response = jsonify(thingy)
    return response, 200
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
