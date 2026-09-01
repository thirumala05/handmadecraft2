# HandmadeCraft — Catalog & E-commerce Upgrade

A small Flask e-commerce demo with a clean responsive UI and a real database-backed user/cart/order flow.

## What was fixed

- Removed hard-coded frontend products and hard-coded user behavior.
- Fixed broken static paths (`style.css`, `script.js`, and product images).
- Replaced the invalid `database.sql` Python file with a real SQL schema.
- Uses SQLite by default so the project works without installing/configuring MySQL.
- Users are created through registration and stored in the database; there are **no seeded users**.
- Passwords are stored using Werkzeug password hashes, never plaintext.
- Cart items are stored per authenticated user in the database.
- Checkout validates current stock/prices on the server, writes orders/order items transactionally, reduces stock, and clears the cart.
- Added `/api/health` for a quick database check.

## Run

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

The SQLite database file `handmadecraft.db` is created automatically on first run. Product seed data is inserted only when the products table is empty. User accounts are never seeded/hard-coded.

## Production note

Set a strong `SECRET_KEY` environment variable before deployment. You can optionally set `HANDMADECRAFT_DB` to place the SQLite file elsewhere.


## Catalog upgrade

The project now includes a database-backed catalog layer:

- 12 seeded handmade products across Home Decor, Candles, Pottery, Gifts, Wellness, Textiles and Festive categories.
- Catalog search across product name, category, description, artisan, material and SKU.
- Category selector and sorting by featured status, price, rating and discount.
- Product detail modal now shows SKU, artisan, material and dispatch time.
- Featured catalog items are stored in the database rather than hard-coded in the browser.
- New `/api/catalog` endpoint returns catalog data and available categories.
- Existing registration, login, cart, checkout and order transaction flow remains intact.

### Windows quick start

```text
cd HANDMADECRAFT_NORMAL
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
py app.py
```

Then open `http://127.0.0.1:5000`.

If you previously ran an older version, this build includes a small automatic database migration for the new catalog columns. If you want the demo catalog to replace old seed data completely, delete `handmadecraft.db` once before starting.


## PDF catalog images
The `static/image/catalog/` folder contains all 19 pages from the supplied catalog PDF as product/showcase images. The catalog entries use these exact local images. The product names, prices, discounts, stock quantities and badges are demo storefront values created for this project and are not claimed as prices from the PDF.
