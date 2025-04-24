# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from db import fetch_data, execute_query

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "hospital_id" not in st.session_state:
    st.session_state.hospital_id = None
if "admin_username" not in st.session_state:
    st.session_state.admin_username = None

# --- Login Page ---
def login_page():
    st.title("Songblood Admin Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        query = """
            SELECT Hospital_ID FROM Admin 
            WHERE Admin_username = %s AND Admin_password = %s
        """
        result = fetch_data(query, (username, password))
        if result:
            st.session_state.logged_in = True
            st.session_state.hospital_id = result[0][0]
            st.session_state.admin_username = username
            st.rerun()
        else:
            st.error("Invalid credentials")

# --- Dashboard ---
def dashboard():
    st.title(f"🏥 Hospital Dashboard")
    st.subheader(f"Logged in as: {st.session_state.admin_username}")

    # Fetch current hospital's inventory
    query = """
        SELECT 'Red Blood' AS type, Blood_Type, Rh, SUM(Amount) AS total 
        FROM RedBlood_inventory 
        WHERE Hospital_ID = %s AND Expiration_date > CURRENT_DATE
        GROUP BY Blood_Type, Rh
        UNION ALL
        SELECT 'Plasma' AS type, Blood_Type, NULL AS Rh, SUM(Amount) AS total 
        FROM plasma_inventory 
        WHERE Hospital_ID = %s AND Expiration_date > CURRENT_DATE
        GROUP BY Blood_Type
        UNION ALL
        SELECT 'Platelets' AS type, Blood_Type, Rh, SUM(Amount) AS total 
        FROM platelets_inventory 
        WHERE Hospital_ID = %s AND Expiration_date > CURRENT_DATE
        GROUP BY Blood_Type, Rh
    """
    inventory = fetch_data(query, (st.session_state.hospital_id, st.session_state.hospital_id, st.session_state.hospital_id))
    
    # Display inventory
    if inventory:
        df = pd.DataFrame(inventory, columns=["Type", "Blood Type", "Rh", "Total"])
        st.write("### Current Inventory")
        fig = px.bar(df, x="Blood Type", y="Total", color="Type", barmode="group")
        st.plotly_chart(fig)
    else:
        st.warning("No inventory data found")

    # Surplus alerts (other hospitals)
    st.write("### Surplus Alerts")
    query = """
        SELECT h.Hospital_name, r.Blood_Type, r.Rh, SUM(r.Amount) AS total
        FROM RedBlood_inventory r
        JOIN hospital h ON r.Hospital_ID = h.Hospital_ID
        WHERE r.Hospital_ID != %s AND r.Expiration_date > CURRENT_DATE
        GROUP BY h.Hospital_name, r.Blood_Type, r.Rh
        ORDER BY total DESC
        LIMIT 5
    """
    surplus = fetch_data(query, (st.session_state.hospital_id,))
    if surplus:
        for row in surplus:
            st.info(f"{row[0]} has {row[3]} units of {row[1]}{row[2] or ''}")

# --- Add Supply ---
def add_supply():
    st.title("Add New Blood Supply")
    blood_type = st.selectbox("Blood Type", ["A", "B", "AB", "O"])
    rh = st.selectbox("Rh Factor", ["+", "-"])
    amount = st.number_input("Amount (ml)", min_value=100, max_value=500, step=50)
    donor_name = st.text_input("Donor Name")
    expiration_date = st.date_input("Expiration Date")

    if st.button("Submit"):
        query = """
            INSERT INTO RedBlood_inventory 
            (Donor_name, Amount, Hospital_ID, Expiration_date, Blood_Type, Rh)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        execute_query(query, (donor_name, amount, st.session_state.hospital_id, expiration_date, blood_type, rh))
        st.success("Blood supply added successfully!")

# --- Donor Search ---
def donor_search():
    st.title("Donor Search")
    search_query = st.text_input("Search by Donor Name or Bag ID")

    if search_query:
        query = """
            SELECT 'Red Blood' AS type, Bag_ID, Donor_name, Blood_Type, Rh, Hospital_ID
            FROM RedBlood_inventory 
            WHERE Donor_name ILIKE %s OR Bag_ID::TEXT ILIKE %s
            UNION ALL
            SELECT 'Plasma' AS type, bag_id, donor_name, blood_type, NULL AS Rh, hospital_id
            FROM plasma_inventory 
            WHERE donor_name ILIKE %s OR bag_id::TEXT ILIKE %s
            UNION ALL
            SELECT 'Platelets' AS type, bag_id, donor_name, blood_type, Rh, hospital_id
            FROM platelets_inventory 
            WHERE donor_name ILIKE %s OR bag_id::TEXT ILIKE %s
        """
        results = fetch_data(query, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
        
        if results:
            df = pd.DataFrame(results, columns=["Type", "Bag ID", "Donor Name", "Blood Type", "Rh", "Hospital ID"])
            st.dataframe(df)
        else:
            st.warning("No results found")

# --- Main App ---
def main():
    st.sidebar.title("Navigation")
    if not st.session_state.logged_in:
        login_page()
    else:
        page = st.sidebar.radio("Go to", ["Dashboard", "Add Supply", "Donor Search"])
        if page == "Dashboard":
            dashboard()
        elif page == "Add Supply":
            add_supply()
        elif page == "Donor Search":
            donor_search()

        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.hospital_id = None
            st.rerun()

if __name__ == "__main__":
    main()
