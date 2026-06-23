from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from extensions import db
from models import Organization

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

# صفحه اصلی داشبورد
@dashboard_bp.route("/")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("dashboard/index.html")

# ============== سازمان‌ها ==============
@dashboard_bp.route("/organizations")
def organizations():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    orgs = Organization.query.order_by(Organization.id.desc()).all()
    return render_template("dashboard/organizations.html", organizations=orgs)

@dashboard_bp.route("/organizations/create", methods=["POST"])
def create_organization():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    name = request.form.get("name")
    description = request.form.get("description")
    
    if Organization.query.filter_by(name=name).first():
        flash("این نام سازمان قبلاً وجود دارد!", "danger")
        return redirect(url_for("dashboard.organizations"))
    
    org = Organization(name=name, description=description)
    db.session.add(org)
    db.session.commit()
    flash("سازمان با موفقیت ایجاد شد.", "success")
    return redirect(url_for("dashboard.organizations"))

@dashboard_bp.route("/organizations/toggle/<int:org_id>")
def toggle_organization(org_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    org = Organization.query.get(org_id)
    if org:
        org.is_active = not org.is_active
        db.session.commit()
        flash("وضعیت سازمان تغییر کرد.", "success")
    return redirect(url_for("dashboard.organizations"))

@dashboard_bp.route("/organizations/delete/<int:org_id>")
def delete_organization(org_id):
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    
    org = Organization.query.get(org_id)
    if org:
        db.session.delete(org)
        db.session.commit()
        flash("سازمان حذف شد.", "success")
    return redirect(url_for("dashboard.organizations"))

# ============== کانال‌ها (فعلاً موقت) ==============
@dashboard_bp.route("/channels")
def channels():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("dashboard/channels.html")

# ============== پست‌ها (فعلاً موقت) ==============
@dashboard_bp.route("/posts")
def posts():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("dashboard/posts.html")                    </td>
                    <td>{{ org.created_at.strftime('%Y-%m-%d') }}</td>
                    <td>
                        <a href="/dashboard/organizations/toggle/{{ org.id }}" class="btn btn-sm btn-warning">
                            تغییر وضعیت
                        </a>
                        <a href="/dashboard/organizations/delete/{{ org.id }}" class="btn btn-sm btn-danger" onclick="return confirm('آیا مطمئن هستید؟')">
                            حذف
                        </a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>

<!-- مودال ایجاد سازمان جدید -->
<div class="modal fade" id="createOrganizationModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">سازمان جدید</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form method="POST" action="/dashboard/organizations/create">
                <div class="modal-body">
                    <div class="mb-3">
                        <label class="form-label">نام سازمان</label>
                        <input type="text" class="form-control" name="name" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label">توضیحات</label>
                        <textarea class="form-control" name="description" rows="3"></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">لغو</button>
                    <button type="submit" class="btn btn-primary">ذخیره</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
