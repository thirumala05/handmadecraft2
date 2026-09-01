import os
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("HANDMADECRAFT_DB", BASE_DIR / "handmadecraft.db"))

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-change-this-secret"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db_connection() as db:
        schema = (BASE_DIR / "database.sql").read_text(encoding="utf-8")
        db.executescript(schema)

        # Lightweight migration for databases created by older project versions.
        existing_columns = {row[1] for row in db.execute("PRAGMA table_info(products)").fetchall()}
        migrations = {
            "sku": "ALTER TABLE products ADD COLUMN sku TEXT",
            "artisan": "ALTER TABLE products ADD COLUMN artisan TEXT NOT NULL DEFAULT 'HandmadeCraft Studio'",
            "material": "ALTER TABLE products ADD COLUMN material TEXT NOT NULL DEFAULT 'Handcrafted material'",
            "delivery_days": "ALTER TABLE products ADD COLUMN delivery_days INTEGER NOT NULL DEFAULT 5",
            "featured": "ALTER TABLE products ADD COLUMN featured INTEGER NOT NULL DEFAULT 0",
        }
        for column, statement in migrations.items():
            if column not in existing_columns:
                db.execute(statement)
        db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_products_sku_unique ON products(sku) WHERE sku IS NOT NULL")

        count = db.execute("SELECT COUNT(*) AS count FROM products").fetchone()["count"]
        if count == 0:
            db.executemany(
                """
                INSERT INTO products
                    (name, category, price, old_price, discount, rating, reviews,
                     image, description, stock, badge, sku, artisan, material,
                     delivery_days, featured)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    ("Blush Bloom Floral Keychain", "Keychains", 199, 299, 33, 4.8, 86, "catalog/catalog_01.jpg",
                     "Cute handmade floral keychain with soft chenille flowers, a ribbon bow and pearl-style detail.",
                     24, "Top Rated", "HC-KC-001", "HandmadeCraft Studio", "Chenille yarn", 4, 1),
                    ("Colorful Mini Bouquet Set", "Bouquets", 549, 799, 31, 4.7, 74, "catalog/catalog_02.jpg",
                     "A cheerful collection of miniature handmade flower bouquets, wrapped and ready for gifting.",
                     15, "Best Seller", "HC-BQ-002", "HandmadeCraft Studio", "Chenille yarn & wrap", 5, 1),
                    ("Royal Blue Rose Bouquet", "Bouquets", 899, 1299, 31, 4.9, 112, "catalog/catalog_03.jpg",
                     "Elegant deep-blue handmade rose bouquet with a premium wrap, ideal for special occasions.",
                     8, "Top Rated", "HC-BQ-003", "HandmadeCraft Studio", "Chenille yarn", 6, 1),
                    ("Aqua Daisy Keychain", "Keychains", 179, 249, 28, 4.6, 63, "catalog/catalog_04.jpg",
                     "Bright blue daisy-inspired handmade keychain with a playful, lightweight finish.",
                     30, "In Stock", "HC-KC-004", "HandmadeCraft Studio", "Chenille yarn", 3, 0),
                    ("Cute Floral Hair Clip Set", "Hair Accessories", 349, 499, 30, 4.8, 141, "catalog/catalog_05.jpg",
                     "Colorful handmade flower hair clips featuring bows, daisies and playful rainbow details.",
                     19, "Popular Pick", "HC-HA-005", "HandmadeCraft Studio", "Chenille yarn & metal clip", 4, 1),
                    ("Mini Flower Pot Collection", "Home Decor", 699, 999, 30, 4.9, 98, "catalog/catalog_06.jpg",
                     "A charming collection of handmade mini potted flowers in multiple colors for desks and shelves.",
                     10, "Top Rated", "HC-HD-006", "HandmadeCraft Studio", "Chenille yarn & pot", 6, 1),
                    ("Crimson Bloom Desk Pot", "Home Decor", 499, 749, 33, 4.7, 52, "catalog/catalog_07.jpg",
                     "Striking red handmade flower arrangement in a compact white planter for a warm desk accent.",
                     13, "In Stock", "HC-HD-007", "HandmadeCraft Studio", "Chenille yarn & planter", 5, 0),
                    ("Pink Daisy Desk Pot", "Home Decor", 499, 749, 33, 4.8, 67, "catalog/catalog_08.jpg",
                     "Soft pink handmade daisies arranged in a textured pot for a cute room or study corner.",
                     17, "Popular Pick", "HC-HD-008", "HandmadeCraft Studio", "Chenille yarn & planter", 5, 0),
                    ("Happy Flower Bookmark", "Stationery", 229, 349, 34, 4.9, 118, "catalog/catalog_09.jpg",
                     "A handmade floral bookmark with a bright red bloom and decorative gift-ready backing.",
                     26, "Best Seller", "HC-ST-009", "HandmadeCraft Studio", "Chenille yarn & card", 3, 1),
                    ("Midnight Rose Bouquet", "Bouquets", 999, 1499, 33, 4.9, 89, "catalog/catalog_10.jpg",
                     "Sophisticated navy and cream handmade roses arranged as a premium bouquet.",
                     7, "Premium Pick", "HC-BQ-010", "HandmadeCraft Studio", "Chenille yarn", 7, 1),
                    ("Champagne Rose Bouquet", "Bouquets", 1099, 1599, 31, 4.8, 71, "catalog/catalog_11.jpg",
                     "Warm champagne-toned handmade roses presented in a full bouquet with an elegant ribbon.",
                     6, "Limited Stock", "HC-BQ-011", "HandmadeCraft Studio", "Chenille yarn", 7, 1),
                    ("Velvet Red Rose Heart", "Bouquets", 949, 1399, 32, 4.9, 103, "catalog/catalog_12.jpg",
                     "Romantic red rose arrangement with a dramatic layered silhouette and decorative finish.",
                     9, "Top Rated", "HC-BQ-012", "HandmadeCraft Studio", "Chenille yarn", 6, 1),
                    ("Single Red Rose Gift Bouquet", "Gifts", 599, 899, 33, 4.8, 92, "catalog/catalog_13.jpg",
                     "A statement handmade red rose with baby's-breath style detailing and a gift-ready black wrap.",
                     14, "Gift Favourite", "HC-GI-013", "HandmadeCraft Studio", "Chenille yarn & wrap", 5, 1),
                    ("Birthday Heart Rose Bouquet", "Gifts", 1199, 1699, 29, 4.9, 128, "catalog/catalog_14.jpg",
                     "Heart-shaped handmade rose bouquet designed for birthdays, anniversaries and memorable gifting.",
                     5, "Best Seller", "HC-GI-014", "HandmadeCraft Studio", "Chenille yarn", 7, 1),
                    ("Strawberry Charm Keychain", "Keychains", 249, 349, 29, 4.7, 79, "catalog/catalog_15.jpg",
                     "Playful strawberry-shaped handmade keychain decorated with pearl-style accents.",
                     22, "New Arrival", "HC-KC-015", "HandmadeCraft Studio", "Chenille yarn", 4, 1),
                    ("Scarlet Rose Classic Bouquet", "Bouquets", 899, 1299, 31, 4.8, 95, "catalog/catalog_16.jpg",
                     "Classic red handmade rose bouquet finished with black-and-gold wrapping and a bold ribbon.",
                     11, "Popular Pick", "HC-BQ-016", "HandmadeCraft Studio", "Chenille yarn", 6, 0),
                    ("Black & White Contrast Bouquet", "Bouquets", 1099, 1599, 31, 4.9, 66, "catalog/catalog_17.jpg",
                     "A striking black, white and burgundy handmade floral arrangement for elegant gifting.",
                     6, "Premium Pick", "HC-BQ-017", "HandmadeCraft Studio", "Chenille yarn & wrap", 7, 1),
                    ("Electric Blue Rose Pair", "Bouquets", 999, 1499, 33, 4.9, 84, "catalog/catalog_18.jpg",
                     "Vivid blue handmade rose bouquets presented in dramatic black wrapping with metallic trim.",
                     8, "Top Rated", "HC-BQ-018", "HandmadeCraft Studio", "Chenille yarn", 7, 1),
                    ("HandmadeCraft Gift Collection", "Collections", 1299, 1899, 32, 4.8, 57, "catalog/catalog_19.jpg",
                     "A showcase collection featuring mini flower pots, bouquets, clips and floral gifts from the catalog.",
                     12, "Collection Pick", "HC-CO-019", "HandmadeCraft Studio", "Mixed handmade materials", 8, 1),
                ],
            )


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    with get_db_connection() as db:
        user = db.execute(
            "SELECT id, name, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return dict(user) if user else None


def require_user():
    user = current_user()
    if not user:
        return None, (jsonify({"success": False, "message": "Please log in first."}), 401)
    return user, None


@app.get("/")
def home():
    return render_template("index.html", user=current_user())


@app.get("/products")
def products_page():
    return redirect(url_for("home") + "#products")


@app.get("/cart")
def cart_page():
    return redirect(url_for("home") + "#products")


@app.get("/api/health")
def health():
    try:
        with get_db_connection() as db:
            db.execute("SELECT 1").fetchone()
        return jsonify({"success": True, "database": "connected"})
    except sqlite3.Error as exc:
        return jsonify({"success": False, "database": "error", "message": str(exc)}), 500


@app.get("/api/products")
def get_products():
    with get_db_connection() as db:
        rows = db.execute(
            """
            SELECT id, name, category, price, old_price AS oldPrice,
                   discount, rating, reviews, image, description, stock, badge,
                   sku, artisan, material, delivery_days AS deliveryDays, featured
            FROM products
            WHERE is_active = 1
            ORDER BY id DESC
            """
        ).fetchall()
    return jsonify({"success": True, "products": [dict(row) for row in rows]})


@app.get("/api/catalog")
def catalog():
    category = str(request.args.get("category", "")).strip()
    search = str(request.args.get("search", "")).strip().lower()

    with get_db_connection() as db:
        query = """
            SELECT id, name, category, price, old_price AS oldPrice,
                   discount, rating, reviews, image, description, stock, badge,
                   sku, artisan, material, delivery_days AS deliveryDays, featured
            FROM products
            WHERE is_active = 1
        """
        params = []
        if category and category.lower() != "all":
            query += " AND category = ?"
            params.append(category)
        if search:
            query += """ AND (
                lower(name) LIKE ? OR lower(category) LIKE ?
                OR lower(description) LIKE ? OR lower(artisan) LIKE ?
                OR lower(material) LIKE ? OR lower(sku) LIKE ?
            )"""
            like = f"%{search}%"
            params.extend([like, like, like, like, like, like])
        query += " ORDER BY featured DESC, id DESC"
        rows = db.execute(query, params).fetchall()

        categories = db.execute(
            "SELECT DISTINCT category FROM products WHERE is_active = 1 ORDER BY category"
        ).fetchall()

    return jsonify({
        "success": True,
        "products": [dict(row) for row in rows],
        "categories": [row["category"] for row in categories],
        "count": len(rows),
    })


@app.get("/api/products/<int:product_id>")
def get_product(product_id):
    with get_db_connection() as db:
        row = db.execute(
            """
            SELECT id, name, category, price, old_price AS oldPrice,
                   discount, rating, reviews, image, description, stock, badge
            FROM products
            WHERE id = ? AND is_active = 1
            """,
            (product_id,),
        ).fetchone()
    if not row:
        return jsonify({"success": False, "message": "Product not found."}), 404
    return jsonify({"success": True, "product": dict(row)})


@app.get("/api/me")
def me():
    user = current_user()
    return jsonify({"success": True, "user": user})


@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if len(name) < 2:
        return jsonify({"success": False, "message": "Please enter your name."}), 400
    if "@" not in email:
        return jsonify({"success": False, "message": "Enter a valid email address."}), 400
    if len(password) < 8:
        return jsonify({"success": False, "message": "Password must be at least 8 characters."}), 400

    try:
        with get_db_connection() as db:
            cursor = db.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "An account with that email already exists."}), 409

    session.clear()
    session["user_id"] = user_id
    return jsonify({"success": True, "user": {"id": user_id, "name": name, "email": email}}), 201


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    with get_db_connection() as db:
        user = db.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    session.clear()
    session["user_id"] = user["id"]
    return jsonify({
        "success": True,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"]},
    })


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"success": True})


@app.get("/api/cart")
def get_cart():
    user, error = require_user()
    if error:
        return error

    with get_db_connection() as db:
        rows = db.execute(
            """
            SELECT p.id, p.name, p.category, p.price, p.old_price AS oldPrice,
                   p.discount, p.rating, p.reviews, p.image, p.description,
                   p.stock, p.badge, c.quantity
            FROM cart_items c
            JOIN products p ON p.id = c.product_id
            WHERE c.user_id = ? AND p.is_active = 1
            ORDER BY c.created_at DESC
            """,
            (user["id"],),
        ).fetchall()

    items = [dict(row) for row in rows]
    total = sum(item["price"] * item["quantity"] for item in items)
    count = sum(item["quantity"] for item in items)
    return jsonify({"success": True, "items": items, "total": total, "count": count})


@app.post("/api/cart")
def add_to_cart():
    user, error = require_user()
    if error:
        return error

    data = request.get_json(silent=True) or {}
    try:
        product_id = int(data.get("product_id"))
        quantity = max(1, int(data.get("quantity", 1)))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid product."}), 400

    with get_db_connection() as db:
        product = db.execute(
            "SELECT id, stock FROM products WHERE id = ? AND is_active = 1",
            (product_id,),
        ).fetchone()
        if not product:
            return jsonify({"success": False, "message": "Product not found."}), 404

        existing = db.execute(
            "SELECT quantity FROM cart_items WHERE user_id = ? AND product_id = ?",
            (user["id"], product_id),
        ).fetchone()
        new_quantity = quantity + (existing["quantity"] if existing else 0)
        if new_quantity > product["stock"]:
            return jsonify({"success": False, "message": "Requested quantity exceeds available stock."}), 400

        db.execute(
            """
            INSERT INTO cart_items (user_id, product_id, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, product_id)
            DO UPDATE SET quantity = excluded.quantity, updated_at = CURRENT_TIMESTAMP
            """,
            (user["id"], product_id, new_quantity),
        )

    return jsonify({"success": True, "message": "Added to cart.", "quantity": new_quantity})


@app.patch("/api/cart/<int:product_id>")
def update_cart(product_id):
    user, error = require_user()
    if error:
        return error

    data = request.get_json(silent=True) or {}
    try:
        quantity = int(data.get("quantity"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Invalid quantity."}), 400

    with get_db_connection() as db:
        if quantity <= 0:
            db.execute(
                "DELETE FROM cart_items WHERE user_id = ? AND product_id = ?",
                (user["id"], product_id),
            )
            return jsonify({"success": True})

        product = db.execute(
            "SELECT stock FROM products WHERE id = ? AND is_active = 1",
            (product_id,),
        ).fetchone()
        if not product:
            return jsonify({"success": False, "message": "Product not found."}), 404
        if quantity > product["stock"]:
            return jsonify({"success": False, "message": "Requested quantity exceeds available stock."}), 400

        cursor = db.execute(
            """
            UPDATE cart_items SET quantity = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND product_id = ?
            """,
            (quantity, user["id"], product_id),
        )
        if cursor.rowcount == 0:
            return jsonify({"success": False, "message": "Cart item not found."}), 404

    return jsonify({"success": True})


@app.delete("/api/cart/<int:product_id>")
def remove_from_cart(product_id):
    user, error = require_user()
    if error:
        return error
    with get_db_connection() as db:
        db.execute(
            "DELETE FROM cart_items WHERE user_id = ? AND product_id = ?",
            (user["id"], product_id),
        )
    return jsonify({"success": True})


@app.post("/api/orders")
def create_order():
    user, error = require_user()
    if error:
        return error

    data = request.get_json(silent=True) or {}
    phone = str(data.get("phone", "")).strip()
    address = str(data.get("address", "")).strip()
    if len(phone) < 7 or len(address) < 8:
        return jsonify({"success": False, "message": "Enter a valid phone number and delivery address."}), 400

    db = get_db_connection()
    try:
        db.execute("BEGIN IMMEDIATE")
        cart = db.execute(
            """
            SELECT c.product_id, c.quantity, p.name, p.price, p.stock
            FROM cart_items c
            JOIN products p ON p.id = c.product_id
            WHERE c.user_id = ? AND p.is_active = 1
            """,
            (user["id"],),
        ).fetchall()
        if not cart:
            db.rollback()
            return jsonify({"success": False, "message": "Your cart is empty."}), 400

        total = 0
        for item in cart:
            if item["quantity"] > item["stock"]:
                db.rollback()
                return jsonify({"success": False, "message": f"Not enough stock for {item['name']}."}), 409
            total += item["price"] * item["quantity"]

        order_cursor = db.execute(
            """
            INSERT INTO orders (user_id, customer_name, email, phone, address, total_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending')
            """,
            (user["id"], user["name"], user["email"], phone, address, total),
        )
        order_id = order_cursor.lastrowid

        for item in cart:
            db.execute(
                """
                INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
                """,
                (order_id, item["product_id"], item["quantity"], item["price"]),
            )
            db.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (item["quantity"], item["product_id"]),
            )

        db.execute("DELETE FROM cart_items WHERE user_id = ?", (user["id"],))
        db.commit()
        return jsonify({"success": True, "order_id": order_id, "total": total}), 201
    except sqlite3.Error as exc:
        db.rollback()
        return jsonify({"success": False, "message": "Could not place order.", "detail": str(exc)}), 500
    finally:
        db.close()


@app.get("/api/orders")
def get_my_orders():
    user, error = require_user()
    if error:
        return error
    with get_db_connection() as db:
        rows = db.execute(
            """
            SELECT id, total_amount, status, created_at
            FROM orders
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user["id"],),
        ).fetchall()
    return jsonify({"success": True, "orders": [dict(row) for row in rows]})


init_db()

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "1") == "1")
