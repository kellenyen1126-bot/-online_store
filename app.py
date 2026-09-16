import streamlit as st

# ------------------------------
# Page Config
# ------------------------------
st.set_page_config(page_title="Stationery Shop", page_icon="✏️", layout="wide")

# ------------------------------
# Product Data
# (Replace with your real products, prices, and image URLs)
# ------------------------------
products = [
    {"id": 1, "name": "Pencil", "price": 10, "image": "image/pencil.jpg.jpg"},
    {"id": 2, "name": "Eraser", "price": 15, "image": "image/eraser.jpg.jpg"},
    {"id": 3, "name": "Ruler", "price": 20, "image": "image/ruler.jpg.jpg"},
]

# ------------------------------
# Demo user account
# (For real use, connect to a database instead)
# ------------------------------
USERS = {
    "admin": "1234"
}

# ------------------------------
# Session State Setup
# ------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "cart" not in st.session_state:
    st.session_state.cart = []

# ------------------------------
# Sidebar: Login / Logout
# ------------------------------
st.sidebar.title("Member Login")

if not st.session_state.logged_in:
    username_input = st.sidebar.text_input("Username")
    password_input = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Log In"):
        if username_input in USERS and USERS[username_input] == password_input:
            st.session_state.logged_in = True
            st.session_state.username = username_input
            st.sidebar.success(f"Welcome, {username_input}!")
        else:
            st.sidebar.error("Incorrect username or password")
else:
    st.sidebar.success(f"Logged in as: {st.session_state.username}")
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

# ------------------------------
# Main Page: Store Title
# ------------------------------
st.title("✏️ Stationery Shop")
st.write("Welcome! Browse our products below:")

# ------------------------------
# Product Listing
# ------------------------------
cols = st.columns(3)

for idx, product in enumerate(products):
    with cols[idx % 3]:
        st.image(product["image"], width=150)
        st.subheader(product["name"])
        st.write(f"Price: ${product['price']}")

        if st.session_state.logged_in:
            if st.button("Add to Cart", key=f"add_{product['id']}"):
                st.session_state.cart.append(product)
                st.success(f"Added {product['name']} to cart")
        else:
            st.info("Log in to purchase")

# ------------------------------
# Shopping Cart
# ------------------------------
st.divider()
st.header("Shopping Cart")

if not st.session_state.logged_in:
    st.warning("Please log in to view your cart.")
elif len(st.session_state.cart) == 0:
    st.info("Your cart is empty.")
else:
    total = 0
    for item in st.session_state.cart:
        st.write(f"- {item['name']} - ${item['price']}")
        total += item["price"]
    st.write(f"**Total: ${total}**")

    if st.button("Clear Cart"):
        st.session_state.cart = []
        st.rerun()
