# app/decorators.py
from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user
from .models import Permissions


def permission_required(permission):
    """权限检查装饰器"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('请登录以访问此页面', 'danger')
                return redirect(url_for('auth.login', next=request.url))
            if not current_user.has_permission(permission):
                flash('您没有权限执行此操作', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# 常用权限的快捷方式
def admin_required(f):
    return permission_required(Permissions.ADMIN)(f)


def moderate_required(f):
    return permission_required(Permissions.MODERATE)(f)


def edit_any_required(f):
    return permission_required(Permissions.EDIT_ANY)(f)


def delete_any_required(f):
    return permission_required(Permissions.DELETE_ANY)(f)
