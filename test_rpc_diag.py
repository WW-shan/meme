
import asyncio
import os
from web3 import AsyncWeb3, AsyncHTTPProvider
from web3.middleware import ExtraDataToPOAMiddleware

# RPC URL
RPC_URL = "https://four.rpc.48.club"
CONTRACT_ADDRESS = "0x5c952063c7fc8610FFDB798152D69F0B9550762b"

async def test_rpc():
    print(f"Testing RPC: {RPC_URL}")
    w3 = AsyncWeb3(AsyncHTTPProvider(RPC_URL))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    try:
        # Check connection and block number
        block = await w3.eth.block_number
        print(f"Current block: {block}")

        # Check again after a delay to see if it advances
        print("Waiting 3 seconds...")
        await asyncio.sleep(3)
        new_block = await w3.eth.block_number
        print(f"New block: {new_block}")

        if new_block > block:
            print("Block number is advancing")
        elif new_block == block:
            print("Block number did not change")
        else:
            print("Block number went backwards?!")

        # Try to fetch logs for the contract in the last few blocks
        from_block = block - 200 # Look back more blocks to be sure
        to_block = block
        print(f"Fetching logs from {from_block} to {to_block}...")

        logs = await w3.eth.get_logs({
            'address': w3.to_checksum_address(CONTRACT_ADDRESS),
            'fromBlock': from_block,
            'toBlock': to_block
        })

        print(f"Found {len(logs)} logs")
        if logs:
            print("Log fetching works. First log topics:")
            print(logs[0]['topics'])
        else:
            print("No logs found.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_rpc())
