import streamlit as st
 
# ------------------------------
# 基本設定
# ------------------------------
st.set_page_config(page_title="線上商店", page_icon="🛒", layout="wide")
 
# ------------------------------
# 模擬商品資料(之後可以改成從資料庫或 CSV 讀取)
# ------------------------------
products = [
    {"id": 1, "name": "商品 A", "price": 299, "image": "https://via.placeholder.com/150"},
    {"id": 2, "name": "商品 B", "price": 599, "image": "https://via.placeholder.com/150"},
    {"id": 3, "name": "商品 C", "price": 199, "image": "https://via.placeholder.com/150"},
]
 
# ------------------------------
# 用 session_state 模擬登入狀態、購物車
# (取代 Flask 的 session)
# ------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "cart" not in st.session_state:
    st.session_state.cart = []
 
# ------------------------------
# 側邊欄:登入區
# (取代 Flask 的 /login 路由)
# ------------------------------
st.sidebar.title("會員登入")
 
if not st.session_state.logged_in:
    username = st.sidebar.text_input("帳號")
    password = st.sidebar.text_input("密碼", type="password")
    if st.sidebar.button("登入"):
        # 這裡示範,正式使用要接資料庫驗證帳密
        if username == "admin" and password == "1234":
            st.session_state.logged_in = True
            st.sidebar.success("登入成功")
        else:
            st.sidebar.error("帳號或密碼錯誤")
else:
    st.sidebar.success("已登入")
    if st.sidebar.button("登出"):
        st.session_state.logged_in = False
 
# ------------------------------
# 主畫面:商品列表
# (取代 Flask 的 render_template('index.html'))
# ------------------------------
st.title("🛒 線上商店")
st.write("歡迎光臨,以下是本店商品:")
 
cols = st.columns(3)
 
for idx, product in enumerate(products):
    with cols[idx % 3]:
        st.image(product["image"], width=150)
        st.subheader(product["name"])
        st.write(f"價格:NT$ {product['price']}")
        if st.button(f"加入購物車", key=f"add_{product['id']}"):
            st.session_state.cart.append(product)
            st.success(f"已加入 {product['name']}")
 
# ------------------------------
# 購物車顯示
# (取代 Flask 的 /cart 路由)
# ------------------------------
st.divider()
st.header("🛍️ 購物車")
 
if len(st.session_state.cart) == 0:
    st.info("購物車目前是空的")
else:
    total = 0
    for item in st.session_state.cart:
        st.write(f"- {item['name']} — NT$ {item['price']}")
        total += item["price"]
    st.write(f"**總金額:NT$ {total}**")
 
    if st.button("清空購物車"):
        st.session_state.cart = []
        st.rerun()
