# src/graph/tools.py
import os
import requests
from datetime import datetime
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv() # 在这里也加载dotenv，确保工具可以访问环境变量

@tool
def search_poi(keyword: str, city: str, poi_type: str = "") -> dict:
    """搜索兴趣点（高德地图API）"""
    if not keyword or not city:
        return {"error": "关键词和城市名称不能为空"}
    base_url = "https://restapi.amap.com/v3/place/text"
    params = {
        "key": os.getenv("AMAP_API_KEY"),
        "keywords": keyword,
        "city": city,
        "types": poi_type,
        "output": "json",
        "offset": 5
    }
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"请求错误: {str(e)}"}

@tool
def get_route(start: str, end: str, city: str = "", mode: str = "walking") -> dict:
    """获取路线规划（高德地图API）"""
    if not start or not end:
        return {"error": "起点和终点不能为空"}
    valid_modes = ["walking", "bus", "driving"]
    if mode not in valid_modes:
        return {"error": f"交通方式必须是 {', '.join(valid_modes)}"}
    base_url = f"https://restapi.amap.com/v3/direction/{mode}"
    params = {"key": os.getenv("AMAP_API_KEY"), "origin": start, "destination": end}
    if city:
        params["city"] = city
    try:
        response = requests.get(base_url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"请求错误: {str(e)}"}

@tool
def get_weather(city: str, date: str = "") -> dict:
    """获取天气预报（高德天气API）"""
    if not city:
        return {"error": "城市名称不能为空"}
    if date:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return {"error": "日期格式必须为 YYYY-MM-DD"}
    base_url = "https://restapi.amap.com/v3/weather/weatherInfo"
    extensions = "all" if date else "base"
    params = {
        "key": os.getenv("AMAP_API_KEY"),
        "city": city,
        "extensions": extensions,
        "output": "json"
    }
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"请求错误: {str(e)}"}

@tool
def get_poi_congestion(poi_id: str) -> dict:
    """获取景点拥挤度（基于高德地图POI详情API）"""
    if not poi_id:
        return {"error": "景点ID不能为空"}
    base_url = "https://restapi.amap.com/v3/place/detail"
    params = {"key": os.getenv("AMAP_API_KEY"), "id": poi_id, "extensions": "all"}
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"请求错误: {str(e)}"}

@tool
def get_opening_hours(poi_id: str) -> dict:
    """获取景点开放时间（高德地图API）"""
    if not poi_id:
        return {"error": "景点ID不能为空"}
    base_url = "https://restapi.amap.com/v3/place/detail"
    params = {"key": os.getenv("AMAP_API_KEY"), "id": poi_id, "extensions": "all"}
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"请求错误: {str(e)}"}

# 所有可用工具
ALL_TOOLS = [search_poi, get_route, get_weather, get_poi_congestion, get_opening_hours]