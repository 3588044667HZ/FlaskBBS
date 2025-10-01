from datetime import datetime

from flask import url_for
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager


# 权限常量
class Permissions:
    VIEW = 1 << 0  # 1 (二进制: 0001) - 查看内容
    POST = 1 << 1  # 2 (二进制: 0010) - 发布帖子
    COMMENT = 1 << 2  # 4 (二进制: 0100) - 发布评论
    EDIT_OWN = 1 << 3  # 8 (二进制: 1000) - 编辑自己内容
    EDIT_ANY = 1 << 4  # 16 (二进制: 10000) - 编辑任何内容
    DELETE_OWN = 1 << 5  # 32 (二进制: 100000) - 删除自己内容
    DELETE_ANY = 1 << 6  # 64 (二进制: 1000000) - 删除任何内容
    MODERATE = 1 << 7  # 128 (二进制: 10000000) - 管理内容
    MANAGE_USERS = 1 << 8  # 256 (二进制: 100000000) - 管理用户
    ADMIN = 1 << 9  # 512 (二进制: 1000000000) - 管理员权限

    # 预定义角色
    USER = VIEW | POST | COMMENT | EDIT_OWN | DELETE_OWN
    MODERATOR = USER | EDIT_ANY | DELETE_ANY | MODERATE
    ADMINISTRATOR = 0xFFFF  # 所有权限


class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    posts = db.relationship('Post', backref='category', lazy=True)  # 从Post里能查到分类,Post.category


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    # is_admin = db.Column(db.Boolean, default=False)
    about_me = db.Column(db.Text)
    avatar = db.Column(db.String(120), default='default.jpg')  # 头像
    # 使用整数存储权限掩码
    permissions = db.Column(db.Integer, default=Permissions.USER)
    # 统一关系命名
    posts = db.relationship('Post', backref='author', lazy='dynamic')  # 在Post处能查到作者，用法：Post.author

    # sessions = db.relationship('Session', backref='participate', lazy='dynamic')

    # sessions = db.relationship('Session', backref='author', lazy='dynamic')
    @property
    def sessions(self):
        return Session.query.filter((Session.user1_id == self.id) | (Session.user2_id == self.id))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar_url(self):
        return url_for('static', filename=f'profile_pics/{self.avatar}', _external=True)

    def set_username(self, user_name):
        self.username = user_name

    def set_email(self, email):
        self.email = email

    # 权限检查方法
    def has_permission(self, permission):
        """检查用户是否拥有指定权限"""
        return (self.permissions & permission) == permission

    def is_admin(self):
        """检查用户是否是管理员"""
        return self.has_permission(Permissions.ADMIN)

    def add_permission(self, permission):
        """添加权限"""
        if not self.has_permission(permission):
            self.permissions |= permission

    def remove_permission(self, permission):
        """移除权限"""
        if self.has_permission(permission):
            self.permissions &= ~permission

    def __repr__(self):
        return f'<User {self.username}>'


class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    views = db.Column(db.Integer, default=0)  # 浏览量

    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 对应user.id
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))  # 对应category.id

    # 评论关系
    comments = db.relationship('Comment', backref='post', lazy='select')  # post.comment查到所有评论
    # author = db.relationship('User', backref='author', lazy='dynamic',
    #                          cascade='all, delete-orphan')  # post.author查到作者
    # 添加一个实际字段存储评论计数
    _comment_count = db.Column('comment_count', db.Integer, default=0)

    # 评论计数属性
    @property
    def comment_count(self):
        return self._comment_count

    @comment_count.setter
    def comment_count(self, value):
        self._comment_count = value

    def __repr__(self):
        return f'<Post {self.title}>'


class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    author_username = db.Column(db.String(64), nullable=False)  # 新增字段
    # 外键
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    # comment_author = db.relationship('User', backref='comment_author', lazy='dynamic',
    #                                  cascade='all, delete-orphan')  # Comment.author查到作者
    # comment_author_name = db.Column(db.Integer, db.ForeignKey('user.username'), nullable=False)
    author = db.relationship('User', backref='author', lazy='select')
    replies = db.relationship(
        'Comment',
        backref=db.backref('parent', remote_side=[id]),
        lazy='select',
        cascade='all, delete-orphan'
    )

    # # 简化关系定义，使用反向引用
    # parent_id = db.relationship('Comment', backref="comment.id")

    @property
    def reply_count(self):
        return self.replies.count()

    def __repr__(self):
        # 使用统一的反向引用名称
        return f'<Comment {self.id} by {self.author.username}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Message(db.Model):  # 消息模型
    tablename = 'message'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 外键关系
    # sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # session_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')

    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)

    session = db.relationship('Session', back_populates='messages', foreign_keys=[session_id])

    def __repr__(self):
        return f'<Message {self.id} from {self.sender_id}>'


class Session(db.Model):  # 会话记录的模型
    __tablename__ = 'session'
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联两个用户（一对一对话）
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # 最后一条消息的ID，用于快速获取最新消息
    last_message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)

    # 关系定义
    user1 = db.relationship('User', foreign_keys=[user1_id, ], backref='conversations_as_user1')
    user2 = db.relationship('User', foreign_keys=[user2_id, ], backref='conversations_as_user2')
    # 调用方式：User.conversations_as_user1
    # User.conversations_as_user2
    last_message = db.relationship('Message', foreign_keys=[last_message_id])
    messages = db.relationship('Message', back_populates='session', lazy='dynamic',
                               foreign_keys='Message.session_id',  # 明确指定外键
                               order_by='Message.created_at.desc()',
                               cascade='all, delete-orphan')

    # 唯一约束，确保同一对用户只有一个对话
    __table_args__ = (
        db.UniqueConstraint('user1_id', 'user2_id', name='unique_conversation_pair'),
    )

    def get_other_user(self, current_user):
        """获取对话中的另一个用户"""
        if current_user.id == self.user1_id:
            return self.user2
        else:
            return self.user1

    @classmethod
    def find_or_create(cls, user1_id, user2_id):
        """查找或创建两个用户之间的对话"""
        # 确保 user1_id 总是较小的那个，避免重复对话
        uid1, uid2 = sorted([user1_id, user2_id])

        conversation = cls.query.filter_by(
            user1_id=uid1,
            user2_id=uid2
        ).first()

        if not conversation:
            conversation = cls(user1_id=uid1, user2_id=uid2)
            db.session.add(conversation)
            db.session.commit()

        return conversation

    def __repr__(self):
        return f'<Conversation {self.user1_id}-{self.user2_id}>'
