from flask import Blueprint, request, jsonify, g, session
from sqlalchemy.exc import IntegrityError
import datetime
from decimal import Decimal

from shared.database.core import SessionLocal
from app_admin.registry import get_model_class
from app_admin.dao import AdminGenericDao
from app_auth.infrastructure.database.persistent_model.user_po import UserPO

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.before_request
def before_request():
    """会话创建与权限检查"""
    g.session = SessionLocal()
    
    # 1. 检查登录
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized: Please login first'}), 401
    
    # 2. 检查 Admin 权限
    # 注意：这里直接查库，确保安全性
    user = g.session.get(UserPO, user_id)
    if not user:
        return jsonify({'error': 'Unauthorized: User not found'}), 401
        
    if user.role != 'admin':
        return jsonify({'error': 'Forbidden: Admin access required'}), 403

@admin_bp.teardown_request
def teardown_request(exception=None):
    """关闭会话"""
    if hasattr(g, 'session'):
        g.session.close()

def _serialize(obj):
    """将 SQLAlchemy 对象序列化为字典"""
    if obj is None:
        return None
    
    data = {}
    # 遍历所有列
    for c in obj.__table__.columns:
        val = getattr(obj, c.name)
        # 处理时间格式
        if isinstance(val, (datetime.datetime, datetime.date, datetime.time)):
            val = val.isoformat()
        # 处理 Decimal 类型
        elif isinstance(val, Decimal):
            val = float(val)
        data[c.name] = val
    return data

@admin_bp.route('/<string:resource_name>', methods=['GET'])
def get_list(resource_name):
    """分页获取列表"""
    model_class = get_model_class(resource_name)
    if not model_class:
        return jsonify({'error': f'Resource {resource_name} not found'}), 404
        
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    dao = AdminGenericDao(g.session)
    items, total = dao.get_list(model_class, page, per_page)
    
    return jsonify({
        'data': [_serialize(item) for item in items],
        'meta': {
            'page': page,
            'per_page': per_page,
            'total': total
        }
    })

@admin_bp.route('/<string:resource_name>/<string:id>', methods=['GET'])
def get_detail(resource_name, id):
    """获取详情"""
    model_class = get_model_class(resource_name)
    if not model_class:
        return jsonify({'error': f'Resource {resource_name} not found'}), 404
        
    dao = AdminGenericDao(g.session)
    item = dao.get_by_id(model_class, id)
    
    if not item:
        return jsonify({'error': 'Not found'}), 404
        
    return jsonify(_serialize(item))

@admin_bp.route('/<string:resource_name>', methods=['POST'])
def create(resource_name):
    """创建记录"""
    model_class = get_model_class(resource_name)
    if not model_class:
        return jsonify({'error': f'Resource {resource_name} not found'}), 404
        
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    dao = AdminGenericDao(g.session)
    try:
        item = dao.create(model_class, data)
        g.session.commit()
        return jsonify(_serialize(item)), 201
    except IntegrityError as e:
        g.session.rollback()
        return jsonify({'error': f'Database integrity error: {str(e.orig)}'}), 400
    except Exception as e:
        g.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/<string:resource_name>/<string:id>', methods=['PUT'])
def update(resource_name, id):
    """更新记录"""
    model_class = get_model_class(resource_name)
    if not model_class:
        return jsonify({'error': f'Resource {resource_name} not found'}), 404
        
    data = request.get_json()
    dao = AdminGenericDao(g.session)
    
    try:
        item = dao.update(model_class, id, data)
        if not item:
            return jsonify({'error': 'Not found'}), 404
            
        g.session.commit()
        return jsonify(_serialize(item))
    except IntegrityError as e:
        g.session.rollback()
        return jsonify({'error': f'Database integrity error: {str(e.orig)}'}), 400
    except Exception as e:
        g.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/<string:resource_name>/<string:id>', methods=['DELETE'])
def delete(resource_name, id):
    """删除记录"""
    model_class = get_model_class(resource_name)
    if not model_class:
        return jsonify({'error': f'Resource {resource_name} not found'}), 404
        
    dao = AdminGenericDao(g.session)
    try:
        success = dao.delete(model_class, id)
        if not success:
            return jsonify({'error': 'Not found'}), 404
            
        g.session.commit()
        return jsonify({'message': 'Deleted successfully'})
    except IntegrityError as e:
        g.session.rollback()
        return jsonify({'error': 'Cannot delete: record is referenced by others'}), 400
    except Exception as e:
        g.session.rollback()
        return jsonify({'error': str(e)}), 500
