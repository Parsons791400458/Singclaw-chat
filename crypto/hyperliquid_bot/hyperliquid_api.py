def _parse_json(self, response):
    """尝试解析JSON响应"""
    try:
        content = response.json()
        if isinstance(content, dict) and ("price" in content or "klines" in content):
            return content
        else:
            # 鸭子类型检查
            if 'price' in content or 'klines' in content:
                return content
            return None
    except:
        return None