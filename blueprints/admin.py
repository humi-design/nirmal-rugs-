"""Admin CMS blueprint: authentication, dashboard and oversight.

Security: passwords hashed (werkzeug), login-required guards, CSRF enabled
(Flask-WTF global CSRF), role checks for destructive actions..
"""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func

from app import db, login_manager
from models import AdminUser, Order, RFQ, ContactSubmission, Product, ThemeSettings, SEOSettings

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    """Only active admins may access protected views."""
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, "is_active_", False):
            return login_manager.unauthorized()
        if current_user.role not in ("admin", "editor"):
            abort(403)
        return view(*args, **kwargs)

    return wrapped


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not email or not password:
            error = "Email and password are required."
        else:
            user = AdminUser.query.filter_by(email=email).first()
            if user and user.check_password(password) and getattr(user, "is_active_", True):
                login_user(user, remember= True)
                return redirect(url_for("admin.dashboard"))
            error = "Invalid credentials."
    return render_template("admin/login.html", error=error)


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
@admin_required
def dashboard():
    stats = {
        "orders_new": Order.query.filter_by(status="New").count(),
        "orders_total": Order.query.count(),
        "rfqs_new": RFQ.query.filter_by(status="New").count(),
        "rfqs_total": RFQ.query.count(),
        "contacts_new": ContactSubmission.query.filter_by(is_read=False).count(),
        "products": Product.query.filter_by(is_published=True).count(),
    }
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    recent_rfqs = RFQ.query.order_by(RFQ.created_at.desc()).limit(5).all()
    recent_contacts = ContactSubmission.query.order_by(ContactSubmission.created_at.desc()).limit(5).all()
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_orders=recent_orders,
        recent_rfqs=recent_rfqs,
        recent_contacts=recent_contacts,
    )


@admin_bp.route("/orders")
@admin_required
def orders():
    items = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin/orders.html", orders=items)


@admin_bp.route("/rfqs")
@admin_required
def rfqs():
    items = RFQ.query.order_by(RFQ.created_at.desc()).all()
    return render_template("admin/rfqs.html", rfqs=items)


@admin_bp.route("/contacts")
@admin_required
def contacts():
    items = ContactSubmission.query.order_by(ContactSubmission.created_at.desc()).all()
    return render_template("admin/contacts.html", contacts=items)
