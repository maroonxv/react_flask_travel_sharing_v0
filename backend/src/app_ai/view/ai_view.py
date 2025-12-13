from flask import request, jsonify, Response, stream_with_context, g
from app_ai import ai_bp
from shared.database.core import SessionLocal

# Dependency Injection (Manual for now)
from app_ai.infrastructure.database.dao_impl.sqlalchemy_ai_conversation_dao import SqlAlchemyAiConversationDao
from app_ai.infrastructure.database.repository_impl.ai_repository_impl import AiRepositoryImpl
from app_ai.infrastructure.retriever.sqlalchemy_mysql_retriever import SqlAlchemyMysqlRetriever
from app_ai.infrastructure.llm.langchain_deepseek_adapter import LangChainDeepSeekAdapter
from app_ai.domain.domain_service.ai_chat_domain_service import AiChatDomainService
from app_ai.services.ai_application_service import AiApplicationService

@ai_bp.before_request
def before_request():
    g.session = SessionLocal()

@ai_bp.teardown_request
def teardown_request(exception=None):
    if hasattr(g, 'session'):
        if exception is None:
            try:
                g.session.commit()
            except Exception as e:
                g.session.rollback()
                # Log error or re-raise?
        else:
            g.session.rollback()
        g.session.close()

def get_ai_service():
    # In a real app, use a DI container or app context
    # We create new instances per request scope to bind to the current db_session
    # Use g.session which is created in before_request
    if not hasattr(g, 'session'):
        # Fallback if not in request context or before_request didn't run
        g.session = SessionLocal()
        
    conversation_dao = SqlAlchemyAiConversationDao(g.session)
    repository = AiRepositoryImpl(conversation_dao)
    retriever = SqlAlchemyMysqlRetriever(g.session)
    llm_client = LangChainDeepSeekAdapter()
    domain_service = AiChatDomainService(llm_client, retriever)
    return AiApplicationService(repository, domain_service)

@ai_bp.route('/chat', methods=['POST'])
def chat():
    # Note: In production, add @login_required decorator
    # For now, we assume user_id is passed in body or headers for testing, 
    # or use a fixed one if not provided (NOT SECURE)
    data = request.json
    user_id = data.get('user_id') 
    if not user_id:
        # Try to get from g.user if auth middleware ran
        if hasattr(g, 'user') and g.user:
            user_id = g.user.id
        else:
            return jsonify({"error": "Unauthorized"}), 401
            
    query = data.get('message')
    conversation_id = data.get('conversation_id')
    
    if not query:
        return jsonify({"error": "Message is required"}), 400
        
    service = get_ai_service()
    
    return Response(
        stream_with_context(service.chat_stream(user_id, query, conversation_id)),
        mimetype='text/event-stream'
    )

@ai_bp.route('/conversations', methods=['GET'])
def list_conversations():
    # Note: Add @login_required
    user_id = request.args.get('user_id') # Temporary
    if not user_id:
         if hasattr(g, 'user') and g.user:
            user_id = g.user.id
         else:
            return jsonify({"error": "Unauthorized"}), 401
            
    service = get_ai_service()
    conversations = service.get_user_conversations(user_id)
    
    return jsonify([{
        "id": c.id,
        "title": c.title,
        "updated_at": c.updated_at.isoformat()
    } for c in conversations])

@ai_bp.route('/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    # Note: Add @login_required
    user_id = request.args.get('user_id') # Temporary
    if not user_id:
         if hasattr(g, 'user') and g.user:
            user_id = g.user.id
         else:
            return jsonify({"error": "Unauthorized"}), 401
            
    service = get_ai_service()
    conversation = service.get_conversation_detail(conversation_id, user_id)
    
    if not conversation:
        return jsonify({"error": "Not found"}), 404
        
    return jsonify({
        "id": conversation.id,
        "title": conversation.title,
        "messages": [msg.to_dict() for msg in conversation.messages]
    })
