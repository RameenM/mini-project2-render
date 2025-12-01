import streamlit as st
import psycopg2
import pandas as pd
import os
from openai import OpenAI

# ------------------ UI STYLING ------------------
st.markdown("""
    <style>
        .stApp {
            background-color: #fafafa;
        }
        .main-header {
            font-size: 32px !important;
            font-weight: 700 !important;
            padding-bottom: 10px;
            color: #333333;
        }
        .subheader {
            font-size: 20px !important;
            margin-top: 15px;
            color: #4a4a4a !important;
        }
        .stTextArea textarea {
            border-radius: 10px !important;
        }
        .stSelectbox div {
            border-radius: 10px !important;
        }
        .stButton>button {
            background-color: #e86e9b !important;
            color: white !important;
            border-radius: 10px !important;
            height: 40px;
            font-size: 16px;
        }
        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            padding-left: 3rem;
            padding-right: 3rem;
        }
        .divider {
            border-bottom: 1px solid #ddd;
            margin-top: 10px;
            margin-bottom: 20px;
        }
    </style>
""", unsafe_allow_html=True)

st.set_page_config(layout="wide")
PASSWORD = "runproject2"

DB_URL = "postgresql://rameen:Lc1CuAsGOfS0dvErr8F0LZtiPBr1PW7s@dpg-d4l3apfpm1nc738jaj50-a.virginia-postgres.render.com/mini_project2"

# ------------------ TITLE ------------------
st.markdown("<div class='main-header'>Mini Project 2 – Streamlit + Render</div>", unsafe_allow_html=True)
st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

# ------------------ PASSWORD ------------------
pw = st.text_input("Enter password:", type="password")
if pw != PASSWORD:
    st.stop()

st.success("Access granted!")

@st.cache_resource
def connect():
    return psycopg2.connect(DB_URL)

conn = connect()

left, right = st.columns(2)

# ------------------ LEFT SIDE: MANUAL SQL ------------------
with left:
    st.markdown("<div class='subheader'>Run SQL Query</div>", unsafe_allow_html=True)

    sql_examples = {
        "Show all regions": "SELECT * FROM region;",
        "Top 10 best-selling products": """
            SELECT p.productname, SUM(od.quantityOrdered) AS total_sold
            FROM orderdetail od 
            JOIN product p ON od.productID = p.productID
            GROUP BY p.productname
            ORDER BY total_sold DESC
            LIMIT 10;
        """,
        "Revenue by region": """
            SELECT r.region,
                   SUM(p.productunitprice * od.quantityOrdered) AS revenue
            FROM orderdetail od
            JOIN product p ON od.productID = p.productID
            JOIN customer c ON od.customerID = c.customerID
            JOIN country co ON c.countryID = co.countryID
            JOIN region r ON co.regionID = r.regionID
            GROUP BY r.region
            ORDER BY revenue DESC;
        """
    }

    sql_choice = st.selectbox(
        "Choose an example SQL query (optional):",
        ["None"] + list(sql_examples.keys())
    )

    if sql_choice != "None":
        query = sql_examples[sql_choice]
        st.code(query)
    else:
        query = st.text_area("Enter SQL:", height=200, placeholder="SELECT * FROM region;")

    if st.button("Run SQL"):
        try:
            df = pd.read_sql(query, conn)
            st.dataframe(df)
        except Exception as e:
            st.error(f"Error: {e}")

# ------------------ RIGHT SIDE: CHATGPT NL → SQL ------------------
with right:
    st.markdown("<div class='subheader'>Natural Language → SQL (ChatGPT)</div>", unsafe_allow_html=True)

    nl_examples = {
        "Which products are selling the most?": "Which products are selling the most?",
        "Which region generates the highest revenue?": "Which region generates the highest revenue?",
        "Show me the total orders per country": "Show me the total orders per country",
        "What is the average quantity ordered per product?": "What is the average quantity ordered per product?"
    }

    nl_choice = st.selectbox(
        "Choose an example natural-language question (optional):",
        ["None"] + list(nl_examples.keys())
    )

    if nl_choice != "None":
        nl = nl_examples[nl_choice]
        st.code(nl)
    else:
        nl = st.text_area(
            "Ask a question:",
            placeholder="Show me the first 10 products"
        )

    if st.button("Generate SQL"):
        try:
            prompt = f"""
            Convert this request into a valid SQL query using the schema:
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

            # Clean SQL 
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
