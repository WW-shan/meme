import asyncio
import sys
from web3 import AsyncWeb3
from datetime import datetime
import json

async def verify_token_source(token_addr):
    rpc = 'https://yolo-intensive-mansion.bsc.quiknode.pro/b6ea63747b9157f1605a615a5b54944993de5c1d/'
    w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc))
    
    token_addr = w3.to_checksum_address(token_addr)
    contract_addr = '0x5c952063c7fc8610FFDB798152D69F0B9550762b'
    
    print(f'检查代币: {token_addr}')
    
    # 检查代币是否存在
    try:
        code = await w3.eth.get_code(token_addr)
        if len(code) <= 2:
            print('  状态: 代币不存在')
            return False
        print('  状态: 代币存在')
    except Exception as e:
        print(f'  错误: {e}')
        return False
    
    # 加载合约ABI
    with open('config/TokenManager.lite.abi', 'r') as f:
        abi = json.load(f)
    
    contract = w3.eth.contract(address=contract_addr, abi=abi)
    
    # 获取当前区块
    current = await w3.eth.block_number
    print(f'  当前区块: {current}')
    
    # 搜索最近500个区块
    found = False
    for start in range(current - 500, current, 50):
        end = min(start + 49, current)
        try:
            # 获取TokenCreate事件
            logs = await w3.eth.get_logs({
                'address': contract_addr,
                'fromBlock': start,
                'toBlock': end,
                'topics': [w3.keccak(text='TokenCreate(uint256,address,address,string,string,uint256,uint256,uint256)').hex()]
            })
            
            for log in logs:
                try:
                    decoded = contract.events.TokenCreate().process_log(log)
                    created_token = decoded['args']['token']
                    if created_token.lower() == token_addr.lower():
                        block = await w3.eth.get_block(log['blockNumber'])
                        dt = datetime.fromtimestamp(block['timestamp'])
                        print(f'  ✓ 找到! 区块 {log["blockNumber"]} - {dt.strftime("%Y-%m-%d %H:%M:%S")}')
                        print(f'  交易: {log["transactionHash"].hex()}')
                        print(f'  名称: {decoded["args"]["name"]}')
                        print(f'  符号: {decoded["args"]["symbol"]}')
                        found = True
                        return True
                except Exception as e:
                    pass
        except Exception as e:
            if 'limit' in str(e).lower():
                await asyncio.sleep(0.5)
    
    if not found:
        print('  ✗ 未找到 (不是通过此合约创建或超出搜索范围)')
    return found

async def main():
    tokens = [
        '0x436fa07901680d72f9aa5b91619c9c0ec7334444',
        '0x4f3fc98124d4f1996674f877f2c9d81516514444', 
        '0x46ea359830fafddc7ab17ac86fd45406ecfd4444'
    ]
    
    results = []
    for token in tokens:
        result = await verify_token_source(token)
        results.append(result)
        print()
        await asyncio.sleep(0.5)
    
    print('='*60)
    print(f'总结: {sum(results)}/{len(results)} 个代币通过监控的合约创建')

asyncio.run(main())
