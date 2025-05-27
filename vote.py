from web3 import Web3
import time
import os
from dotenv import load_dotenv

# Load environment variables from GitHub Secrets or .env (optional for local testing)
load_dotenv()

# Get sensitive information from environment variables
private_key = os.getenv("PRIVATE_KEY")
taiko_rpc_url = os.getenv("TAIKO_RPC_URL")
my_address = Web3.to_checksum_address(os.getenv("MY_WALLET_ADDRESS"))
vote_contract_address = Web3.to_checksum_address(os.getenv("VOTE_CONTRACT_ADDRESS"))

# Connect to the Taiko network
web3 = Web3(Web3.HTTPProvider(taiko_rpc_url))
if not web3.is_connected():
    print("Error: Unable to connect to the Taiko network.")
    exit()

# ABI for the vote() function
vote_abi = '''
[
    {
        "constant": false,
        "inputs": [],
        "name": "vote",
        "outputs": [],
        "payable": false,
        "stateMutability": "nonpayable",
        "type": "function"
    }
]
'''

# Initialize the voting contract
vote_contract = web3.eth.contract(address=vote_contract_address, abi=vote_abi)

# Get the next transaction nonce
def get_next_nonce():
    return web3.eth.get_transaction_count(my_address)

# Wait for transaction confirmation
def wait_for_confirmation(tx_hash, timeout=300):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            receipt = web3.eth.get_transaction_receipt(tx_hash)
            if receipt and receipt['status'] == 1:
                print(f"Status: Transaction {web3.to_hex(tx_hash)} confirmed.")
                return True
            elif receipt and receipt['status'] == 0:
                print(f"Status: Transaction {web3.to_hex(tx_hash)} failed.")
                return False
        except:
            pass
        time.sleep(30)
    print(f"Status: Timeout waiting for confirmation of transaction {web3.to_hex(tx_hash)}.")
    return False

# Perform the vote (EIP-1559)
def vote():
    nonce = get_next_nonce()
    gas_estimate = web3.eth.estimate_gas({
        'to': vote_contract_address,
        'data': '0x632a9a52'
    })

    gas_price_gwei = 0.234
    max_priority_fee_per_gas = web3.to_wei(gas_price_gwei, 'gwei')
    max_fee_per_gas = web3.to_wei(gas_price_gwei, 'gwei')

    transaction = {
        'to': vote_contract_address,
        'chainId': 167000,
        'gas': gas_estimate,
        'maxFeePerGas': max_fee_per_gas,
        'maxPriorityFeePerGas': max_priority_fee_per_gas,
        'nonce': nonce,
        'data': '0x632a9a52',
        'type': 2
    }

    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)

    try:
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"\nStatus: Vote transaction sent.")
        print(f"Tx Hash: {web3.to_hex(tx_hash)}")

        if wait_for_confirmation(tx_hash):
            print("Vote confirmed successfully.")
            return True
    except Exception as e:
        print(f"Error while sending vote transaction: {e}")
    return False

# Number of times to vote
total_votes = 80

# Voting loop
for i in range(total_votes):
    print(f"\nVoting {i+1} of {total_votes}...")
    if vote():
        print(f"Vote {i+1} succeeded.")
    else:
        print(f"Vote {i+1} failed.")
    time.sleep(5)

print("\nVoting process completed.")
