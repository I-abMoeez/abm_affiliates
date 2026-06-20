# Admin dashboard (Python Flask)
# Features:
# - Admin authentication (email/password)
# - Manage affiliate products
# - View click analytics (by country / product / time)
#
# This file is intentionally self-contained.

import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, session, url_for, jsonify

try:
    from supabase import create_client
except Exception:
    create_client = None

# Load local .env if present
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path, override=False)
except Exception:
    pass

import click_tracker

app = Flask(__name__)

# --------------------
# Config / Supabase
# --------------------

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Authentication.
# Supabase Auth admin system uses an invite code + Supabase sign up/reset.
# Customer accounts should not access the admin dashboard because we enforce role checks.

# Invite code required to sign up as an admin (set in env). Example: export ADMIN_INVITE_CODE="change-me"
ADMIN_INVITE_CODE = os.getenv("ADMIN_INVITE_CODE", "03153157294")

# Optional: legacy local admin (still supported). If ADMIN_EMAIL/ADMIN_PASSWORD are set and Supabase is not configured,
# you can still use the local flow.
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "imoeezqureshi@gmail.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "memoeez7294")



# Secret for Flask sessions
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")
app.secret_key = FLASK_SECRET_KEY

# Basic security hardening for session cookies
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    # Set to True only when behind HTTPS. Leave False by default for local dev.
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
)

# Login rate limiting (simple in-memory). For multi-process deployments use Redis.
LOGIN_MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
LOGIN_WINDOW_SECONDS = int(os.getenv("LOGIN_WINDOW_SECONDS", "300"))
_login_attempts = {}  # {ip_or_email: [timestamps...] }



def _require_auth():
    # Role-based access control: only allow authenticated admin role
    if session.get("admin_role") != "admin" or not session.get("admin_authenticated"):
        return redirect(url_for("admin_login"))
    return None



def _get_supabase_clients():
    if create_client is None:
        return None, None
    if not SUPABASE_URL or not SUPABASE_ANON_KEY or not SUPABASE_SERVICE_ROLE_KEY:
        return None, None

    try:
        # supabase-py v2.x create_client signature does not accept `auth=`.
        # Creating clients without extra options keeps it compatible across versions.
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        supabase_anon = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        return supabase_anon, supabase_admin
    except Exception:
        return None, None


supabase_anon, supabase_admin = _get_supabase_clients()


# --------------------
# Routes: Auth
# --------------------


@app.route("/admin")
def admin_home():
    auth = _require_auth()
    if auth:
        return auth

    return redirect(url_for("admin_products"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_authenticated"):
        return redirect(url_for("admin_products"))

    error = None
    if request.method == "POST":
        # Simple rate limiting per client IP (best-effort)
        client_ip = (request.headers.get("X-Forwarded-For", "") or request.remote_addr or "").split(",")[0].strip()
        key = client_ip or "unknown"

        # Use timezone-aware UTC to avoid datetime.utcnow deprecation warnings
        now = datetime.now().timestamp()
        attempts = _login_attempts.get(key, [])
        # keep only attempts within window
        attempts = [t for t in attempts if now - t <= LOGIN_WINDOW_SECONDS]

        if len(attempts) >= LOGIN_MAX_ATTEMPTS:
            error = "Too many login attempts. Try again later."
        else:
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""

            # Avoid subtle truthiness bugs by normalizing once.
            expected_email = (ADMIN_EMAIL or "").strip().lower()
            expected_password = ADMIN_PASSWORD or ""

            if email == expected_email and password == expected_password:
                session["admin_role"] = "admin"
                session["admin_authenticated"] = True
                session["admin_email"] = email

                # reset attempts on success
                _login_attempts.pop(key, None)
                return redirect(url_for("admin_products"))

            # record failed attempt
            attempts.append(now)
            _login_attempts[key] = attempts
            error = "Invalid email or password"



    return render_template("admin/login.html", error=error, admin_email=ADMIN_EMAIL)


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


# --------------------
# Routes: Products
# --------------------


@app.route("/admin/products")
def admin_products():
    auth = _require_auth()
    if auth:
        return auth

    if supabase_anon is None:
        return "Supabase not configured", 500

    items = []
    data = (
        supabase_anon.table("affiliate_products")
        .select("id,name,category_id,category,image_url,affiliate_link,created_at,updated_at")
        .order("created_at", desc=True)
        .limit(200)
        .execute()
    )
    items = data.data or []

    return render_template("admin/products.html", items=items)


@app.route("/admin/products/new", methods=["GET", "POST"])
def admin_products_new():
    auth = _require_auth()
    if auth:
        return auth

    if request.method == "POST":
        if supabase_admin is None:
            return "Supabase not configured", 500

        payload = {
            "name": request.form.get("name"),
            "image_url": request.form.get("image_url"),
            "affiliate_link": request.form.get("affiliate_link"),
            "description": request.form.get("description"),
            "category": request.form.get("category"),
            "category_id": request.form.get("category_id") or None,
        }

        # Basic validation
        for k in ["name", "image_url", "affiliate_link", "description"]:
            if not payload.get(k):
                return render_template("admin/product_form.html", item=None, error=f"Missing field: {k}")

        supabase_admin.table("affiliate_products").insert(payload).execute()
        return redirect(url_for("admin_products"))

    return render_template("admin/product_form.html", item=None, error=None)


@app.route("/admin/products/<pid>/edit", methods=["GET", "POST"])
def admin_products_edit(pid):
    auth = _require_auth()
    if auth:
        return auth

    if supabase_anon is None:
        return "Supabase not configured", 500

    if request.method == "POST":
        payload = {
            "name": request.form.get("name"),
            "image_url": request.form.get("image_url"),
            "affiliate_link": request.form.get("affiliate_link"),
            "description": request.form.get("description"),
            "category": request.form.get("category"),
            "category_id": request.form.get("category_id") or None,
        }

        for k in ["name", "image_url", "affiliate_link", "description"]:
            if not payload.get(k):
                return render_template("admin/product_form.html", item={"id": pid, **payload}, error=f"Missing field: {k}")

        supabase_admin.table("affiliate_products").update(payload).eq("id", pid).execute()
        return redirect(url_for("admin_products"))

    item = (
        supabase_anon.table("affiliate_products")
        .select("id,name,category_id,category,image_url,affiliate_link,description,created_at,updated_at")
        .eq("id", pid)
        .single()
        .execute()
    ).data

    return render_template("admin/product_form.html", item=item, error=None)


@app.route("/admin/products/<pid>/delete", methods=["POST"])
def admin_products_delete(pid):
    auth = _require_auth()
    if auth:
        return auth

    if supabase_admin is None:
        return "Supabase not configured", 500

    supabase_admin.table("affiliate_products").delete().eq("id", pid).execute()
    return redirect(url_for("admin_products"))


# --------------------
# Routes: Analytics
# --------------------


@app.route("/admin/analytics")
def admin_analytics():
    auth = _require_auth()
    if auth:
        return auth

    if supabase_anon is None:
        return "Supabase not configured", 500

    # Total clicks
    total = supabase_anon.table("affiliate_clicks").select("id", count="exact").execute()
    total_count = (total.count or 0) if hasattr(total, "count") else 0

    # Clicks by country (last 90 days)
    # Using RPC is ideal, but we keep it simple via select + app-side aggregation.
    ninety_days_ago = (datetime.utcnow().timestamp() - 90 * 24 * 3600)
    ninety_days_ago_iso = datetime.utcfromtimestamp(ninety_days_ago).isoformat()

    rows = (
        supabase_anon.table("affiliate_clicks")
        .select("country_code,country_name")
        .gte("created_at", ninety_days_ago_iso)
        .limit(50000)
        .execute()
    ).data

    by_country = {}
    for r in rows or []:
        cc = r.get("country_code") or "??"
        cn = r.get("country_name") or None
        by_country[cc] = by_country.get(cc, {"country_code": cc, "country_name": cn, "count": 0})
        by_country[cc]["count"] += 1

    top_countries = sorted(by_country.values(), key=lambda x: x["count"], reverse=True)[:20]

    # Clicks by product (top 10)
    product_rows = (
        supabase_anon.table("affiliate_clicks")
        .select("product_id, affiliate_url")
        .limit(50000)
        .execute()
    ).data

    by_product = {}
    for r in product_rows or []:
        pid = r.get("product_id")
        by_product[pid] = by_product.get(pid, 0) + 1

    top_product_ids = sorted(by_product.keys(), key=lambda k: by_product[k], reverse=True)[:10]

    # Fetch product names for those IDs
    product_names = {}
    if top_product_ids:
        prod = (
            supabase_anon.table("affiliate_products")
            .select("id,name")
            .in_("id", top_product_ids)
            .execute()
        ).data
        for p in prod or []:
            product_names[p["id"]] = p.get("name")

    top_products = [
        {"product_id": pid, "name": product_names.get(pid) or "Unknown", "count": by_product[pid]}
        for pid in top_product_ids
    ]

    return render_template("admin/analytics.html", total_count=total_count, top_countries=top_countries, top_products=top_products)


# --------------------
# API (optional) for charting
# --------------------


@app.get("/admin/api/health")
def admin_health():
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("ADMIN_PORT", "5001")))

