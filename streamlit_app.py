import streamlit as st
import psycopg2
import os
import pandas as pd
from openai import OpenAI   

st.set_page_config(layout="wide")
PASSWORD = "runproject2"

DB_URL = "postgresql://rameen:Lc1CuAsGOfS0dvErr8F0LZtiPBr1PW7s@dpg-d4l3apfpm1nc738jaj50-a.virginia-postgres.render.com/mini_project2"

st.title("Mini Project 2 – Streamlit + Render")

pw = st.text_input("Enter password:", type="password")
if pw != PASSWORD:
    st.stop()

st.success("Access granted!")


@st.cache_resource
def connect():
    return psycopg2.connect(DB_URL)

conn = connect()

left, right = st.columns(2)


with left:
    st.subheader("Run SQL Query")

    query = st.text_area("Enter SQL:", height=200, placeholder="SELECT * FROM region;")

    if st.button("Run SQL"):
        try:
            df = pd.read_sql(query, conn)
            st.dataframe(df)
        except Exception as e:
            st.error(f"Error: {e}")


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

            sql = response.choices[0].message.content.strip()
            st.code(sql)

            try:
                df = pd.read_sql(sql, conn)
                st.dataframe(df)
            except Exception as e:
                st.error(f"SQL Error: {e}")

        except Exception as e:
            st.error(f"ChatGPT error: {e}")
