@dashboard_bp.route("/channels/<int:channel_id>/posts/export")
def export_channel_posts(channel_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    channel = Channel.query.get(channel_id)
    if not channel:
        flash("کانال پیدا نشد!", "danger")
        return redirect(url_for("dashboard.channels"))
    
    # دریافت پارامترهای فیلتر
    type_filter = request.args.get("type", "")
    status_filter = request.args.get("status", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    
    # ساخت کوئری پایه
    query = Post.query.filter_by(channel_id=channel_id).order_by(Post.publish_date.desc())
    
    # اعمال فیلترها
    if type_filter:
        query = query.filter(Post.post_type == type_filter)
    if status_filter:
        query = query.filter(Post.status == status_filter)
    if date_from:
        query = query.filter(Post.publish_date >= datetime.strptime(date_from, "%Y-%m-%d"))
    if date_to:
        query = query.filter(Post.publish_date <= datetime.strptime(date_to, "%Y-%m-%d"))
    
    posts = query.all()
    
    # تولید فایل اکسل
    excel_file = generate_excel(posts, title=f"پست‌های {channel.channel_name}")
    
    # تولید نام فایل امن (انگلیسی)
    safe_filename = f"posts_{channel.channel_name}.xlsx"
    safe_filename = safe_filename.replace(" ", "_").replace(":", "_").replace("،", "_")
    
    return Response(
        excel_file.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={safe_filename}",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
    )
