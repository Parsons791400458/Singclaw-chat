"""
测试 Sui 市价单买入 - 3倍杠杆
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hyperliquid_api import HyperliquidAPI
from datetime import datetime
import json

def test_sui_market_buy():
    """测试 SUI 市价单买入"""
    print("=" * 60)
    print("SUI 市价单买入测试 - 3倍杠杆")
    print("=" * 60)
    
    # 从 config.py 读取配置
    from config import API_KEY, api_secret, TESTNET
    
    print(f"测试网: {TESTNET}")
    print(f"API Key: {API_KEY[:10]}...{API_KEY[-4:]}")
    
    # 初始化 API
    api = HyperliquidAPI(API_KEY, api_secret, testnet=TESTNET)
    
    # 1. 健康检查
    print("\n1. 健康检查...")
    if api.health_check():
        print("✅ API 健康检查通过")
    else:
        print("❌ API 健康检查失败")
        return False
    
    # 2. 获取账户信息
    print("\n2. 获取账户信息...")
    account_info = api.get_account_info()
    if account_info:
        print(f"账户余额: {account_info.get('balance', 'N/A')}")
        print(f"账户详情: {json.dumps(account_info, indent=2)}")
    else:
        print("❌ 无法获取账户信息")
        return False
    
    # 3. 获取 SUI 当前价格
    print("\n3. 获取 SUI 价格...")
    symbol = "SUIUSDT"
    current_price = api.get_price(symbol)
    if current_price:
        print(f"✅ {symbol} 当前价格: ${current_price:.4f}")
    else:
        print(f"❌ 无法获取 {symbol} 价格")
        # 尝试使用备用价格（CoinGecko）
        print("尝试使用 CoinGecko 备用价格...")
        try:
            import requests
            resp = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=sui&vs_currencies=usd", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                current_price = data.get("sui", {}).get("usd", 0)
                print(f"✅ CoinGecko SUI 价格: ${current_price:.4f}")
            else:
                print(f"❌ CoinGecko 价格获取失败: {resp.status_code}")
                return False
        except Exception as e:
            print(f"❌ 备用价格获取异常: {e}")
            return False
    
    # 4. 设置交易参数
    print("\n4. 设置交易参数...")
    capital = 1000.0  # 投入本金
    leverage = 3.0    # 3倍杠杆
    
    # 计算仓位（3倍杠杆意味着投入更多）
    position_size_usd = capital * leverage
    print(f"本金: ${capital}")
    print(f"杠杆: {leverage}x")
    print(f"仓位规模: ${position_size_usd:.2f}")
    
    # 转换为 SUI 数量
    position_size_sui = position_size_usd / current_price
    print(f"交易数量: {position_size_sui:.4f} SUI")
    
    # 5. 执行市价买入
    print("\n5. 执行市价买入...")
    print(f"符号: {symbol}")
    print(f"方向: buy")
    print(f"数量: {position_size_sui:.4f} SUI")
    print(f"订单类型: market (市价单)")
    print(f"预期价格: ≈ ${current_price:.4f}")
    
    # 调用下单接口
    order = api.place_order(
        symbol=symbol,
        side="buy",
        amount=position_size_sui,
        price=None,  # 市价单不需要价格
        order_type="market",
        reduce_only=False
    )
    
    if order:
        print("\n✅ 订单已提交!")
        print(f"订单详情: {json.dumps(order, indent=2)}")
        
        # 保存订单信息
        order_record = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "side": "buy",
            "order_type": "market",
            "amount": position_size_sui,
            "estimated_price": current_price,
            "leverage": leverage,
            "order_response": order,
            "config": {
                "api_key": API_KEY,
                "testnet": TESTNET
            }
        }
        
        with open('/root/.openclaw/workspace/crypto/hyperliquid_bot/test_sui_order.json', 'w') as f:
            json.dump(order_record, f, indent=2)
        print("\n📝 订单记录已保存到 test_sui_order.json")
        
        # 6. 等待片刻后查询订单状态
        print("\n6. 查询订单状态...")
        import time
        time.sleep(3)
        
        order_id = order.get("order_id") or order.get("id")
        if order_id:
            status = api.get_order_status(order_id)
            if status:
                print(f"订单状态: {json.dumps(status, indent=2)}")
            else:
                print("⚠️ 无法查询订单状态")
        else:
            print("⚠️ 响应中未找到订单ID")
        
        # 7. 再次获取账户信息，查看余额变化
        print("\n7. 检查余额变化...")
        new_account_info = api.get_account_info()
        if new_account_info:
            print(f"更新后余额: {new_account_info.get('balance', 'N/A')}")
            
            # 如果有钱包地址，显示
            if "address" in new_account_info:
                print(f"钱包地址: {new_account_info['address']}")
        else:
            print("⚠️ 无法获取更新后的账户信息")
        
        print("\n" + "=" * 60)
        print("✅ 测试完成!")
        print("=" * 60)
        
        return True
    else:
        print("\n❌ 订单提交失败")
        print("请检查:")
        print("  1. API 密钥是否正确")
        print("  2. 测试网 URL 是否正确")
        print("  3. 签名逻辑是否正确")
        print("  4. 订单参数是否符合要求")
        return False

if __name__ == "__main__":
    try:
        success = test_sui_market_buy()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
