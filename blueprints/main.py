"""Public facing routes: pages, products, catalog, about, craft, etc."""
from flask import Blueprint, render_template, request, Response

from app import db
from models import Page, Product, Category, Market, Certification

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    page = Page.query.filter_by(slug="home", is_published=True).first()
    featured = Product.query.filter_by(is_published=True, featured=True).order_by(Product.created_at.desc()).limit(6).all()
    categories = Category.query.order_by(Category.order_val.asc()).all()
    markets = Market.query.filter_by(is_active=True).order_by(Market.order_val.asc()).all()
    certifications = Certification.query.filter_by(is_published=True).order_by(Certification.order_val.asc()).all()
    latest = Product.query.filter_by(is_published=True).order_by(Product.created_at.desc()).limit(4).all()
    return render_template("public/home.html", page=page, featured=featured, categories=categories, markets=markets, certifications=certifications, latest=latest)


@main_bp.route("/about")
def about():
    return render_template("public/about.html", page=Page.query.filter_by(slug="about", is_published=True).first())


@main_bp.route("/products")
def products():
    q = request.args.get("q", "").strip()
    cat = request.args.get("category", "").strip()
    query = Product.query.filter_by(is_published=True)
    if cat:
        query = query.join(Category).filter(Category.slug == cat)
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Product.name.ilike(like), Product.short_description.ilike(like)))
    products_list = query.order_by(Product.created_at.desc()).all()
    categories_list = Category.query.order_by(Category.order_val.asc()).all()
    return render_template("public/products.html", products=products_list, categories=categories_list, active_category=cat, q=q)


@main_bp.route("/products/<slug>")
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, is_published=True).first_or_404()
    related = Product.query.filter(Product.category_id == product.category_id, Product.id != product.id, Product.is_published == True).limit(3).all()
    return render_template("public/product_detail.html", product=product, related=related)


@main_bp.route("/craft")
def craft():
    return render_template("public/craft.html")


@main_bp.route("/bespoke")
def bespoke():
    all_categories = Category.query.order_by(Category.order_val.asc()).all()
    return render_template("public/bespoke.html", categories=all_categories)


@main_bp.route("/manufacturing")
def manufacturing():
    return render_template("public/manufacturing.html")


@main_bp.route("/quality")
def quality():
    certifications = Certification.query.filter_by(is_published=True).order_by(Certification.order_val.asc()).all()
    return render_template("public/quality.html", certifications=certifications)


@main_bp.route("/sustainability")
def sustainability():
    return render_template("public/sustainability.html")


@main_bp.route("/global")
def global_export():
    markets = Market.query.filter_by(is_active=True).order_by(Market.order_val.asc()).all()
    return render_template("public/global.html", markets=markets)


@main_bp.route("/contact")
def contact():
    return render_template("public/contact.html")


@main_bp.route("/sitemap.xml")
def sitemap():
    pages = [
        ("/", "1.0"), ("/about", "0.8"), ("/products", "0.9"), ("/craft", "0.7"),
        ("/bespoke", "0.8"), ("/manufacturing", "0.6"), ("/quality", "0.6"),
        ("/sustainability", "0.6"), ("/global", "0.7"), ("/contact", "0.8"),
        ("/request-quote", "0.7"), ("/place-order", "0.8"),
    ]
    for p in Product.query.filter_by(is_published=True).all():
        pages.append((f"/products/{p.slug}", "0.7"))
    body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, prio in pages:
        body.append(f"<url><loc>{request.host_url.strip(chr(47))}{path}</loc><priority>{prio}</priority></url>")
    body.append("</urlset>")
    return Response("\n".join(body), mimetype="application/xml")


@main_bp.route("/robots.txt")
def robots():
    text = "User-agent: *\nAllow: /\nDisallow: /admin/\n\nSitemap: " + request.host_url.rstrip("/") + "/sitemap.xml\n"
    return Response(text, mimetype="text/plain")
