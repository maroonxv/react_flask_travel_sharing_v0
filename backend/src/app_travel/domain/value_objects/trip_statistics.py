"""
旅行统计值对象

包含旅行统计报表等值对象。
"""
from dataclasses import dataclass
from typing import List

from app_travel.domain.value_objects.travel_value_objects import Money, Location


@dataclass(frozen=True)
class TripStatistics:
    """旅行统计报表值对象
    
    包含整个旅行的统计信息：
    - 总里程
    - 总游玩时间
    - 总交通时间
    - 预估总花费（活动 + 交通）
    - 所有去过的地点（用于打卡地图）
    """
    total_distance_meters: float      # 总里程（米）
    total_play_time_minutes: int      # 总游玩时间（分钟）
    total_transit_time_minutes: int   # 总交通时间（分钟）
    total_estimated_cost: Money       # 预估总花费
    activity_cost: Money              # 活动花费
    transit_cost: Money               # 交通花费
    activity_count: int               # 活动数量
    visited_locations: tuple          # 所有去过的地点（用于打卡地图）
    
    def __init__(
        self,
        total_distance_meters: float,
        total_play_time_minutes: int,
        total_transit_time_minutes: int,
        total_estimated_cost: Money,
        activity_cost: Money,
        transit_cost: Money,
        activity_count: int,
        visited_locations: List[Location]
    ):
        """初始化统计报表
        
        将 visited_locations 列表转换为元组以保持不可变性。
        """
        object.__setattr__(self, 'total_distance_meters', total_distance_meters)
        object.__setattr__(self, 'total_play_time_minutes', total_play_time_minutes)
        object.__setattr__(self, 'total_transit_time_minutes', total_transit_time_minutes)
        object.__setattr__(self, 'total_estimated_cost', total_estimated_cost)
        object.__setattr__(self, 'activity_cost', activity_cost)
        object.__setattr__(self, 'transit_cost', transit_cost)
        object.__setattr__(self, 'activity_count', activity_count)
        object.__setattr__(self, 'visited_locations', tuple(visited_locations))
    
    @property
    def total_distance_km(self) -> float:
        """获取总里程（公里）"""
        return self.total_distance_meters / 1000
    
    @property
    def total_play_time_hours(self) -> float:
        """获取总游玩时间（小时）"""
        return self.total_play_time_minutes / 60
    
    @property
    def total_transit_time_hours(self) -> float:
        """获取总交通时间（小时）"""
        return self.total_transit_time_minutes / 60
    
    @property
    def total_time_minutes(self) -> int:
        """获取总时间（分钟）"""
        return self.total_play_time_minutes + self.total_transit_time_minutes
    
    @property
    def total_time_hours(self) -> float:
        """获取总时间（小时）"""
        return self.total_time_minutes / 60
    
    @property
    def visited_location_count(self) -> int:
        """获取去过的地点数量"""
        return len(self.visited_locations)
    
    @property
    def unique_locations(self) -> List[Location]:
        """获取去重后的地点列表"""
        seen = set()
        unique = []
        for loc in self.visited_locations:
            key = (loc.name, loc.latitude, loc.longitude)
            if key not in seen:
                seen.add(key)
                unique.append(loc)
        return unique
    
    def to_dict(self) -> dict:
        """转换为字典格式（便于API响应）"""
        return {
            "total_distance_km": round(self.total_distance_km, 2),
            "total_distance_meters": round(self.total_distance_meters, 2),
            "total_play_time_minutes": self.total_play_time_minutes,
            "total_play_time_hours": round(self.total_play_time_hours, 2),
            "total_transit_time_minutes": self.total_transit_time_minutes,
            "total_transit_time_hours": round(self.total_transit_time_hours, 2),
            "total_time_minutes": self.total_time_minutes,
            "total_time_hours": round(self.total_time_hours, 2),
            "total_estimated_cost": str(self.total_estimated_cost),
            "activity_cost": str(self.activity_cost),
            "transit_cost": str(self.transit_cost),
            "activity_count": self.activity_count,
            "visited_location_count": self.visited_location_count,
            "visited_locations": [
                {
                    "name": loc.name,
                    "latitude": loc.latitude,
                    "longitude": loc.longitude,
                    "address": loc.address
                }
                for loc in self.visited_locations
            ]
        }
    
    def __str__(self) -> str:
        return (
            f"TripStatistics("
            f"距离={self.total_distance_km:.1f}km, "
            f"游玩={self.total_play_time_hours:.1f}h, "
            f"交通={self.total_transit_time_hours:.1f}h, "
            f"花费={self.total_estimated_cost}, "
            f"打卡点={self.visited_location_count}个)"
        )
