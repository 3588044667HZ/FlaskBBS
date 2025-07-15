# app/admin.py
# import os
from datetime import datetime, timedelta

# from PIL import Image
from flask import Blueprint, render_template, redirect, url_for, flash, request
# from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from app import db
from app.decorators import admin_required
from app.forms import AdminUserForm, AdminPostForm, AdminCategoryForm
from app.models import User, Post, Category, Comment, Permissions

# 创建管理员蓝图
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """管理员仪表盘"""
    stats = {
        'users': User.query.count(),
        'posts': Post.query.count(),
        'comments': Comment.query.count(),
        'categories': Category.query.count(),
        'active_users': User.query.filter(User.last_seen >= datetime.utcnow() - timedelta(days=7)).count()
    }
    return render_template('admin/dashboard.html', stats=stats, User=User, Post=Post)


@admin_bp.route('/users')
@admin_required
def users():  # todo 补全筛选功能
    """用户管理列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    users_ = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('admin/users.html', users=users_)


@admin_bp.route('/user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """编辑用户信息"""
    user = User.query.get_or_404(user_id)

    return render_template('admin/edit_user.html', user=user, Permissions=Permissions)


@admin_bp.route('/posts')
@admin_required
def posts():
    """帖子管理列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    posts_ = Post.query.options(
        joinedload(Post.author),
        joinedload(Post.category)
    ).order_by(Post.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template('admin/posts.html', posts=posts_)


@admin_bp.route('/post/<int:post_id>', methods=['GET', 'POST'])
@admin_required
def edit_post(post_id):
    """编辑帖子信息"""
    post = Post.query.get_or_404(post_id)
    form = AdminPostForm(obj=post)
    form.category.choices = [(c.id, c.name) for c in Category.query.order_by('name')]

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.category_id = form.category.data
        post.is_pinned = form.is_pinned.data
        post.is_featured = form.is_featured.data
        db.session.commit()
        flash('帖子已更新', 'success')
        return redirect(url_for('admin.posts'))

    return render_template('admin/edit_post.html', form=form, post=post)


@admin_bp.route('/categories')
@admin_required
def categories():
    """分类管理列表"""
    categories_ = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=categories_)


@admin_bp.route('/category/add', methods=['GET', 'POST'])
@admin_required
def add_category():
    """添加分类"""
    form = AdminCategoryForm()

    if form.validate_on_submit():
        category = Category(name=form.name.data)
        db.session.add(category)
        db.session.commit()
        flash('分类已添加', 'success')
        return redirect(url_for('admin.categories'))

    return render_template('admin/add_category.html', form=form)


@admin_bp.route('/category/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    """编辑分类"""
    category = Category.query.get_or_404(category_id)
    form = AdminCategoryForm(obj=category)

    if form.validate_on_submit():
        category.name = form.name.data
        db.session.commit()
        flash('分类已更新', 'success')
        return redirect(url_for('admin.categories'))

    return render_template('admin/edit_category.html', form=form, category=category)


@admin_bp.route('/category/delete/<int:category_id>', methods=['POST'])
@admin_required
def delete_category(category_id):
    """删除分类"""
    category = Category.query.get_or_404(category_id)

    # 将关联帖子移到默认分类
    default_category = Category.query.filter_by(name='默认分类').first()
    if not default_category:
        default_category = Category(name='默认分类')
        db.session.add(default_category)
        db.session.commit()

    for post in category.posts:
        post.category = default_category

    db.session.delete(category)
    db.session.commit()
    flash('分类已删除', 'success')
    return redirect(url_for('admin.categories'))


@admin_bp.route('/comments')
@admin_required
def comments():
    """评论管理列表"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    comments_ = Comment.query.options(
        joinedload(Comment.author),
        joinedload(Comment.post)
    ).order_by(Comment.created_at.desc()).paginate(page, per_page)

    return render_template('admin/comments.html', comments=comments_)


@admin_bp.route('/comment/delete/<int:comment_id>', methods=['POST'])
@admin_required
def delete_comment(comment_id):
    """删除评论"""
    comment = Comment.query.get_or_404(comment_id)
    post_id = comment.post_id

    # 递归删除子评论
    def delete_comment_and_replies(c):
        for reply in c.replies:
            delete_comment_and_replies(reply)
        db.session.delete(c)

    delete_comment_and_replies(comment)
    db.session.commit()

    # 更新帖子评论计数
    post = Post.query.get(post_id)
    if post:
        post.comment_count = len(post.comments)
        db.session.commit()

    flash('评论已删除', 'success')
    return redirect(url_for('admin.comments'))


@admin_bp.route('/user/<int:user_id>/reset_password', methods=['GET', 'POST'])
@admin_required
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('admin.reset_user_password', user_id=user_id))

        if len(new_password) < 8:
            flash('密码长度至少为8个字符', 'danger')
            return redirect(url_for('admin.reset_user_password', user_id=user_id))

        user.set_password(new_password)
        db.session.commit()
        flash('用户密码已重置', 'success')
        return redirect(url_for('admin.edit_user', user_id=user_id))

    return render_template('admin/reset_password.html', user=user)


@admin_bp.route('/change_user_info/<int:user_id>', methods=['POST'])
@admin_required
def change_user_info(user_id):
    form = AdminUserForm(request.form)  # 接收前端信息
    user = User.query.get_or_404(user_id)
    print(form.can_edit_any.data)
    if form.can_comment:
        user.add_permission(Permissions.EDIT_ANY)
    else:
        user.remove_permission(Permissions.EDIT_ANY)
    if form.can_comment.data:
        user.add_permission(Permissions.COMMENT)
    else:
        user.remove_permission(Permissions.COMMENT)
    if form.can_delete_any:
        user.add_permission(Permissions.DELETE_ANY)
    else:
        user.remove_permission(Permissions.DELETE_ANY)
    if form.can_delete_own:
        user.add_permission(Permissions.DELETE_OWN)
    else:
        user.remove_permission(Permissions.DELETE_OWN)
    if form.can_edit_own:
        user.add_permission(Permissions.EDIT_OWN)
    else:
        user.remove_permission(Permissions.EDIT_OWN)
    if form.can_manage_users:
        user.add_permission(Permissions.MANAGE_USERS)
    else:
        user.remove_permission(Permissions.MANAGE_USERS)
    if form.can_moderate:
        user.add_permission(Permissions.MODERATE)
    else:
        user.remove_permission(Permissions.MODERATE)
    if form.can_post:
        user.add_permission(Permissions.POST)
    else:
        user.remove_permission(Permissions.POST)
    if form.can_view:
        user.add_permission(Permissions.VIEW)
    else:
        user.remove_permission(Permissions.VIEW)
    if form.is_admin:
        user.add_permission(Permissions.ADMIN)
    else:
        user.remove_permission(Permissions.ADMIN)
    # if form.validate_on_submit():
    #     user.username = form.username.data
    #     user.email = form.email.data
    #     # user.permissions = form.permissions.data
    #     user.is_active = form.is_active.data
    #
    #     # 处理头像上传
    #     if form.avatar.data:
    #         avatar_file = form.avatar.data
    #         filename = secure_filename(f"{user.id}_{avatar_file.filename}")
    #         avatar_path = os.path.join(current_app.root_path, 'static', 'profile_pics', filename)
    #
    #         # 调整图片大小
    #         output_size = (150, 150)
    #         img = Image.open(avatar_file)
    #         img.thumbnail(output_size)
    #         img.save(avatar_path)
    #
    #         user.avatar = filename

    db.session.commit()
    flash('用户信息已更新', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    User.query.delete(user)
    return redirect((url_for('admin.users')))
