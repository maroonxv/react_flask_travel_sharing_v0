"""
旅行应用服务 - 应用层

协调领域对象完成用例，管理事务边界，发布领域事件。
遵循 DDD 原则：应用层保持无状态，尽可能薄。
复杂业务逻辑由领域层（聚合根、领域服务）处理。
"""
from datetime import date, time
from typing import List, Optional, Dict, Any
from decimal import Decimal

from app_travel.domain.aggregate.trip_aggregate import Trip
from app_travel.domain.entity.activity import Activity
from app_travel.domain.demand_interface.i_trip_repository import ITripRepository
from app_travel.domain.demand_interface.i_geo_service import IGeoService
from app_travel.domain.domain_service.itinerary_service import ItineraryService
from app_travel.domain.value_objects.travel_value_objects import (
    TripId, TripName, TripDescription, DateRange, Money,
    TripStatus, TripVisibility, MemberRole, ActivityType, Location
)
from app_travel.domain.value_objects.itinerary_value_objects import TransitCalculationResult
from app_travel.domain.value_objects.trip_statistics import TripStatistics
from shared.event_bus import EventBus


class TravelService:
    """旅行应用服务
    
    职责：
    - 协调领域对象完成用例
    - 管理事务边界
    - 发布领域事件
    
    设计原则：
    - 无状态：不保存任何业务状态，所有状态由领域对象管理
    - 薄应用层：复杂逻辑委托给领域服务（ItineraryService）和聚合根（Trip）
    - 编排者：负责调用顺序和事件发布，不包含业务逻辑
    """
    
    def __init__(
        self,
        trip_repository: ITripRepository,
        geo_service: IGeoService,
        event_bus: Optional[EventBus] = None
    ):
        """初始化应用服务
        
        Args:
            trip_repository: 旅行仓库
            geo_service: 地理服务（用于创建 ItineraryService）
            event_bus: 事件总线（可选，默认使用全局实例）
        """
        self._trip_repository = trip_repository
        self._geo_service = geo_service
        self._event_bus = event_bus or EventBus.get_instance()
    
    def _create_itinerary_service(self) -> ItineraryService:
        """创建行程服务实例（无状态，每次调用创建新实例）"""
        return ItineraryService(self._geo_service)
    
    def _publish_events(self, trip: Trip) -> None:
        """发布聚合根中累积的领域事件"""
        events = trip.pop_events()
        self._event_bus.publish_all(events)
    
    # ==================== Trip CRUD ====================
    
    def create_trip(
        self,
        name: str,
        description: str,
        creator_id: str,
        start_date: date,
        end_date: date,
        budget_amount: Optional[float] = None,
        budget_currency: str = "CNY",
        visibility: str = "private",
        cover_image_url: Optional[str] = None
    ) -> Trip:
        """创建旅行
        
        Args:
            name: 旅行名称
            description: 旅行描述
            creator_id: 创建者ID
            start_date: 开始日期
            end_date: 结束日期
            budget_amount: 预算金额（可选）
            budget_currency: 预算货币（默认CNY）
            visibility: 可见性（默认private）
            cover_image_url: 封面图片URL（可选）
            
        Returns:
            创建的旅行实例
        """
        # 构建值对象
        trip_name = TripName(name)
        trip_desc = TripDescription(description)
        date_range = DateRange(start_date, end_date)
        budget = Money(Decimal(str(budget_amount)), budget_currency) if budget_amount else None
        trip_visibility = TripVisibility.from_string(visibility)
        
        # 通过工厂方法创建（领域逻辑在聚合根中）
        trip = Trip.create(
            name=trip_name,
            description=trip_desc,
            creator_id=creator_id,
            date_range=date_range,
            budget=budget,
            visibility=trip_visibility,
            cover_image_url=cover_image_url
        )
        
        # 持久化
        self._trip_repository.save(trip)
        
        # 发布事件
        self._publish_events(trip)
        
        return trip
    
    def get_trip(self, trip_id: str) -> Optional[Trip]:
        """获取旅行
        
        Args:
            trip_id: 旅行ID
            
        Returns:
            旅行实例，不存在返回 None
        """
        return self._trip_repository.find_by_id(TripId(trip_id))
    
    def update_trip(
        self,
        trip_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        visibility: Optional[str] = None,
        budget_amount: Optional[float] = None,
        budget_currency: str = "CNY",
        status: Optional[str] = None,
        cover_image_url: Optional[str] = None
    ) -> Optional[Trip]:
        """更新旅行基本信息
        
        Args:
            trip_id: 旅行ID
            name: 新名称（可选）
            description: 新描述（可选）
            visibility: 新可见性（可选）
            budget_amount: 新预算金额（可选）
            budget_currency: 预算货币
            status: 新状态（可选）
            cover_image_url: 新封面图片URL（可选）
            
        Returns:
            更新后的旅行实例
        """
        trip = self._trip_repository.find_by_id(TripId(trip_id))
        if not trip:
            return None
        
        # 委托给聚合根处理（领域逻辑在聚合根中）
        # 构建值对象
        trip_name = TripName(name) if name else None
        trip_desc = TripDescription(description) if description is not None else None
        trip_visibility = TripVisibility.from_string(visibility) if visibility else None
        
        budget = None
        if budget_amount is not None:
             budget = Money(Decimal(str(budget_amount)), budget_currency) if budget_amount > 0 else None
        
        # 调用聚合根的 update_info 方法
        # 注意：这里我们使用 update_info 来统一处理信息更新，而不是分散的 update_xxx
        # 之前的 update_name 等方法如果不再使用可以考虑移除或保留兼容
        
        # 为了兼容现有代码，我们先使用聚合根提供的具体方法，对于新加的 cover_image_url 和 visibility，
        # 如果聚合根有 update_info 最好用那个。
        # 查看 Trip 聚合根代码，它有 update_info 方法支持 name, description, budget, visibility, cover_image_url
        
        trip.update_info(
            name=trip_name,
            description=trip_desc,
            budget=budget,
            visibility=trip_visibility,
            cover_image_url=cover_image_url
        )
        
        if status:
            trip.update_status(TripStatus.from_string(status))
        
        # 持久化
        self._trip_repository.save(trip)
        
        # 发布事件
        self._publish_events(trip)
        
        return trip
    
    def delete_trip(self, trip_id: str) -> bool:
        """删除旅行
        
        Args:
            trip_id: 旅行ID
            
        Returns:
            是否成功删除
        """
        tid = TripId(trip_id)
        if not self._trip_repository.exists(tid):
            return False
        
        self._trip_repository.delete(tid)
        return True
    
    def list_user_trips(
        self, 
        user_id: str, 
        status: Optional[str] = None
    ) -> List[Trip]:
        """获取用户参与的旅行列表
        
        Args:
            user_id: 用户ID
            status: 状态筛选（可选）
            
        Returns:
            旅行列表
        """
        trip_status = TripStatus.from_string(status) if status else None
        return self._trip_repository.find_by_member(user_id, trip_status)
    
    def list_created_trips(self, creator_id: str) -> List[Trip]:
        """获取用户创建的旅行列表"""
        return self._trip_repository.find_by_creator(creator_id)
    
    def list_public_trips(self, limit: int = 20, offset: int = 0, search_query: Optional[str] = None) -> List[Trip]:
        """获取公开的旅行列表"""
        return self._trip_repository.find_public(limit, offset, search_query)
    
    # ==================== 成员管理 ====================
    
    def add_member(
        self,
        trip_id: str,
        user_id: str,
        role: str = "member",
        added_by: str = None
    ) -> Optional[Trip]:
        """添加成员
        
        Args:
            trip_id: 旅行ID
            user_id: 被添加用户ID
            role: 角色
            added_by: 操作者ID
        """
        trip = self._trip_repository.find_by_id(TripId(trip_id))
        if not trip:
            return None
        
        # 检查是否为好友
        if added_by and added_by != user_id:
            try:
                from app_social.services.social_service import SocialService
                social_service = SocialService()
                if not social_service.are_friends(added_by, user_id):
                    raise ValueError(f"User {user_id} is not your friend")
            except ImportError:
                # 忽略循环依赖或模块未找到，降级处理
                pass
            except Exception as e:
                # 重新抛出业务异常
                raise e

        # 委托给聚合根（业务规则在聚合根中）
        trip.add_member(
            user_id=user_id,
            role=MemberRole.from_string(role),
            added_by=added_by
        )
        
        self._trip_repository.save(trip)
        self._publish_events(trip)
        
        return trip
    
    def remove_member(
        self,
        trip_id: str,
        user_id: str,
        removed_by: str,
        reason: Optional[str] = None
    ) -> Optional[Trip]:
        """移除成员"""
        trip = self._trip_repository.find_by_id(TripId(trip_id))
        if not trip:
            return None
        
        trip.remove_member(user_id, removed_by, reason)
        
        self._trip_repository.save(trip)
        self._publish_events(trip)
        
        return trip
    
    def change_member_role(
        self,
        trip_id: str,
        user_id: str,
        new_role: str,
        changed_by: str
    ) -> Optional[Trip]:
        """更改成员角色"""
        trip = self._trip_repository.find_by_id(TripId(trip_id))
        if not trip:
            return None
        
        trip.change_member_role(user_id, MemberRole.from_string(new_role), changed_by)
        
        self._trip_repository.save(trip)
        self._publish_events(trip)
        
        return trip
    
    # ==================== 活动与行程管理 ====================
    
    def add_activity(
        self,
        trip_id: str,
        day_index: int,
        operator_id: str,
        name: str,
        activity_type: str,
        location_name: str,
        start_time: time,
        end_time: time,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        address: Optional[str] = None,
        cost_amount: Optional[float] = None,
        cost_currency: str = "CNY",
        notes: str = ""
    ) -> Optional[TransitCalculationResult]:
        """添加活动到指定日期
        
        自动计算与前一个活动之间的交通。
        
        Returns:
            TransitCalculationResult 包含计算的交通和可能的警告
        """
        trip = self._trip_repository.find_by_id(TripId(trip_id))
        if not trip:
            return None
        
        # 构建活动实体
        location = Location(
            name=location_name,
            latitude=latitude,
            longitude=longitude,
            address=address
        )
        cost = Money(Decimal(str(cost_amount)), cost_currency) if cost_amount else None
        
        activity = Activity.create(
            name=name,
            activity_type=ActivityType.from_string(activity_type),
            location=location,
            start_time=start_time,
            end_time=end_time,
            cost=cost,
            notes=notes
        )
        
        # 委托给聚合根，传入行程服务（无状态）
        itinerary_service = self._create_itinerary_service()
        result = trip.add_activity(day_index, activity, operator_id, itinerary_service)
        
        self._trip_repository.save(trip)
        self._publish_events(trip)
        
        return result or TransitCalculationResult()
    
    def modify_activity(
        self,
        trip_id: str,
        day_index: int,
        activity_id: str,
        operator_id: str,
        **updates
    ) -> Optional[TransitCalculationResult]:
        """修改活动
        
        修改后重新计算相邻的交通。
        
        Args:
            trip_id: 旅行ID
            day_index: 日期索引
            activity_id: 活动ID
            operator_id: 操作者ID
            **updates: 要更新的字段
        """
        trip = self._trip_repository.find_by_id(TripId(trip_id))
        if not trip:
            return None
        
        # 处理特殊字段转换
        if 'location_name' in updates:
            updates['location'] = Location(
                name=updates.pop('location_name'),
                latitude=updates.pop('latitude', None),
                longitude=updates.pop('longitude', None),
                address=updates.pop('address', None)
            )
        if 'activity_type' in updates:
            updates['activity_type'] = ActivityType.from_string(updates['activity_type'])
        if 'cost_amount' in updates:
            cost_amount = updates.pop('cost_amount')
            cost_currency = updates.pop('cost_currency', 'CNY')
            updates['cost'] = Money(Decimal(str(cost_amount)), cost_currency) if cost_amount else None
        
        # 委托给聚合根
        itinerary_service = self._create_itinerary_service()
        result = trip.modify_activity(day_index, activity_id, operator_id, itinerary_service, **updates)
        
        self._trip_repository.save(trip)
        self._publish_events(trip)
        
        return result or TransitCalculationResult()

    def remove_activity(
        self,
        trip_id: str,
        day_index: int,
        activity_id: str,
        operator_id: str
    ) -> Optional[TransitCalculationResult]:
        """移除活动"""
        trip = self._trip_repository.find_by_id(TripId(trip_id))
        if not trip:
            return None
        
        itinerary_service = self._create_itinerary_service()
        result = trip.remove_activity(day_index, activity_id, operator_id, itinerary_service)
        
        self._trip_repository.save(trip)
        self._publish_events(trip)
        
        return result or TransitCalculationResult()

    def update_day_itinerary(
        self,
        trip_id: str,
        day_index: int,
        activities_data: List[Dict[str, Any]],
        operator_id: str
    ) -> Optional[TransitCalculationResult]:
        """批量更新某日行程
        
        Args:
            trip_id: 旅行ID
            day_index: 日期索引
            activities_data: 活动数据列表
            operator_id: 操作者ID
        """
        trip = self._trip_repository.find_by_id(TripId(trip_id))
        if not trip:
            return None
        
        # 构建活动列表
        activities = []
        for data in activities_data:
            location = Location(
                name=data['location_name'],
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                address=data.get('address')
            )
            cost_amount = data.get('cost_amount')
            cost = Money(Decimal(str(cost_amount)), data.get('cost_currency', 'CNY')) if cost_amount else None
            
            activity = Activity.create(
                name=data['name'],
                activity_type=ActivityType.from_string(data['activity_type']),
                location=location,
                start_time=data['start_time'],
                end_time=data['end_time'],
                cost=cost,
                notes=data.get('notes', '')
            )
            activities.append(activity)
        
        # 委托给聚合根
        itinerary_service = self._create_itinerary_service()
        result = trip.update_day_itinerary(day_index, activities, operator_id, itinerary_service)
        
        self._trip_repository.save(trip)
        self._publish_events(trip)
        
        return result or TransitCalculationResult()
    
    # ==================== 地理编码（无状态代理）====================
    
    def geocode_location(self, fuzzy_name: str) -> Optional[Dict[str, Any]]:
        """解析模糊地名为精确坐标
        
        直接委托给 IGeoService，无状态。
        
        Args:
            fuzzy_name: 模糊地名
            
        Returns:
            位置信息字典，包含 name, latitude, longitude, address
        """
        location = self._geo_service.geocode(fuzzy_name)
        if location:
            return {
                'name': location.name,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'address': location.address
            }
        return None
    
    # ==================== 统计报表 ====================
    
    def get_trip_statistics(self, trip_id: str) -> Optional[Dict[str, Any]]:
        """获取旅行统计报表
        
        委托给聚合根生成统计信息。
        
        Args:
            trip_id: 旅行ID
            
        Returns:
            统计信息字典
        """
        trip = self._trip_repository.find_by_id(TripId(trip_id))
        if not trip:
            return None
        
        # 委托给聚合根
        stats = trip.generate_statistics()
        return stats.to_dict()
    
    # ==================== 状态管理 ====================
    
    def start_trip(self, trip_id: str) -> Optional[Trip]:
        """开始旅行"""
        trip = self._trip_repository.find_by_id(TripId(trip_id))
        if not trip:
            return None
        
        trip.start()
        
        self._trip_repository.save(trip)
        self._publish_events(trip)
        
        return trip
    
    def complete_trip(self, trip_id: str) -> Optional[Trip]:
        """完成旅行"""
        trip = self._trip_repository.find_by_id(TripId(trip_id))
        if not trip:
            return None
        
        trip.complete()
        
        self._trip_repository.save(trip)
        self._publish_events(trip)
        
        return trip
    
    def cancel_trip(self, trip_id: str, reason: Optional[str] = None) -> Optional[Trip]:
        """取消旅行"""
        trip = self._trip_repository.find_by_id(TripId(trip_id))
        if not trip:
            return None
        
        trip.cancel(reason)
        
        self._trip_repository.save(trip)
        self._publish_events(trip)
        
        return trip
    
    # ==================== 日程备注 ====================
    
    def update_day_notes(self, trip_id: str, day_index: int, notes: str) -> Optional[Trip]:
        """更新日程备注"""
        trip = self._trip_repository.find_by_id(TripId(trip_id))
        if not trip:
            return None
        
        trip.update_day_notes(day_index, notes)
        
        self._trip_repository.save(trip)
        self._publish_events(trip)
        
        return trip
    
    def update_day_theme(self, trip_id: str, day_index: int, theme: str) -> Optional[Trip]:
        """更新日程主题"""
        trip = self._trip_repository.find_by_id(TripId(trip_id))
        if not trip:
            return None
        
        day = trip.get_day(day_index)
        if day:
            day.update_theme(theme)
            self._trip_repository.save(trip)
        
        return trip
