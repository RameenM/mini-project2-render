import psycopg2
from psycopg2.extras import execute_batch
import sqlite3


DB_URL = "postgresql://rameen:Lc1CuAsGOfS0dvErr8F0LZtiPBr1PW7s@dpg-d4l3apfpm1nc738jaj50-a.virginia-postgres.render.com/mini_project2"



def get_pg_connection():
    return psycopg2.connect(DB_URL)


SQLITE_DB = "normalized.db"

def fetch_sqlite_table(table):
    conn = sqlite3.connect(SQLITE_DB)
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table};")
    rows = cur.fetchall()
    colnames = [d[0] for d in cur.description]
    conn.close()
    return colnames, rows


def create_tables_pg(conn):
    cur = conn.cursor()

  
    cur.execute("DROP TABLE IF EXISTS OrderDetail;")
    cur.execute("DROP TABLE IF EXISTS Product;")
    cur.execute("DROP TABLE IF EXISTS ProductCategory;")
    cur.execute("DROP TABLE IF EXISTS Customer;")
    cur.execute("DROP TABLE IF EXISTS Country;")
    cur.execute("DROP TABLE IF EXISTS Region;")

    
    cur.execute("""
        CREATE TABLE Region (
            RegionID INTEGER PRIMARY KEY,
            Region TEXT NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE Country (
            CountryID INTEGER PRIMARY KEY,
            Country TEXT NOT NULL,
            RegionID INTEGER NOT NULL REFERENCES Region(RegionID)
        );
    """)

    cur.execute("""
        CREATE TABLE Customer (
            CustomerID INTEGER PRIMARY KEY,
            FirstName TEXT NOT NULL,
            LastName TEXT NOT NULL,
            Address TEXT NOT NULL,
            City TEXT NOT NULL,
            CountryID INTEGER NOT NULL REFERENCES Country(CountryID)
        );
    """)

    cur.execute("""
        CREATE TABLE ProductCategory (
            ProductCategoryID INTEGER PRIMARY KEY,
            ProductCategory TEXT NOT NULL,
            ProductCategoryDescription TEXT NOT NULL
        );
    """)

    cur.execute("""
        CREATE TABLE Product (
            ProductID INTEGER PRIMARY KEY,
            ProductName TEXT NOT NULL,
            ProductUnitPrice REAL NOT NULL,
            ProductCategoryID INTEGER NOT NULL REFERENCES ProductCategory(ProductCategoryID)
        );
    """)

    cur.execute("""
        CREATE TABLE OrderDetail (
            OrderID INTEGER PRIMARY KEY,
            CustomerID INTEGER NOT NULL REFERENCES Customer(CustomerID),
            ProductID INTEGER NOT NULL REFERENCES Product(ProductID),
            OrderDate TEXT NOT NULL,
            QuantityOrdered INTEGER NOT NULL
        );
    """)

    conn.commit()


def insert_data_pg(conn, table_name):
    cur = conn.cursor()
    colnames, rows = fetch_sqlite_table(table_name)
    placeholder = ",".join(["%s"] * len(colnames))
    columns = ",".join(colnames)

    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholder});"
    execute_batch(cur, sql, rows)
    conn.commit()

# ====== MAIN ======
def main():
    print("Connecting to Render...")
    pg = get_pg_connection()
    print("Connected.")

    print("Creating tables on Render...")
    create_tables_pg(pg)
    print("Tables created.")

    print("Inserting data...")
    for table in ["Region", "Country", "Customer", "ProductCategory", "Product", "OrderDetail"]:
        print(f"   -> {table}")
        insert_data_pg(pg, table)

    print("Upload complete.")
    pg.close()

if __name__ == "__main__":
    main()
