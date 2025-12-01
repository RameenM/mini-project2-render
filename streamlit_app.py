```python
import streamlit as st
import psycopg2
import pandas as pd
import os
from openai import OpenAI

st.set_page_config(layout="wide")
PASSWORD = "runproject2"

DB_URL = "postgresql://rameen:Lc1CuAsGOfS0dvErr8F0LZtiPBr1PW7s@dpg-d4l3apfpm1nc738jaj50-a.virginia-postgres.render.com/mini_project2"

st.title("Mini Project 2 – Streamlit + Render")

pw = st.text_input("Enter password:", type="password")
if pw != PASSWORD:
    st.stop()

st.success("Access granted!")


# ---------- DATABASE CONNECTION ----------
@st.cache_resource
def connect():
    return psycopg2.connect(DB_URL)

conn = connect()


# ---------- LAYOUT ----------
left, right = st.columns(2)

# ========================================================
# LEFT SIDE — Manual SQL
# ========================================================
with left:
    st.subheader("Run SQL Query")

    query = st.text_area("Enter SQL:", height=200, placeholder="SELECT * FROM region;")

    if st.button("Run SQL"):
        try:
            df = pd.read_sql(query, conn)
            st.dataframe(df)
        except Exception as e:
            st.error(f"Error: {e}")


# ========================================================
# RIGHT SIDE — ChatGPT NATURAL LANGUAGE → SQL
# ========================================================
with right:
    st.subheader("Natural Language → SQL (ChatGPT)")

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

            # -------- CLEAN SQL OUTPUT --------
            clean_sql = sql_raw

            # Remove markdown fences
            clean_sql = clean_sql.replace("```sql", "")
            clean_sql = clean_sql.replace("```", "")

            # Remove "sql " prefix (case-insensitive)
            if clean_sql.lower().startswith("sql "):
                clean_sql = clean_sql[4:]

            # Remove stray backticks
            clean_sql = clean_sql.replace("`", "").strip()

            st.code(clean_sql)

            # -------- EXECUTE CLEANED SQL --------
            try:
                df = pd.read_sql(clean_sql, conn)
                st.dataframe(df)
            except Exception as e:
                st.error(f"SQL Error: {e}")

        except Exception as e:
            st.error(f"ChatGPT error: {e}")
