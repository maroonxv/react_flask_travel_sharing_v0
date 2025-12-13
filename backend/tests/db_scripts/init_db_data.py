import sys
import os
import random
import uuid
from datetime import datetime, timedelta, date, time

# Add backend/src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
# current_dir: .../backend/tests/db_scripts
# up1: .../backend/tests
# up2: .../backend
backend_dir = os.path.dirname(os.path.dirname(current_dir))
backend_src = os.path.join(backend_dir, 'src')
sys.path.append(backend_src)
print(f"Added {backend_src} to sys.path")

from app import create_app
from shared.database.core import engine, SessionLocal, Base
from app_auth.infrastructure.external_service.password_hasher_impl import PasswordHasherImpl
from app_auth.domain.value_objects.user_value_objects import Password, UserRole
from app_social.domain.value_objects.friendship_value_objects import FriendshipStatus
from app_social.domain.value_objects.social_value_objects import PostVisibility, ConversationType, ConversationRole
from app_travel.domain.value_objects.travel_value_objects import TripStatus, TripVisibility, MemberRole
import json

# Import POs
from app_auth.infrastructure.database.persistent_model.user_po import UserPO
from app_social.infrastructure.database.persistent_model.post_po import PostPO, CommentPO, LikePO, PostImagePO, PostTagPO
from app_social.infrastructure.database.persistent_model.conversation_po import ConversationPO, conversation_participants
from app_social.infrastructure.database.persistent_model.message_po import MessagePO
from app_social.infrastructure.database.po.friendship_po import FriendshipPO
from app_travel.infrastructure.database.persistent_model.trip_po import TripPO, TripMemberPO, TripDayPO, ActivityPO, TransitPO
from app_ai.infrastructure.database.persistent_model.ai_po import AiConversationPO, AiMessagePO

def generate_uuid():
    return str(uuid.uuid4())

def init_data():
    print("Initializing database with mock data...")
    session = SessionLocal()
    hasher = PasswordHasherImpl()
    
    try:
        # 1. Clear existing data (Optional, be careful in prod)
        # For this script, we assume we want to add data, but to avoid duplicates, 
        # we might want to check if users exist or just append.
        # Let's clean up for a fresh start since this is a test script.
        print("Cleaning up old data...")
        session.query(AiMessagePO).delete()
        session.query(AiConversationPO).delete()
        session.query(PostImagePO).delete()
        session.query(PostTagPO).delete()
        session.query(CommentPO).delete()
        session.query(LikePO).delete()
        session.query(PostPO).delete()
        session.query(MessagePO).delete()
        session.execute(conversation_participants.delete())
        session.query(ConversationPO).delete()
        session.query(FriendshipPO).delete()
        session.query(ActivityPO).delete()
        session.query(TransitPO).delete()
        session.query(TripDayPO).delete()
        session.query(TripMemberPO).delete()
        session.query(TripPO).delete()
        session.query(UserPO).delete()
        session.commit()

        # 2. Create Users
        print("Creating users...")
        users = []
        user_data = [
            {"username": "travel_lover", "email": "lover@test.com", "bio": "热爱旅行，走遍世界", "location": "Beijing"},
            {"username": "photo_master", "email": "photo@test.com", "bio": "用镜头记录美好", "location": "Shanghai"},
            {"username": "foodie_jenny", "email": "jenny@test.com", "bio": "唯有美食与爱不可辜负", "location": "Guangzhou"},
            {"username": "backpacker_tom", "email": "tom@test.com", "bio": "穷游背包客", "location": "Shenzhen"},
            {"username": "nature_hiker", "email": "hiker@test.com", "bio": "大自然搬运工", "location": "Chengdu"},
            {"username": "city_walker", "email": "walker@test.com", "bio": "城市漫步者", "location": "Hangzhou"},
            {"username": "history_buff", "email": "history@test.com", "bio": "追寻历史的足迹", "location": "Xi'an"},
            {"username": "beach_boy", "email": "beach@test.com", "bio": "阳光沙滩海浪", "location": "Sanya"},
        ]

        default_password = hasher.hash(Password("password123"))

        for data in user_data:
            user = UserPO(
                id=generate_uuid(),
                username=data["username"],
                email=data["email"],
                hashed_password=default_password.value,
                bio=data["bio"],
                location=data["location"],
                is_active=True,
                is_email_verified=True,
                role=UserRole.USER.value,
                created_at=datetime.utcnow()
            )
            session.add(user)
            users.append(user)
        
        session.commit()
        print(f"Created {len(users)} users.")

        # 3. Create Friendships
        print("Creating friendships...")
        # Make a circle of friends + some random connections
        existing_pairs = set()

        def add_friendship(requester_id, addressee_id, status):
            pair = (requester_id, addressee_id)
            if pair in existing_pairs:
                return
            
            f = FriendshipPO(id=generate_uuid(), requester_id=requester_id, addressee_id=addressee_id, status=status)
            session.add(f)
            existing_pairs.add(pair)

        for i in range(len(users)):
            # Follow the next person
            next_user = users[(i + 1) % len(users)]
            add_friendship(users[i].id, next_user.id, FriendshipStatus.ACCEPTED)
            
            # Follow the previous person
            prev_user = users[(i - 1) % len(users)]
            add_friendship(users[i].id, prev_user.id, FriendshipStatus.ACCEPTED)
            
            # Random follow
            rand_user = random.choice(users)
            if rand_user.id != users[i].id:
                 add_friendship(users[i].id, rand_user.id, FriendshipStatus.PENDING)

        session.commit()

        # 4. Create Posts
        print("Creating posts...")
        
        destinations = {
            "dunhuang": {
                "name": "敦煌",
                "images": ["dunhuang1.jpg", "dunhuang2.jpg", "dunhuang3.jpg", "dunhuang4.jpg"],
                "texts": [
                    ("千年莫高窟，梦回丝绸之路", "莫高窟的壁画真是太震撼了，每一幅画都在诉说着千年的故事。站在洞窟前，仿佛能听到历史的回响。#敦煌 #莫高窟 #历史"),
                    ("鸣沙山月牙泉，大漠孤烟直", "爬上鸣沙山看日落，金黄色的沙丘延绵不绝。月牙泉静静地躺在沙漠怀抱中，真是沙漠之眼。#鸣沙山 #月牙泉"),
                    ("西出阳关无故人", "来到阳关遗址，感受古人的离别之情。大漠戈壁，苍凉而壮阔。"),
                    ("敦煌夜市的美食", "晚上的敦煌夜市好热闹，驴肉黄面、杏皮水都超级好吃！强烈推荐！#美食 #敦煌夜市")
                ]
            },
            "shanghai": {
                "name": "上海",
                "images": ["shanghai1.avif", "shanghai2.webp", "shanghai3.jpg", "shanghai4.jpg"],
                "texts": [
                    ("外滩的夜景，魔都繁华", "站在外滩看对面的陆家嘴三件套，灯光璀璨，不愧是魔都。江风吹拂，非常惬意。#上海 #外滩 #夜景"),
                    ("武康路Citywalk", "梧桐树下的老洋房，每一栋都有故事。在武康大楼前打个卡，喝杯咖啡，享受午后时光。#Citywalk #武康路"),
                    ("豫园的传统与现代", "豫园的灯会依然那么美，九曲桥上人山人海。传统园林与现代城市的完美融合。"),
                    ("上海迪士尼童话之旅", "在迪士尼度过了神奇的一天，烟花秀太感动了！每个人在这里都能变回孩子。#迪士尼")
                ]
            },
            "zhangjiajie": {
                "name": "张家界",
                "images": ["zhangjiajie1.jpg", "zhangjiajie2.jpg", "zhangjiajie3.webp", "zhangjiajie4.jpg"],
                "texts": [
                    ("阿凡达哈利路亚山原型", "终于见到了传说中的乾坤柱，云雾缭绕，真的像悬浮在空中一样。大自然的鬼斧神工！#张家界 #阿凡达"),
                    ("天门山999级天梯", "爬上天门洞真的需要体力，但是上面的风景值了！翼装飞行表演太刺激了。"),
                    ("金鞭溪的清凉", "漫步在金鞭溪，溪水潺潺，猴子在树上跳来跳去。这里是天然的大氧吧。"),
                    ("玻璃栈道挑战", "走在悬崖峭壁上的玻璃栈道，腿都软了。但是脚下的深渊景色绝美。#挑战自我")
                ]
            },
            "hongkong": {
                "name": "香港",
                "images": ["hongkong1.jpg", "hongkong2.jpg", "hongkong3.jpg", "hongkong4.jpg"],
                "texts": [
                    ("维多利亚港的璀璨", "坐天星小轮游维港，两岸的摩天大楼灯火通明。这就是东方之珠的魅力。#香港 #维多利亚港"),
                    ("旺角街头，港风满满", "走在旺角的街道上，满眼的霓虹灯牌，仿佛置身于港片场景中。咖喱鱼蛋和鸡蛋仔必吃！"),
                    ("太平山顶俯瞰全港", "坐缆车上太平山顶，整个香港尽收眼底。白天的繁忙与夜晚的辉煌都令人着迷。"),
                    ("中环的叮叮车", "坐上古老的叮叮车，穿梭在现代化的中环，感受时间的交错。#叮叮车")
                ]
            }
        }

        posts = []
        user_index = 0
        
        for city_key, data in destinations.items():
            images = data["images"]
            texts = data["texts"]
            
            for i in range(4):
                # Assign a user cyclically
                author = users[user_index % len(users)]
                user_index += 1
                
                title, content = texts[i]
                image_file = images[i]
                
                post = PostPO(
                    id=generate_uuid(),
                    author_id=author.id,
                    title=title,
                    text=content,
                    visibility=PostVisibility.PUBLIC.value,
                    created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
                )
                session.add(post)
                posts.append(post)
                
                # Add Image
                # Note: In real app, uploads/post_images/filename
                img_url = f"/static/uploads/post_images/{image_file}"
                post_img = PostImagePO(
                    post_id=post.id,
                    image_url=img_url,
                    display_order=0
                )
                session.add(post_img)
                
                # Update JSON fields for consistency
                post.images_json = json.dumps([img_url])
                
                # Add Tags (Simple extraction from text)
                tag_list = []
                if "#" in content:
                    tags = [t.strip() for t in content.split("#") if t.strip()]
                    # First part is text, subsequent are tags
                    for tag_text in tags[1:]: 
                        # Clean up tag text (take first word)
                        tag_clean = tag_text.split()[0]
                        tag = PostTagPO(post_id=post.id, tag=tag_clean)
                        session.add(tag)
                        tag_list.append(tag_clean)
                else:
                    # Default tag based on city
                    tag = PostTagPO(post_id=post.id, tag=data["name"])
                    session.add(tag)
                    tag_list.append(data["name"])
                
                post.tags_json = json.dumps(tag_list)

        session.commit()
        print(f"Created {len(posts)} posts.")

        # 5. Add Likes and Comments
        print("Adding interactions...")
        for post in posts:
            # Random likes
            num_likes = random.randint(0, len(users))
            likers = random.sample(users, num_likes)
            for liker in likers:
                like = LikePO(user_id=liker.id, post_id=post.id)
                session.add(like)
            
            # Random comments
            num_comments = random.randint(0, 5)
            commenters = random.sample(users, min(num_comments, len(users)))
            comments_pool = ["太美了！", "想去！", "拍得真好", "羡慕", "下次一起去", "这是哪里呀？", "收藏了"]
            
            for commenter in commenters:
                comment = CommentPO(
                    id=generate_uuid(),
                    post_id=post.id,
                    author_id=commenter.id,
                    content=random.choice(comments_pool),
                    created_at=datetime.utcnow()
                )
                session.add(comment)
        
        session.commit()

        # 6. Create Trips
        print("Creating trips...")
        trip = TripPO(
            id=generate_uuid(),
            name="我的国庆之旅",
            description="计划去北京玩几天",
            creator_id=users[0].id,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=15),
            visibility=TripVisibility.PUBLIC.value,
            status=TripStatus.PLANNING.value,
            budget_amount=5000,
            cover_image_url="/static/uploads/post_images/dunhuang1.jpg" # Reuse image
        )
        session.add(trip)
        
        # Add members
        tm1 = TripMemberPO(trip_id=trip.id, user_id=users[0].id, role=MemberRole.ADMIN.value, nickname="队长")
        tm2 = TripMemberPO(trip_id=trip.id, user_id=users[1].id, role=MemberRole.MEMBER.value, nickname="摄影师")
        session.add(tm1)
        session.add(tm2)
        
        # Add Day
        day1 = TripDayPO(trip_id=trip.id, day_number=1, date=trip.start_date, theme="到达")
        session.add(day1)
        session.flush() # get day id
        
        # Add Activity
        act1 = ActivityPO(
            id=generate_uuid(),
            trip_day_id=day1.id,
            name="入住酒店",
            activity_type="accommodation",
            location_name="北京饭店",
            start_time=time(14, 0),
            end_time=time(15, 0)
        )
        session.add(act1)
        
        session.commit()

        # 7. Create Conversations
        print("Creating conversations...")
        # Chat between user 0 and 1
        u1 = users[0]
        u2 = users[1]
        
        conv = ConversationPO(
            id=generate_uuid(),
            conversation_type=ConversationType.PRIVATE.value,
            created_at=datetime.utcnow()
        )
        session.add(conv)
        session.flush() # ensure conv.id is available

        # Add participants
        stmt = conversation_participants.insert().values([
            {'conversation_id': conv.id, 'user_id': u1.id, 'role': ConversationRole.MEMBER.value},
            {'conversation_id': conv.id, 'user_id': u2.id, 'role': ConversationRole.MEMBER.value}
        ])
        session.execute(stmt)

        # Let's just create a message
        msg1 = MessagePO(
            id=generate_uuid(),
            conversation_id=conv.id,
            sender_id=u1.id,
            content_text="你好啊，最近去哪里玩了？",
            message_type="text",
            sent_at=datetime.utcnow()
        )
        msg2 = MessagePO(
            id=generate_uuid(),
            conversation_id=conv.id,
            sender_id=u2.id,
            content_text="刚从上海回来，照片发你了。",
            message_type="text",
            sent_at=datetime.utcnow() + timedelta(seconds=10)
        )
        session.add(msg1)
        session.add(msg2)
        
        session.commit()
        
        print("Database initialization completed successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    init_data()
