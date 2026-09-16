import streamlit as st
import sqlalchemy
from sqlalchemy import text
import hashlib
from datetime import datetime

# ------------------------------
# Page Config
# ------------------------------
st.set_page_config(page_title="Stationery Shop", page_icon="✏️", layout="wide")

# ------------------------------
# Database Connection
# (Connection string is stored in Streamlit Secrets as DB_URL)
# ------------------------------
@st.cache_resource
def get_engine():
    return sqlalchemy.create_engine(st.secrets["DB_URL"])

engine = get_engine()

# ------------------------------
# Database Setup (creates tables if they don't exist yet)
# ------------------------------
def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'customer'
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                price NUMERIC NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0,
                image_url TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                username TEXT NOT NULL,
                order_time TIMESTAMP DEFAULT NOW(),
                total NUMERIC NOT NULL
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS order_items (
                id SERIAL PRIMARY KEY,
                order_id INTEGER REFERENCES orders(id),
                product_name TEXT,
                quantity INTEGER,
                price NUMERIC
            )
        """))

        # Seed default admin account if no users exist yet
        result = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
        if result == 0:
            admin_pw = hashlib.sha256("1234".encode()).hexdigest()
            conn.execute(
                text("INSERT INTO users (username, password, role) VALUES (:u, :p, 'admin')"),
                {"u": "admin", "p": admin_pw}
            )

        # Seed default products if none exist yet
        result = conn.execute(text("SELECT COUNT(*) FROM products")).scalar()
        if result == 0:
            default_products = [
                {"name": "Pencil", "price": 10, "stock": 50, "image_url": "image/pencil.jpg"},
                {"name": "Eraser", "price": 15, "stock": 50, "image_url": "image/eraser.jpg"},
                {"name": "Ruler", "price": 20, "stock": 50, "image_url": "image/ruler.jpg"},
            ]
            for p in default_products:
                conn.execute(
                    text("INSERT INTO products (name, price, stock, image_url) VALUES (:name, :price, :stock, :image_url)"),
                    p
                )

init_db()

# ------------------------------
# Helper Functions
# ------------------------------
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def get_products():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM products ORDER BY id")).mappings().all()
    return [dict(r) for r in rows]

def get_user(username):
    with engine.connect() as conn:
        row = conn.execute(text("SELECT * FROM users WHERE username = :u"), {"u": username}).mappings().first()
    return dict(row) if row else None

# ------------------------------
# Session State Setup
# ------------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "cart" not in st.session_state:
    st.session_state.cart = []
if "show_signup" not in st.session_state:
    st.session_state.show_signup = False

# ------------------------------
# Sidebar: Login / Signup / Logout
# ------------------------------
st.sidebar.title("Account")

if st.session_state.user is None:

    if not st.session_state.show_signup:
        st.sidebar.subheader("Log In")
        login_username = st.sidebar.text_input("Username", key="login_user")
        login_password = st.sidebar.text_input("Password", type="password", key="login_pw")

        if st.sidebar.button("Log In"):
            u = get_user(login_username)
            if u and u["password"] == hash_pw(login_password):
                st.session_state.user = {"username": u["username"], "role": u["role"]}
                st.rerun()
            else:
                st.sidebar.error("Incorrect username or password")

        if st.sidebar.button("Create a customer account"):
            st.session_state.show_signup = True
            st.rerun()

    else:
        st.sidebar.subheader("Sign Up (Customer)")
        new_username = st.sidebar.text_input("Choose a username", key="signup_user")
        new_password = st.sidebar.text_input("Choose a password", type="password", key="signup_pw")

        if st.sidebar.button("Create Account"):
            if not new_username or not new_password:
                st.sidebar.error("Please fill in both fields")
            elif get_user(new_username):
                st.sidebar.error("Username already taken")
            else:
                with engine.begin() as conn:
                    conn.execute(
                        text("INSERT INTO users (username, password, role) VALUES (:u, :p, 'customer')"),
                        {"u": new_username, "p": hash_pw(new_password)}
                    )
                st.sidebar.success("Account created! Please log in.")
                st.session_state.show_signup = False
                st.rerun()

        if st.sidebar.button("Back to login"):
            st.session_state.show_signup = False
            st.rerun()

else:
    st.sidebar.success(f"Logged in as: {st.session_state.user['username']} ({st.session_state.user['role']})")
    if st.sidebar.button("Log Out"):
        st.session_state.user = None
        st.session_state.cart = []
        st.rerun()

# ------------------------------
# Main Title
# ------------------------------
st.title("✏️ Stationery Shop")

# ==============================
# ADMIN VIEW
# ==============================
if st.session_state.user and st.session_state.user["role"] == "admin":

    tab1, tab2 = st.tabs(["Manage Products", "All Orders"])

    with tab1:
        st.subheader("Current Products")
        products = get_products()
        for p in products:
            with st.expander(f"{p['name']} — ${p['price']} — Stock: {p['stock']}"):
                new_name = st.text_input("Name", value=p["name"], key=f"name_{p['id']}")
                new_price = st.number_input("Price", value=float(p["price"]), key=f"price_{p['id']}")
                new_stock = st.number_input("Stock", value=int(p["stock"]), step=1, key=f"stock_{p['id']}")
                new_image = st.text_input("Image URL or path", value=p["image_url"] or "", key=f"img_{p['id']}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Save Changes", key=f"save_{p['id']}"):
                        with engine.begin() as conn:
                            conn.execute(
                                text("UPDATE products SET name=:n, price=:pr, stock=:s, image_url=:i WHERE id=:id"),
                                {"n": new_name, "pr": new_price, "s": new_stock, "i": new_image, "id": p["id"]}
                            )
                        st.success("Updated!")
                        st.rerun()
                with col2:
                    if st.button("Delete Product", key=f"del_{p['id']}"):
                        with engine.begin() as conn:
                            conn.execute(text("DELETE FROM products WHERE id=:id"), {"id": p["id"]})
                        st.success("Deleted!")
                        st.rerun()

        st.divider()
        st.subheader("Add New Product")
        with st.form("add_product_form"):
            add_name = st.text_input("Product Name")
            add_price = st.number_input("Price", min_value=0.0, step=1.0)
            add_stock = st.number_input("Stock", min_value=0, step=1)
            add_image = st.text_input("Image URL (e.g. https://... or image/filename.jpg)")
            submitted = st.form_submit_button("Add Product")
            if submitted:
                if not add_name:
                    st.error("Please enter a product name")
                else:
                    with engine.begin() as conn:
                        conn.execute(
                            text("INSERT INTO products (name, price, stock, image_url) VALUES (:n, :p, :s, :i)"),
                            {"n": add_name, "p": add_price, "s": add_stock, "i": add_image}
                        )
                    st.success(f"Added {add_name}!")
                    st.rerun()

    with tab2:
        st.subheader("All Orders")
        with engine.connect() as conn:
            orders = conn.execute(text("SELECT * FROM orders ORDER BY order_time DESC")).mappings().all()
        if not orders:
            st.info("No orders yet.")
        for o in orders:
            with st.expander(f"Order #{o['id']} — {o['username']} — ${o['total']} — {o['order_time']}"):
                with engine.connect() as conn:
                    items = conn.execute(
                        text("SELECT * FROM order_items WHERE order_id = :oid"), {"oid": o["id"]}
                    ).mappings().all()
                for item in items:
                    st.write(f"- {item['product_name']} x {item['quantity']} — ${item['price']}")

# ==============================
# CUSTOMER / GUEST VIEW
# ==============================
else:
    tab1, tab2 = st.tabs(["Shop", "My Orders"])

    with tab1:
        st.write("Welcome! Browse our products below:")
        products = get_products()
        cols = st.columns(3)

        for idx, p in enumerate(products):
            with cols[idx % 3]:
                if p["image_url"]:
                    st.image(p["image_url"], width=150)
                st.subheader(p["name"])
                st.write(f"Price: ${p['price']}")
                st.write(f"In stock: {p['stock']}")

                if st.session_state.user:
                    qty = st.number_input("Qty", min_value=1, max_value=max(int(p["stock"]), 1), step=1, key=f"qty_{p['id']}")
                    if st.button("Add to Cart", key=f"add_{p['id']}"):
                        if p["stock"] < qty:
                            st.error("Not enough stock")
                        else:
                            st.session_state.cart.append({
                                "id": p["id"], "name": p["name"], "price": float(p["price"]), "qty": qty
                            })
                            st.success(f"Added {qty} x {p['name']} to cart")
                else:
                    st.info("Log in to purchase")

        # ------------------------------
        # Shopping Cart & Checkout
        # ------------------------------
        st.divider()
        st.header("🛒 Shopping Cart")

        if not st.session_state.user:
            st.warning("Please log in to view your cart.")
        elif len(st.session_state.cart) == 0:
            st.info("Your cart is empty.")
        else:
            total = 0
            for i, item in enumerate(st.session_state.cart):
                st.write(f"- {item['name']} x {item['qty']} — ${item['price'] * item['qty']}")
                total += item['price'] * item['qty']

            st.write(f"**Total: ${total}**")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Clear Cart"):
                    st.session_state.cart = []
                    st.rerun()
            with col2:
                if st.button("Checkout"):
                    with engine.begin() as conn:
                        # check stock is still enough for every item
                        for item in st.session_state.cart:
                            current_stock = conn.execute(
                                text("SELECT stock FROM products WHERE id=:id"), {"id": item["id"]}
                            ).scalar()
                            if current_stock < item["qty"]:
                                st.error(f"Not enough stock for {item['name']}")
                                st.stop()

                        order_id = conn.execute(
                            text("INSERT INTO orders (username, total) VALUES (:u, :t) RETURNING id"),
                            {"u": st.session_state.user["username"], "t": total}
                        ).scalar()

                        for item in st.session_state.cart:
                            conn.execute(
                                text("INSERT INTO order_items (order_id, product_name, quantity, price) VALUES (:oid, :n, :q, :p)"),
                                {"oid": order_id, "n": item["name"], "q": item["qty"], "p": item["price"]}
                            )
                            conn.execute(
                                text("UPDATE products SET stock = stock - :q WHERE id=:id"),
                                {"q": item["qty"], "id": item["id"]}
                            )

                    st.session_state.cart = []
                    st.success("Order placed successfully!")
                    st.rerun()

    with tab2:
        st.subheader("My Order History")
        if not st.session_state.user:
            st.warning("Please log in to view your orders.")
        else:
            with engine.connect() as conn:
                orders = conn.execute(
                    text("SELECT * FROM orders WHERE username = :u ORDER BY order_time DESC"),
                    {"u": st.session_state.user["username"]}
                ).mappings().all()
            if not orders:
                st.info("You haven't placed any orders yet.")
            for o in orders:
                with st.expander(f"Order #{o['id']} — ${o['total']} — {o['order_time']}"):
                    with engine.connect() as conn:
                        items = conn.execute(
                            text("SELECT * FROM order_items WHERE order_id = :oid"), {"oid": o["id"]}
                        ).mappings().all()
                    for item in items:
                        st.write(f"- {item['product_name']} x {item['quantity']} — ${item['price']}")
