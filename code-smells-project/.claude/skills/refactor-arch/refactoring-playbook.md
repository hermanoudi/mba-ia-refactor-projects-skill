# Refactoring Playbook

Each pattern maps to one or more anti-patterns from `anti-patterns-catalog.md`.

---

## P1 — Extract Model from God Class

**Targets:** C1 (God Class), C4 (Flat Architecture)

**Before** (Python/Flask — everything in one file):
```python
# app.py — 400 lines doing everything
@app.route('/products')
def get_products():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE active = 1")
    rows = cursor.fetchall()
    result = [{"id": r[0], "name": r[1], "price": r[2]} for r in rows]
    conn.close()
    return jsonify(result)
```

**After** — model handles data, controller handles logic, route handles HTTP:
```python
# models/product_model.py
def get_active_products(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price FROM products WHERE active = 1")
    rows = cursor.fetchall()
    return [{"id": r[0], "name": r[1], "price": r[2]} for r in rows]

# controllers/product_controller.py
from models.product_model import get_active_products

def list_products(conn):
    return get_active_products(conn)

# views/product_routes.py
from flask import Blueprint, jsonify
from controllers.product_controller import list_products

product_bp = Blueprint('products', __name__)

@product_bp.route('/products')
def get_products():
    products = list_products(current_app.db)
    return jsonify(products)
```

---

## P2 — Move Secrets to Environment Variables

**Targets:** C2 (Hardcoded Credentials)

**Before:**
```python
# app.py
app.config['SECRET_KEY'] = 'minha-chave-super-secreta-123'
DATABASE_URL = 'postgresql://admin:senha123@localhost/mydb'
```

**After:**
```python
# config/settings.py
import os

SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set")

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///dev.db')
```
```bash
# .env (add to .gitignore)
SECRET_KEY=use-a-real-random-value-here
DATABASE_URL=postgresql://user:pass@localhost/mydb
```

---

## P3 — Parameterize SQL Queries

**Targets:** C3 (SQL Injection)

**Before:**
```python
def get_user(username):
    cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

**After:**
```python
def get_user(username):
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    # or with psycopg2: cursor.execute("... WHERE username = %s", (username,))
```

---

## P4 — Extract Business Logic from Controller

**Targets:** H1 (Business Logic in Controller)

**Before** (Node.js/Express):
```javascript
// routes/order.routes.js
router.post('/orders', async (req, res) => {
  const { userId, items } = req.body;
  // 40 lines of business logic: calculate totals, check stock, apply discounts...
  let total = 0;
  for (const item of items) {
    const product = await Product.findById(item.productId);
    if (product.stock < item.qty) return res.status(400).json({ error: 'Out of stock' });
    total += product.price * item.qty * (item.qty > 10 ? 0.9 : 1);
  }
  const order = await Order.create({ userId, items, total });
  res.json(order);
});
```

**After:**
```javascript
// controllers/order.controller.js
const OrderModel = require('../models/order.model');
const ProductModel = require('../models/product.model');

async function createOrder(userId, items) {
  let total = 0;
  for (const item of items) {
    const product = await ProductModel.findById(item.productId);
    if (product.stock < item.qty) throw new Error('Out of stock');
    const discount = item.qty > 10 ? 0.9 : 1;
    total += product.price * item.qty * discount;
  }
  return OrderModel.create({ userId, items, total });
}

// routes/order.routes.js
router.post('/orders', async (req, res, next) => {
  try {
    const order = await createOrder(req.body.userId, req.body.items);
    res.json(order);
  } catch (err) {
    next(err);
  }
});
```

---

## P5 — Introduce Dependency Injection

**Targets:** H2 (Hard Coupling)

**Before:**
```python
class OrderService:
    def __init__(self):
        self.db = Database()          # hard-coupled
        self.emailer = EmailService() # hard-coupled

    def place_order(self, data):
        ...
```

**After:**
```python
class OrderService:
    def __init__(self, db, emailer):  # injected
        self.db = db
        self.emailer = emailer

# In app.py (composition root):
db = Database(config.DATABASE_URL)
emailer = EmailService(config.SMTP_HOST)
order_service = OrderService(db=db, emailer=emailer)
```

---

## P6 — Eliminate Global Mutable State

**Targets:** H3 (Global Mutable State)

**Before** (Flask):
```python
# app.py
cart = {}  # shared mutable global

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    cart[request.json['item']] = request.json['qty']  # race condition
```

**After:**
```python
# Use Flask's request-scoped context or session
from flask import session

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    cart = session.get('cart', {})
    cart[request.json['item']] = request.json['qty']
    session['cart'] = cart
    return jsonify(cart)
```

---

## P7 — Replace Deprecated APIs

**Targets:** H4 (Deprecated API Usage)

**Before** (Flask ≥ 2.3 deprecated `before_first_request`):
```python
@app.before_first_request
def init_db():
    db.create_all()
```

**After:**
```python
# Use app context directly in create_app()
def create_app():
    app = Flask(__name__)
    with app.app_context():
        db.create_all()
    return app
```

**Before** (Node.js deprecated `url.parse`):
```javascript
const url = require('url');
const parsed = url.parse(req.url);
```

**After:**
```javascript
const parsed = new URL(req.url, `http://${req.headers.host}`);
```

---

## P8 — Fix N+1 Queries

**Targets:** M1 (N+1 Query Problem)

**Before:**
```python
orders = Order.query.all()
for order in orders:
    # Executes a new query per order — N+1
    items = OrderItem.query.filter_by(order_id=order.id).all()
    order.items = items
```

**After:**
```python
# SQLAlchemy eager loading
orders = Order.query.options(joinedload(Order.items)).all()
# Single JOIN query, no loop queries
```

---

## P9 — Add Input Validation Layer

**Targets:** M2 (Missing Input Validation)

**Before** (Python/Flask):
```python
@app.route('/users', methods=['POST'])
def create_user():
    data = request.json  # no validation
    user = User(name=data['name'], email=data['email'])
    db.session.add(user)
```

**After** (with Marshmallow):
```python
from marshmallow import Schema, fields, ValidationError

class UserSchema(Schema):
    name = fields.Str(required=True, validate=lambda x: len(x) >= 2)
    email = fields.Email(required=True)

@app.route('/users', methods=['POST'])
def create_user():
    try:
        data = UserSchema().load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400
    user = User(**data)
    db.session.add(user)
```

---

## P10 — Add Centralized Error Handler

**Targets:** M3 (Improper Error Handling)

**Before:**
```python
@app.route('/products/<int:id>')
def get_product(id):
    try:
        product = Product.query.get(id)
        return jsonify(product.to_dict())
    except Exception as e:
        return str(e), 500  # leaks internal details
```

**After:**
```python
# middlewares/error_handler.py
def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(Exception)
    def unhandled(e):
        app.logger.exception("Unhandled error")
        return jsonify({"error": "Internal server error"}), 500

# app.py
from middlewares.error_handler import register_error_handlers
register_error_handlers(app)

# Route — let exceptions propagate to the handler
@app.route('/products/<int:id>')
def get_product(id):
    product = Product.query.get_or_404(id)
    return jsonify(product.to_dict())
```
