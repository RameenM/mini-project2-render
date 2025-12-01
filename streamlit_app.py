import streamlit as st
import psycopg2
import pandas as pd
import os
from openai import OpenAI

# ---------------- DARK MODE PROFESSIONAL UI ----------------
st.markdown("""
    <style>
        .stApp {
            background-color: #111111;
        }
        .main-header {
            font-size: 32px !important;
            font-weight: 700 !important;
            padding-bottom: 10px;
            color: #ffffff;
        }
        .subheader {
            font-size: 20px !important;
            margin-top: 15px;
            color: #dddddd !important;
        }
        .divider {
            border-bottom: 1px solid #444444;
            margin-top: 10px;
            margin-bottom: 20px;
        }
        textarea, .stTextArea textarea {
            background-color: #1e1e1e !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            border: 1px solid #444444 !important;
        }
        .stTextInput>div>div>input {
            background-color: #1e1e1e !important;
            color: white !important;
            border-radius: 8px !important;
            border: 1px solid #444444 !important;
        }
        .stSelectbox div {
            background-color: #1e1e1e !important;
            color: #ffffff !important;
            border-radius: 8px !important;
        }
        .stButton>button {
            background-color: #0066cc !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 8px 18px;
            font-size: 15px;
            border: 1px solid #005bb5 !important;
        }
    </style>
""", unsafe_allow_html=True)

st.set_page_config(layout="wide")
PASSWORD = "runproject2"

DB_URL = "postgresql://rameen:Lc1CuAsGOfS0dvErr8F0LZtiPBr1PW7s@dpg-d4l3apfpm1nc738jaj50-a.virginia-postgres.render.com/mini_project2"

# ---------------- HEADER ----------------
st.markdown("<div class='main-header'>Mini Project 2 – Streamlit + Render</div>", unsafe_allow_html=True)
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ---------------- PASSWORD ----------------
pw = st.text_input("Enter password:", type="password")
if pw != PASSWORD:
    st.stop()

st.success("Access granted.")

@st.cache_resource
def connect():
    return psycopg2.connect(DB_URL)

conn = connect()

left, right = st.columns(2)

# ---------------- LEFT: MANUAL SQL ----------------
with left:
    st.markdown("<div class='subheader'>Run SQL Query</div>", unsafe_allow_html=True)

    sql_examples = {
        "Show all regions": "SELECT * FROM region;",
        "Show all countries": "SELECT * FROM country ORDER BY country;",
        "Show 10 customers": "SELECT * FROM customer LIMIT 10;",
        "Top 10 best-selling products": """
            SELECT p.productname, SUM(od.quantityOrdered) AS total_sold
            FROM orderdetail od
            JOIN product p ON od.productID = p.productID
            GROUP BY p.productname
            ORDER BY total_sold DESC
            LIMIT 10;
        """,
        "Total revenue by product": """
            SELECT p.productname,
                   SUM(p.productunitprice * od.quantityOrdered) AS revenue
            FROM orderdetail od
            JOIN product p ON od.productID = p.productID
            GROUP BY p.productname
            ORDER BY revenue DESC;
        """,
        "Total revenue by region": """
            SELECT r.region,
                   SUM(p.productunitprice * od.quantityOrdered) AS revenue
            FROM orderdetail od
            JOIN product p ON od.productID = p.productID
            JOIN customer c ON od.customerID = c.customerID
            JOIN country co ON c.countryID = co.countryID
            JOIN region r ON co.regionID = r.regionID
            GROUP BY r.region
            ORDER BY revenue DESC;
        """,
        "Customer order count by country": """
            SELECT co.country,
                   COUNT(*) AS total_orders
            FROM orderdetail od
            JOIN customer c ON od.customerID = c.customerID
            JOIN country co ON c.countryID = co.countryID
            GROUP BY co.country
            ORDER BY total_orders DESC;
        """,
        "Average quantity ordered per product": """
            SELECT p.productname,
                   AVG(od.quantityOrdered) AS avg_quantity
            FROM orderdetail od
            JOIN product p ON od.productID = p.productID
            GROUP BY p.productname
            ORDER BY avg_quantity DESC;
        """,
        "Most active customers (top 10)": """
            SELECT c.firstname || ' ' || c.lastname AS customer_name,
                   COUNT(*) AS order_count
            FROM orderdetail od
            JOIN customer c ON od.customerID = c.customerID
            GROUP BY customer_name
            ORDER BY order_count DESC
            LIMIT 10;
        """,
        "Highest revenue region (with avg qty)": """
            SELECT r.region,
                   SUM(p.productunitprice * od.quantityOrdered) AS total_revenue,
                   AVG(od.quantityOrdered) AS avg_quantity
            FROM orderdetail od
            JOIN product p ON od.productID = p.productID
            JOIN customer c ON od.customerID = c.customerID
            JOIN country co ON c.countryID = co.countryID
            JOIN region r ON co.regionID = r.regionID
            GROUP BY r.region
            ORDER BY total_revenue DESC
            LIMIT 1;
        """
    }

    sql_choice = st.selectbox(
        "Choose example query:",
        ["None"] + list(sql_examples.keys())
    )

    if sql_choice != "None":
        query = sql_examples[sql_choice]
    else:
        query = st.text_area("Enter SQL:", height=200, placeholder="SELECT * FROM region;")

    if st.button("Run SQL"):
        try:
            df = pd.read_sql(query, conn)
            st.dataframe(df)
        except Exception as e:
            st.error(f"Error: {e}")

# ---------------- RIGHT: NATURAL LANGUAGE → SQL ----------------
with right:
    st.markdown("<div class='subheader'>Natural Language → SQL</div>", unsafe_allow_html=True)

    nl_examples = {
        "Which products are selling the most?": "Which products are selling the most?",
        "Which region generates the highest revenue?": "Which region generates the highest revenue?",
        "Show total orders per country": "Show total orders per country",
        "Average quantity ordered per product": "Average quantity ordered per product",
        "Top 10 customers by number of orders": "Top 10 customers by number of orders",
        "Revenue by product": "Revenue by product",
        "List customers with their country": "List customers with their country",
        "Which country places the most orders?": "Which country places the most orders?",
        "Top 5 regions by revenue": "Top 5 regions by revenue",
        "Highest revenue region with average quantity": "Highest revenue region with average quantity"
    }

    nl_choice = st.selectbox(
        "Choose example question:",
        ["None"] + list(nl_examples.keys())
    )

    if nl_choice != "None":
        nl = nl_examples[nl_choice]
    else:
        nl = st.text_area("Ask a question:", placeholder="Show me the first 10 products")

    if st.button("Generate SQL"):
        try:
            prompt = f"""
            Convert this request into a valid SQL query using this schema:
            region(regionID, region)
            country(countryID, country, regionID)
            customer(customerID, firstname, lastname, address, city, countryID)
            product(productID, productname, productunitprice, productcategoryID)
            orderdetail(orderID, customerID, productID, orderDate, quantityOrdered)

            User request: {nl}
            Output ONLY the SQL query.
            """

            client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            sql_raw = response.choices[0].message.content.strip()

            clean_sql = sql_raw.replace("```sql", "").replace("```", "")
            if clean_sql.lower().startswith("sql "):
                clean_sql = clean_sql[4:]
            clean_sql = clean_sql.replace("`", "").strip()

            st.code(clean_sql)

            try:
                df = pd.read_sql(clean_sql, conn)
                st.dataframe(df)
            except Exception as e:
                st.error(f"SQL Error: {e}")

        except Exception as e:
            st.error(f"ChatGPT error: {e}")
