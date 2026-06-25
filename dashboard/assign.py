from flask import render_template, redirect, url_for, session, request, flash
from extensions import db
from models import Organization, Channel, Post
from sqlalchemy import func
from .core import dashboard_bp  # این خط مهم است

@dashboard_bp.route("/channels/assign")
def assign_channels():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    unassigned_channels = Channel.query.filter_by(organization_id=None).all()
    organizations = Organization.query.all()
    return render_template(
        "dashboard/assign_channels.html",
        unassigned_channels=unassigned_channels,
        organizations=organizations
    )

@dashboard_bp.route("/channels/assign/<int:channel_id>", methods=["POST"])
def assign_channel(channel_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    channel = Channel.query.get(channel_id)
    if not channel:
        flash("کانال پیدا نشد!", "danger")
        return redirect(url_for("dashboard.assign_channels"))
    organization_id = request.form.get("organization_id")
    if organization_id:
        channel.organization_id = organization_id
        db.session.commit()
        flash(f"کانال {channel.channel_name} به سازمان انتخاب شده متصل شد.", "success")
    else:
        flash("لطفاً یک سازمان انتخاب کنید.", "danger")
    return redirect(url_for("dashboard.assign_channels"))
