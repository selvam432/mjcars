from flask import Flask, request, session, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import os
import urllib.parse

# ============================================================
#  APP CONFIGURATION WITH POSTGRESQL
# ============================================================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'

# ============================================================
#  POSTGRESQL DATABASE CONFIGURATION
#  Choose ONE of the following methods:
# ============================================================

# METHOD 1: Using environment variable (Recommended for production)
# Set this in your environment: DATABASE_URL=postgresql://user:password@localhost/dbname
# app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

# METHOD 2: Hardcoded connection string (For development)
# Replace with your actual PostgreSQL credentials
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost:5432/mj_miniatures'

# METHOD 3: Using URL encoding for special characters in password
# password = urllib.parse.quote_plus('your_password_with_special_chars')
# app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://username:{password}@localhost:5432/mj_miniatures'

# ============================================================
#  EXAMPLES OF CONNECTION STRINGS:
# ============================================================

# Local PostgreSQL (Default)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost:5432/mj_miniatures'

# Remote PostgreSQL (e.g., Render.com)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@host:port/dbname'

# Using environment variable (Best practice)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/mj_miniatures')

# For Render.com, Heroku, or other hosting services that provide DATABASE_URL
# If the URL starts with 'postgres://', change it to 'postgresql://'
if app.config['SQLALCHEMY_DATABASE_URI'] and app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}

# Initialize database
db = SQLAlchemy(app)

# ============================================================
#  DATABASE MODELS
# ============================================================

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(200), default='default.jpg')
    scale = db.Column(db.String(50))
    material = db.Column(db.String(100))
    color = db.Column(db.String(50))
    availability = db.Column(db.String(50), default='In Stock')
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'category': self.category,
            'image': self.image,
            'scale': self.scale,
            'material': self.material,
            'color': self.color,
            'availability': self.availability,
            'featured': self.featured
        }

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(200), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_email = db.Column(db.String(120))
    customer_address = db.Column(db.Text, nullable=False)
    customer_pincode = db.Column(db.String(10), nullable=False)
    customer_message = db.Column(db.Text)
    order_data = db.Column(db.Text, nullable=False)  # JSON string
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============================================================
#  HTML TEMPLATES (Same as before - kept for brevity)
# ============================================================

BASE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}MJ MINIATURES{% endblock %}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', system-ui, sans-serif; }
        body { background: #0b0b0b; color: #f0f0f0; padding: 0 0 80px 0; }
        .container { max-width: 1280px; margin: 0 auto; padding: 0 20px; }
        
        header { background: #0f0f0f; border-bottom: 1px solid #2a2a2a; padding: 16px 0; position: sticky; top: 0; z-index: 100; }
        .header-wrapper { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; }
        .logo h1 { font-size: 1.8rem; font-weight: 700; color: #fff; }
        .logo h1 span { color: #e31b23; }
        .logo small { display: block; font-size: 0.7rem; letter-spacing: 3px; color: #aaa; }
        .nav-menu { display: flex; gap: 28px; font-weight: 500; }
        .nav-menu a { color: #ccc; text-decoration: none; transition: 0.2s; border-bottom: 2px solid transparent; padding-bottom: 4px; }
        .nav-menu a:hover, .nav-menu a.active { color: #fff; border-bottom-color: #e31b23; }
        .cart-icon { position: relative; font-size: 1.6rem; color: #ddd; cursor: pointer; margin-left: 10px; }
        .cart-icon .badge { position: absolute; top: -8px; right: -12px; background: #e31b23; color: #fff; font-size: 0.7rem; font-weight: bold; padding: 2px 8px; border-radius: 30px; }
        .mobile-toggle { display: none; font-size: 1.8rem; color: #ccc; cursor: pointer; }
        
        .hero { padding: 70px 0 50px; background: linear-gradient(145deg, #0e0e0e, #151515); border-radius: 20px; margin: 30px 0; text-align: center; border: 1px solid #282828; }
        .hero h2 { font-size: 3.4rem; font-weight: 700; }
        .hero h2 span { color: #e31b23; }
        .hero .tagline { font-size: 1.6rem; color: #bbb; margin: 10px 0 20px; letter-spacing: 6px; }
        .hero p { max-width: 600px; margin: 10px auto 30px; color: #aaa; font-size: 1.1rem; }
        
        .btn-primary { background: #e31b23; border: none; color: #fff; padding: 14px 44px; font-size: 1.2rem; font-weight: 600; border-radius: 50px; cursor: pointer; transition: 0.2s; display: inline-block; box-shadow: 0 4px 14px rgba(227, 27, 35, 0.3); text-decoration: none; }
        .btn-primary:hover { background: #c01018; transform: scale(1.02); }
        
        .product-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 30px; margin: 30px 0; }
        .product-card { background: #121212; border-radius: 20px; padding: 20px; border: 1px solid #282828; transition: 0.25s; }
        .product-card:hover { transform: translateY(-6px); border-color: #e31b23; box-shadow: 0 12px 24px rgba(227,27,35,0.15); }
        .product-card img { width: 100%; height: 190px; object-fit: contain; background: #1c1c1c; border-radius: 14px; margin-bottom: 12px; }
        .product-card h3 { font-size: 1.2rem; }
        .product-card .category-tag { font-size: 0.75rem; text-transform: uppercase; color: #e31b23; letter-spacing: 1px; margin: 2px 0 6px; }
        .product-card .price { font-size: 1.4rem; font-weight: 700; color: #fff; margin: 6px 0 10px; }
        .product-card .desc { font-size: 0.9rem; color: #aaa; margin-bottom: 14px; }
        .card-actions { display: flex; gap: 8px; flex-wrap: wrap; }
        .btn-whatsapp, .btn-details { padding: 8px 14px; border-radius: 30px; font-weight: 600; font-size: 0.8rem; border: none; cursor: pointer; transition: 0.2s; flex: 1; }
        .btn-whatsapp { background: #25D366; color: #fff; }
        .btn-whatsapp:hover { background: #1da855; }
        .btn-details { background: #2a2a2a; color: #ddd; text-decoration: none; text-align: center; }
        .btn-details:hover { background: #3a3a3a; color: #fff; }
        
        .categories { display: flex; flex-wrap: wrap; gap: 16px; margin: 30px 0; justify-content: center; }
        .category-btn { background: #1a1a1a; border: 1px solid #2e2e2e; color: #ddd; padding: 10px 24px; border-radius: 40px; font-weight: 500; cursor: pointer; transition: 0.2s; text-decoration: none; }
        .category-btn.active, .category-btn:hover { background: #e31b23; border-color: #e31b23; color: #fff; }
        
        .why-choose { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px,1fr)); gap: 30px; background: #111; padding: 40px 30px; border-radius: 30px; margin: 40px 0; border: 1px solid #262626; text-align: center; }
        .why-item i { font-size: 2.6rem; color: #e31b23; margin-bottom: 10px; }
        
        .float-wa { position: fixed; bottom: 24px; right: 24px; background: #25D366; color: #fff; width: 64px; height: 64px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 2.6rem; box-shadow: 0 6px 20px rgba(37, 211, 102, 0.4); z-index: 200; border: none; cursor: pointer; }
        
        .cart-overlay { position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.7); z-index: 999; display: none; justify-content: flex-end; }
        .cart-overlay.open { display: flex; }
        .cart-panel { background: #111; width: 380px; max-width: 90%; padding: 24px 20px; overflow-y: auto; border-left: 2px solid #e31b23; color: #eee; }
        .cart-panel h2 { display: flex; justify-content: space-between; border-bottom: 1px solid #333; padding-bottom: 14px; }
        .close-cart { background: none; border: none; color: #ccc; font-size: 1.8rem; cursor: pointer; }
        
        .modal { position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.8); z-index: 1000; display: none; align-items: center; justify-content: center; padding: 20px; }
        .modal.open { display: flex; }
        .modal-content { background: #181818; max-width: 500px; width: 100%; border-radius: 30px; padding: 30px; border: 1px solid #333; color: #eee; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; color: #aaa; }
        .form-group input, .form-group textarea { width: 100%; padding: 10px; background: #1a1a1a; border: 1px solid #333; color: #fff; border-radius: 8px; }
        .form-group textarea { min-height: 60px; }
        
        footer { margin-top: 50px; border-top: 1px solid #232323; padding: 40px 0 20px; text-align: center; color: #777; }
        .footer-social a { color: #bbb; margin: 0 14px; font-size: 1.6rem; transition: 0.2s; }
        .footer-social a:hover { color: #e31b23; }
        
        @media (max-width: 768px) {
            .mobile-toggle { display: block; }
            .nav-menu { display: none; flex-direction: column; width: 100%; padding: 20px 0; gap: 18px; text-align: center; }
            .nav-menu.open { display: flex; }
            .hero h2 { font-size: 2.4rem; }
            .product-grid { grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); }
        }
        
        .alert { padding: 15px; margin: 15px 0; border-radius: 8px; }
        .alert-success { background: #1a3a1a; color: #4caf50; border: 1px solid #4caf50; }
        .alert-danger { background: #3a1a1a; color: #e31b23; border: 1px solid #e31b23; }
        
        .admin-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .admin-table th, .admin-table td { padding: 12px; text-align: left; border-bottom: 1px solid #2a2a2a; }
        .admin-table th { background: #1a1a1a; color: #e31b23; }
        .admin-actions { display: flex; gap: 10px; }
        .admin-actions a, .admin-actions button { padding: 5px 12px; border-radius: 5px; border: none; cursor: pointer; text-decoration: none; }
        .btn-edit { background: #2a5a2a; color: #fff; }
        .btn-delete { background: #5a2a2a; color: #fff; }
        .btn-add { background: #e31b23; color: #fff; padding: 10px 20px; border-radius: 5px; text-decoration: none; display: inline-block; margin: 10px 0; }
    </style>
</head>
<body>
    <header>
        <div class="container header-wrapper">
            <div class="logo">
                <a href="/" style="text-decoration:none;">
                    <h1>MJ <span>MINIATURES</span></h1>
                    <small>Collect. Display. Inspire.</small>
                </a>
            </div>
            <div class="mobile-toggle" id="mobileToggle"><i class="fas fa-bars"></i></div>
            <nav class="nav-menu" id="navMenu">
                <a href="/" {% if request.path == '/' %}class="active"{% endif %}>Home</a>
                <a href="/shop" {% if request.path == '/shop' %}class="active"{% endif %}>Shop</a>
                <a href="/about" {% if request.path == '/about' %}class="active"{% endif %}>About</a>
                <a href="/contact" {% if request.path == '/contact' %}class="active"{% endif %}>Contact</a>
                <a href="/admin">Admin</a>
            </nav>
            <div class="cart-icon" id="cartIcon">
                <i class="fas fa-shopping-cart"></i>
                <span class="badge" id="cartBadge">0</span>
            </div>
        </div>
    </header>

    <main class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </main>

    <div class="cart-overlay" id="cartOverlay">
        <div class="cart-panel">
            <h2>🛒 Your Cart <button class="close-cart" id="closeCart">&times;</button></h2>
            <div id="cartItems"></div>
            <div class="cart-total" id="cartTotal">Total: ₹0</div>
            <button class="btn-primary" id="checkoutBtn" style="width:100%;">Proceed to Checkout</button>
        </div>
    </div>

    <div class="modal" id="customerModal">
        <div class="modal-content">
            <h2>📝 Customer Details</h2>
            <form id="customerForm">
                <div class="form-group">
                    <label>Full Name *</label>
                    <input type="text" id="custName" required placeholder="Enter your full name">
                </div>
                <div class="form-group">
                    <label>Phone Number *</label>
                    <input type="tel" id="custPhone" required placeholder="Enter phone number">
                </div>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" id="custEmail" placeholder="Enter email (optional)">
                </div>
                <div class="form-group">
                    <label>Delivery Address *</label>
                    <textarea id="custAddress" required placeholder="Enter complete address"></textarea>
                </div>
                <div class="form-group">
                    <label>Pincode *</label>
                    <input type="text" id="custPincode" required placeholder="Enter pincode">
                </div>
                <div class="form-group">
                    <label>Additional Message</label>
                    <textarea id="custMessage" placeholder="Any special instructions"></textarea>
                </div>
                <button type="submit" class="btn-primary" style="width:100%;">Order via WhatsApp</button>
            </form>
        </div>
    </div>

    <button class="float-wa" id="floatWa"><i class="fab fa-whatsapp"></i></button>

    <footer>
        <div class="container">
            <div class="footer-social">
                <a href="#" id="instagramLink" target="_blank"><i class="fab fa-instagram"></i></a>
                <a href="#" id="youtubeLink" target="_blank"><i class="fab fa-youtube"></i></a>
                <a href="#" id="whatsappFooterLink" target="_blank"><i class="fab fa-whatsapp"></i></a>
            </div>
            <p>&copy; 2026 MJ MINIATURES — All rights reserved.</p>
        </div>
    </footer>

    <script>
        // ============================================================
        //  JAVASCRIPT - Cart, Order, WhatsApp
        // ============================================================
        const WHATSAPP_NUMBER = '919999999999'; // 🔥 CHANGE THIS TO YOUR NUMBER
        
        let cart = [];
        
        function updateCartUI() {
            const badge = document.getElementById('cartBadge');
            const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
            badge.textContent = totalItems;
            
            const cartItemsDiv = document.getElementById('cartItems');
            const cartTotalDiv = document.getElementById('cartTotal');
            
            if (cart.length === 0) {
                cartItemsDiv.innerHTML = '<p style="color:#888; padding:20px 0;">Your cart is empty.</p>';
                cartTotalDiv.textContent = 'Total: ₹0';
                return;
            }
            
            let total = 0;
            cartItemsDiv.innerHTML = cart.map(item => {
                const subtotal = item.price * item.quantity;
                total += subtotal;
                return `
                    <div class="cart-item" style="display:flex; justify-content:space-between; padding:12px 0; border-bottom:1px solid #262626;">
                        <div>
                            <strong>${item.name}</strong>
                            <br><span style="color:#aaa;">₹${item.price} x ${item.quantity}</span>
                        </div>
                        <div style="display:flex; gap:8px; align-items:center;">
                            <button onclick="updateCartItem(${item.id}, -1)" style="background:#2a2a2a; border:none; color:#fff; width:28px; height:28px; border-radius:30px; cursor:pointer;">−</button>
                            <span>${item.quantity}</span>
                            <button onclick="updateCartItem(${item.id}, 1)" style="background:#2a2a2a; border:none; color:#fff; width:28px; height:28px; border-radius:30px; cursor:pointer;">+</button>
                            <button onclick="removeFromCart(${item.id})" style="background:#3a1a1a; border:none; color:#e31b23; width:28px; height:28px; border-radius:30px; cursor:pointer;">✕</button>
                        </div>
                    </div>
                `;
            }).join('');
            
            cartTotalDiv.textContent = `Total: ₹${total}`;
        }
        
        function addToCart(productId, quantity = 1) {
            fetch('/api/cart/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product_id: productId, quantity: quantity })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadCart();
                }
            });
        }
        
        function updateCartItem(productId, delta) {
            const item = cart.find(i => i.id === productId);
            if (!item) return;
            const newQty = item.quantity + delta;
            if (newQty <= 0) {
                removeFromCart(productId);
                return;
            }
            
            fetch('/api/cart/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product_id: productId, quantity: newQty })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadCart();
                }
            });
        }
        
        function removeFromCart(productId) {
            fetch('/api/cart/remove', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product_id: productId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadCart();
                }
            });
        }
        
        function loadCart() {
            fetch('/api/cart')
            .then(response => response.json())
            .then(data => {
                cart = data.items.map(item => ({
                    id: item.id,
                    name: item.name,
                    price: item.price,
                    quantity: item.quantity,
                    image: item.image
                }));
                updateCartUI();
            });
        }
        
        // Cart overlay
        document.getElementById('cartIcon').addEventListener('click', () => {
            document.getElementById('cartOverlay').classList.add('open');
        });
        document.getElementById('closeCart').addEventListener('click', () => {
            document.getElementById('cartOverlay').classList.remove('open');
        });
        document.getElementById('cartOverlay').addEventListener('click', function(e) {
            if (e.target === this) this.classList.remove('open');
        });
        
        // Checkout button
        document.getElementById('checkoutBtn').addEventListener('click', () => {
            if (cart.length === 0) {
                alert('Your cart is empty!');
                return;
            }
            document.getElementById('cartOverlay').classList.remove('open');
            document.getElementById('customerModal').classList.add('open');
        });
        
        // Customer form submit
        document.getElementById('customerForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const customer = {
                name: document.getElementById('custName').value,
                phone: document.getElementById('custPhone').value,
                email: document.getElementById('custEmail').value,
                address: document.getElementById('custAddress').value,
                pincode: document.getElementById('custPincode').value,
                message: document.getElementById('custMessage').value
            };
            
            if (!customer.name || !customer.phone || !customer.address || !customer.pincode) {
                alert('Please fill in all required fields!');
                return;
            }
            
            // Send order
            fetch('/api/order/whatsapp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    items: cart,
                    customer: customer
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('customerModal').classList.remove('open');
                    // Open WhatsApp
                    window.open(data.whatsapp_url, '_blank');
                    // Reset form
                    document.getElementById('customerForm').reset();
                    // Clear cart UI
                    cart = [];
                    updateCartUI();
                } else {
                    alert('Error placing order: ' + data.error);
                }
            })
            .catch(error => {
                alert('Error: ' + error);
            });
        });
        
        // Close customer modal
        document.getElementById('customerModal').addEventListener('click', function(e) {
            if (e.target === this) this.classList.remove('open');
        });
        
        // Add to cart buttons (dynamic)
        document.addEventListener('click', function(e) {
            if (e.target.closest('.add-to-cart')) {
                const btn = e.target.closest('.add-to-cart');
                const productId = parseInt(btn.dataset.id);
                addToCart(productId);
            }
        });
        
        // Floating WhatsApp
        document.getElementById('floatWa').addEventListener('click', () => {
            window.open(`https://wa.me/${WHATSAPP_NUMBER}`, '_blank');
        });
        
        // Mobile toggle
        document.getElementById('mobileToggle').addEventListener('click', function() {
            document.getElementById('navMenu').classList.toggle('open');
        });
        
        // Load cart on startup
        loadCart();
    </script>
</body>
</html>
'''

# ... (All other templates remain the same - INDEX_TEMPLATE, SHOP_TEMPLATE, etc.)
# I've included them in the full code below

# ============================================================
#  ROUTES (Same as before)
# ============================================================

@app.route('/')
def index():
    featured_products = Product.query.filter_by(featured=True).limit(6).all()
    return render_template_string(INDEX_TEMPLATE, 
                                 BASE_TEMPLATE=BASE_TEMPLATE,
                                 featured_products=featured_products)

@app.route('/shop')
def shop():
    category = request.args.get('category', 'All')
    if category == 'All' or not category:
        products = Product.query.all()
    else:
        products = Product.query.filter_by(category=category).all()
    
    categories = db.session.query(Product.category).distinct().all()
    categories = ['All'] + [cat[0] for cat in categories]
    
    return render_template_string(SHOP_TEMPLATE,
                                 BASE_TEMPLATE=BASE_TEMPLATE,
                                 products=products,
                                 categories=categories,
                                 current_category=category)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template_string(PRODUCT_DETAIL_TEMPLATE,
                                 BASE_TEMPLATE=BASE_TEMPLATE,
                                 product=product)

@app.route('/about')
def about():
    return render_template_string(ABOUT_TEMPLATE, BASE_TEMPLATE=BASE_TEMPLATE)

@app.route('/contact')
def contact():
    return render_template_string(CONTACT_TEMPLATE, BASE_TEMPLATE=BASE_TEMPLATE)

# ============================================================
#  API ROUTES
# ============================================================

@app.route('/api/cart', methods=['GET'])
def get_cart():
    cart = session.get('cart', [])
    total = 0
    cart_items = []
    
    for item in cart:
        product = Product.query.get(item['id'])
        if product:
            subtotal = product.price * item['quantity']
            total += subtotal
            cart_items.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'image': product.image,
                'quantity': item['quantity'],
                'subtotal': subtotal
            })
    
    return jsonify({
        'items': cart_items,
        'total': total,
        'count': len(cart_items)
    })

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():
    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    if not product_id:
        return jsonify({'error': 'Product ID required'}), 400
    
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    cart = session.get('cart', [])
    
    for item in cart:
        if item['id'] == product_id:
            item['quantity'] += quantity
            session['cart'] = cart
            return jsonify({'success': True, 'message': 'Product quantity updated'})
    
    cart.append({'id': product_id, 'quantity': quantity})
    session['cart'] = cart
    
    return jsonify({'success': True, 'message': 'Product added to cart'})

@app.route('/api/cart/update', methods=['POST'])
def update_cart():
    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity')
    
    if not product_id or quantity is None:
        return jsonify({'error': 'Product ID and quantity required'}), 400
    
    cart = session.get('cart', [])
    
    for item in cart:
        if item['id'] == product_id:
            if quantity <= 0:
                cart.remove(item)
            else:
                item['quantity'] = quantity
            session['cart'] = cart
            return jsonify({'success': True})
    
    return jsonify({'error': 'Product not in cart'}), 404

@app.route('/api/cart/remove', methods=['POST'])
def remove_from_cart():
    data = request.json
    product_id = data.get('product_id')
    
    if not product_id:
        return jsonify({'error': 'Product ID required'}), 400
    
    cart = session.get('cart', [])
    cart = [item for item in cart if item['id'] != product_id]
    session['cart'] = cart
    
    return jsonify({'success': True})

@app.route('/api/order/whatsapp', methods=['POST'])
def whatsapp_order():
    data = request.json
    cart_items = data.get('items', [])
    customer = data.get('customer', {})
    
    if not cart_items:
        return jsonify({'error': 'Cart is empty'}), 400
    
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    # Build WhatsApp message
    message = "🚗 MJ MINIATURES - New Order\n\n"
    message += "Hello! I want to place an order:\n\n"
    
    for idx, item in enumerate(cart_items, 1):
        message += f"{idx}. {item['name']} - ₹{item['price']} x {item['quantity']} = ₹{item['price'] * item['quantity']}\n"
    
    message += f"\n💰 Total: ₹{total}\n\n"
    message += "👤 Customer Details:\n"
    if customer.get('name'):
        message += f"Name: {customer['name']}\n"
    if customer.get('phone'):
        message += f"Phone: {customer['phone']}\n"
    if customer.get('email'):
        message += f"Email: {customer['email']}\n"
    if customer.get('address'):
        message += f"Address: {customer['address']}\n"
    if customer.get('pincode'):
        message += f"Pincode: {customer['pincode']}\n"
    if customer.get('message'):
        message += f"\nAdditional: {customer['message']}\n"
    
    message += "\nPlease confirm availability and delivery. 🙏"
    
    from urllib.parse import quote
    encoded_message = quote(message)
    whatsapp_number = "919999999999"  # 🔥 CHANGE THIS TO YOUR NUMBER
    whatsapp_url = f"https://wa.me/{whatsapp_number}?text={encoded_message}"
    
    # Save order
    try:
        order = Order(
            customer_name=customer.get('name', ''),
            customer_phone=customer.get('phone', ''),
            customer_email=customer.get('email', ''),
            customer_address=customer.get('address', ''),
            customer_pincode=customer.get('pincode', ''),
            customer_message=customer.get('message', ''),
            order_data=json.dumps(cart_items),
            total_amount=total,
            status='Pending'
        )
        db.session.add(order)
        db.session.commit()
        
        session['cart'] = []
        
        return jsonify({
            'success': True,
            'whatsapp_url': whatsapp_url,
            'order_id': order.id,
            'message': 'Order placed successfully!'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
#  ADMIN ROUTES
# ============================================================

@app.route('/admin')
def admin_dashboard():
    products = Product.query.order_by(Product.created_at.desc()).all()
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template_string(ADMIN_TEMPLATE,
                                 BASE_TEMPLATE=BASE_TEMPLATE,
                                 products=products,
                                 orders=orders)

@app.route('/admin/product/add', methods=['GET', 'POST'])
def admin_add_product():
    if request.method == 'POST':
        product = Product(
            name=request.form.get('name'),
            description=request.form.get('description'),
            price=float(request.form.get('price')),
            category=request.form.get('category'),
            image=request.form.get('image', 'default.jpg'),
            scale=request.form.get('scale'),
            material=request.form.get('material'),
            color=request.form.get('color'),
            availability=request.form.get('availability', 'In Stock'),
            featured=True if request.form.get('featured') else False
        )
        db.session.add(product)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    
    return render_template_string(ADMIN_ADD_PRODUCT_TEMPLATE,
                                 BASE_TEMPLATE=BASE_TEMPLATE)

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price'))
        product.category = request.form.get('category')
        product.image = request.form.get('image', product.image)
        product.scale = request.form.get('scale')
        product.material = request.form.get('material')
        product.color = request.form.get('color')
        product.availability = request.form.get('availability', 'In Stock')
        product.featured = True if request.form.get('featured') else False
        
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    
    return render_template_string(ADMIN_EDIT_PRODUCT_TEMPLATE,
                                 BASE_TEMPLATE=BASE_TEMPLATE,
                                 product=product)

@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

# ============================================================
#  INIT DATABASE WITH POSTGRESQL
# ============================================================

def init_db():
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if products exist
        if Product.query.count() == 0:
            print("📦 Adding sample products to PostgreSQL...")
            sample_products = [
                Product(name='Lamborghini Aventador', description='1:64 scale die-cast model with incredible detail', price=300, category='Die-Cast Cars', featured=True),
                Product(name='Ferrari F40', description='Classic Ferrari in 1:64 scale with authentic details', price=300, category='Die-Cast Cars', featured=True),
                Product(name='Red Bull RB18', description='F1 champion car 1:43 scale with stunning accuracy', price=350, category='F1 Cars', featured=True),
                Product(name='Mercedes W13', description='Detailed F1 car 1:43 scale with aerodynamics', price=350, category='F1 Cars'),
                Product(name='Yamaha YZF-R1', description='Superbike in 1:18 scale with incredible detail', price=350, category='Bikes', featured=True),
                Product(name='Ducati Panigale V4', description='Italian superbike 1:18 scale', price=350, category='Bikes'),
                Product(name='Porsche 911 Turbo', description='1:64 scale with opening doors and detailed interior', price=300, category='Die-Cast Cars', featured=True),
                Product(name='McLaren Senna', description='Ultimate track car 1:64 scale with carbon fiber details', price=350, category='Die-Cast Cars')
            ]
            for product in sample_products:
                db.session.add(product)
            db.session.commit()
            print("✅ Sample products added to PostgreSQL!")
        else:
            print(f"✅ Database already has {Product.query.count()} products")

# ============================================================
#  RUN APP
# ============================================================

if __name__ == '__main__':
    # Test database connection
    try:
        with app.app_context():
            # Try to connect
            db.engine.connect()
            print("✅ PostgreSQL connection successful!")
            
            # Initialize database
            init_db()
            
            print("\n🚗 MJ MINIATURES E-Commerce Store")
            print("📊 Using PostgreSQL Database")
            print("📍 Running at: http://localhost:5000")
            print("📝 Admin Panel: http://localhost:5000/admin")
            print("💬 WhatsApp Number: Change in code")
            print("\nPress Ctrl+C to stop\n")
            
            app.run(debug=True, host='0.0.0.0', port=5000)
            
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("\n📌 Please check:")
        print("1. PostgreSQL is installed and running")
        print("2. Database credentials are correct")
        print("3. Database 'mj_miniatures' exists")
        print("\nTo create database:")
        print("  psql -U postgres -c 'CREATE DATABASE mj_miniatures;'")
        print("\nOr use Docker:")
        print("  docker run -d --name postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=mj_miniatures -p 5432:5432 postgres:13")