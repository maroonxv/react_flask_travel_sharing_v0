from typing import List, Dict, Any, Optional
from shared.database.core import SessionLocal
from shared.event_bus import get_event_bus
from app_social.infrastructure.database.dao_impl.sqlalchemy_friendship_dao import SqlAlchemyFriendshipDao
from app_social.infrastructure.database.repository_impl.friendship_repository_impl import FriendshipRepositoryImpl
from app_social.domain.aggregate.friendship_aggregate import Friendship
from app_social.domain.value_objects.friendship_value_objects import FriendshipId, FriendshipStatus

class FriendshipService:
    def __init__(self):
        self._event_bus = get_event_bus()

    def send_friend_request(self, requester_id: str, addressee_id: str) -> Dict[str, Any]:
        session = SessionLocal()
        try:
            dao = SqlAlchemyFriendshipDao(session)
            repo = FriendshipRepositoryImpl(dao)

            # Check if relationship already exists
            existing = repo.find_by_users(requester_id, addressee_id)
            if existing:
                if existing.status == FriendshipStatus.PENDING:
                    raise ValueError("Friend request already pending.")
                if existing.status == FriendshipStatus.ACCEPTED:
                    raise ValueError("Already friends.")
                if existing.status == FriendshipStatus.BLOCKED:
                    raise ValueError("Cannot send friend request.")
                # If REJECTED, maybe allow new request? 
                # Requirement says "Create... status:Pending". 
                # If rejected, can we retry? Usually yes.
                # If so, we might need to recreate or update existing.
                # Friendship.create generated new ID. Attempting to create new one.
                # But find_by_users finds *any*.
                # If we create new one, we have multiple rows for same pair?
                # PO has unique constraint on (requester, addressee). 
                # Wait, unique constraint is `uq_friendship_requester_addressee`.
                # Directionality matters in DB constraint unique(requester, addressee)?
                # Or unique(least(a,b), greatest(a,b))? usually databases enforce strict pair unless check constraint.
                # My PO defined `UniqueConstraint('requester_id', 'addressee_id')`.
                # This implies (A, B) is different from (B, A).
                # But `Relation` value object logic and `find_by_users` logic suggested treating them as a pair.
                # If I have (A, B) REJECTED, and now A requests B again.
                # If I try to insert (A, B), it violates unique constraint if I don't delete old one or update it.
                # Or if I insert (B, A), it works?
                # Best approach: If exists, update it? Or delete old and create new?
                # Aggregate `Friendship` usually manages the lifecycle.
                # If we want to restart, maybe `friendship.restart()`? Or just create new if old is "dead".
                # Given DB constraints, upgrading existing is safer.
                if existing.status == FriendshipStatus.REJECTED:
                    # Allow retry?
                    # Ideally we should "reset" the existing aggregate request.
                    # But Aggregate doesn't have "re-request" method.
                    # I will implementing logic to delete old one and create new one if rejected?
                    # Or soft delete?
                    # Let's assume for now we reject duplicate requests if not purely new.
                    # Or better: "If rejected, allow sending new request". 
                    # Implementation: Update existing row to new ID? No, ID is PK.
                    # Update existing row to PENDING? 
                    # If I use `Friendship.create`, it makes a NEW ID.
                    # If I try to save new generic implementation, it will fail unique constraint if (A,B) exists.
                    # So I must delete the old one or update the old one.
                    # Let's choose to DELETE the old one if it is REJECTED, then create new.
                    pass
                else:
                    # If not PENDING/ACCEPTED/BLOCKED, maybe it's REJECTED?
                    # If REJECTED, we proceed to create new (and must handle DB collision).
                    # Actually, let's just create new. If DB error, we catch it.
                    # But better to handle collision explicitly.
                    pass

            friendship = Friendship.create(requester_id, addressee_id)
            
            # If we had a REJECTED one, we should probably remove it to avoid Unique Violation
            # OR we update the existing one? Updating means reuse ID.
            # `Friendship.create` returns NEW object.
            # If I want to support re-requesting, I should probably delete the old REJECTED/BLOCKED record if appropriate.
            # But BLOCKED should not be deletable by requester.
            # If REJECTED, it can be flushed.
            if existing and existing.status == FriendshipStatus.REJECTED:
                 # Delete existing PO?
                 # Repo doesn't have delete. 
                 # Let's rely on DAO or Session?
                 # Hack: session.delete(existing_po).
                 # I will just use `session.query(FriendshipPO).filter_by(id=existing.id.value).delete()`
                 # This violates DDD slightly (Service touching DB directly via Repo).
                 # Better: Add `delete` to Repository.
                 # For now, simplistic approach: raise error if exists "You have been rejected, cannot try again" (strict)
                 # VS "Allow retry". 
                 # Let's stick to strict for now to avoid complexity, unless user complained. 
                 # Wait, typical social apps allow retry after some time.
                 # I'll Assume strict for MVP: If REJECTED, cannot request again immediately? 
                 # Or maybe I just update the status of existing one?
                 # But I don't have `renew` method on Aggregate.
                 # Let's Raise Error if any relationship exists for now.
                 if existing.status == FriendshipStatus.REJECTED:
                      raise ValueError("Friend request was rejected. Cannot send again.") 

            repo.save(friendship)
            
            self._event_bus.publish_all(friendship.pop_events())
            session.commit()
            return {"friendship_id": friendship.id.value, "status": friendship.status.value}

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def accept_friend_request(self, request_id: str, operator_id: str) -> None:
        session = SessionLocal()
        try:
            dao = SqlAlchemyFriendshipDao(session)
            repo = FriendshipRepositoryImpl(dao)

            friendship = repo.find_by_id(FriendshipId(request_id))
            if not friendship:
                raise ValueError("Friend request not found.")

            friendship.accept(operator_id)
            
            repo.save(friendship)
            self._event_bus.publish_all(friendship.pop_events())
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def reject_friend_request(self, request_id: str, operator_id: str) -> None:
        session = SessionLocal()
        try:
            dao = SqlAlchemyFriendshipDao(session)
            repo = FriendshipRepositoryImpl(dao)

            friendship = repo.find_by_id(FriendshipId(request_id))
            if not friendship:
                raise ValueError("Friend request not found.")

            friendship.reject(operator_id)
            
            repo.save(friendship)
            self._event_bus.publish_all(friendship.pop_events())
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_pending_requests(self, user_id: str, type: str = 'incoming') -> List[Dict[str, Any]]:
        session = SessionLocal()
        try:
            dao = SqlAlchemyFriendshipDao(session)
            repo = FriendshipRepositoryImpl(dao)
            
            requests = repo.find_pending_requests(user_id, type)
            
            # Enrich with user info
            from app_auth.infrastructure.database.dao_impl.sqlalchemy_user_dao import SqlAlchemyUserDao
            from app_auth.infrastructure.database.repository_impl.user_repository_impl import UserRepositoryImpl
            from app_auth.domain.value_objects.user_value_objects import UserId
            
            user_dao = SqlAlchemyUserDao(session)
            user_repo = UserRepositoryImpl(user_dao)
            
            results = []
            if not requests:
                return []
                
            # Collect IDs to fetch
            target_ids = set()
            for r in requests:
                if type == 'incoming':
                    target_ids.add(r.requester_id)
                else:
                    target_ids.add(r.addressee_id)
            
            # Batch fetch
            users_map = {}
            if target_ids:
                users = user_repo.find_by_ids([UserId(uid) for uid in target_ids])
                for u in users:
                    users_map[u.id.value] = {
                        "name": u.username.value,
                        "avatar": u.profile.avatar_url
                    }
            
            for r in requests:
                target_id = r.requester_id if type == 'incoming' else r.addressee_id
                user_info = users_map.get(target_id, {})
                results.append({
                    "id": r.id.value,
                    "requester_id": r.requester_id,
                    "addressee_id": r.addressee_id,
                    "created_at": r.created_at.isoformat(),
                    "status": r.status.value,
                    "other_user": {
                        "id": target_id,
                        "name": user_info.get("name", "Unknown"),
                        "avatar": user_info.get("avatar")
                    }
                })
            return results
        finally:
            session.close()

    def get_friends(self, user_id: str) -> List[Dict[str, Any]]:
        session = SessionLocal()
        try:
            dao = SqlAlchemyFriendshipDao(session)
            repo = FriendshipRepositoryImpl(dao)
            friend_ids = repo.find_friends(user_id)
            
            if not friend_ids:
                return []
                
            # Enrich with user info
            from app_auth.infrastructure.database.dao_impl.sqlalchemy_user_dao import SqlAlchemyUserDao
            from app_auth.infrastructure.database.repository_impl.user_repository_impl import UserRepositoryImpl
            from app_auth.domain.value_objects.user_value_objects import UserId
            
            user_dao = SqlAlchemyUserDao(session)
            user_repo = UserRepositoryImpl(user_dao)
            
            users = user_repo.find_by_ids([UserId(uid) for uid in friend_ids])
            results = []
            for u in users:
                results.append({
                    "id": u.id.value,
                    "name": u.username.value,
                    "avatar": u.profile.avatar_url,
                    "bio": u.profile.bio
                })
            return results
        finally:
            session.close()

    def get_friendship_status(self, user_id: str, target_id: str) -> Dict[str, Any]:
        """Get status between two users."""
        session = SessionLocal()
        try:
            dao = SqlAlchemyFriendshipDao(session)
            repo = FriendshipRepositoryImpl(dao)
            
            friendship = repo.find_by_users(user_id, target_id)
            if not friendship:
                return {"status": None}
            
            return {
                "id": friendship.id.value,
                "status": friendship.status.value,
                "requester_id": friendship.requester_id, # Helpful to know if I sent it or they sent it
                "addressee_id": friendship.addressee_id,
                "is_requester": friendship.requester_id == user_id
            }
        finally:
            session.close()
