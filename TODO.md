后续步骤



3. 使用 Alembic 创建数据库迁移

4. 添加 init.py exports 以方便导入




这是一个使用领域驱动设计原则设计的项目。项目描述在  。分成app_auth, app_social和app_travel三个app，每一个app是一个限界上下文。app_auth的职责是处理用户认证和授权，包括用户注册、登录、注销、密码重置等功能，拥有user这一实体聚合根。app_auth有领域层、应用层和接口层，与前端的路由由接口层auth_view（还未搭建）负责，而不是由auth_service负责。
为了更好地搭建app_auth的应用层auth_service，请检查以下条目，并把结果告诉我，不要着急编写代码：
1. app_auth领域层的聚合根、领域服务是否足够完善，能否撑得起一个“充血模型”（而不是贫血模型）
2. app_auth定义的需求方接口是否足够完善。（目前包括Repository接口和password_hasher），是否需要新的接口？
3. app_auth定义的需求方接口在基础设施层的实现是否完整可用


我已经接受了你创建的i_email_service和console_email_service，请需要调用的地方调用i_email_service定义的能力




请根据app_auth的领域层travel_sharing_app_v0\backend\src\app_social\domain、基础设施层travel_sharing_app_v0\backend\src\app_social\infrastructure，编写app_social的应用层social_service。请注意在应用层之上还有负责前端路由的auth_view（还未搭建）。
至少负责：
1. 准备数据
	从user_repository中Fetch数据
2. 调用领域层的领域服务和聚合根，编排用户注册、登录、注销、密码重置等功能的业务逻辑
3. 持久化用户数据到数据库
4. 在领域总线上发布事务事件
5. 使用Flask 内置 Session（基于 Cookie），登录成功直接调用 session['user_id'] = user.id，让浏览器自动处理 Cookie



一、请根据app_auth的应用层travel_sharing_app_v0\backend\src\app_auth\services\auth_application_service.py，编写app_auth的接口层travel_sharing_app_v0\backend\src\app_auth\view\auth_view.py，负责处理前端路由。
注意：
1. 前端使用 React.js框架编写
2. 前后端使用RESTful API进行通信

二、请将app_auth的蓝图注册到travel_sharing_app_v0\backend\src\app.py



在travel_sharing_app_v0\backend\tests\integration\application_service\test_auth_service_int.py（现在为空）中用pytest撰写针对travel_sharing_app_v0\backend\src\app_auth\services\auth_application_service.py的覆盖率很高的测试，并根据测试结果修改travel_sharing_app_v0\backend\src\app_auth\services\auth_application_service.py。禁止在测试不通过时修改测试代码使其通过（这是先射箭再画靶子的愚蠢行为），取而代之的是你应该修改被测试的代码travel_sharing_app_v0\backend\src\app_auth\services\auth_application_service.py



在travel_sharing_app_v0\backend\tests\integration\view\test_auth_view.py（现在为空）中用pytest撰写针对travel_sharing_app_v0\backend\src\app_auth\view\auth_view.py的覆盖率很高的测试，并根据测试结果修改travel_sharing_app_v0\backend\src\app_auth\view\auth_view.py。禁止在测试不通过时修改测试代码使其通过（这是先射箭再画靶子的愚蠢行为），取而代之的是你应该修改被测试的代码travel_sharing_app_v0\backend\src\app_auth\view\auth_view.py。测试中要验证auth_view作为接口层使用RESTful API与React前端进行交互的能力
用虚拟环境中的python（travel_sharing_app_v0\backend\.venv\Scripts\python.exe）来运行



在travel_sharing_app_v0\backend\tests\integration\view\test_travel_view.py（现在为空）中用pytest撰写针对travel_sharing_app_v0\backend\src\app_travel\view\travel_view.py的覆盖率很高的测试，并根据测试结果修改travel_sharing_app_v0\backend\src\app_travel\view\travel_view.py。禁止在测试不通过时修改测试代码使其通过（这是先射箭再画靶子的愚蠢行为），取而代之的是你应该修改被测试的代码travel_sharing_app_v0\backend\src\app_travel\view\travel_view.py。测试中要验证travel_view作为接口层使用RESTful API与React前端进行交互的能力
用虚拟环境中的python（travel_sharing_app_v0\backend\.venv\Scripts\python.exe）来运行




接下来，我要搭建整个项目的React.js前端部分了。请根据目前项目已实现的代码，帮我完善以下提示词，要求细致地描述每个页面的功能以及美学风格（我希望使用暗色系，但是颜色可以丰富一点）

注意只是完善以下提示词，不是执行以下提示词：

提示词：“这是一个使用领域驱动设计原则设计的项目。项目描述在  。分成app_auth, app_social和app_travel三个app，每一个app是一个限界上下文。请编写整个项目的React.js前端页面，前端与后端通过RESTful API进行通信。
要求：
......“
