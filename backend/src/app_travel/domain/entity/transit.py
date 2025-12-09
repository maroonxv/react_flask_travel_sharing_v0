"""
Transit 实体 - TripDay 的子实体

表示两个活动之间的移动/交通。
"""
from dataclasses import dataclass
from datetime import time, datetime, date, timedelta
from typing import Optional
import uuid

from app_travel.domain.value_objects.transit_value_objects import (
    TransportMode, RouteInfo, TransitCost
)


@dataclass
class Transit:
    """交通实体
    
    表示两个活动之间的移动，包含路线信息和费用估算。
    作为 TripDay 的子实体存在。
    """
    
    id: str
    from_activity_id: str        # 起始活动ID
    to_activity_id: str          # 目标活动ID
    transport_mode: TransportMode
    route_info: RouteInfo
    departure_time: time         # 出发时间（对应from_activity的结束时间）
    arrival_time: time           # 到达时间（应不晚于to_activity的开始时间）
    estimated_cost: Optional[TransitCost] = None
    notes: str = ""
    
    @classmethod
    def create(
        cls,
        from_activity_id: str,
        to_activity_id: str,
        transport_mode: TransportMode,
        route_info: RouteInfo,
        departure_time: time,
        estimated_cost: Optional[TransitCost] = None,
        notes: str = ""
    ) -> 'Transit':
        """创建交通实体
        
        Args:
            from_activity_id: 起始活动ID
            to_activity_id: 目标活动ID
            transport_mode: 交通方式
            route_info: 路线信息
            departure_time: 出发时间
            estimated_cost: 预估费用（可选）
            notes: 备注
            
        Returns:
            Transit: 新创建的交通实体
        """
        # 计算到达时间
        departure_dt = datetime.combine(date.today(), departure_time)
        arrival_dt = departure_dt + timedelta(seconds=route_info.duration_seconds)
        arrival_time = arrival_dt.time()
        
        # 如果没有提供费用，自动计算
        if estimated_cost is None:
            estimated_cost = TransitCost.calculate_for_mode(
                transport_mode, 
                route_info.distance_meters
            )
        
        return cls(
            id=str(uuid.uuid4()),
            from_activity_id=from_activity_id,
            to_activity_id=to_activity_id,
            transport_mode=transport_mode,
            route_info=route_info,
            departure_time=departure_time,
            arrival_time=arrival_time,
            estimated_cost=estimated_cost,
            notes=notes
        )
    
    @classmethod
    def create_from_activities(
        cls,
        from_activity: 'Activity',
        to_activity: 'Activity',
        route_info: RouteInfo,
        transport_mode: TransportMode
    ) -> 'Transit':
        """根据两个活动创建交通实体
        
        Args:
            from_activity: 起始活动
            to_activity: 目标活动
            route_info: 路线信息
            transport_mode: 交通方式
            
        Returns:
            Transit: 新创建的交通实体
        """
        return cls.create(
            from_activity_id=from_activity.id,
            to_activity_id=to_activity.id,
            transport_mode=transport_mode,
            route_info=route_info,
            departure_time=from_activity.end_time
        )
    
    @property
    def duration_minutes(self) -> int:
        """获取交通时长（分钟）"""
        return self.route_info.duration_minutes
    
    @property
    def distance_meters(self) -> float:
        """获取距离（米）"""
        return self.route_info.distance_meters
    
    @property
    def distance_km(self) -> float:
        """获取距离（公里）"""
        return self.route_info.distance_km
    
    def update(
        self,
        transport_mode: Optional[TransportMode] = None,
        route_info: Optional[RouteInfo] = None,
        notes: Optional[str] = None
    ) -> None:
        """更新交通信息
        
        Args:
            transport_mode: 新的交通方式
            route_info: 新的路线信息
            notes: 新的备注
        """
        if transport_mode is not None:
            self.transport_mode = transport_mode
        if route_info is not None:
            self.route_info = route_info
            # 重新计算到达时间
            departure_dt = datetime.combine(date.today(), self.departure_time)
            arrival_dt = departure_dt + timedelta(seconds=route_info.duration_seconds)
            self.arrival_time = arrival_dt.time()
        if notes is not None:
            self.notes = notes
        
        # 重新计算费用
        if transport_mode is not None or route_info is not None:
            self.estimated_cost = TransitCost.calculate_for_mode(
                self.transport_mode,
                self.route_info.distance_meters
            )
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transit):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        return hash(self.id)
    
    def __repr__(self) -> str:
        return (
            f"Transit(id={self.id}, "
            f"from={self.from_activity_id}, "
            f"to={self.to_activity_id}, "
            f"mode={self.transport_mode.value})"
        )


# 需要导入timedelta
from datetime import timedelta

# TYPE_CHECKING导入避免循环依赖
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app_travel.domain.entity.activity import Activity
