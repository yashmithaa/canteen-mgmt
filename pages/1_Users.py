import streamlit as st
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db_utils
import config

st.set_page_config(
    page_title="Users Management",
    page_icon="👥",
    layout="wide"
)

st.title("Users Management")
st.markdown("Manage students, faculty, and staff information and wallets")
st.markdown("---")

# Create tabs
tab1, tab2, tab3 = st.tabs(["View Users", "Add New User", "Wallet Management"])

# Tab 1: View Users
with tab1:
    st.subheader("All Users")
    
    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        search_term = st.text_input("Search by Name or SRN", "")
    
    with col2:
        user_type_filter = st.selectbox(
            "Filter by User Type",
            ["All", "student", "faculty", "staff"]
        )
    
    with col3:
        st.write("")
        st.write("")
        refresh = st.button("Refresh", use_container_width=True)
    
    # Build query
    query = "SELECT * FROM Users WHERE 1=1"
    params = []
    
    if search_term:
        query += " AND (name LIKE %s OR srn LIKE %s)"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
    
    if user_type_filter != "All":
        query += " AND user_type = %s"
        params.append(user_type_filter)
    
    query += " ORDER BY created_at DESC"
    
    # Fetch users
    try:
        if params:
            users_df = db_utils.fetch_query(query, tuple(params))
        else:
            users_df = db_utils.fetch_query(query)
        
        if not users_df.empty:
            st.success(f"Found {len(users_df)} users")
            
            # Format wallet balance
            users_df['wallet_balance'] = users_df['wallet_balance'].apply(lambda x: f"₹{x:.2f}")
            
            # Display dataframe
            st.dataframe(
                users_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "user_id": "ID",
                    "srn": "SRN",
                    "name": "Name",
                    "email": "Email",
                    "phone": "Phone",
                    "user_type": st.column_config.TextColumn(
                        "User Type",
                        help="Student, Faculty, or Staff"
                    ),
                    "wallet_balance": "Wallet Balance",
                    "created_at": st.column_config.DatetimeColumn(
                        "Created At",
                        format="DD/MM/YYYY HH:mm"
                    ),
                    "updated_at": st.column_config.DatetimeColumn(
                        "Updated At",
                        format="DD/MM/YYYY HH:mm"
                    )
                }
            )
            
            # Export option
            # csv = users_df.to_csv(index=False)
            # st.download_button(
            #     label="📥 Download as CSV",
            #     data=csv,
            #     file_name="users_export.csv",
            #     mime="text/csv"
            # )
        else:
            st.info("No users found matching the criteria")
    
    except Exception as e:
        st.error(f"Error loading users: {e}")

# Tab 2: Add New User
with tab2:
    st.subheader("Add New User")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            srn = st.text_input("SRN *", placeholder="e.g., PES2UG23CS001")
            name = st.text_input("Full Name *", placeholder="e.g., John Doe")
            email = st.text_input("Email *", placeholder="e.g., john.doe@pes.edu")
        
        with col2:
            phone = st.text_input("Phone Number", placeholder="e.g., 9876543210")
            user_type = st.selectbox("User Type *", ["student", "faculty", "staff"])
            wallet_balance = st.number_input("Initial Wallet Balance", min_value=0.0, value=0.0, step=50.0)
        
        submitted = st.form_submit_button("Add User", use_container_width=True)
        
        if submitted:
            if not srn or not name or not email:
                st.error("Please fill in all required fields marked with *")
            else:
                # Validate phone (if provided)
                if phone and (len(phone) != 10 or not phone.isdigit()):
                    st.error("Phone number must be exactly 10 digits")
                else:
                    # Insert user
                    query = """
                    INSERT INTO Users (srn, name, email, phone, user_type, wallet_balance)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    params = (srn, name, email, phone if phone else None, user_type, wallet_balance)
                    
                    success = db_utils.execute_query(query, params)
                    
                    if success:
                        st.success(f"User {name} added successfully!")
                    else:
                        st.error("Failed to add user. Check if SRN or email already exists.")

# Tab 3: Wallet Management
with tab3:
    st.subheader("Wallet Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Add Funds")
        
        # Get all users for dropdown
        try:
            users = db_utils.fetch_query("SELECT user_id, name, srn, wallet_balance FROM Users ORDER BY name")
            
            if not users.empty:
                user_options = [f"{row['name']} ({row['srn']}) - ₹{row['wallet_balance']:.2f}" 
                               for _, row in users.iterrows()]
                user_ids = users['user_id'].tolist()
                
                selected_idx = st.selectbox(
                    "Select User",
                    range(len(user_options)),
                    format_func=lambda x: user_options[x]
                )
                
                selected_user_id = user_ids[selected_idx]
                selected_user_name = users.iloc[selected_idx]['name']
                current_balance = users.iloc[selected_idx]['wallet_balance']
                
                st.info(f"Current Balance: ₹{current_balance:.2f}")
                
                amount_to_add = st.number_input(
                    "Amount to Add (₹)",
                    min_value=1.0,
                    max_value=10000.0,
                    value=100.0,
                    step=50.0
                )
                
                if st.button("Add Funds", use_container_width=True):
                    try:
                        # Call stored procedure
                        db_utils.call_procedure('add_funds_to_wallet', (selected_user_id, amount_to_add))
                        
                        # Get new balance
                        new_balance = db_utils.call_function('get_wallet_balance', (selected_user_id,))
                        
                        st.success(f"Added ₹{amount_to_add:.2f} to {selected_user_name}'s wallet")
                        st.success(f"New Balance: ₹{new_balance:.2f}")
                    except Exception as e:
                        st.error(f"Error adding funds: {e}")
            else:
                st.warning("No users found in the database")
        
        except Exception as e:
            st.error(f"Error loading users: {e}")
    
    with col2:
        st.markdown("### Check Balance")
        
        try:
            users = db_utils.fetch_query("SELECT user_id, name, srn FROM Users ORDER BY name")
            
            if not users.empty:
                user_options_check = [f"{row['name']} ({row['srn']})" 
                                     for _, row in users.iterrows()]
                user_ids_check = users['user_id'].tolist()
                
                selected_idx_check = st.selectbox(
                    "Select User to Check",
                    range(len(user_options_check)),
                    format_func=lambda x: user_options_check[x],
                    key="check_balance"
                )
                
                selected_user_id_check = user_ids_check[selected_idx_check]
                selected_user_name_check = users.iloc[selected_idx_check]['name']
                
                if st.button("Check Balance", use_container_width=True):
                    try:
                        balance = db_utils.call_function('get_wallet_balance', (selected_user_id_check,))
                        
                        st.markdown(f"""
                        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                    padding: 2rem; border-radius: 10px; text-align: center; color: white;'>
                            <h3>{selected_user_name_check}</h3>
                            <h1>₹{balance:.2f}</h1>
                            <p>Current Wallet Balance</p>
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error checking balance: {e}")
            else:
                st.warning("No users found in the database")
        
        except Exception as e:
            st.error(f"Error loading users: {e}")
    
    st.markdown("---")
    
    # Recent wallet transactions
    st.subheader("Recent Wallet Transactions")
    
    try:
        transactions = db_utils.fetch_query("""
            SELECT 
                u.name,
                u.srn,
                o.order_id,
                o.total_amount,
                o.payment_status,
                o.order_date
            FROM Orders o
            JOIN Users u ON o.user_id = u.user_id
            WHERE o.payment_method = 'wallet'
            ORDER BY o.order_date DESC
            LIMIT 10
        """)
        
        if not transactions.empty:
            st.dataframe(transactions, use_container_width=True, hide_index=True)
        else:
            st.info("No recent wallet transactions")
    
    except Exception as e:
        st.error(f"Error loading transactions: {e}")
