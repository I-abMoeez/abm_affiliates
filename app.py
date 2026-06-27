from flask import Flask, render_template, request, jsonify

import os
import requests
# Load local .env if present (so you don't need to set env vars manually)
try:
    from dotenv import load_dotenv
    # Explicit path to avoid "wrong cwd" issues when running from another folder
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path, override=False)
        print(f"[INFO] Loaded env from: {env_path}")
    else:
        print(f"[WARN] .env not found at: {env_path}")
except Exception as e:
    # If python-dotenv can't parse the file (e.g., unexpected formatting),
    # we still want the app to run with any env vars already present.
    print(f"[WARN] dotenv load failed: {e}")

# Prevent noisy python-dotenv parse warnings from breaking runtime.
# If parsing fails, variables may still be present via OS environment.



# Helpful startup check (shows up in Flask terminal)
_missing = [
    k for k in ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"]
    if os.getenv(k) in (None, "")
]
if _missing:
    print("[WARN] Missing env vars:", ", ".join(_missing))




from click_tracker import get_country_from_ip

try:
    from supabase import create_client
except Exception:
    create_client = None

app = Flask(__name__)


@app.context_processor
def _inject_globals():
    return {"stores": STORES, "categories": CATEGORIES, "store_labels": STORE_LABELS}


PRODUCTS = [
    {
        "id": 1,
        "name": "Sony WH-1000XM5",
        "store": "amazon",
        "category": "audio",
        "category_label": "Audio",
        "price": 349.99,
        "original_price": 399.99,
        "rating": 4.8,
        "reviews": 12847,
        "image": "https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?w=600&q=80",
        "badge": "Best Seller",
        "description": "Industry-leading noise cancellation with 30-hour battery life. The gold standard for wireless headphones.",
        "affiliate_url": "https://amazon.com",
        "manual_url": "",
        "features": ["30hr battery", "ANC Pro", "Multipoint", "LDAC"],
    },
    {
        "id": 2,
        "name": "Apple MacBook Air M3",
        "store": "amazon",
        "category": "laptops",
        "category_label": "Laptops",
        "price": 1099.00,
        "original_price": 1299.00,
        "rating": 4.9,
        "reviews": 8932,
        "image": "https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?w=600&q=80",
        "badge": "Editor's Pick",
        "description": "Blazing fast M3 chip with 18-hour battery. Fanless, silent, impossibly thin.",
        "affiliate_url": "https://apple.com",
        "manual_url": "",
        "features": ["M3 chip", "18hr battery", "Fanless", "15\" display"],
    },
    {
        "id": 3,
        "name": "Samsung 65\" Neo QLED",
        "store": "amazon",
        "category": "tvs",
        "category_label": "TVs",
        "price": 1299.99,
        "original_price": 1799.99,
        "rating": 4.7,
        "reviews": 5214,
        "image": "https://images.unsplash.com/photo-1593359677879-a4bb92f4834a?w=600&q=80",
        "badge": "Hot Deal",
        "description": "Mini LED quantum dots deliver cinema-grade picture. Deep blacks, vivid color, 144Hz gaming.",
        "affiliate_url": "https://samsung.com",
        "manual_url": "",
        "features": ["4K 144Hz", "Neo QLED", "HDR2000", "Gaming Hub"],
    },
    {
        "id": 4,
        "name": "DJI Mini 4 Pro",
        "store": "amazon",
        "category": "cameras",
        "category_label": "Cameras",
        "price": 759.00,
        "original_price": 759.00,
        "rating": 4.8,
        "reviews": 3421,
        "image": "https://images.unsplash.com/photo-1473968512647-3e447244af8f?w=600&q=80",
        "badge": "New",
        "description": "Under 249g with 4K/60fps and omnidirectional obstacle sensing. The perfect travel drone.",
        "affiliate_url": "https://dji.com",
        "manual_url": "",
        "features": ["249g weight", "4K/60fps", "34min flight", "Obstacle avoid"],
    },
    {
        "id": 5,
        "name": "Bose QuietComfort Ultra",
        "store": "amazon",
        "category": "audio",
        "category_label": "Audio",
        "price": 299.00,
        "original_price": 329.00,
        "rating": 4.6,
        "reviews": 7102,
        "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&q=80",
        "badge": None,
        "description": "Spatial audio with CustomTune technology. Bose's best ANC headphone ever made.",
        "affiliate_url": "https://bose.com",
        "manual_url": "",
        "features": ["Spatial Audio", "CustomTune", "24hr battery", "EQ app"],
    },
    {
        "id": 6,
        "name": "ASUS ROG Zephyrus G14",
        "store": "daraz",
        "category": "laptops",
        "category_label": "Laptops",
        "price": 1449.00,
        "original_price": 1599.00,
        "rating": 4.7,
        "reviews": 2891,
        "image": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=600&q=80",
        "badge": "Top Rated",
        "description": "AMD Ryzen 9 + RTX 4060 in a 14\" ultraportable. Serious gaming power without the bulk.",
        "affiliate_url": "https://asus.com",
        "manual_url": "",
        "features": ["RTX 4060", "Ryzen 9", "120Hz OLED", "2.2kg"],
    },
]

STORES = [
    {"slug": "amazon", "label": "Amazon", "icon": "🛒", "desc": "Amazon products & deals", "count": 5, "color": "#ff9900"},
    {"slug": "daraz", "label": "Daraz", "icon": "🛍️", "desc": "Daraz products & deals", "count": 1, "color": "#fe7300"},
]

CATEGORIES = []


STORE_LABELS = {"amazon": "Amazon", "daraz": "Daraz"}


@app.route("/")
def index():
    featured = [p for p in PRODUCTS if p["badge"]][:3]
    return render_template("index.html", products=featured, categories=CATEGORIES, stores=STORES)


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", stores=STORES, categories=CATEGORIES)


@app.route("/store/<slug>")
def store_view(slug):
    store = next((s for s in STORES if s["slug"] == slug), None)
    if not store:
        return "Store not found", 404
    items = [p for p in PRODUCTS if p["store"] == slug]
    return render_template("store.html", store=store, products=items, stores=STORES, categories=CATEGORIES)


@app.route("/category/<slug>")
def category(slug):
    cat = next((c for c in CATEGORIES if c["slug"] == slug), None)
    if not cat:
        return "Category not found", 404
    items = [p for p in PRODUCTS if p["category"] == slug]
    return render_template("category.html", category=cat, products=items, categories=CATEGORIES, stores=STORES)


@app.route("/product/<int:pid>")
def product(pid):
    item = next((p for p in PRODUCTS if p["id"] == pid), None)
    if not item:
        return "Product not found", 404
    related = [p for p in PRODUCTS if p["category"] == item["category"] and p["id"] != pid][:3]
    return render_template("product.html", product=item, related=related, categories=CATEGORIES, stores=STORES)


def _get_supabase_admin():
    if create_client is None:
        return None

    url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not service_role_key:
        return None

    # Use service role for writes
    # Note: supabase-py version in this project doesn't support auth={...}
    return create_client(url, service_role_key)



@app.post("/track-click")
def track_click():
    """Record a click and geolocate the visitor IP.

    Expected JSON body:
    { productId, affiliateUrl, referrer?, utm_source?, utm_medium?, utm_campaign?, utm_term?, utm_content? }
    """

    try:
        body = request.get_json(silent=True) or {}
        product_id = body.get("productId")
        affiliate_url = body.get("affiliateUrl")

        if not product_id or not affiliate_url:
            return jsonify({"error": "Missing productId or affiliateUrl"}), 400

        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.remote_addr
        country_code, country_name = get_country_from_ip(ip)

        supabase_admin = _get_supabase_admin()
        if supabase_admin is None:
            return jsonify({"error": "Supabase is not configured. Set SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY."}), 500

        # Schema expects affiliate_products.id as UUID.
        # Frontend currently sends numeric productId; convert/mapping is required.
        # For now, pass product_id through as-is (fix requires updating frontend/admin to use UUIDs).
        insert_row = {
            # Our Supabase schema stores product_id as TEXT for public numeric IDs
            "product_id": str(product_id),


            "affiliate_url": affiliate_url,
            "ip": ip,
            "user_agent": request.headers.get("User-Agent"),
            "country_code": country_code,
            "country_name": country_name,
            "referrer": body.get("referrer") or request.headers.get("Referer"),
            "utm_source": body.get("utm_source"),
            "utm_medium": body.get("utm_medium"),
            "utm_campaign": body.get("utm_campaign"),
            "utm_term": body.get("utm_term"),
            "utm_content": body.get("utm_content"),
        }

        # supabase-py API: insert(...).execute()
        # We use the service role client so writes succeed.
        resp = (
            supabase_admin.table("affiliate_clicks").insert(insert_row).execute()
        )

        return jsonify({"ok": True, "insert": resp.data if hasattr(resp, "data") else None}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _render_not_found(e=None):
    available = [
        "GET /",
        "GET /dashboard",
        "GET /store/<slug>",
        "GET /category/<slug>",
        "GET /product/<pid>",
        "POST /track-click",
    ]
    return (
        "<h1>404 - URL not found</h1>"
        "<p>Requested URL was not matched by any route.</p>"
        "<h3>Available routes:</h3><ul>"
        + "".join(f"<li>{r}</li>" for r in available)
        + "</ul><p>If you’re running a different server (e.g. api/), check its port too.</p>"
    ), 404


@app.errorhandler(404)
def not_found_handler(e):
    return _render_not_found(e)


@app.errorhandler(500)
def internal_error_handler(e):
    return (
        "<h1>500 - Server error</h1>"
        "<p>Something crashed while processing this request.</p>"
        "<p>Check Flask console output for traceback.</p>"
    ), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    # Avoid blank pages by ensuring Flask logs errors in console.
    app.run(debug=True, host="0.0.0.0", port=port)


