from fastapi import APIRouter

shop_router = APIRouter()

@shop_router.get("/bed")  
def get_all_beds():
    return [{"type": "单人床","price": 1200},{"type": "双人床","price": 2400}]
    
@shop_router.get("/cap")
def get_all_caps():
    return [{"type": "棒球帽","price": 500},{"type": "渔夫帽","price": 100}]