import streamlit as st
from supabase import create_client
import hashlib

# ------------------------------
# Page Config
# ------------------------------
st.set_page_config(page_title="Stationery Shop", page_icon="✏️", layout="wide")

# ------------------------------
# Supabase Connection
# (URL and key are stored in Streamlit Secrets)
# ------------------------------
@st.cache_resource
def get_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

sb = get_client()

# ------------------------------
# Helper Functions
# ------------------------------
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def get_products():
    res = sb.table("products").select("*").order("id").execute()
    return res.data

def get_user(username):
    res = sb.table("users").select("*").eq("username", username).execute()
    return res.data[0] if res.data else None

# ------------------------------
# Session State Setup
# ------------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "cart" not in st.session_state:
    st.session_state.cart = []
if "show_signup" not in st.session_state:
    st.session_state.show_signup = False
if "signup_success" not in st.session_state:
    st.session_state.signup_success = False

# ------------------------------
# Sidebar: Login / Signup / Logout
# ------------------------------
st.sidebar.title("Account")

if st.session_state.user is None:

    if not st.session_state.show_signup:
        st.sidebar.subheader("Log In")

        if st.session_state.signup_success:
            st.sidebar.success("✅ Account created successfully! Please log in below.")
            st.session_state.signup_success = False

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
                sb.table("users").insert({
                    "username": new_username,
                    "password": hash_pw(new_password),
                    "role": "customer"
                }).execute()
                st.session_state.show_signup = False
                st.session_state.signup_success = True
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
            with st.expander(f"{p['name']} — NT${p['price']} — Stock: {p['stock']}"):
                new_name = st.text_input("Name", value=p["name"], key=f"name_{p['id']}")
                new_price = st.number_input("Price", value=float(p["price"]), key=f"price_{p['id']}")
                new_stock = st.number_input("Stock", value=int(p["stock"]), step=1, key=f"stock_{p['id']}")
                new_image = st.text_input("Image URL or path", value=p["image_url"] or "", key=f"img_{p['id']}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Save Changes", key=f"save_{p['id']}"):
                        sb.table("products").update({
                            "name": new_name, "price": new_price,
                            "stock": new_stock, "image_url": new_image
                        }).eq("id", p["id"]).execute()
                        st.success("Updated!")
                        st.rerun()
                with col2:
                    if st.button("Delete Product", key=f"del_{p['id']}"):
                        sb.table("products").delete().eq("id", p["id"]).execute()
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
                    sb.table("products").insert({
                        "name": add_name, "price": add_price,
                        "stock": add_stock, "image_url": add_image
                    }).execute()
                    st.success(f"Added {add_name}!")
                    st.rerun()

    with tab2:
        st.subheader("All Orders")
        orders = sb.table("orders").select("*").order("order_time", desc=True).execute().data
        if not orders:
            st.info("No orders yet.")
        for o in orders:
            with st.expander(f"Order #{o['id']} — {o['username']} — NT${o['total']} — {o['order_time']}"):
                items = sb.table("order_items").select("*").eq("order_id", o["id"]).execute().data
                for item in items:
                    st.write(f"- {item['product_name']} x {item['quantity']} — NT${item['price']}")

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
                st.write(f"Price: NT${p['price']}")
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
                st.write(f"- {item['name']} x {item['qty']} — NT${item['price'] * item['qty']}")
                total += item['price'] * item['qty']

            st.write(f"**Total: NT${total}**")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Clear Cart"):
                    st.session_state.cart = []
                    st.rerun()
            with col2:
                if st.button("Checkout"):
                    # check stock is still enough for every item
                    ok = True
                    for item in st.session_state.cart:
                        current = sb.table("products").select("stock").eq("id", item["id"]).execute().data
                        if not current or current[0]["stock"] < item["qty"]:
                            st.error(f"Not enough stock for {item['name']}")
                            ok = False
                            break

                    if ok:
                        order = sb.table("orders").insert({
                            "username": st.session_state.user["username"],
                            "total": total
                        }).execute()
                        order_id = order.data[0]["id"]

                        for item in st.session_state.cart:
                            sb.table("order_items").insert({
                                "order_id": order_id,
                                "product_name": item["name"],
                                "quantity": item["qty"],
                                "price": item["price"]
                            }).execute()

                            current = sb.table("products").select("stock").eq("id", item["id"]).execute().data[0]["stock"]
                            sb.table("products").update({
                                "stock": current - item["qty"]
                            }).eq("id", item["id"]).execute()

                        st.session_state.cart = []
                        st.success("Order placed successfully!")
                        st.rerun()

    with tab2:
        st.subheader("My Order History")
        if not st.session_state.user:
            st.warning("Please log in to view your orders.")
        else:
            orders = sb.table("orders").select("*").eq(
                "username", st.session_state.user["username"]
            ).order("order_time", desc=True).execute().data
            if not orders:
                st.info("You haven't placed any orders yet.")
            for o in orders:
                with st.expander(f"Order #{o['id']} — NT${o['total']} — {o['order_time']}"):
                    items = sb.table("order_items").select("*").eq("order_id", o["id"]).execute().data
                    for item in items:
                        st.write(f"- {item['product_name']} x {item['quantity']} — NT${item['price']}")
