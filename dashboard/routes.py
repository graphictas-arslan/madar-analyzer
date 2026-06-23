{% extends "base.html" %}
{% block title %}مدیریت سازمان‌ها{% endblock %}
{% block content %}
<div class="d-flex justify-content-between align-items-center mb-4">
    <h2>مدیریت سازمان‌ها</h2>
    <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#createOrganizationModal">
        <i class="fas fa-plus"></i> سازمان جدید
    </button>
</div>

<!-- لیست سازمان‌ها -->
<div class="card">
    <div class="card-body">
        <table class="table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>نام سازمان</th>
                    <th>توضیحات</th>
                    <th>وضعیت</th>
                    <th>تاریخ ایجاد</th>
                    <th>عملیات</th>
                </tr>
            </thead>
            <tbody>
                {% for org in organizations %}
                <tr>
                    <td>{{ org.id }}</td>
                    <td>{{ org.name }}</td>
                    <td>{{ org.description or '-' }}</td>
                    <td>
                        {% if org.is_active %}
                            <span class="badge bg-success">فعال</span>
                        {% else %}
                            <span class="badge bg-danger">غیرفعال</span>
                        {% endif %}
                    </td>
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
