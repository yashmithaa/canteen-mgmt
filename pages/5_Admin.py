import streamlit as st
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db_utils
import config

st.set_page_config(
    page_title="Admin & Debug",
    page_icon="⚙️",
    layout="wide"
)

st.title("Admin & Debug Tools")
st.markdown("Database administration, monitoring, and debugging utilities")
st.markdown("---")

# Warning banner
st.warning("**Admin Area**: These tools can modify the database structure and data. Use with caution!")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "Database Info", 
    "Triggers", 
    "Procedures", 
    "Functions", 
    # "Integrity Checks"
])

# Tab 1: Database Info
with tab1:
    st.subheader("Database Information")
    
    # Connection test
    status, msg = db_utils.test_connection()
    if status:
        st.success(f"{msg}")
    else:
        st.error(f"{msg}")
    
    st.markdown("---")
    
    # Database statistics
    st.subheader("Table Statistics")
    
    try:
        stats = db_utils.fetch_query("""
            SELECT 'Users' as table_name, COUNT(*) as record_count FROM Users
            UNION ALL
            SELECT 'Categories', COUNT(*) FROM Categories
            UNION ALL
            SELECT 'Menu_Items', COUNT(*) FROM Menu_Items
            UNION ALL
            SELECT 'Orders', COUNT(*) FROM Orders
            UNION ALL
            SELECT 'Order_Items', COUNT(*) FROM Order_Items
        """)
        
        if not stats.empty:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.dataframe(stats, use_container_width=True, hide_index=True)
            
            with col2:
                import plotly.express as px
                fig = px.bar(
                    stats,
                    x='table_name',
                    y='record_count',
                    title='Records per Table',
                    labels={'table_name': 'Table', 'record_count': 'Record Count'},
                    color='record_count',
                    color_continuous_scale='viridis'
                )
                st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error loading stats: {e}")
    
    st.markdown("---")
    
    # Table structures
    st.subheader("Table Structures")
    
    tables = ['Users', 'Categories', 'Menu_Items', 'Orders', 'Order_Items']
    
    selected_table = st.selectbox("Select Table to View Structure", tables)
    
    if st.button("Show Structure", use_container_width=True):
        try:
            structure = db_utils.get_table_info(selected_table)
            if not structure.empty:
                st.dataframe(structure, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # Views
    st.subheader("Database Views")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("View Order_Summary", use_container_width=True):
            try:
                view_data = db_utils.fetch_query("SELECT * FROM Order_Summary LIMIT 10")
                st.dataframe(view_data, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        if st.button("View Popular_Items", use_container_width=True):
            try:
                view_data = db_utils.fetch_query("SELECT * FROM Popular_Items LIMIT 10")
                st.dataframe(view_data, use_container_width=True, hide_index=True)
            except Exception as e:
                st.error(f"Error: {e}")

# Tab 2: Triggers
with tab2:
    st.subheader("Database Triggers")
    
    try:
        triggers = db_utils.get_triggers()
        
        if not triggers.empty:
            st.success(f"Found {len(triggers)} trigger(s)")
            
            # Display triggers in expandable sections
            for idx, trigger in triggers.iterrows():
                with st.expander(f"🔹 {trigger['Trigger']} - {trigger['Event']} on {trigger['Table']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Timing:** {trigger['Timing']}")
                        st.markdown(f"**Event:** {trigger['Event']}")
                        st.markdown(f"**Table:** {trigger['Table']}")
                    
                    with col2:
                        st.markdown(f"**Definer:** {trigger['Definer']}")
                        st.markdown(f"**Character Set:** {trigger['character_set_client']}")
                    
                    st.markdown("**Statement:**")
                    st.code(trigger['Statement'], language='sql')
            
            # Export
            csv = triggers.to_csv(index=False)
            st.download_button(
                label="Export Triggers Info",
                data=csv,
                file_name="triggers_info.csv",
                mime="text/csv"
            )
        else:
            st.info("No triggers found in the database")
    
    except Exception as e:
        st.error(f"Error loading triggers: {e}")
    
    st.markdown("---")
    
    # Test triggers section
    st.subheader("Test Triggers")
    
    with st.expander("Test Wallet Deduction Trigger"):
        st.markdown("""
        This trigger (`deduct_wallet_after_payment`) automatically deducts money from user's wallet 
        when an order payment status changes to 'completed' and payment method is 'wallet'.
        """)
        
        # Get pending wallet orders
        pending_wallet_orders = db_utils.fetch_query("""
            SELECT o.order_id, u.name, o.total_amount, u.wallet_balance
            FROM Orders o
            JOIN Users u ON o.user_id = u.user_id
            WHERE o.payment_method = 'wallet' 
            AND o.payment_status = 'pending'
            LIMIT 5
        """)
        
        if not pending_wallet_orders.empty:
            st.dataframe(pending_wallet_orders, use_container_width=True, hide_index=True)
            st.info("Update payment status to 'completed' in the Orders page to see the trigger in action")
        else:
            st.info("No pending wallet orders to test")
    
    with st.expander("Test Stock Trigger"):
        st.markdown("""
        This trigger (`disable_item_when_out_of_stock`) automatically marks items as unavailable 
        when stock reaches 0.
        """)
        
        low_stock = db_utils.fetch_query("""
            SELECT item_id, item_name, stock, is_available
            FROM Menu_Items
            WHERE stock <= 5
            ORDER BY stock ASC
            LIMIT 5
        """)
        
        if not low_stock.empty:
            st.dataframe(low_stock, use_container_width=True, hide_index=True)
            st.info("Set stock to 0 in Menu Management to see auto-disable in action")
        else:
            st.success("All items have healthy stock levels")

# Tab 3: Procedures
with tab3:
    st.subheader("Stored Procedures")
    
    try:
        procedures = db_utils.get_procedures()
        
        if not procedures.empty:
            # Filter for canteen database
            procedures = procedures[procedures['Db'] == config.DB_NAME]
            
            st.success(f"Found {len(procedures)} procedure(s)")
            
            # Display procedures
            for idx, proc in procedures.iterrows():
                with st.expander(f"🔹 {proc['Name']} ({proc['Type']})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Database:** {proc['Db']}")
                        st.markdown(f"**Type:** {proc['Type']}")
                        st.markdown(f"**Definer:** {proc['Definer']}")
                    
                    with col2:
                        st.markdown(f"**Created:** {proc['Created']}")
                        st.markdown(f"**Modified:** {proc['Modified']}")
                        st.markdown(f"**Character Set:** {proc['character_set_client']}")
            
            # Export
            csv = procedures.to_csv(index=False)
            st.download_button(
                label="Export Procedures Info",
                data=csv,
                file_name="procedures_info.csv",
                mime="text/csv"
            )
        else:
            st.info("No procedures found in the database")
    
    except Exception as e:
        st.error(f"Error loading procedures: {e}")
    
    st.markdown("---")
    
    # Test procedures
    st.subheader("Test Stored Procedures")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("Test add_funds_to_wallet"):
            st.markdown("Add funds to a user's wallet")
            
            users = db_utils.fetch_query("SELECT user_id, name, wallet_balance FROM Users LIMIT 5")
            if not users.empty:
                st.dataframe(users, use_container_width=True, hide_index=True)
                
                test_user_id = st.number_input("User ID", min_value=1, value=1)
                test_amount = st.number_input("Amount to Add", min_value=1.0, value=100.0)
                
                if st.button("Test Add Funds", key="test_add_funds"):
                    try:
                        db_utils.call_procedure('add_funds_to_wallet', (test_user_id, test_amount))
                        st.success(f"Added ₹{test_amount} to user {test_user_id}")
                    except Exception as e:
                        st.error(f"Error: {e}")
    
    with col2:
        with st.expander("Test place_new_order"):
            st.markdown("Place a new order using stored procedure")
            
            st.info("This procedure creates a new order with one item")
            
            test_user = st.number_input("User ID", min_value=1, value=1, key="order_user")
            test_method = st.selectbox("Payment Method", ["wallet", "cash", "upi", "card"])
            test_item = st.number_input("Item ID", min_value=1, value=1)
            test_qty = st.number_input("Quantity", min_value=1, value=1)
            
            if st.button("🛒 Test Place Order", key="test_place_order"):
                try:
                    result = db_utils.call_procedure(
                        'place_new_order',
                        (test_user, test_method, test_item, test_qty)
                    )
                    if result:
                        st.success(f"Order placed! Order ID: {result[0][0]}")
                except Exception as e:
                    st.error(f"Error: {e}")

# Tab 4: Functions
with tab4:
    st.subheader("Stored Functions")
    
    try:
        functions = db_utils.get_functions()
        
        if not functions.empty:
            # Filter for canteen database
            functions = functions[functions['Db'] == config.DB_NAME]
            
            st.success(f"Found {len(functions)} function(s)")
            
            # Display functions
            for idx, func in functions.iterrows():
                with st.expander(f"🔹 {func['Name']} ({func['Type']})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Database:** {func['Db']}")
                        st.markdown(f"**Type:** {func['Type']}")
                        st.markdown(f"**Definer:** {func['Definer']}")
                    
                    with col2:
                        st.markdown(f"**Created:** {func['Created']}")
                        st.markdown(f"**Modified:** {func['Modified']}")
                        st.markdown(f"**Character Set:** {func['character_set_client']}")
            
            # Export
            csv = functions.to_csv(index=False)
            st.download_button(
                label="Export Functions Info",
                data=csv,
                file_name="functions_info.csv",
                mime="text/csv"
            )
        else:
            st.info("No functions found in the database")
    
    except Exception as e:
        st.error(f"Error loading functions: {e}")
    
    st.markdown("---")
    
    # Test functions
    st.subheader("Test Stored Functions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.expander("Test get_wallet_balance"):
            st.markdown("Get user's current wallet balance")
            
            test_user_id = st.number_input("User ID", min_value=1, value=1, key="func_user")
            
            if st.button("Check Balance", key="test_balance"):
                try:
                    balance = db_utils.call_function('get_wallet_balance', (test_user_id,))
                    st.success(f"Balance: ₹{balance:.2f}")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col2:
        with st.expander("Test get_order_total"):
            st.markdown("Calculate total for an order")
            
            test_order_id = st.number_input("Order ID", min_value=1, value=1, key="func_order")
            
            if st.button("Get Total", key="test_total"):
                try:
                    total = db_utils.call_function('get_order_total', (test_order_id,))
                    st.success(f"Order Total: ₹{total:.2f}")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col3:
        with st.expander("Test get_total_sales_for_item"):
            st.markdown("Get total sales revenue for an item")
            
            test_item_id = st.number_input("Item ID", min_value=1, value=1, key="func_item")
            
            if st.button("Get Sales", key="test_sales"):
                try:
                    sales = db_utils.call_function('get_total_sales_for_item', (test_item_id,))
                    st.success(f"Total Sales: ₹{sales:.2f}")
                except Exception as e:
                    st.error(f"Error: {e}")

# Tab 5: Integrity Checks
# with tab5:
    st.subheader("Data Integrity Checks")
    
    st.markdown("""
    These checks verify the referential integrity and data consistency of the database.
    All checks should return 0 violations for a healthy database.
    """)
    
    if st.button("Run All Integrity Checks", use_container_width=True, type="primary"):
        try:
            # Test 1: Orders without valid users
            test1 = db_utils.fetch_query("""
                SELECT 
                    'Orders without valid user' as test,
                    COUNT(*) as violations
                FROM Orders o 
                LEFT JOIN Users u ON o.user_id = u.user_id 
                WHERE u.user_id IS NULL
            """)
            
            # Test 2: Order_Items without valid orders
            test2 = db_utils.fetch_query("""
                SELECT 
                    'Order_Items without valid order' as test,
                    COUNT(*) as violations
                FROM Order_Items oi 
                LEFT JOIN Orders o ON oi.order_id = o.order_id 
                WHERE o.order_id IS NULL
            """)
            
            # Test 3: Order_Items without valid menu items
            test3 = db_utils.fetch_query("""
                SELECT 
                    'Order_Items without valid menu item' as test,
                    COUNT(*) as violations
                FROM Order_Items oi 
                LEFT JOIN Menu_Items mi ON oi.item_id = mi.item_id 
                WHERE mi.item_id IS NULL
            """)
            
            # Test 4: Menu_Items without valid categories
            test4 = db_utils.fetch_query("""
                SELECT 
                    'Menu_Items without valid category' as test,
                    COUNT(*) as violations
                FROM Menu_Items mi 
                LEFT JOIN Categories c ON mi.category_id = c.category_id 
                WHERE c.category_id IS NULL
            """)
            
            # Test 5: Negative wallet balances
            test5 = db_utils.fetch_query("""
                SELECT 
                    'Users with negative balance' as test,
                    COUNT(*) as violations
                FROM Users
                WHERE wallet_balance < 0
            """)
            
            # Test 6: Duplicate SRNs
            test6 = db_utils.fetch_query("""
                SELECT 
                    'Duplicate SRNs' as test,
                    COUNT(*) - COUNT(DISTINCT srn) as violations
                FROM Users
            """)
            
            # Combine all tests
            all_tests = pd.concat([test1, test2, test3, test4, test5, test6], ignore_index=True)
            
            # Display results
            st.subheader("Integrity Check Results")
            
            # Color code the results
            def highlight_violations(row):
                if row['violations'] > 0:
                    return ['background-color: #ffcccc'] * len(row)
                else:
                    return ['background-color: #ccffcc'] * len(row)
            
            styled_df = all_tests.style.apply(highlight_violations, axis=1)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Summary
            total_violations = all_tests['violations'].sum()
            
            if total_violations == 0:
                st.success("All integrity checks passed! Database is consistent.")
            else:
                st.error(f"Found {total_violations} total violation(s). Please review and fix.")
            
            # Export
            csv = all_tests.to_csv(index=False)
            st.download_button(
                label="Download Integrity Report",
                data=csv,
                file_name="integrity_check_report.csv",
                mime="text/csv"
            )
        
        except Exception as e:
            st.error(f"Error running integrity checks: {e}")
    
    st.markdown("---")
    
    # Additional checks
    st.subheader("Additional Data Quality Checks")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Check Invalid Emails", use_container_width=True):
            try:
                invalid_emails = db_utils.fetch_query("""
                    SELECT user_id, name, email
                    FROM Users
                    WHERE email NOT REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
                """)
                
                if not invalid_emails.empty:
                    st.warning(f"Found {len(invalid_emails)} invalid email(s)")
                    st.dataframe(invalid_emails, use_container_width=True, hide_index=True)
                else:
                    st.success("All emails are valid")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        if st.button("Check Orphaned Records", use_container_width=True):
            try:
                # Check for items with no orders
                orphaned = db_utils.fetch_query("""
                    SELECT mi.item_id, mi.item_name
                    FROM Menu_Items mi
                    LEFT JOIN Order_Items oi ON mi.item_id = oi.item_id
                    WHERE oi.item_id IS NULL
                """)
                
                if not orphaned.empty:
                    st.info(f"Found {len(orphaned)} item(s) with no orders yet")
                    st.dataframe(orphaned, use_container_width=True, hide_index=True)
                else:
                    st.success("All items have been ordered at least once")
            except Exception as e:
                st.error(f"Error: {e}")


