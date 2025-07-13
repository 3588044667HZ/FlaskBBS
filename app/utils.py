# app/utils.py
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app import db
from app.models import Post, Comment


class CustomPagination:
    def __init__(self, items, page, per_page, total):
        self.items = items
        self.page = page
        self.per_page = per_page
        self.total = total
        self.pages = (total + per_page - 1) // per_page
        self.has_prev = page > 1
        self.has_next = page < self.pages
        self.prev_num = page - 1 if self.has_prev else None
        self.next_num = page + 1 if self.has_next else None

    def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
        # 实现与 Flask-SQLAlchemy 相同的分页迭代器
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
                    (self.page - left_current - 1 < num < self.page + right_current) or \
                    num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num


def create_posts_with_comment_count(pagination, category=None):
    """将查询结果转换为带有评论计数的 Post 对象列表"""
    posts = []
    for post, comment_count_val in pagination.items:
        new_post = Post(
            id=post.id,
            title=post.title,
            content=post.content,
            created_at=post.created_at,
            last_updated=post.last_updated,
            views=post.views,
            user_id=post.user_id,
            category_id=post.category_id,
            _comment_count=comment_count_val,
            author=post.author
        )

        # 保留关联对象
        # new_post.author = user or post.author
        new_post.category = category or post.category
        posts.append(new_post)

    return CustomPagination(
        items=posts,
        page=pagination.page,
        per_page=pagination.per_page,
        total=pagination.total
    )


def base_posts_query():
    """创建基础查询（包含评论计数）"""
    # 修复：将 group_by 移到查询对象上
    comment_count = db.session.query(
        Comment.post_id,
        func.count(Comment.id).label('comment_count')
    ).group_by(Comment.post_id).subquery()  # 修正位置

    return db.session.query(
        Post,
        func.coalesce(comment_count.c.comment_count, 0).label('comment_count')
    ).outerjoin(
        comment_count, Post.id == comment_count.c.post_id
    ).options(
        joinedload(Post.author),
        joinedload(Post.category)
    )


def load_comments_with_replies(post_id):
    """加载评论及其回复，按层级结构组织"""
    # 获取所有评论（包括回复）
    all_comments = Comment.query.filter_by(post_id=post_id) \
        .options(db.joinedload(Comment.author)) \
        .order_by(Comment.created_at.asc()) \
        .all()

    # 创建评论字典
    comment_dict = {c.id: c for c in all_comments}

    # 组织层级结构
    top_level = []
    for comment in all_comments:
        if comment.parent_id is None:
            top_level.append(comment)
        else:
            parent = comment_dict.get(comment.parent_id)
            if parent:
                if not hasattr(parent, 'replies'):
                    parent.replies = []
                parent.replies.append(comment)

    # 对每个层级的回复排序
    def sort_replies(comment):
        if hasattr(comment, 'replies'):
            comment.replies = sorted(comment.replies, key=lambda r: r.created_at)
            for reply in comment.replies:
                sort_replies(reply)

    for comment in top_level:
        sort_replies(comment)

    return top_level
