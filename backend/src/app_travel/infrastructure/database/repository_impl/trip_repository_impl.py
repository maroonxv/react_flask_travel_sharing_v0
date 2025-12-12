"""
旅行仓库实现

实现 ITripRepository 接口。
负责 Trip 聚合根及其子实体（TripMember, TripDay, Activity, Transit）的持久化。
"""
from typing import List, Optional

from app_travel.domain.demand_interface.i_trip_repository import ITripRepository
from app_travel.domain.aggregate.trip_aggregate import Trip
from app_travel.domain.value_objects.travel_value_objects import TripId, TripStatus
from app_travel.infrastructure.database.dao_interface.i_trip_dao import ITripDao
from app_travel.infrastructure.database.persistent_model.trip_po import (
    TripPO, TripMemberPO, TripDayPO, ActivityPO, TransitPO
)


class TripRepositoryImpl(ITripRepository):
    """旅行仓库实现"""
    
    def __init__(self, trip_dao: ITripDao):
        """初始化仓库
        
        Args:
            trip_dao: 旅行数据访问对象
        """
        self._trip_dao = trip_dao
    
    def save(self, trip: Trip) -> None:
        """保存旅行（新增或更新）
        
        Args:
            trip: 旅行聚合根
        """
        existing_po = self._trip_dao.find_by_id(trip.id.value)
        
        if existing_po:
            # 更新现有旅行
            existing_po.update_from_domain(trip)
            # 同步子实体
            self._sync_members(existing_po, trip)
            self._sync_days(existing_po, trip)
            self._trip_dao.update(existing_po)
        else:
            # 添加新旅行
            trip_po = TripPO.from_domain(trip)
            self._trip_dao.add(trip_po)
    
    def _sync_members(self, trip_po: TripPO, trip: Trip) -> None:
        """同步成员
        
        Args:
            trip_po: 旅行持久化对象
            trip: Trip 领域实体
        """
        # 获取当前成员ID集合
        existing_member_ids = {m.user_id for m in trip_po.members}
        new_member_ids = {m.user_id for m in trip.members}
        
        # 删除不再存在的成员
        trip_po.members = [m for m in trip_po.members if m.user_id in new_member_ids]
        
        # 更新或添加成员
        for member in trip.members:
            existing = next((m for m in trip_po.members if m.user_id == member.user_id), None)
            if existing:
                existing.role = member.role.value
                existing.nickname = member.nickname
            else:
                trip_po.members.append(TripMemberPO.from_domain(member, trip.id.value))
    
    def _sync_days(self, trip_po: TripPO, trip: Trip) -> None:
        """同步日程
        
        Args:
            trip_po: 旅行持久化对象
            trip: Trip 领域实体
        """
        # 简化处理：清空并重新创建日程
        # 生产环境中应该做更精细的同步
        trip_po.days.clear()
        
        for day in trip.days:
            day_po = TripDayPO.from_domain(day, trip.id.value)
            # 添加活动
            for activity in day.activities:
                day_po.activities.append(ActivityPO.from_domain(activity, 0))  # ID 将由数据库生成
            # 添加交通
            for transit in day.transits:
                day_po.transits.append(TransitPO.from_domain(transit, 0))  # ID 将由数据库生成
            trip_po.days.append(day_po)
    
    def find_by_id(self, trip_id: TripId) -> Optional[Trip]:
        """根据ID查找旅行
        
        Args:
            trip_id: 旅行ID
            
        Returns:
            旅行实例，不存在则返回 None
        """
        trip_po = self._trip_dao.find_by_id(trip_id.value)
        if trip_po:
            return trip_po.to_domain()
        return None
    
    def find_by_member(self, user_id: str, status: Optional[TripStatus] = None) -> List[Trip]:
        """查找用户参与的旅行
        
        Args:
            user_id: 用户ID
            status: 可选的状态筛选
            
        Returns:
            旅行列表
        """
        status_value = status.value if status else None
        trip_pos = self._trip_dao.find_by_member(user_id, status_value)
        return [po.to_domain() for po in trip_pos]
    
    def find_by_creator(self, creator_id: str) -> List[Trip]:
        """查找用户创建的旅行
        
        Args:
            creator_id: 创建者ID
            
        Returns:
            旅行列表
        """
        trip_pos = self._trip_dao.find_by_creator(creator_id)
        return [po.to_domain() for po in trip_pos]
    
    def find_public(self, limit: int = 20, offset: int = 0, search_query: Optional[str] = None) -> List[Trip]:
        """查找公开的旅行
        
        Args:
            limit: 每页数量
            offset: 偏移量
            search_query: 搜索关键词
            
        Returns:
            旅行列表
        """
        trip_pos = self._trip_dao.find_public(limit, offset, search_query)
        return [po.to_domain() for po in trip_pos]
    
    def delete(self, trip_id: TripId) -> None:
        """删除旅行
        
        Args:
            trip_id: 旅行ID
        """
        self._trip_dao.delete(trip_id.value)
    
    def exists(self, trip_id: TripId) -> bool:
        """检查旅行是否存在
        
        Args:
            trip_id: 旅行ID
            
        Returns:
            是否存在
        """
        return self._trip_dao.exists(trip_id.value)
