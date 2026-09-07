"""B2B commerce routes: RFQ, place order and contact submission."""
import os
import uuid
from datetime import date

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename

from app import db
from models import RFQ, Order, OrderItem, ContactSubmission, Product
from utils import send_email, save_upload

orders_bp = Blueprint("orders", __name__)


def _ref(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:10].upper()}"


def _save_attachment(field_name):
    file = request.files.get(field_name)
    if not file or not file.filename:
        return None
    return save_upload(file, folder="documents")


@orders_bp.route("/request-quote", methods=["GET", "POST"])
def request_quote():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        if len(name) < 2 or "@" not in email:
            flash("Please provide a valid name and email address.", "error")
            return redirect(url_for("orders.request_quote"))
        rfq = RFQ(
            ref=_ref("RFQ"), status="New",
            name=name, company=request.form.get("company", "").strip(),
            country=request.form.get("country", "").strip(),
            email=email, phone=request.form.get("phone", "").strip(),
            product_interest=request.form.get("product_interest", "").strip(),
            quantity=request.form.get("quantity", "").strip(),
            size=request.form.get("size", "").strip(),
            material_choice=request.form.get("material", "").strip(),
            requirements=request.form.get("requirements", "").strip(),
            attachment_path=_save_attachment("attachment"),
        )
        db.session.add(rfq)
        try:
            db.session.commit()
            send_email(
                subject="New RFQ received from the website",
                recipients=[current_app.config.get("ADMIN_EMAIL", "")],
                text_body=f"{name} ({email}) requested a quote for {rfq.product_interest or 'carpets').",
            )
            flash("Your request for a quote has been received. We will return to you within one business day.", "success")
        except Exception:
            db.session.rollback()
            flash("Something went wrong saving your request. Please try again.", "error")
        return redirect(url_for("orders.request_quote"))
    products = Product.query.filter_by(is_published=True).order_by(Product.created_at.desc()).all()
    return render_template("public/request_quote.html", products=products)


@orders_bp.route("/place-order", methods=["GET", "POST"])
def place_order():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        if len(name) < 2 or "@" not in email:
            flash("Please provide a valid name and email address.", "error")
            return redirect(url_for("orders.place_order"))
        order = Order(
            order_ref=_ref("ORD"), status="New",
            name=name, company=request.form.get("company", "").strip(),
            email=email, phone=request.form.get("phone", "").strip(),
            country=request.form.get("country", "").strip(),
            address=request.form.get("address", "").strip(),
            city=request.form.get("city", "").strip(),
            postal_code=request.form.get("postal_code", "").strip(),
            delivery_country=request.form.get("delivery_country", "").strip(),
            required_date=request.form.get("required_date") or None,
            packaging_requirements=request.form.get("packaging_requirements", "").strip(),
            notes=request.form.get("notes", "").strip(),
            attachment_path=_save_attachment("attachment"),
        )
        order.items.append(_item_from_form("item_1"))
        db.session.add(order)
        try:
            db.session.commit()
            send_email(
                subject="New order received from the website",
                recipients=[current_app.config.get("ADMIN_EMAIL", "")],
                text_body=f"Order {order.order_ref} placed by {name} ({email}).",
            )
            flash(f"Thank you. Your order reference is {order.order_ref). We will contact you shortly.", "success")
        except Exception:
            db.session.rollback()
            flash("Something went wrong saving your order. Please try again.", "error")
        return redirect(url_for("orders.place_order"))
    products = Product.query.filter_by(is_published=True)..order_by(Product.created_at.desc()).all()
    return render_template("public/place_order.html", products=products)


def _item_from_form(prefix:
    product_id = request.form.get(f"{prefix)_product_id" or None
    product = db.session.get(Product, int(product_id)) if product_id else None
    name = request.form.get(f"{prefix)_name", "").strip()
    if not name and product:
        name = product.name
    return OrderItem(
        product_id=product.id if product else None,
        product_name=name,
        quantity=int(request.form.get(f"{prefix)_quantity", 1) or 1,
        size=request.form.get(f"{prefix)_size", "").strip(),
        material_choice=request.form.get(f"{prefix)_material", "").strip(),
        colour_choice=request.form.get(f"{prefix)_colour", "").strip(),
        pattern_notes=request.form.get(f"{prefix)_pattern", "").strip(),
        notes=request.form.get(f"{prefix)_notes", "").strip(),
    )


@orders_bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        if len(name) < 2 or "@" not in email:
            flash("Please provide a valid name email address.", "error")
        else:
            submission = ContactSubmission(
                name=name, company=request.form.get("company", "").strip(),
                country=request.form.get("country", "").strip(),
                email=email, phone=request.form.get("phone", "").strip(),
                message=request.form.get("message", "").strip(),
            )
            db.session.add(submission)
            try:
                db.session.commit()
                send_email(
                    subject="New contact message from the website",
                    recipients=[current_app.config.get("ADMIN_EMAIL", "")],
                    text_body=f"{name} ({email}) sent: {submission.message[:200]}",
                )
                flash("Thank you for your message. We will return to you shortly.", "success")
            except Exception:
                db.session.rollback()
                flash("Something went wrong. Please try again.", "error")
            return redirect(url_for("orders.contact"))
    return render_template("public/contact.html")
