from datetime import datetime

import bleach
import markdown
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from markupsafe import Markup

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请登录以访问此页面'
login_manager.login_message_category = 'info'
ALLOWED_TAGS = frozenset(list(bleach.ALLOWED_TAGS) + [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'p', 'br', 'div', 'span', 'pre', 'code', 'blockquote',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'img'
])

ALLOWED_ATTRIBUTES = {
    **bleach.ALLOWED_ATTRIBUTES,
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'a': ['href', 'title', 'rel'],
    'code': ['class'],
    'span': ['class']
}


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)

    # 注册蓝图
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .admin import admin_bp  # 导入管理员蓝图
    app.register_blueprint(admin_bp)

    @app.template_filter('safe_markdown')
    def safe_markdown_filter(text):
        if not text:
            return ""

        # 转换 Markdown 为 HTML
        html = markdown.markdown(
            text,
            extensions=[
                'fenced_code',
                'tables',
                'codehilite',
                'nl2br'
            ]
        )

        # 清理 HTML
        clean_html = bleach.clean(
            html,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True
        )

        Markup(clean_html)

    @app.template_filter('time_ago')
    def time_ago_filter(value):
        now = datetime.utcnow()
        diff = now - value

        if diff.days > 365:
            years = diff.days // 365
            return f'{years}年前'
        if diff.days > 30:
            months = diff.days // 30
            return f'{months}个月前'
        if diff.days > 0:
            return f'{diff.days}天前'
        if diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f'{hours}小时前'
        if diff.seconds > 60:
            minutes = diff.seconds // 60
            return f'{minutes}分钟前'
        return '刚刚'

    return app
