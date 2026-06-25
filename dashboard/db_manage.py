from flask import render_template, redirect, url_for, session, request, flash
from extensions import db
from . import dashboard_bp

@dashboard_bp.route("/db-manage", methods=["GET", "POST"])
def db_manage():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    message = None
    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "create_tables":
                db.create_all()
                message = "✅ جدول‌ها با موفقیت ایجاد شدند!"
            elif action == "fix_channels":
                with db.engine.connect() as conn:
                    conn.execute("""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='channels' AND column_name='channel_id') THEN
                                ALTER TABLE channels ADD COLUMN channel_id VARCHAR(150);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='channels' AND column_name='channel_name') THEN
                                ALTER TABLE channels ADD COLUMN channel_name VARCHAR(250);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='channels' AND column_name='platform_id') THEN
                                ALTER TABLE channels ADD COLUMN platform_id INTEGER;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='channels' AND column_name='organization_id') THEN
                                ALTER TABLE channels ADD COLUMN organization_id INTEGER;
                            END IF;
                        END $$;
                    """)
                    conn.commit()
                message = "✅ فیلدهای جدول channels تعمیر شدند!"
            elif action == "fix_posts":
                with db.engine.connect() as conn:
                    conn.execute("""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='channel_id') THEN
                                ALTER TABLE posts ADD COLUMN channel_id INTEGER;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='platform_post_id') THEN
                                ALTER TABLE posts ADD COLUMN platform_post_id VARCHAR(200);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='post_type') THEN
                                ALTER TABLE posts ADD COLUMN post_type VARCHAR(50);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='author_name') THEN
                                ALTER TABLE posts ADD COLUMN author_name VARCHAR(200);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='publish_date') THEN
                                ALTER TABLE posts ADD COLUMN publish_date TIMESTAMP;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='status') THEN
                                ALTER TABLE posts ADD COLUMN status VARCHAR(50);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='score') THEN
                                ALTER TABLE posts ADD COLUMN score FLOAT;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='caption') THEN
                                ALTER TABLE posts ADD COLUMN caption TEXT;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='text') THEN
                                ALTER TABLE posts ADD COLUMN text TEXT;
                            END IF;
                        END $$;
                    """)
                    conn.commit()
                message = "✅ فیلدهای جدول posts تعمیر شدند!"
            elif action == "fix_all":
                db.create_all()
                with db.engine.connect() as conn:
                    conn.execute("""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='channels' AND column_name='channel_id') THEN
                                ALTER TABLE channels ADD COLUMN channel_id VARCHAR(150);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='channels' AND column_name='channel_name') THEN
                                ALTER TABLE channels ADD COLUMN channel_name VARCHAR(250);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='channels' AND column_name='platform_id') THEN
                                ALTER TABLE channels ADD COLUMN platform_id INTEGER;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='channels' AND column_name='organization_id') THEN
                                ALTER TABLE channels ADD COLUMN organization_id INTEGER;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='channel_id') THEN
                                ALTER TABLE posts ADD COLUMN channel_id INTEGER;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='platform_post_id') THEN
                                ALTER TABLE posts ADD COLUMN platform_post_id VARCHAR(200);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='post_type') THEN
                                ALTER TABLE posts ADD COLUMN post_type VARCHAR(50);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='author_name') THEN
                                ALTER TABLE posts ADD COLUMN author_name VARCHAR(200);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='publish_date') THEN
                                ALTER TABLE posts ADD COLUMN publish_date TIMESTAMP;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='status') THEN
                                ALTER TABLE posts ADD COLUMN status VARCHAR(50);
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='score') THEN
                                ALTER TABLE posts ADD COLUMN score FLOAT;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='caption') THEN
                                ALTER TABLE posts ADD COLUMN caption TEXT;
                            END IF;
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='posts' AND column_name='text') THEN
                                ALTER TABLE posts ADD COLUMN text TEXT;
                            END IF;
                        END $$;
                    """)
                    conn.commit()
                message = "✅ همه فیلدها تعمیر شدند!"
            else:
                message = "⚠️ عملیات نامعتبر است."
        except Exception as e:
            message = f"❌ خطا: {str(e)}"
    return render_template("dashboard/db_manage.html", message=message)
