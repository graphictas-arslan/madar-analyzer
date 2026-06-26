from models import User, Channel

def get_user_role(user):
    """برگرداندن نقش کاربر"""
    return user.role.name if user.role else None

def can_view_channel(user, channel_id):
    """آیا کاربر می‌تواند این کانال را ببیند؟"""
    if user.role.name == "admin":
        return True
    if user.role.name == "channel_admin":
        return channel_id in user.channel_ids
    return False

def can_score_post(user):
    """آیا کاربر می‌تواند به پست امتیاز بدهد؟"""
    return user.role.name in ["admin"]

def can_manage_users(user):
    """آیا کاربر می‌تواند کاربران را مدیریت کند؟"""
    return user.role.name == "admin"

def can_export_excel(user):
    """آیا کاربر می‌تواند خروجی اکسل بگیرد؟"""
    return user.role.name in ["admin", "channel_admin", "manager"]
