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

<img width="1904" height="905" alt="image-20250713125715447" src="https://github.com/user-attachments/assets/bef83131-14e0-4acc-8cba-ff12ab66dca9" />
<img width="1914" height="901" alt="image-20250713125737970" src="https://github.com/user-attachments/assets/ccf746c6-5189-4734-81ba-037f3c382326" />
<img width="1820" height="707" alt="image-20250713125755252" src="https://github.com/user-attachments/assets/e683ebe3-f172-4e60-8023-cbe6f44bcf30" />
<img width="1901" height="890" alt="image-20250713130046312" src="https://github.com/user-attachments/assets/73927dc8-9a11-45a8-bcd6-219ebbddda45" />
<img width="1893" height="892" alt="image-20250713130111296" src="https://github.com/user-attachments/assets/e8191707-6b27-4b84-857f-10643269a348" />
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

管理员账号创建教程：打开app.db找到user表permissions字段改成65535