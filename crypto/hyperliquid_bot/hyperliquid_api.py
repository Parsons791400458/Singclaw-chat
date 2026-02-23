"""
Hyperliquid API Client - 封装Hyperliquid交易所API
需要配置: API_BASE_URL, API_KEY, API_SECRET
"""

import requests
import json
import time
import hashlib
import hmac
from typing import Dict, List, Optional

class HyperliquidAPI:
    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = True):
        """
        初始化Hyperliquid API客户端
        
        Args:
            api_key: API密钥（可选，测试网可能不需要）
            api_secret: API密钥（可选）
            testnet: 是否使用测试网
        """
        self.api_key = api_key
        self.api_secret = api_secret
        
        # 配置URL - 需要根据实际文档调整
        if testnet:
            self.base_url = "https://api-testnet.hyperliquid.xyz"
        else:
            self.base_url = "https://api.hyperliquid.xyz"
        
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
        
        if api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {api_key}"
            })
    
    def _sign_request(self, method: str, path: str, body: Dict = None) -> Dict:
        """
        签名请求 - 需要根据Hyperliquid的具体签名算法实现
        
        Returns:
            包含签名后的headers
        """
        # TODO: 实现具体的签名逻辑
        # Hyperliquid可能使用类似：
        # signature = hmac.new(
        #     self.api_secret.encode(),
        #     f"{method}{path}{json.dumps(body) if body else ''}".encode(),
        #     hashlib.sha256
        # ).hexdigest()
        
        headers = self.session.headers.copy()
        # TODO: 添加签名头
        return headers
    
    def get_price(self, symbol: str) -> Optional[float]:
        """
        获取当前价格
        
        Args:
            symbol: 交易对，如 "BTCUSDT"
            
        Returns:
            当前价格或None
        """
        try:
            # 假设的端点 - 需要根据实际API文档调整
            endpoint = f"/v1/markets/{symbol}/price"
            response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return float(data.get("price", 0))
            else:
                print(f"获取价格失败: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"获取价格异常: {e}")
            return None
    
    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> Optional[List[Dict]]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对
            interval: 时间间隔 (1m, 5m, 15m, 1h, 4h, 1d)
            limit: 获取数量
            
        Returns:
            K线数据列表
        """
        try:
            # 假设的端点
            endpoint = f"/v1/markets/{symbol}/klines"
            params = {
                "interval": interval,
                "limit": limit
            }
            response = self.session.get(f"{self.base_url}{endpoint}", params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("klines", [])
            else:
                print(f"获取K线失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"获取K线异常: {e}")
            return None
    
    def get_account_info(self) -> Optional[Dict]:
        """获取账户信息"""
        try:
            endpoint = "/v1/account"
            response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"获取账户信息失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"获取账户信息异常: {e}")
            return None
    
    def place_order(self, symbol: str, side: str, amount: float, price: float = None, 
                   order_type: str = "limit", reduce_only: bool = False) -> Optional[Dict]:
        """
        下单
        
        Args:
            symbol: 交易对
            side: 方向 "buy" 或 "sell"
            amount: 数量
            price: 价格（市价单为None）
            order_type: 订单类型 "limit" 或 "market"
            reduce_only: 是否只减仓
            
        Returns:
            订单信息
        """
        try:
            endpoint = "/v1/orders"
            data = {
                "symbol": symbol,
                "side": side,
                "amount": amount,
                "type": order_type,
                "reduceOnly": reduce_only
            }
            
            if price is not None:
                data["price"] = price
            
            # 签名请求
            headers = self._sign_request("POST", endpoint, data)
            response = self.session.post(
                f"{self.base_url}{endpoint}",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                order = response.json()
                print(f"下单成功: {order}")
                return order
            else:
                print(f"下单失败: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"下单异常: {e}")
            return None
    
    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        try:
            endpoint = f"/v1/orders/{order_id}"
            headers = self._sign_request("DELETE", endpoint)
            response = self.session.delete(
                f"{self.base_url}{endpoint}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"取消订单成功: {order_id}")
                return True
            else:
                print(f"取消订单失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"取消订单异常: {e}")
            return False
    
    def get_positions(self) -> List[Dict]:
        """获取当前持仓"""
        try:
            endpoint = "/v1/positions"
            response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("positions", [])
            else:
                print(f"获取持仓失败: {response.status_code}")
                return []
        except Exception as e:
            print(f"获取持仓异常: {e}")
            return []
    
    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """查询订单状态"""
        try:
            endpoint = f"/v1/orders/{order_id}"
            response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"查询订单状态失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"查询订单状态异常: {e}")
            return None
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False


# 测试函数
def test_api():
    """测试API连接"""
    api = HyperliquidAPI(testnet=True)
    
    print("=== Hyperliquid API 测试 ===")
    
    # 健康检查
    if api.health_check():
        print("✅ API健康检查通过")
    else:
        print("❌ API健康检查失败")
    
    # 测试获取价格（使用CoinGecko作为备用）
    print("\n测试获取价格...")
    price = api.get_price("BTCUSDT")
    if price:
        print(f"✅ BTC/USDT 价格: ${price}")
    else:
        print("❌ 获取价格失败")
    
    # 测试账户信息
    print("\n测试获取账户信息...")
    account = api.get_account_info()
    if account:
        print(f"✅ 账户余额: {account.get('balance', 'N/A')}")
    else:
        print("❌ 获取账户信息失败")


if __name__ == "__main__":
    test_api()