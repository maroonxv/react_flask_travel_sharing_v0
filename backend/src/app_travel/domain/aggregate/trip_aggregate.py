"""
Trip 聚合根 - 充血模型

管理整个旅行生命周期：计划中 -> 进行中 -> 已完成/已取消
包含：日程(TripDay)、成员(TripMember)、活动(Activity)、交通(Transit)
"""
from datetime import datetime, date, timedelta
from typing import List, Optional, TYPE_CHECKING

from app_travel.domain.value_objects.travel_value_objects import (
    TripId, TripName, TripDescription, DateRange, Money,
    TripStatus, TripVisibility, MemberRole, Location
)
from app_travel.domain.entity.trip_day_entity import TripDay
from app_travel.domain.entity.trip_member import TripMember
from app_travel.domain.entity.activity import Activity
from app_travel.domain.entity.transit import Transit
from app_travel.domain.value_objects.itinerary_value_objects import (
    TransitCalculationResult, ItineraryWarning
)
from app_travel.domain.domain_event.travel_events import (
    DomainEvent, TripCreatedEvent, TripStartedEvent, TripCompletedEvent,
    TripCancelledEvent, TripUpdatedEvent, TripMemberAddedEvent,
    TripMemberRemovedEvent, TripMemberRoleChangedEvent,
    ActivityAddedEvent, ActivityRemovedEvent, ActivityUpdatedEvent, ItineraryUpdatedEvent
)

if TYPE_CHECKING:
    from app_travel.domain.domain_service.itinerary_service import ItineraryService


class Trip:
    """旅行聚合根 - 充血模型
    
    包含旅行的所有业务逻辑，管理成员、日程和活动。
    所有状态变更都通过业务方法进行，并发布相应的领域事件。
    """
    
    def __init__(
        self,
        trip_id: TripId,
        name: TripName,
        description: TripDescription,
        creator_id: str,
        date_range: DateRange,
        budget: Optional[Money] = None,
        visibility: TripVisibility = TripVisibility.PRIVATE,
        status: TripStatus = TripStatus.PLANNING,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self._id = trip_id
        self._name = name
        self._description = description
        self._creator_id = creator_id
        self._date_range = date_range
        self._budget = budget
        self._visibility = visibility
        self._status = status
        self._created_at = created_at or datetime.utcnow()
        self._updated_at = updated_at or self._created_at
        self._members: List[TripMember] = []
        self._days: List[TripDay] = []
        self._domain_events: List[DomainEvent] = []
    
    # ==================== 工厂方法 ====================
    
    @classmethod
    def create(
        cls,
        name: TripName,
        description: TripDescription,
        creator_id: str,
        date_range: DateRange,
        budget: Optional[Money] = None,
        visibility: TripVisibility = TripVisibility.PRIVATE
    ) -> 'Trip':
        """创建新旅行
        
        创建者自动成为管理员成员，并根据日期范围初始化日程。
        """
        trip = cls(
            trip_id=TripId.generate(),
            name=name,
            description=description,
            creator_id=creator_id,
            date_range=date_range,
            budget=budget,
            visibility=visibility
        )
        
        # 创建者自动成为管理员
        trip._members.append(TripMember.create_admin(creator_id))
        
        # 根据日期范围初始化日程
        trip._initialize_days()
        
        # 发布事件
        trip._add_event(TripCreatedEvent(
            trip_id=trip.id.value,
            creator_id=creator_id,
            name=name.value,
            start_date=str(date_range.start_date),
            end_date=str(date_range.end_date)
        ))
        
        return trip
    
    @classmethod
    def reconstitute(
        cls,
        trip_id: TripId,
        name: TripName,
        description: TripDescription,
        creator_id: str,
        date_range: DateRange,
        members: List[TripMember],
        days: List[TripDay],
        budget: Optional[Money] = None,
        visibility: TripVisibility = TripVisibility.PRIVATE,
        status: TripStatus = TripStatus.PLANNING,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ) -> 'Trip':
        """从持久化数据重建旅行（不发布事件）"""
        trip = cls(
            trip_id=trip_id,
            name=name,
            description=description,
            creator_id=creator_id,
            date_range=date_range,
            budget=budget,
            visibility=visibility,
            status=status,
            created_at=created_at,
            updated_at=updated_at
        )
        trip._members = members
        trip._days = days
        return trip
    
    def _initialize_days(self) -> None:
        """根据日期范围初始化日程"""
        self._days = []
        current_date = self._date_range.start_date
        day_number = 1
        
        while current_date <= self._date_range.end_date:
            self._days.append(TripDay.create(day_number, current_date))
            current_date += timedelta(days=1)
            day_number += 1
    
    # ==================== 属性访问器 ====================
    
    @property
    def id(self) -> TripId:
        return self._id
    
    @property
    def name(self) -> TripName:
        return self._name
    
    @property
    def description(self) -> TripDescription:
        return self._description
    
    @property
    def creator_id(self) -> str:
        return self._creator_id
    
    @property
    def date_range(self) -> DateRange:
        return self._date_range
    
    @property
    def budget(self) -> Optional[Money]:
        return self._budget
    
    @property
    def visibility(self) -> TripVisibility:
        return self._visibility
    
    @property
    def status(self) -> TripStatus:
        return self._status
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    @property
    def members(self) -> List[TripMember]:
        return self._members.copy()
    
    @property
    def days(self) -> List[TripDay]:
        return self._days.copy()
    
    @property
    def member_count(self) -> int:
        return len(self._members)
    
    @property
    def total_days(self) -> int:
        return len(self._days)
    
    # ==================== 成员管理 ====================
    
    def add_member(
        self,
        user_id: str,
        role: MemberRole = MemberRole.MEMBER,
        added_by: Optional[str] = None,
        nickname: Optional[str] = None
    ) -> None:
        """添加成员
        
        Args:
            user_id: 用户ID
            role: 成员角色
            added_by: 添加者ID（可选）
            nickname: 昵称（可选）
            
        Raises:
            ValueError: 用户已是成员或旅行已完成
        """
        if self._find_member(user_id):
            raise ValueError(f"User {user_id} is already a member")
        
        if self._status == TripStatus.COMPLETED:
            raise ValueError("Cannot add member to completed trip")
        
        if self._status == TripStatus.CANCELLED:
            raise ValueError("Cannot add member to cancelled trip")
        
        member = TripMember(user_id=user_id, role=role, nickname=nickname)
        self._members.append(member)
        self._updated_at = datetime.utcnow()
        
        self._add_event(TripMemberAddedEvent(
            trip_id=self._id.value,
            user_id=user_id,
            role=role.value,
            added_by=added_by or self._creator_id
        ))
    
    def remove_member(self, user_id: str, removed_by: str, reason: Optional[str] = None) -> None:
        """移除成员
        
        Args:
            user_id: 待移除的用户ID
            removed_by: 操作者ID
            reason: 移除原因（可选）
            
        Raises:
            ValueError: 权限不足、成员不存在或尝试移除创建者
        """
        operator = self._find_member(removed_by)
        if not operator or not operator.is_admin():
            raise ValueError("Only admin can remove members")
        
        if user_id == self._creator_id:
            raise ValueError("Cannot remove trip creator")
        
        member = self._find_member(user_id)
        if not member:
            raise ValueError(f"User {user_id} is not a member")
        
        self._members = [m for m in self._members if m.user_id != user_id]
        self._updated_at = datetime.utcnow()
        
        self._add_event(TripMemberRemovedEvent(
            trip_id=self._id.value,
            user_id=user_id,
            removed_by=removed_by,
            reason=reason
        ))
    
    def change_member_role(self, user_id: str, new_role: MemberRole, changed_by: str) -> None:
        """更改成员角色
        
        Args:
            user_id: 用户ID
            new_role: 新角色
            changed_by: 操作者ID
        """
        operator = self._find_member(changed_by)
        if not operator or not operator.is_admin():
            raise ValueError("Only admin can change member roles")
        
        member = self._find_member(user_id)
        if not member:
            raise ValueError(f"User {user_id} is not a member")
        
        if user_id == self._creator_id and new_role != MemberRole.ADMIN:
            raise ValueError("Cannot demote trip creator")
        
        old_role = member.role
        if new_role == MemberRole.ADMIN:
            member.promote_to_admin()
        else:
            member.demote_to_member()
        
        self._updated_at = datetime.utcnow()
        
        self._add_event(TripMemberRoleChangedEvent(
            trip_id=self._id.value,
            user_id=user_id,
            old_role=old_role.value,
            new_role=new_role.value
        ))
    
    def is_member(self, user_id: str) -> bool:
        """检查是否为成员"""
        return self._find_member(user_id) is not None
    
    def is_admin(self, user_id: str) -> bool:
        """检查是否为管理员"""
        member = self._find_member(user_id)
        return member is not None and member.is_admin()
    
    def _find_member(self, user_id: str) -> Optional[TripMember]:
        """查找成员"""
        for member in self._members:
            if member.user_id == user_id:
                return member
        return None
    
    # ==================== 日程管理 ====================
    
    def get_day(self, day_index: int) -> Optional[TripDay]:
        """获取指定日期的日程（基于0索引）"""
        if 0 <= day_index < len(self._days):
            return self._days[day_index]
        return None
    
    def get_day_by_date(self, d: date) -> Optional[TripDay]:
        """根据日期获取日程"""
        for day in self._days:
            if day.date == d:
                return day
        return None
    
    # ==================== 活动管理（分离 add 和 modify）====================
    
    def add_activity(
        self, 
        day_index: int, 
        activity: Activity,
        itinerary_service: Optional['ItineraryService'] = None
    ) -> Optional[TransitCalculationResult]:
        """添加活动到指定日期
        
        如果提供 itinerary_service，会自动计算与前一个活动之间的交通。
        
        Args:
            day_index: 日期索引（从0开始）
            activity: 活动实体
            itinerary_service: 行程服务（可选）
            
        Returns:
            TransitCalculationResult: 如果计算了交通则返回结果，否则返回 None
        """
        if day_index < 0 or day_index >= len(self._days):
            raise ValueError(f"Invalid day index: {day_index}")
        
        if self._status == TripStatus.COMPLETED:
            raise ValueError("Cannot modify completed trip")
        
        day = self._days[day_index]
        
        # 获取前一个活动（在添加新活动之前）
        prev_activity = self._get_previous_activity_for_new(day, activity)
        
        # 添加活动
        day.add_activity(activity)
        self._updated_at = datetime.utcnow()
        
        result = None
        
        # 计算与前一个活动的交通
        if itinerary_service and prev_activity:
            result = TransitCalculationResult()
            try:
                transit = itinerary_service.calculate_transit_between_two_activities(
                    prev_activity, activity
                )
                day.add_transit(transit)
                result.add_transit(transit)
                
                # 检查时间可行性
                warnings = itinerary_service.validate_itinerary_feasibility(
                    [prev_activity, activity], [transit]
                )
                for warning in warnings:
                    result.add_warning(warning)
            except Exception as e:
                result.add_warning(ItineraryWarning.unreachable(
                    prev_activity.id, activity.id, str(e)
                ))
        
        self._add_event(ActivityAddedEvent(
            trip_id=self._id.value,
            day_index=day_index,
            activity_id=activity.id,
            activity_name=activity.name
        ))
        
        return result
    
    def modify_activity(
        self,
        day_index: int,
        activity_id: str,
        itinerary_service: Optional['ItineraryService'] = None,
        **updates
    ) -> Optional[TransitCalculationResult]:
        """修改指定活动
        
        修改后重新计算：
        1. 前一个Activity -> 该Activity 的Transit
        2. 该Activity -> 后一个Activity 的Transit
        
        Args:
            day_index: 日期索引
            activity_id: 活动ID
            itinerary_service: 行程服务（可选）
            **updates: 要更新的字段
            
        Returns:
            TransitCalculationResult: 如果计算了交通则返回结果，否则返回 None
        """
        if day_index < 0 or day_index >= len(self._days):
            raise ValueError(f"Invalid day index: {day_index}")
        
        if self._status == TripStatus.COMPLETED:
            raise ValueError("Cannot modify completed trip")
        
        day = self._days[day_index]
        activity = day.find_activity(activity_id)
        
        if not activity:
            raise ValueError(f"Activity {activity_id} not found")
        
        # 记录修改前的前后活动
        prev_activity = day.get_previous_activity(activity)
        next_activity = day.get_next_activity(activity)
        
        # 更新活动
        activity.update(**updates)
        
        # 重新排序（因为时间可能变化）
        day._activities.sort(key=lambda a: a.start_time)
        
        self._updated_at = datetime.utcnow()
        
        result = None
        
        # 重新计算相关的Transit
        if itinerary_service:
            result = TransitCalculationResult()
            
            # 重新计算：前一个Activity -> 该Activity
            if prev_activity:
                day.remove_transit_between(prev_activity.id, activity_id)
                try:
                    transit = itinerary_service.calculate_transit_between_two_activities(
                        prev_activity, activity
                    )
                    day.add_transit(transit)
                    result.add_transit(transit)
                except Exception as e:
                    result.add_warning(ItineraryWarning.unreachable(
                        prev_activity.id, activity_id, str(e)
                    ))
            
            # 重新计算：该Activity -> 后一个Activity
            if next_activity:
                day.remove_transit_between(activity_id, next_activity.id)
                try:
                    transit = itinerary_service.calculate_transit_between_two_activities(
                        activity, next_activity
                    )
                    day.add_transit(transit)
                    result.add_transit(transit)
                except Exception as e:
                    result.add_warning(ItineraryWarning.unreachable(
                        activity_id, next_activity.id, str(e)
                    ))
            
            # 验证可行性
            all_activities = day.activities
            all_transits = day.transits
            warnings = itinerary_service.validate_itinerary_feasibility(
                all_activities, all_transits
            )
            for warning in warnings:
                result.add_warning(warning)
        
        
        self._add_event(ActivityUpdatedEvent(
            trip_id=self._id.value,
            day_index=day_index,
            activity_id=activity.id
        ))
        
        return result
    
    def remove_activity(
        self, 
        day_index: int, 
        activity_id: str,
        itinerary_service: Optional['ItineraryService'] = None
    ) -> Optional[TransitCalculationResult]:
        """从指定日期移除活动
        
        移除后重新计算前后活动之间的Transit。
        
        Args:
            day_index: 日期索引
            activity_id: 活动ID
            itinerary_service: 行程服务（可选）
            
        Returns:
            TransitCalculationResult: 如果计算了交通则返回结果，否则返回 None
        """
        if day_index < 0 or day_index >= len(self._days):
            raise ValueError(f"Invalid day index: {day_index}")
        
        day = self._days[day_index]
        activity = day.find_activity(activity_id)
        
        if not activity:
            return None
        
        # 记录前后活动
        prev_activity = day.get_previous_activity(activity)
        next_activity = day.get_next_activity(activity)
        
        # 移除活动（同时会移除相关Transit）
        if day.remove_activity(activity_id):
            self._updated_at = datetime.utcnow()
            
            result = None
            
            # 如果前后活动都存在，计算它们之间的新Transit
            if itinerary_service and prev_activity and next_activity:
                result = TransitCalculationResult()
                try:
                    transit = itinerary_service.calculate_transit_between_two_activities(
                        prev_activity, next_activity
                    )
                    day.add_transit(transit)
                    result.add_transit(transit)
                except Exception as e:
                    result.add_warning(ItineraryWarning.unreachable(
                        prev_activity.id, next_activity.id, str(e)
                    ))
            
            self._add_event(ActivityRemovedEvent(
                trip_id=self._id.value,
                day_index=day_index,
                activity_id=activity_id
            ))
            
            return result
        
        return None
    
    def update_day_itinerary(
        self, 
        day_index: int, 
        activities: List[Activity],
        itinerary_service: Optional['ItineraryService'] = None
    ) -> Optional[TransitCalculationResult]:
        """批量更新某日行程
        
        如果提供 itinerary_service，会自动计算所有活动之间的交通。
        
        Args:
            day_index: 日期索引
            activities: 新的活动列表
            itinerary_service: 行程服务（可选）
            
        Returns:
            TransitCalculationResult: 如果计算了交通则返回结果，否则返回 None
        """
        if day_index < 0 or day_index >= len(self._days):
            raise ValueError(f"Invalid day index: {day_index}")
        
        day = self._days[day_index]
        day.replace_activities(activities)
        self._updated_at = datetime.utcnow()
        
        result = None
        
        # 计算所有活动之间的交通
        if itinerary_service and len(activities) >= 2:
            result = itinerary_service.calculate_transits_between_activities(activities)
            # 添加所有Transit到日程
            for transit in result.transits:
                day.add_transit(transit)
        
        self._add_event(ItineraryUpdatedEvent(
            trip_id=self._id.value,
            day_index=day_index
        ))
        
        return result
    
    def update_day_notes(self, day_index: int, notes: str) -> None:
        """更新某日备注"""
        if day_index < 0 or day_index >= len(self._days):
            raise ValueError(f"Invalid day index: {day_index}")
        
        self._days[day_index].update_notes(notes)
        self._updated_at = datetime.utcnow()
    
    def _get_previous_activity_for_new(
        self, day: TripDay, new_activity: Activity
    ) -> Optional[Activity]:
        """获取新活动的前一个活动（在新活动添加之前调用）"""
        activities = day.activities
        if not activities:
            return None
        
        # 按时间排序
        sorted_activities = sorted(activities, key=lambda a: a.start_time)
        
        # 找到新活动应该插入的位置的前一个活动
        for i, a in enumerate(sorted_activities):
            if a.start_time > new_activity.start_time:
                if i > 0:
                    return sorted_activities[i - 1]
                return None
        
        # 新活动在所有活动之后
        return sorted_activities[-1] if sorted_activities else None
    
    # ==================== 状态管理 ====================
    
    def start(self) -> None:
        """开始旅行"""
        if self._status != TripStatus.PLANNING:
            raise ValueError(f"Cannot start trip with status: {self._status.value}")
        
        self._status = TripStatus.IN_PROGRESS
        self._updated_at = datetime.utcnow()
        
        self._add_event(TripStartedEvent(
            trip_id=self._id.value,
            creator_id=self._creator_id
        ))
    
    def complete(self) -> None:
        """完成旅行"""
        if self._status != TripStatus.IN_PROGRESS:
            raise ValueError(f"Cannot complete trip with status: {self._status.value}")
        
        self._status = TripStatus.COMPLETED
        self._updated_at = datetime.utcnow()
        
        self._add_event(TripCompletedEvent(
            trip_id=self._id.value,
            creator_id=self._creator_id,
            name=self._name.value
        ))
    
    def cancel(self, reason: Optional[str] = None) -> None:
        """取消旅行"""
        if self._status == TripStatus.COMPLETED:
            raise ValueError("Cannot cancel completed trip")
        
        if self._status == TripStatus.CANCELLED:
            return  # 已取消
        
        self._status = TripStatus.CANCELLED
        self._updated_at = datetime.utcnow()
        
        self._add_event(TripCancelledEvent(
            trip_id=self._id.value,
            reason=reason
        ))
    
    # ==================== 信息更新 ====================
    
    def update_name(self, new_name: TripName) -> None:
        """更新旅行名称"""
        if self._name == new_name:
            return
        
        self._name = new_name
        self._updated_at = datetime.utcnow()
        
        self._add_event(TripUpdatedEvent(
            trip_id=self._id.value,
            updated_fields=('name',)
        ))
    
    def update_description(self, new_description: TripDescription) -> None:
        """更新旅行描述"""
        self._description = new_description
        self._updated_at = datetime.utcnow()
    
    def update_visibility(self, new_visibility: TripVisibility) -> None:
        """更新可见性"""
        if self._visibility == new_visibility:
            return
        
        self._visibility = new_visibility
        self._updated_at = datetime.utcnow()
    
    def update_budget(self, new_budget: Optional[Money]) -> None:
        """更新预算"""
        self._budget = new_budget
        self._updated_at = datetime.utcnow()
    
    # ==================== 统计报表 ====================
    
    def generate_statistics(self) -> 'TripStatistics':
        """生成整个旅行的统计报表
        
        Returns:
            TripStatistics: 包含总里程、游玩时间、交通时间、花费、打卡地点
        """
        from app_travel.domain.value_objects.trip_statistics import TripStatistics
        
        total_distance = 0.0
        total_play_time = 0
        total_transit_time = 0
        activity_count = 0
        activity_cost = Money.zero()
        transit_cost = Money.zero()
        visited_locations: List[Location] = []
        
        for day in self._days:
            # 统计活动
            total_play_time += day.calculate_total_play_time()
            activity_count += len(day.activities)
            activity_cost = activity_cost + day.calculate_activity_cost()
            
            for activity in day.activities:
                visited_locations.append(activity.location)
            
            # 统计交通
            total_distance += day.calculate_total_transit_distance()
            total_transit_time += day.calculate_total_transit_time()
            transit_cost = transit_cost + day.calculate_transit_cost()
        
        return TripStatistics(
            total_distance_meters=total_distance,
            total_play_time_minutes=total_play_time,
            total_transit_time_minutes=total_transit_time,
            total_estimated_cost=activity_cost + transit_cost,
            activity_cost=activity_cost,
            transit_cost=transit_cost,
            activity_count=activity_count,
            visited_locations=visited_locations
        )
    
    # ==================== 查询方法 ====================
    
    def calculate_total_cost(self) -> Money:
        """计算旅行总花费"""
        total = Money.zero()
        for day in self._days:
            day_cost = day.calculate_total_cost()
            total = total + day_cost
        return total
    
    def is_within_budget(self) -> bool:
        """检查是否在预算内"""
        if not self._budget:
            return True
        return self.calculate_total_cost().amount <= self._budget.amount
    
    def can_be_edited_by(self, user_id: str) -> bool:
        """检查用户是否可以编辑此旅行"""
        if self._status in [TripStatus.COMPLETED, TripStatus.CANCELLED]:
            return False
        return self.is_member(user_id)
    
    # ==================== 事件管理 ====================
    
    def _add_event(self, event: DomainEvent) -> None:
        """添加领域事件到内部队列"""
        self._domain_events.append(event)
    
    def pop_events(self) -> List[DomainEvent]:
        """弹出所有待发布的领域事件"""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Trip):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        return hash(self._id.value)
    
    def __repr__(self) -> str:
        return f"Trip(id={self._id.value}, name={self._name.value}, status={self._status.value})"
