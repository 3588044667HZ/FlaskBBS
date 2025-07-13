# 一个flask后端的轻量化论坛

注：本论坛处于开发中，功能尚不完善

features:

- 发贴

- 编辑帖子

- 删除帖子

- 基本管理员面板

- 评论/回复评论

- 板块分类

- **所有帖子支持md语法**

  **没有实现任何点赞功能**

实现效果：

![image-20250713125715447](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20250713125715447.png)

![image-20250713125737970](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20250713125737970.png)

![image-20250713125755252](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20250713125755252.png)

![image-20250713130046312](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20250713130046312.png)

![image-20250713130111296](C:\Users\Administrator\AppData\Roaming\Typora\typora-user-images\image-20250713130111296.png)

**登录管理员页面的url:/admin/login**

**使用方法：**

1.在虚拟环境中运行：

```python
from app import create_app, db
app = create_app()
app.app_context().push()
db.drop_all()  # 删除旧表
db.create_all()  # 创建新表
```

2.添加初始分类：

```python
>>> from app.models import Category
>>> categories = ['技术讨论', '资源共享', '问题求助', '社区公告']
>>> for name in categories:
...     category = Category(name=name)
...     db.session.add(category)
...
>>> db.session.commit()
>>> exit()
```

3.直接运行run.py

注：页面渲染不正确时请尝试科学上网，因为某些css的链接可能被墙。