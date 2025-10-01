import json
import os
from datetime import datetime

import flask
from PIL import Image
from flask import Blueprint, request, current_app, render_template, redirect, url_for, flash
from flask_login import current_user, login_required
# from app.forms import CommentForm
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

from app import db
from app.forms import CommentForm, EditPostForm, ProfileForm, PostForm
from app.models import Post, Comment, Category, User, Permissions, Session, Message
from app.utils import base_posts_query, create_posts_with_comment_count

# import json

# from app.decorators import admin_required, moderate_required, edit_any_required, delete_any_required

main = Blueprint('main', __name__)


@main.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('POSTS_PER_PAGE', 10)
    search_query = request.args.get('q', '')

    # 获取基础查询
    query = base_posts_query()

    if search_query:
        query = query.filter(Post.title.ilike(f'%{search_query}%'))

    # 排序和分页
    query = query.order_by(Post.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # 转换结果
    posts = create_posts_with_comment_count(pagination)

    return render_template('index.html', posts=posts, search_query=search_query)


# @main.route('/post/<int:post_id>', methods=['GET', 'POST'])
# def post_detail(post_id):
#     post = Post.query.get_or_404(post_id)
#     form = CommentForm()
#
#     if form.validate_on_submit():
#         comment = Comment(
#             content=form.content.data,
#             post_id=post.id,
#             user_id=current_user.id
#         )
#         db.session.add(comment)
#         post.comment_count = post.comments.count()  # 更新评论计数
#         db.session.commit()
#         return redirect(url_for('main.post_detail', post_id=post.id))
#
#     return render_template('post_detail.html', post=post, form=form)


# @main.route('/post/<int:post_id>', methods=['GET', 'POST'])
# def post_detail(post_id):
#     # 获取帖子及其关联数据
#     post = Post.query.options(
#         joinedload(Post.author),
#         joinedload(Post.category),
#         joinedload(Post.comments).joinedload(Comment.author)  # 加载评论及其作者
#     ).get_or_404(post_id)
#
#     form = CommentForm()
#
#     # 处理评论提交
#     if form.validate_on_submit() and current_user.is_authenticated:
#         parent_id = request.form.get('parent_id')
#         if parent_id:
#             try:
#                 parent_id = int(parent_id)
#                 # 验证父评论属于当前帖子
#                 parent_comment = next((c for c in post.comments if c.id == parent_id), None)
#                 if not parent_comment:
#                     parent_id = None
#             except (ValueError, TypeError):
#                 parent_id = None
#         # print("author", User.query.get_or_404(current_user.id))
#         comment = Comment(
#             content=form.content.data,
#             post_id=post.id,
#             user_id=current_user.id,
#             author=User.query.get_or_404(current_user.id),
#             parent_id=parent_id,
#             author_username=current_user.username
#         )
#         db.session.add(comment)
#         post.comment_count = len(post.comments) + 1  # 更新评论计数
#         db.session.commit()
#         flash('评论已发布', 'success')
#         return redirect(url_for('main.post_detail', post_id=post.id))
#
#     # 增加浏览量
#     if request.method == 'GET':
#         post.views += 1
#         db.session.commit()
#     # print("post.comments:", post.comments)
#     # for i in post.comments:
#     # print(f"comment{i.parent_id}:{i.content}")
#     # 按创建时间排序评论
#     sorted_comments = sorted(
#         [c for c in post.comments if not c.parent_id],
#         key=lambda x: x.created_at
#     )
#     # print('sorted_comments:', sorted_comments)
#     for i in sorted_comments:
#         print(i.id)
#     return render_template('post_detail.html', post=post, form=form, top_level_comments=sorted_comments)
@main.route('/post/<int:post_id>', methods=['GET'])
def post_detail(post_id):
    # 获取帖子及其关联数据
    post = Post.query.options(
        joinedload(Post.author),
        joinedload(Post.category),
        joinedload(Post.comments).joinedload(Comment.author)  # 加载评论及其作者
    ).get_or_404(post_id)

    # 增加浏览量（仅GET请求）
    post.views += 1
    db.session.commit()

    # 构建评论树
    # 创建一个字典，将评论ID映射到评论对象
    # comments_dict = {comment.id: comment for comment in post.comments}

    # 创建一个按父评论ID分组的字典
    comments_by_parent = {}
    # print("post.comments:", post.comments)
    for comment in post.comments:
        if comment.parent_id not in comments_by_parent:
            comments_by_parent[comment.parent_id] = []
        comments_by_parent[comment.parent_id].append(comment)

    # 为每个评论添加replies属性
    for comment in post.comments:
        if comment.id in comments_by_parent:
            comment.replies = sorted(comments_by_parent[comment.id], key=lambda c: c.created_at)
        else:
            comment.replies = []
    # print("comments_by_parent:", comments_by_parent)
    # 获取顶级评论（parent_id为None）
    top_level_comments = sorted(comments_by_parent.get("", []), key=lambda c: c.created_at)
    # for i in comments_by_parent.get("", []):
    #     # print(i.id)
    # print("top_level_comments:", top_level_comments)

    form = CommentForm()

    return render_template('post_detail.html', post=post, form=form, top_level_comments=top_level_comments)


@main.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    if current_user != post.author and not current_user.has_permission(Permissions.EDIT_ANY):
        flash('您没有权限编辑此帖子', 'danger')
        return redirect(url_for('main.post_detail', post_id=post.id))

    form = EditPostForm()

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        # 如果需要添加分类编辑功能
        # post.category_id = form.category.data
        db.session.commit()
        flash('帖子已成功更新', 'success')
        return redirect(url_for('main.post_detail', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content

    return render_template('edit_post.html', form=form, post=post)


# 获取评论（按时间顺序）并预加载回复
# comments = Comment.query.filter_by(post_id=post_id, parent_id=None) \
#     .options(db.joinedload(Comment.replies)) \
#     .order_by(Comment.created_at.asc()) \
#     .all()
#
# # 对每个评论的回复进行排序
# for comment in comments:
#     if comment.replies:
#         # 使用 Python 排序而不是 SQL 查询
#         comment.replies = sorted(
#             comment.replies,
#             key=lambda r: r.created_at
#         )
#
# # 增加帖子浏览量
# post.views = post.views + 1 if post.views else 1
# db.session.commit()
@main.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):  # 删除帖子
    post = Post.query.get_or_404(post_id)
    # print(1)
    # 检查权限
    if current_user != post.author and not current_user.has_permission(Permissions.DELETE_ANY):
        flash('您没有权限删除此帖子', 'danger')
        return redirect(url_for('main.post_detail', post_id=post.id))
    # print(4)
    # 删除所有相关评论（如果已实现评论功能）
    Comment.query.filter_by(post_id=post.id).delete()
    # print(2)
    db.session.delete(post)
    # print(3)
    db.session.commit()
    flash('帖子已成功删除', 'success')
    return redirect(url_for('main.index'))


@main.route('/user/<username>')
def user_profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('POSTS_PER_PAGE', 10)

    # 获取基础查询并过滤用户
    query_ = base_posts_query().filter(Post.user_id == user.id)

    # 排序和分页
    query1 = query_.order_by(Post.created_at.desc())
    pagination = query1.paginate(page=page, per_page=per_page)

    # 转换结果query1,
    posts = create_posts_with_comment_count(pagination)

    return render_template('user_profile.html', user=user, posts=posts)


@main.route('/profile/<username>')  # 点击编辑资料按钮后的路由
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = ProfileForm()
    return render_template('edit_profile.html', current_user=user, form=form)


@main.route('/edit_profile', methods=['GET', 'POST'])  # 编辑个人信息
@login_required
def edit_profile():
    form = ProfileForm()

    if form.validate_on_submit():
        # 处理头像上传
        if form.avatar.data:
            avatar_file = form.avatar.data
            filename = secure_filename(f"{current_user.id}_{avatar_file.filename}")
            avatar_path = os.path.join(current_app.root_path, 'static', 'profile_pics', filename)

            # 调整图片大小
            output_size = (150, 150)
            i = Image.open(avatar_file)
            i.thumbnail(output_size)
            i.save(avatar_path)

            current_user.avatar = filename

        # 保存其他信息
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('个人资料已更新', 'success')
        return redirect(url_for('main.user_profile', username=current_user.username))

    elif request.method == 'GET':
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', form=form)


@main.route('/categories')
def list_categories():
    categories = Category.query.order_by(Category.name).all()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('POSTS_PER_PAGE', 10)

    # 获取搜索查询参数
    search_query = request.args.get('q', '')

    # 构建基础查询
    query = Post.query.order_by(Post.created_at.desc())

    # 添加搜索过滤
    if search_query:
        query = query.filter(
            or_(
                Post.title.ilike(f'%{search_query}%'),
                Post.content.ilike(f'%{search_query}%')
            )
        )

    posts = query.paginate(page=page, per_page=per_page)
    return render_template('categories.html', categories=categories, posts=posts)


@main.route('/category/<int:category_id>')
def category_posts(category_id):
    category = Category.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('POSTS_PER_PAGE', 10)

    # 获取基础查询并过滤分类
    query = base_posts_query().filter(Post.category_id == category.id)

    # 排序和分页
    query = query.order_by(Post.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page)

    # 转换结果
    posts = create_posts_with_comment_count(pagination=pagination, category=category)

    return render_template('category_posts.html', category=category, posts=posts)


# @main.route('/add_category', methods=['GET', 'POST'])
# @login_required
# def add_category():
#     if not current_user.is_admin:
#         flash('只有管理员可以添加分类', 'danger')
#         return redirect(url_for('main.index'))
#
#     form = CategoryForm()
#     if form.validate_on_submit():
#         category = Category(name=form.name.data)
#         db.session.add(category)
#         db.session.commit()
#         flash('分类已添加', 'success')
#         return redirect(url_for('main.list_categories'))
#     return render_template('add_category.html', form=form)


@main.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            content=form.content.data,
            author=current_user,
            category_id=form.category.data
        )
        db.session.add(post)
        db.session.commit()
        flash('帖子发布成功！', 'success')
        return redirect(url_for('main.index'))
    return render_template('create_post.html', form=form)


# @main.route('/add_comment<int:post_id>', methods=['GET', 'POST'])
# @login_required
# def add_comment(post_id):
#     if not current_user.is_authenticated:
#         flash('请登录后发表评论', 'danger')
#         return redirect(url_for('main.post_detail', post_id=post_id))
#     comment = Comment(
#         content=
#     )
# @main.route('/post/<int:post_id>/comment', methods=['POST'])
# @main.route('/add_comment/<int:post_id>', methods=['POST'])
# @login_required
# def add_comment(post_id):
#     post = Post.query.get_or_404(post_id)
#     print(request.form)
#     form = CommentForm()
#
#     if form.validate_on_submit():
#         comment = Comment(
#             content=form.content.data,
#             post_id=post.id,
#             user_id=current_user.id,
#             author=current_user.username  # 确保有 author 字段
#         )
#         db.session.add(comment)
#         post.comment_count = post.comments.count()  # 更新评论计数
#         db.session.commit()
#         flash('评论已发布', 'success')
#
#     return redirect(url_for('main.post_detail', post_id=post.id))

# @main.route('/add_comment/<int:post_id>', methods=['POST'])
# @login_required
# def add_comment(post_id):
#     post = Post.query.get_or_404(post_id)
#     form = CommentForm(request.form)  # 使用 request.form 初始化表单
#     print("form.content.data:", form.content.data)
#     print("parent_id:", form.parent_id.data)
#     print("form:", request.form)
#
#     if form.validate_on_submit():
#         print('suc')
#         # 获取父评论ID（如果有）
#         # parent_id = request.form.get('parent_id', None)
#         parent_id = form.parent_id
#         if parent_id:
#             try:
#                 parent_id = int(parent_id)
#                 # 验证父评论属于当前帖子
#                 parent_comment = Comment.query.filter_by(id=parent_id, post_id=post_id).first()
#                 if not parent_comment:
#                     parent_id = None
#             except (ValueError, TypeError):
#                 parent_id = None
#
#         # 创建新评论
#         comment = Comment(
#             content=form.content.data,
#             post_id=post.id,
#             user_id=current_user.id,
#             author=current_user,
#             parent_id=parent_id,
#             author_username=current_user.username
#         )
#
#         db.session.add(comment)
#
#         # 更新评论计数
#         post.comment_count = Comment.query.filter_by(post_id=post.id).count()
#         db.session.commit()
#
#         flash('评论已发布', 'success')
#
#         # 重定向到新评论位置
#         return redirect(url_for('main.post_detail', post_id=post.id) + f'#comment-{comment.id}')
#
#     # 表单验证失败
#     flash('评论内容不能为空', 'danger')
#     return redirect(url_for('main.post_detail', post_id=post.id))
@main.route('/add_comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)

    # 直接从请求中获取数据
    content = request.form.get('content', '').strip()
    parent_id = request.form.get('parent_id', None)
    # print("add_comment:", content, parent_id)

    # 验证内容非空
    if not content:
        flash('评论内容不能为空', 'danger')
        return redirect(url_for('main.post_detail', post_id=post.id))

    # 验证父评论ID（如果存在）
    if parent_id:
        try:
            parent_id = int(parent_id)
            # 验证父评论属于当前帖子
            parent_comment = Comment.query.filter_by(id=parent_id, post_id=post.id).first()
            if not parent_comment:
                parent_id = None
        except (ValueError, TypeError):
            parent_id = None

    # 创建新评论
    comment = Comment(
        content=content,
        post_id=post.id,
        user_id=current_user.id,
        author=current_user,
        parent_id=parent_id,
        author_username=current_user.username
    )

    db.session.add(comment)

    # 更新评论计数
    post.comment_count = Comment.query.filter_by(post_id=post.id).count()
    db.session.commit()

    flash('评论已发布', 'success')

    # 重定向到新评论位置
    return redirect(url_for('main.post_detail', post_id=post.id) + f'#comment-{comment.id}')


@main.route('/edit_comment/<int:comment_id>', methods=['GET', 'POST'])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    # 检查权限
    if current_user != comment.author and not current_user.is_admin:
        flash('您没有权限编辑此评论', 'danger')
        return redirect(url_for('main.post_detail', post_id=comment.post_id))

    form = CommentForm()

    if form.validate_on_submit():
        comment.content = form.content.data
        comment.updated_at = datetime.utcnow()
        db.session.commit()
        flash('评论已更新', 'success')
        return redirect(url_for('main.post_detail', post_id=comment.post_id) + f'#comment-{comment.id}')

    elif request.method == 'GET':
        form.content.data = comment.content

    return render_template('edit_comment.html', form=form, comment=comment)


@main.route('/delete_comment/<int:comment_id>', methods=['POST'])  # 删除评论和子评论
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post_id = comment.post_id

    # 检查权限
    if current_user != comment.author and not current_user.is_admin:
        flash('您没有权限删除此评论', 'danger')
        return redirect(url_for('main.post_detail', post_id=post_id))

    # 递归删除子评论
    def delete_comment_and_replies(c):
        for reply in c.replies:
            delete_comment_and_replies(reply)
        db.session.delete(c)

    delete_comment_and_replies(comment)
    db.session.commit()

    flash('评论已删除', 'success')
    return redirect(url_for('main.post_detail', post_id=post_id))


@main.route("/message_page")
@login_required
def message_page():
    print('sessions:', User.query.get_or_404(current_user.id).sessions.all())
    return render_template("message_page.html", user=current_user)


@main.route("/chat/<int:user_id>", methods=['GET', 'POST'])
@login_required
def chat(user_id):
    user = User.query.get_or_404(user_id)
    session = Session().find_or_create(user.id, current_user.id)
    db.session.add(session)
    db.session.commit()
    print('chat ', session)
    return redirect(url_for('main.message_page'))


@main.route("/send_message", methods=['GET', 'POST'])
@login_required
def send_msg():
    print('send_msg', flask.request.json)
    user = User.query.get_or_404(flask.request.json['user_id'])
    # print(1)
    message = Message(
        sender_id=current_user.id,
        recipient_id=user.id,
        session_id=flask.request.json.get('session_id', -1),
        content=flask.request.json.get('content', ''),
    )
    # print(2)
    db.session.add(message)
    # print(3)
    db.session.commit()
    # print('send_msg ', message)
    # print(4)
    return json.dumps({'msg': 'success'})


@main.route("/get_all_sessions", methods=['GET', 'POST'])
@login_required
def get_all_sessions():
    sessions = []
    for i in User.query.get_or_404(current_user.id).sessions.all():
        messages = []
        for j in sorted(i.messages.all(), key=lambda m: m.created_at):
            messages.append({
                "type": "sent" if j.sender_id == current_user.id else "received",
                'content': j.content,
                "time": str(j.created_at)
            })
        sessions.append({
            'id': i.id,
            'user_id': i.get_other_user(current_user=current_user).id,
            'name': i.get_other_user(current_user=current_user).username,
            "avatar": i.get_other_user(current_user=current_user).avatar_url(),
            'lastMessage': i.last_message,
            'time': str(i.updated_at),
            "unread": 0,
            'messages': messages

        })
        print(sessions)
        return json.dumps(sessions)
