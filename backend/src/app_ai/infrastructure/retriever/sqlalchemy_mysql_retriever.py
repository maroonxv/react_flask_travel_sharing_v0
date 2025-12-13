from typing import List
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app_ai.domain.demand_interface.i_retriever import IRetriever
from app_ai.domain.value_objects.retrieved_document import RetrievedDocument
from app_travel.infrastructure.database.persistent_model.trip_po import ActivityPO
from app_social.infrastructure.database.persistent_model.post_po import PostPO

class SqlAlchemyMysqlRetriever(IRetriever):
    def __init__(self, session: Session):
        self.session = session

    def search(self, query: str, limit: int = 5) -> List[RetrievedDocument]:
        documents = []
        
        # 1. Search Activities (App Travel)
        # Simple keyword matching on name, location, and type
        activities = self.session.query(ActivityPO).filter(
            or_(
                ActivityPO.name.like(f'%{query}%'),
                ActivityPO.location_name.like(f'%{query}%'),
                ActivityPO.activity_type.like(f'%{query}%')
            )
        ).limit(limit).all()
        
        for act in activities:
            content = f"Name: {act.name}\nType: {act.activity_type}\nLocation: {act.location_name} ({act.location_address or ''})\nNotes: {act.notes or 'None'}"
            documents.append(RetrievedDocument(
                content=content,
                source_type="activity",
                reference_id=act.id,
                title=act.name,
                score=1.0 # Simple match, no scoring yet
            ))
            
        # 2. Search Posts (App Social)
        # Simple keyword matching on title and text
        posts = self.session.query(PostPO).filter(
            or_(
                PostPO.title.like(f'%{query}%'),
                PostPO.text.like(f'%{query}%')
            ),
            PostPO.is_deleted == False,
            PostPO.visibility == 'public'
        ).limit(limit).all()
        
        for post in posts:
            # Truncate text to avoid context window overflow
            text_preview = post.text[:500] + "..." if len(post.text) > 500 else post.text
            content = f"Title: {post.title}\nContent: {text_preview}"
            documents.append(RetrievedDocument(
                content=content,
                source_type="post",
                reference_id=post.id,
                title=post.title,
                score=1.0
            ))
            
        return documents[:limit]
