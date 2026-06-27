@dashboard_bp.route("/")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    total_posts = Post.query.count()
    total_channels = Channel.query.count()
    scored_posts = Post.query.filter(Post.score.isnot(None)).count()
    avg_score = db.session.query(func.avg(Post.score)).filter(Post.score.isnot(None)).scalar() or 0
    posts = Post.query.order_by(Post.publish_date.desc()).limit(10).all()
    
    return render_template(
        "dashboard/index.html",
        total_posts=total_posts,
        total_channels=total_channels,
        scored_posts=scored_posts,
        avg_score=round(avg_score, 1),
        posts=posts
    )
