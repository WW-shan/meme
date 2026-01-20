import asyncio
import sys
from web3 import AsyncWeb3
from datetime import datetime

async def check_token(token_addr):
    # 使用QuickNode节点
    rpc = 'https://yolo-intensive-mansion.bsc.quiknode.pro/b6ea63747b9157f1605a615a5b54944993de5c1d/'
    w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(rpc))
    
    # 转换为checksum地址
    token_addr = w3.to_checksum_address(token_addr)
    
    print(f'查询代币: {token_addr}')
    
    # 获取代币创建交易
    code = await w3.eth.get_code(token_addr)
    if len(code) <= 2:
        print('❌ 代币合约不存在')
        return
    
    print('✅ 代币合约存在')
    
    # 查询TokenManager合约的事件
    contract_addr = '0x5c952063c7fc8610FFDB798152D69F0B9550762b'
    current = await w3.eth.block_number
    
    print(f'当前区块: {current}')
    print(f'搜索最近200个区块的TokenCreate事件...')
    
    # 分批搜索避免限制
    for start in range(current - 200, current, 50):
        end = min(start + 49, current)
        try:
            logs = await w3.eth.get_logs({
                'address': contract_addr,
                'fromBlock': start,
                'toBlock': end
            })
            
            for log in logs:
                # 检查是否包含目标代币地址
                log_data = str(log).lower()
                if token_addr.lower() in log_data:
                    block = await w3.eth.get_block(log['blockNumber'])
                    dt = datetime.fromtimestamp(block['timestamp'])
                    print(f'\n✅ 找到! 区块 {log["blockNumber"]} - {dt.strftime("%Y-%m-%d %H:%M:%S")}')
                    print(f'   交易: {log["transactionHash"].hex()}')
                    return
        except Exception as e:
            print(f'搜索区块 {start}-{end} 出错: {e}')
    
    print('❌ 未在最近200个区块找到该代币的创建事件')

if __name__ == '__main__':
    token = sys.argv[1] if len(sys.argv) > 1 else '0x89e0da7c2e43700e6b301489f6cdacc169294444'
    asyncio.run(check_token(token))
