"""SQLAlchemy models in one module for clarity.

Covers: administration, theme, SEO, CMS pages/sections, products,
categories, images, specs, orders, RFQs, contacts, media, markets,
certifications and testimonial/inquiry helpers.
"""
import os
import uuid
from datetime import datetime, date, timezone
from urllib.parse import urlparse

from flask import current_app, url_for
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event

from app import db


# ---------------------------------------------------------------- helpers

def _random_slug() -> str:
    return uuid.uuid4().hex[:10]


def slugify(value: str) -> str:
    """ASCII-ish slug used for products and categories."""
    import re
    cleaned = (value or "" ).lower().strip()
    cleaned = re.sub(r"[^\w\s-]", "", cleaned)
    cleaned = re.sub(r"[\s_]+", "-", cleaned)
    return cleaned or _random_slug()

def upload_path(filename: str) -> str:
    """Join the upload folder for persisted relative paths."""
    return os.path.join("uploads", filename)


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------- admin

class AdminUser(UserMixin, db.Model):
    __tablename__ = "admin_users"
    id = db.Column(db.Integer, primary_key= True)
    name = db.Column(db.String(120), default="Admin")
    email = db.Column(db.String(255), unique= True, nullable= False)
    password_hash = db.Column(db.String(255), nullable= False)
    role = db.Column(db.String(32), default="admin")  # admin | editor
    is_active_ = db.Column(db.Boolean, default= True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def is_active(self) -> bool:
        return self.is_active_


# ---------------------------------------------------------------- theme

class ThemeSettings(db.Model):
    __tablename__ = "theme_settings"
    id = db.Column(db.Integer, primary_key= True)
    site_name = db.Column(db.String(160), default="Nirmal Rugs")
    tagline = db.Column(db.String(255), default="Handcrafted carpets and rugs, crafted for the world.")

    primary_color = db.Column(db.String(9), default="#12355B")   # deep midnight blue
    secondary_color = db.Column(db.String(9), default="#1E4D7B")  # rich navy
    accent_color = db.Column(db.String(9), default="#E86A17")    # premium orange
    background_color = db.Column(db.String(9), default="#F7F4EE")  # warm ivory
    surface_color = db.Column(db.String(9), default="#FFFFFF")
    text_color = db.Column(db.String(9), default="#101820")
    muted_color = db.Column(db.String(9), default="#5B6470")
    dark_background = db.Column(db.String(9), default="#071426")
    on_dark_text = db.Column(db.String(9), default="#F4EFE4")

    heading_font = db.Column(db.String(120), default="Fraunces")
    body_font = db.Column(db.String(120), default="Outfit")
    button_style = db.Column(db.String(32), default="pill")  # pill | sharp | rounded
    border_radius = db.Column(db.Integer, default=14)
    animation_intensity = db.Column(db.String(16), default="medium")  # low | medium | high
    default_light_dark = db.Column(db.String(16), default="dark")

    logo_path = db.Column(db.String(500), nullable= True)
    favicon_path = db.Column(db.String(500), nullable= True)
    og_image_path = db.Column(db.String(500), nullable= True)

    hero_headline = db.Column(db.String(255), default="CRAFTED FOR THE WORLD.")
    hero_subheadline = db.Column(db.String(400), default="Where craftsmanship, imagination and precision become extraordinary carpets and rugs.")
    hero_cta_primary = db.Column(db.String(80), default="EXPLORE THE COLLECTION")
    hero_cta_primary_url = db.Column(db.String(255), default="/products")
    hero_cta_secondary = db.Column(db.String(80), default="CREATE BESPOKE")
    hero_cta_secondary_url = db.Column(db.String(255), default="/bespoke")
    footer_text = db.Column(db.Text, default="Nirmal Rugs — a precision house of handcrafted contemporary carpets, rugs and floor art. Crafted for the world.")

    def css_vars(self) -> dict:

        """CSS variables consumed by every template."""
        return {
            "primary": self.primary_color,
            "secondary": self.secondary_color,
            "accent": self.accent_color,
            "background": self.background_color,
            "surface": self.surface_color,
            "text": self.text_color,
            "muted": self.muted_color,
            "dark": self.dark_background,
            "on-dark": self.on_dark_text,
            "heading-font": self.heading_font,
            "body-font": self.body_font,
            "radius": f"{self.radius or 14}px",
            "radius-lg": f"{(self.radius or 14) * 2}px",
            "radius-sm": f"{max(4, (self.radius or 14) // 2)}px",
        }

    @classmethod
    def get_active(cls) -> "ThemeSettings":
        t = db.session.get(cls, 1)
        if t is None:
            t = cls(id= 1)
            if hasattr(db, "session") and db.session:
                db.session.add(t)
                try:
                    db.session.commit()
                except Exception:
                    db.session.rollback()
        return t


# ---------------------------------------------------------------- seo

class SEOSettings(db.Model):
    __tablename__ = "seo_settings"
    id = db.Column(db.Integer, primary_key= True)
    site_title = db.Column(db.String(200), default="Nirmal Rugs | Handcrafted Luxury Carpets&Rugs&Manufacturer&Exporter")
    site_description = db.Column(db.Text, default="A precision house of handcrafted contemporary carpets, rugs and bespoke floor art — designed, woven and world-ready for hotels, residences and international trade.")
    robots_txt = db.Column(db.Text, default="User-agent: *\nAllow: /\nDisallow: /admin/\n")
    google_site_verification = db.Column(db.String(255))

    @classmethod
    def get_active(cls) -> "SEOSettings":
        s = db.session.get(cls, 1)
        if s is None:
            s = cls(id= 1)
            db.session.add(s)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
        return s


# ---------------------------------------------------------------- pages & sections

class Page(db.Model):
    __tablename__ = "pages"
    id = db.Column(db.Integer, primary_key= True)
    slug = db.Column(db.String(120), unique= True, default=slugify)
    title = db.Column(db.String(200), nullable= False)
    subtitle = db.Column(db.String(400))
    meta_title = db.Column(db.String(200))
    meta_description = db.Column(db.String(400))
    og_image_path = db.Column(db.String(500))
    featured_image_path = db.Column(db.String(500))
    is_published = db.Column(db.Boolean, default= True)
    in_navigation = db.Column(db.Boolean, default= False)
    nav_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    sections = db.relationship("PageSection", backref= "page_ref", lazy= "dynamic", order_by= "PageSection.order_val", cascade= "all, delete-orphan")

    def section_list(self):
        return self.sections.order_by(PageSection.order_val.asc()).all()


class PageSection(db.Model):
    __tablename__ = "page_sections"
    id = db.Column(db.Integer, primary_key= True)
    page_id = db.Column(db.Integer, db.ForeignKey("pages.id", ondelete= "CASCADE"), nullable= False)
    section_type = db.Column(db.String(64), nullable= False)  # hero,text,image,len,products...
    order_val = db.Column(db.Integer, default=0)
    is_visible = db.Column(db.Boolean, default= True)

    # generic content (JSON)
    content = db.Column(db.JSON, default=dict)

    def __repr__(self) -> str:
        return f"<PageSection {self.section_type} #{self.order_val}>"


# ---------------------------------------------------------------- catalog

class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key= True)
    slug = db.Column(db.String(120), unique= True, nullable= False)
    name = db.Column(db.String(160), nullable= False)
    description = db.Column(db.Text)
    image_path = db.Column(db.String(500))
    order_val = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    products = db.relationship("Product", backref= "category_rel", lazy= "dynamic")


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key= True)
    slug = db.Column(db.String(160), unique= True, nullable= False)
    sku = db.Column(db.String(80), unique= True)
    name = db.Column(db.String(200), nullable= False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete= "SET NULL"))
    short_description = db.Column(db.String(500))
    description = db.Column(db.Text)

    material = db.Column(db.String(255), default="Wool")
    construction = db.Column(db.String(255), default="Hand-knotted")
    available_sizes = db.Column(db.String(500), default="2x3, 3x5, 5x8, 8x10, 10x14 (ft)")  # comma list
    weight = db.Column(db.String(120), default="2.8 kg/m²")
    colours = db.Column(db.String(500), default="Ivory, Navy, Terracotta")
    pattern = db.Column(db.String(255), default="Contemporary abstract")
    moq = db.Column(db.String(120), default="20 pcs / design")
    applications = db.Column(db.String(500), default="Hospitality, Residential, Office")
    customization = db.Column(db.String(255), default="Size, colour, pattern available")
    weave_density = db.Column(db.String(120))
    pile_height = db.Column(db.String(120))
    knot_count = db.Column(db.String(120))
    back_type = db.Column(db.String(120))

    price_from = db.Column(db.Numeric(12,2), nullable= True)
    currency = db.Column(db.String(8), default="USD")
    featured = db.Column(db.Boolean, default= False)
    is_published = db.Column(db.Boolean, default= True)
    model_path = db.Column(db.String(500))   # GLB/GLTF
    badge = db.Column(db.String(80), default="Handcrafted")
    story_quote = db.Column(db.String(400))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    images = db.relationship("ProductImage", backref= "product", lazy= "dynamic", order_by= "ProductImage.order_val", cascade= "all, delete-orphan")
    specs = db.relationship("ProductSpecification", backref= "product", lazy= "dynamic", cascade= "all, delete-orphan")

    def spec_dict(self) -> dict:
        return {s.key: s.value for s in self.specs.all()}

    def gallery(self) -> list:
        return self.images.order_by(ProductImage.order_val.asc()).all() if self.images else []

    @property
    def category_name(self) -> str:
        return self.category_rel.name if self.category_rel else "—"


class ProductImage(db.Model):
    __tablename__ = "product_images"
    id = db.Column(db.Integer, primary_key= True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete= "CASCADE"), nullable= False)
    path = db.Column(db.String(500), nullable= False)
    alt = db.Column(db.String(255))
    order_val = db.Column(db.Integer, default=0)


class ProductSpecification(db.Model):
    __tablename__ = "product_specifications"
    id = db.Column(db.Integer, primary_key= True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete= "CASCADE"), nullable= False)
    key = db.Column(db.String(160), nullable= False)
    value = db.Column(db.String(500), nullable= False)
    order_val = db.Column(db.Integer, default=0)


# ---------------------------------------------------------------- commerce

class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key= True)
    order_ref = db.Column(db.String(32), unique= True, nullable= False)
    status = db.Column(db.String(40), default="New", index= True)

    # customer
    name = db.Column(db.String(200), nullable= False)
    company = db.Column(db.String(255))
    email = db.Column(db.String(255), nullable= False)
    phone = db.Column(db.String(80))
    country = db.Column(db.String(120))
    address = db.Column(db.Text)
    city = db.Column(db.String(120))
    postal_code = db.Column(db.String(40))

    # order details
    delivery_country = db.Column(db.String(120))
    required_date = db.Column(db.Date)
    packaging_requirements = db.Column(db.String(500))
    notes = db.Column(db.Text)
    attachment_path = db.Column(db.String(500))
    admin_notes = db.Column(db.Text)
    admin_quote = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    items = db.relationship("OrderItem", backref= "order", lazy= "dynamic", cascade= "all, delete-orphan")

    ORDER_STATUSES = [
        "New", "Enquiry Received", "Reviewing", "Quote Prepared", "Awaiting Customer",
        "Confirmed", "In Production", "Quality Inspection", "Ready for Shipment",
        "Shipped", "Completed", "Cancelled",
    ]

    def total_quantity(self) -> int:

        """Order items may include custom bespoke lines with no product link."""
        return sum(i.quantity or 0 for i in self.items.all())


class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key= True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete= "CASCADE"), nullable= False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id", ondelete= "SET NULL"))
    product_name = db.Column(db.String(255), nullable= False)
    quantity = db.Column(db.Integer, default= 1)
    size = db.Column(db.String(120))
    material_choice = db.Column(db.String(120))
    colour_choice = db.Column(db.String(120))
    pattern_notes = db.Column(db.String(500))
    unit_price = db.Column(db.Numeric(12,2))
    notes = db.Column(db.String(500))


class RFQ(db.Model):
    __tablename__ = "rfqs"
    id = db.Column(db.Integer, primary_key= True)
    ref = db.Column(db.String(32), unique= True, nullable= False)
    status = db.Column(db.String(40), default="New", index= True)

    name = db.Column(db.String(200), nullable= False)
    company = db.Column(db.String(255))
    country = db.Column(db.String(120))
    email = db.Column(db.String(255), nullable= False)
    phone = db.Column(db.String(80))

    product_interest = db.Column(db.String(255))
    quantity = db.Column(db.String(120))
    size = db.Column(db.String(255))
    material_choice = db.Column(db.String(255))
    requirements = db.Column(db.Text)
    attachment_path = db.Column(db.String(500))
    admin_notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ContactSubmission(db.Model):
    __tablename__ = "contact_submissions"
    id = db.Column(db.Integer, primary_key= True)
    name = db.Column(db.String(200), nullable= False)
    company = db.Column(db.String(255))
    country = db.Column(db.String(120))
    email = db.Column(db.String(255), nullable= False)
    phone = db.Column(db.String(80))
    message = db.Column(db.Text, nullable= False)
    is_read = db.Column(db.Boolean, default= False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------- media

class Media(db.Model):
    __tablename__ = "media"
    id = db.Column(db.Integer, primary_key= True)
    path = db.Column(db.String(500), nullable= False)
    kind = db.Column(db.String(32), default="image")  # image|video|model|document
    title = db.Column(db.String(255))
    alt = db.Column(db.String(255))
    size_bytes = db.Column(db.BigInteger, default= 0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------- global markets

class Market(db.Model):
    __tablename__ = "markets"
    id = db.Column(db.Integer, primary_key= True)
    country = db.Column(db.String(120), nullable= False)
    region = db.Column(db.String(120))
    description = db.Column(db.Text)
    image_path = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default= True)
    order_val = db.Column(db.Integer, default= 0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Certification(db.Model):
    __tablename__ = "certifications"
    id = db.Column(db.Integer, primary_key= True)
    name = db.Column(db.String(200), nullable= False)
    description = db.Column(db.Text)
    document_path = db.Column(db.String(500))
    image_path = db.Column(db.String(500))
    is_published = db.Column(db.Boolean, default= True)
    order_val = db.Column(db.Integer, default= 0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


# ------------------------------------------------------------------

def all_models() -> list:
    return [AdminUser, ThemeSettings, SEOSettings, Page] + [PageSection, Category, Product, ProductImage, ProductSpecification, Order, OrderItem, RFQ, ContactSubmission, Media, Market, Certification]
