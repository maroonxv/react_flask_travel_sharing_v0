修改整个项目的风格

查看别人主页，查看它们发布的帖子和公开的Trip，添加好友的功能


在trip中添加一张图片


1. 增加删除自己发布的帖子的功能
2. 现在在trip_detail页面添加成员时，数据库中有更新，但是显示在前端页面上的trip成员数仍然是1，请修正
3. 现在每一个trip的预算无法显示在旅行页面和trip_detail页面，请修正
4. 添加在trip_detail页面点击成员后，弹出一个弹窗，显示所有成员的头像和名称，并且如果是该trip的admin，则可以点击删除成员按钮删除成员


1. trip_detail的成员列表弹窗中增加取消按钮，点击取消按钮后，弹窗关闭，不做任何操作
2. 现在trip_detail页面没法显示交通方式。数据库中的transits表中已经存储了交通方式，但是在前端页面上没有显示出来。修正这个问题
3. 在trip_detail的成员列表弹窗中点击用户后，可以转到该用户的个人主页


1. 在trip_detail页面的状态处，要可以修改trip的状态，总共有PLANNING, COMPLETED, CANCELLED, IN_PROGRESS四种状态
2. trip_detail的成员列表弹窗中增加取消按钮
3. 现在在trip_detail的成员列表弹窗中点击用户头像/昵称，或者在帖子处点击用户头像/昵称，都不可以转到该用户的个人主页，请修正
4. 在trip_detail页面把交通方式放在activity之间，而不是单独放在下面；而且显示中文，不要显示英文


增加管理员页面


用户在trip中添加activity后，后台自动调用travel_sharing_app_v0\backend\src\app_travel\infrastructure\external_service\gaode_geo_service_impl.py计算路径时间的功能有问题，现在路径并不能计算出来，请修正




疑问：
1. 现在帖子的评论没法显示发表评论的用户，是否需要在数据库的comment表中增加一个字段来存储评论的用户ID？现在这个表中的parent_id是做什么的？
2. 现在user表中有一个role字段，用于存储user或者admin身份，但是现在项目没有管理员页面。若要增加一个管理员页面专门用来管理数据库中的所有内容，我需要修改、增加哪些代码？
3. 


一、增加好友关系：
1. 需要新增一张关联表（friendships），通常包含以下字段：
    - requester_id (申请人)
    - addressee_id (被申请人)
    - status (状态：pending/accepted/blocked)
    - created_at (创建时间)
2. 逻辑写在 app_social中

二、若在旅行界面，每个 Trip 可以添加一张图片，需要修改数据库范式
1. backend/src/app_travel/infrastructure/database/persistent_model/trip_po.py中
2. 需要在 trips 表中增加一个字段，例如 cover_image_url (VARCHAR/String)，用于存储封面图片的链接。
3. 同时需要在 Trip 领域实体 ( trip_aggregate.py ) 和值对象中增加对应的属性。
4. 可能要修改 travel_sharing_app_v0\backend\src\shared\storage\local_file_storage.py 中的路径，与帖子的图片位置分离开

三、若要在群聊中分享帖子（用卡片形式的富文本来分析）
1. backend/src/app_social/domain/value_objects/social_value_objects.py 中的 MessageContent 类扩展 message_type 枚举，增加 post_share 类型
2. 在前后端增加相应的解析逻辑


我可以将所有的sqlalchemy_dao的实现修改为使用原始SQL，而功能不变吗？