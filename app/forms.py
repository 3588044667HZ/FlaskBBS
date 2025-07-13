from flask_wtf.file import FileAllowed
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

from app.models import Category
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, HiddenField, \
    FileField, IntegerField


class LoginForm(FlaskForm):  # 登录表单
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')


class RegistrationForm(FlaskForm):  # 注册表单
    username = StringField('用户名', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    password2 = PasswordField(
        '重复密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')


class PostForm(FlaskForm):  # 发表帖子表单
    title = StringField('标题', validators=[DataRequired(), Length(min=1, max=100)])
    content = TextAreaField('内容', validators=[DataRequired()])
    category = SelectField('分类', coerce=int, validators=[DataRequired()])
    submit = SubmitField('发布')

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        # 动态加载分类选项
        self.category.choices = [(c.id, c.name) for c in Category.query.order_by('name')]


class EditPostForm(FlaskForm):  # 编辑帖子表单
    title = StringField('标题', validators=[DataRequired(), Length(min=1, max=100)])
    content = TextAreaField('内容', validators=[DataRequired()])
    submit = SubmitField('更新帖子')


class ProfileForm(FlaskForm):  # 个人信息上传表单
    avatar = FileField('头像', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], '只允许上传图片文件')
    ])
    about_me = TextAreaField('个人简介', validators=[Length(max=200)])
    submit = SubmitField('更新资料')


class CategoryForm(FlaskForm):  # 添加分类的表单
    name = StringField('分类名称', validators=[DataRequired(), Length(min=2, max=50)])
    submit = SubmitField('添加分类')

    def validate_name(self, field):
        if Category.query.filter_by(name=field.data).first():
            raise ValidationError('该分类名称已存在')


class CommentForm(FlaskForm):  # 发表评论表单
    content = TextAreaField('评论内容', validators=[
        DataRequired(message='评论内容不能为空'),
        Length(min=2, max=1000, message='评论长度需在2-1000个字符之间')
    ])
    parent_id = HiddenField('父评论ID', default=None)
    submit = SubmitField('提交评论')

    def set_parent_id(self, parent_id):
        self.parent_id = parent_id


class AdminUserForm(FlaskForm):
    """管理员编辑用户表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    avatar = FileField('头像', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], '只允许上传图片文件')
    ])
    permissions = IntegerField('权限掩码', validators=[DataRequired()])
    is_active = BooleanField('激活状态')
    submit = SubmitField('更新')


class AdminPostForm(FlaskForm):
    """管理员编辑帖子表单"""
    title = StringField('标题', validators=[DataRequired(), Length(min=1, max=100)])
    content = TextAreaField('内容', validators=[DataRequired()])
    category = SelectField('分类', coerce=int, validators=[DataRequired()])
    is_pinned = BooleanField('置顶')
    is_featured = BooleanField('精华')
    submit = SubmitField('更新')


class AdminCategoryForm(FlaskForm):
    """管理员分类表单"""
    name = StringField('分类名称', validators=[DataRequired(), Length(min=2, max=50)])
    submit = SubmitField('保存')

    def validate_name(self, field):
        """验证分类名称是否唯一"""
        if Category.query.filter(Category.name == field.data).first():
            raise ValidationError('该分类名称已存在')
