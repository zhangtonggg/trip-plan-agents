from pydantic import BaseModel,field_validator
from typing import List
from datetime import datetime

class TravelRequest(BaseModel):
    departure: str
    destination: str
    start_date: str
    end_date: str
    interests: List[str] = []
    avoid_crowds: bool = False
    team_outing: bool = False

    @field_validator('departure', 'destination')
    @classmethod
    def validate_location(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("地点不能为空")
        return v

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("日期格式应为YYYY-MM-DD")