from flask import Flask
from flask_cors import CORS
import os

# 导入共享数据库配置
from shared.database.core import engine, Base

# 导入所有 PO 模块以注册到 Base
# Auth
from app_auth.infrastructure.database.persistent_model.user_po import UserPO
# Social
from app_social.infrastructure.database.persistent_model.post_po import PostPO, CommentPO, LikePO
from app_social.infrastructure.database.persistent_model.conversation_po import ConversationPO
from app_social.infrastructure.database.persistent_model.message_po import MessagePO
# Travel
from app_travel.infrastructure.database.persistent_model.trip_po import TripPO, TripMemberPO, TripDayPO, ActivityPO, TransitPO
from app_travel.view.travel_view import travel_bp
from app_social.view.social_view import social_bp
from app_auth.view.auth_view import auth_bp

def create_app():
    # 配置静态文件目录
    # static_url_path='/static' 表示 URL 前缀
    # static_folder='static' 表示实际文件夹路径（相对于 app.py 所在目录）
    app = Flask(__name__, static_url_path='/static', static_folder='static')
    CORS(app)
    
    # 确保上传目录存在
    upload_dir = os.path.join(app.static_folder, 'uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    # 初始化数据库表
    # 在实际生产环境中，建议使用 Alembic 进行数据库迁移，而不是 create_all
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized.")
    
    # 注册蓝图
    app.register_blueprint(travel_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(auth_bp)
    
    @app.route('/health')
    def health_check():
        return {'status': 'healthy'}
        
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
