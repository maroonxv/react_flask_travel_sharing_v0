from flask import Blueprint, request, jsonify, g, current_app, session
from datetime import datetime, date, time
from decimal import Decimal
import traceback

from shared.database.core import SessionLocal
from app_travel.infrastructure.database.dao_impl.sqlalchemy_trip_dao import SqlAlchemyTripDao
from app_travel.infrastructure.database.repository_impl.trip_repository_impl import TripRepositoryImpl
from app_travel.infrastructure.external_service.gaode_geo_service_impl import GaodeGeoServiceImpl
from app_travel.services.travel_service import TravelService
from app_travel.domain.aggregate.trip_aggregate import Trip
from app_travel.domain.value_objects.itinerary_value_objects import TransitCalculationResult

# 创建蓝图
travel_bp = Blueprint('travel', __name__, url_prefix='/api/travel')

# ==================== 依赖注入与会话管理 ====================

@travel_bp.before_request
def create_session():
    """每个请求开始前创建数据库会话"""
    g.session = SessionLocal()

@travel_bp.teardown_request
def shutdown_session(exception=None):
    """请求结束时关闭数据库会话"""
    if hasattr(g, 'session'):
        g.session.close()

def get_travel_service() -> TravelService:
    """获取 TravelService 实例
    
    组装依赖：
    TravelService -> TripRepositoryImpl -> SqlAlchemyTripDao -> Session
                  -> GaodeGeoServiceImpl
    """
    trip_dao = SqlAlchemyTripDao(g.session)
    trip_repo = TripRepositoryImpl(trip_dao)
    # 这里可以从配置获取 API Key，暂使用默认值
    geo_service = GaodeGeoServiceImpl()
    
    return TravelService(trip_repo, geo_service)

from app_auth.infrastructure.database.persistent_model.user_po import UserPO

# ==================== 序列化辅助函数 ====================

def serialize_trip(trip: Trip) -> dict:
    """将 Trip 聚合根序列化为字典"""
    
    # 批量获取用户信息以展示头像和用户名
    members_data = []
    if trip.members:
        user_ids = [m.user_id for m in trip.members]
        # 使用 g.session 查询 UserPO
        # 注意：UserPO 属于 auth 模块，这里跨模块查询是为了性能（避免 N+1 调用 Auth Service）
        # 在严格的微服务架构中，应该调用 AuthService 的批量接口
        try:
            users = g.session.query(UserPO).filter(UserPO.id.in_(user_ids)).all()
            user_map = {u.id: u for u in users}
        except Exception:
            # 如果查询失败，降级处理
            user_map = {}
            
        for m in trip.members:
            user = user_map.get(m.user_id)
            members_data.append({
                'user_id': m.user_id,
                'role': m.role.value,
                'nickname': m.nickname, # 这里的 nickname 是 trip 内的备注名
                'username': user.username if user else 'Unknown',
                'avatar_url': user.avatar_url if user else None
            })

    return {
        'id': trip.id.value,
        'name': trip.name.value,
        'description': trip.description.value,
        'creator_id': trip.creator_id,
        'start_date': trip.date_range.start_date.isoformat(),
        'end_date': trip.date_range.end_date.isoformat(),
        'days_count': trip.total_days,
        'budget': {
            'amount': float(trip.budget.amount),
            'currency': trip.budget.currency
        } if trip.budget else None,
        'budget_amount': float(trip.budget.amount) if trip.budget else 0, # Flat field for frontend convenience
        'visibility': trip.visibility.value,
        'status': trip.status.value,
        'created_at': trip.created_at.isoformat(),
        'updated_at': trip.updated_at.isoformat(),
        'member_count': len(trip.members), # Helper count
        'members': members_data,
        'days': [
            serialize_trip_day(day) for day in trip.days
        ]
    }

def serialize_trip_day(day) -> dict:
    """序列化 TripDay"""
    return {
        'day_index': day.day_number - 1, # 0-based
        'day_number': day.day_number, # 1-based
        'date': day.date.isoformat(),
        'weekday': day.date.weekday(), # 0=Monday
        'theme': day.theme,
        'notes': day.notes,
        'activities': [serialize_activity(a) for a in day.activities],
        'transits': [serialize_transit(t) for t in day.transits]
    }

def serialize_activity(activity) -> dict:
    """序列化 Activity"""
    return {
        'id': activity.id,
        'name': activity.name,
        'type': activity.activity_type.value,
        'start_time': activity.start_time.strftime('%H:%M'),
        'end_time': activity.end_time.strftime('%H:%M'),
        'location': {
            'name': activity.location.name,
            'latitude': activity.location.latitude,
            'longitude': activity.location.longitude,
            'address': activity.location.address
        },
        'cost': {
            'amount': float(activity.cost.amount),
            'currency': activity.cost.currency
        } if activity.cost else None,
        'notes': activity.notes
    }

def serialize_transit(transit) -> dict:
    """序列化 Transit"""
    return {
        'from_activity_id': transit.from_activity_id,
        'to_activity_id': transit.to_activity_id,
        'mode': transit.transport_mode.value,
        'distance_meters': transit.route_info.distance_meters,
        'duration_seconds': transit.route_info.duration_seconds,
        'cost': {
            'amount': float(transit.estimated_cost.estimated_cost.amount),
            'currency': transit.estimated_cost.estimated_cost.currency
        } if transit.estimated_cost else None,
        # polyline 可能很长，视前端需求决定是否返回
        'polyline': transit.route_info.polyline 
    }

def serialize_transit_result(result: TransitCalculationResult) -> dict:
    """序列化交通计算结果"""
    if not result:
        return {}
    
    return {
        'transits': [serialize_transit(t) for t in result.transits],
        'warnings': [
            {
                'type': w.type.value,
                'message': w.message,
                'related_activity_ids': w.related_activity_ids
            } for w in result.warnings
        ]
    }

# ==================== API 路由 ====================

@travel_bp.route('/trips', methods=['POST'])
def create_trip():
    """创建新旅行"""
    data = request.get_json()
    service = get_travel_service()
    
    try:
        trip = service.create_trip(
            name=data['name'],
            description=data.get('description', ''),
            creator_id=data['creator_id'],
            start_date=date.fromisoformat(data['start_date']),
            end_date=date.fromisoformat(data['end_date']),
            budget_amount=data.get('budget_amount'),
            budget_currency=data.get('budget_currency', 'CNY'),
            visibility=data.get('visibility', 'private')
        )
        g.session.commit()
        return jsonify(serialize_trip(trip)), 201
    except ValueError as e:
        print(f"Create trip ValueError: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@travel_bp.route('/trips/<trip_id>', methods=['GET'])
def get_trip(trip_id):
    """获取旅行详情"""
    service = get_travel_service()
    trip = service.get_trip(trip_id)
    
    if not trip:
        return jsonify({'error': 'Trip not found'}), 404
        
    return jsonify(serialize_trip(trip))

@travel_bp.route('/trips/<trip_id>', methods=['PUT'])
def update_trip(trip_id):
    """更新旅行基本信息"""
    data = request.get_json()
    service = get_travel_service()
    
    try:
        trip = service.update_trip(
            trip_id=trip_id,
            name=data.get('name'),
            description=data.get('description'),
            visibility=data.get('visibility'),
            budget_amount=data.get('budget_amount'),
            budget_currency=data.get('budget_currency', 'CNY')
        )
        
        if not trip:
            return jsonify({'error': 'Trip not found'}), 404
            
        g.session.commit()
        return jsonify(serialize_trip(trip))
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@travel_bp.route('/trips/<trip_id>', methods=['DELETE'])
def delete_trip(trip_id):
    """删除旅行"""
    service = get_travel_service()
    success = service.delete_trip(trip_id)
    
    if not success:
        return jsonify({'error': 'Trip not found'}), 404
        
    g.session.commit()
    return '', 204

@travel_bp.route('/trips/<trip_id>/members', methods=['POST'])
def add_member(trip_id):
    """添加成员"""
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({'error': 'user_id is required'}), 400
        
    service = get_travel_service()
    
    # 尝试从 session 获取当前用户 ID作为 added_by
    current_user_id = session.get('user_id')
    
    try:
        trip = service.add_member(
            trip_id=trip_id,
            user_id=data['user_id'],
            role=data.get('role', 'member'),
            added_by=current_user_id
        )
        
        if not trip:
            return jsonify({'error': 'Trip not found'}), 404
            
        g.session.commit()
        return jsonify(serialize_trip(trip)), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@travel_bp.route('/users/<user_id>/trips', methods=['GET'])
def list_user_trips(user_id):
    """获取用户参与的旅行"""
    status = request.args.get('status')
    service = get_travel_service()
    
    trips = service.list_user_trips(user_id, status)
    return jsonify([serialize_trip(t) for t in trips])

@travel_bp.route('/trips/public', methods=['GET'])
def list_public_trips():
    """获取公开旅行"""
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    service = get_travel_service()
    
    trips = service.list_public_trips(limit, offset)
    return jsonify([serialize_trip(t) for t in trips])

@travel_bp.route('/trips/<trip_id>/members/<user_id>', methods=['DELETE'])
def remove_member(trip_id, user_id):
    """移除成员"""
    # 简单的认证检查
    operator_id = session.get('user_id')
    if not operator_id:
        return jsonify({'error': 'Not authenticated'}), 401
        
    service = get_travel_service()
    try:
        updated_trip = service.remove_member(
            trip_id=trip_id,
            user_id=user_id,
            removed_by=operator_id
        )
        if not updated_trip:
            return jsonify({'error': 'Trip not found'}), 404
            
        g.session.commit()
        return jsonify(serialize_trip(updated_trip)), 200
    except ValueError as e:
        g.session.rollback()
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        g.session.rollback()
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500


# ==================== 活动与行程管理 (调用领域服务逻辑) ====================

@travel_bp.route('/trips/<trip_id>/days/<int:day_index>/activities', methods=['POST'])
def add_activity(trip_id, day_index):
    """添加活动
    
    会自动调用 Domain Service (ItineraryService) 计算交通和验证可行性。
    """
    data = request.get_json()
    service = get_travel_service()
    
    try:
        # 解析时间字符串 "HH:MM" -> time 对象
        start_time = time.fromisoformat(data['start_time'])
        end_time = time.fromisoformat(data['end_time'])
        
        result = service.add_activity(
            trip_id=trip_id,
            day_index=day_index,
            name=data['name'],
            activity_type=data['activity_type'],
            location_name=data['location_name'],
            start_time=start_time,
            end_time=end_time,
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            address=data.get('address'),
            cost_amount=data.get('cost_amount'),
            cost_currency=data.get('cost_currency', 'CNY'),
            notes=data.get('notes', '')
        )
        
        if result is None:
             # 可能 trip 不存在或 index 错误，TravelService 返回 None
             # 这里简单处理，实际上 TravelService 若找不到 trip 会返回 None
             # 若 index 越界会抛出 ValueError
             return jsonify({'error': 'Trip not found'}), 404

        g.session.commit()
        return jsonify(serialize_transit_result(result)), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500

@travel_bp.route('/trips/<trip_id>/days/<int:day_index>/activities/<activity_id>', methods=['PUT'])
def modify_activity(trip_id, day_index, activity_id):
    """修改活动
    
    会自动调用 Domain Service 重新计算交通。
    """
    data = request.get_json()
    service = get_travel_service()
    
    try:
        updates = data.copy()
        
        # 处理时间格式
        if 'start_time' in updates:
            updates['start_time'] = time.fromisoformat(updates['start_time'])
        if 'end_time' in updates:
            updates['end_time'] = time.fromisoformat(updates['end_time'])
            
        result = service.modify_activity(
            trip_id=trip_id,
            day_index=day_index,
            activity_id=activity_id,
            **updates
        )
        
        if result is None:
            return jsonify({'error': 'Trip or Activity not found'}), 404
            
        g.session.commit()
        return jsonify(serialize_transit_result(result))
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@travel_bp.route('/trips/<trip_id>/days/<int:day_index>/activities/<activity_id>', methods=['DELETE'])
def remove_activity(trip_id, day_index, activity_id):
    """移除活动"""
    service = get_travel_service()
    
    try:
        result = service.remove_activity(trip_id, day_index, activity_id)
        
        if result is None:
            # 可能是 Activity 不存在，或者 Trip 不存在
            # 这里如果不报错，说明可能是静默失败或无需计算交通
            return jsonify({'message': 'Activity removed (or not found)'}), 200
            
        g.session.commit()
        return jsonify(serialize_transit_result(result))
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@travel_bp.route('/trips/<trip_id>/statistics', methods=['GET'])
def get_trip_statistics(trip_id):
    """获取旅行统计报表"""
    service = get_travel_service()
    stats = service.get_trip_statistics(trip_id)
    
    if not stats:
        return jsonify({'error': 'Trip not found'}), 404
        
    return jsonify(stats)

@travel_bp.route('/locations/geocode', methods=['GET'])
def geocode_location():
    """地址解析（辅助接口）"""
    address = request.args.get('address')
    if not address:
        return jsonify({'error': 'Address required'}), 400
        
    service = get_travel_service()
    result = service.geocode_location(address)
    
    if not result:
        return jsonify({'error': 'Location not found'}), 404
        
    return jsonify(result)
