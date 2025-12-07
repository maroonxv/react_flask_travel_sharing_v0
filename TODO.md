后续步骤



3. 使用 Alembic 创建数据库迁移

4. 添加 init.py exports 以方便导入







1. 在 travel_sharing_app_v0\backend\tests\integration\view\test_social_view.py（现在为空） 中为 travel_sharing_app_v0\backend\src\app_social\view\social_view.py 撰写覆盖率很高的集成测试。在测试不通过的时候，不要修改测试代码使得测试通过（这是极其愚蠢的先射箭后画靶子的行为），而是要修改被测试的代码使得测试通过