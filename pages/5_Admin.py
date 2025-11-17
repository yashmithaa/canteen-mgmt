import streamlit as st
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db_utils
import config

st.set_page_config(
    page_title="Admin & Debug",
    page_icon="",
    layout="wide"
)

st.title("Admin & Debug Tools")
st.markdown("Database administration, monitoring, and debugging utilities")
st.markdown("---")

# Warning banner
st.warning("**Admin Area**: These tools can modify the database structure and data. Use with caution!")

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Database Info",
    "User Privileges",
    "Triggers", 
    "Procedures", 
    "Functions",
    "Query Examples"
])

# Tab 1: Database Info
with tab1:
    st.subheader("Database Information")
    
    # Connection test
    status, msg = db_utils.test_connection()
    if status:
        st.success(msg)
    else:
        st.error(msg)
    
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

# Tab 2: User Privileges
with tab2:
    st.subheader("Database Users and Privileges")
    
    st.info("""
    The canteen database has 4 types of users with different privilege levels:
    - **Admin**: Full database control
    - **Manager**: Data manipulation only
    - **Staff**: Limited CRUD operations
    - **Read-Only**: View-only access for reporting
    """)
    

    # Privilege comparison table
    st.markdown("### Privilege Comparison")
    
    privilege_data = {
        'Privilege': ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'EXECUTE'],
        'Admin': ['Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes', 'Yes'],
        'Manager': ['Yes', 'Yes', 'Yes', 'Yes', 'No', 'No', 'No', 'Yes'],
        'Staff': ['Yes (Limited)', 'Yes (Limited)', 'Yes (Limited)', 'No', 'No', 'No', 'No', 'Yes'],
        'Read-Only': ['Yes', 'No', 'No', 'No', 'No', 'No', 'No', 'No']
    }
    
    privilege_df = pd.DataFrame(privilege_data)
    st.dataframe(privilege_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    


# Tab 3: Triggers
with tab3:
    st.subheader("Database Triggers")
    
    try:
        triggers = db_utils.get_triggers()
        
        if not triggers.empty:
            st.success(f"Found {len(triggers)} trigger(s)")
            
            # Display triggers in expandable sections
            for idx, trigger in triggers.iterrows():
                with st.expander(f"{trigger['Trigger']} - {trigger['Event']} on {trigger['Table']}"):
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

# Tab 4: Procedures
with tab4:
    st.subheader("Stored Procedures")
    
    try:
        procedures = db_utils.get_procedures()
        
        if not procedures.empty:
            # Filter for canteen database
            procedures = procedures[procedures['Db'] == config.DB_NAME]
            
            st.success(f"Found {len(procedures)} procedure(s)")
            
            # Display procedures
            for idx, proc in procedures.iterrows():
                with st.expander(f"{proc['Name']} ({proc['Type']})"):
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
            
            if st.button("Test Place Order", key="test_place_order"):
                try:
                    result = db_utils.call_procedure(
                        'place_new_order',
                        (test_user, test_method, test_item, test_qty)
                    )
                    if result:
                        st.success(f"Order placed! Order ID: {result[0][0]}")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # DELETE procedures
    st.subheader("Delete Operations Procedures")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.expander("Test delete_order"):
            st.markdown("Delete an order (restores stock & refunds wallet)")
            
            test_order_id = st.number_input("Order ID to Delete", min_value=1, value=1, key="del_order")
            
            if st.button("Test Delete Order", key="test_delete_order"):
                try:
                    result = db_utils.call_procedure('delete_order', (test_order_id,))
                    if result:
                        st.success(result[0][0])
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col2:
        with st.expander("Test delete_user"):
            st.markdown("Delete a user (only if no orders)")
            
            test_user_del = st.number_input("User ID to Delete", min_value=1, value=1, key="del_user")
            
            if st.button("Test Delete User", key="test_delete_user"):
                try:
                    result = db_utils.call_procedure('delete_user', (test_user_del,))
                    if result:
                        st.success(result[0][0])
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col3:
        with st.expander("Test delete_menu_item"):
            st.markdown("Delete a menu item (soft/hard delete)")
            
            test_item_del = st.number_input("Item ID to Delete", min_value=1, value=1, key="del_item")
            
            if st.button("Test Delete Item", key="test_delete_item"):
                try:
                    result = db_utils.call_procedure('delete_menu_item', (test_item_del,))
                    if result:
                        st.success(result[0][0])
                except Exception as e:
                    st.error(f"Error: {e}")

# Tab 5: Functions
with tab5:
    st.subheader("Stored Functions")
    
    try:
        functions = db_utils.get_functions()
        
        if not functions.empty:
            # Filter for canteen database
            functions = functions[functions['Db'] == config.DB_NAME]
            
            st.success(f"Found {len(functions)} function(s)")
            
            # Display functions
            for idx, func in functions.iterrows():
                with st.expander(f"{func['Name']} ({func['Type']})"):
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

# Tab 6: Query Examples
with tab6:
    st.subheader("SQL Query Examples")
    
    st.info("This section demonstrates the different types of queries used in the application")
    
    # Nested Query Example
    st.markdown("### 1. Nested Query Example")
    st.markdown("**Purpose**: Find users who have spent more than the average order amount")
    
    nested_query = """
    SELECT 
        u.name,
        u.srn,
        SUM(o.total_amount) as total_spent
    FROM Users u
    JOIN Orders o ON u.user_id = o.user_id
    WHERE o.payment_status = 'completed'
    GROUP BY u.user_id, u.name, u.srn
    HAVING total_spent > (
        SELECT AVG(total_amount) 
        FROM Orders 
        WHERE payment_status = 'completed'
    )
    ORDER BY total_spent DESC
    """
    
    st.code(nested_query, language='sql')
    
    if st.button("Run Nested Query", key="run_nested"):
        try:
            result = db_utils.fetch_query(nested_query)
            if not result.empty:
                st.success(f"Found {len(result)} users spending above average")
                st.dataframe(result, use_container_width=True, hide_index=True)
            else:
                st.info("No results found")
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # JOIN Query Example
    st.markdown("### 2. JOIN Query Example")
    st.markdown("**Purpose**: Get complete order details with customer and item information")
    
    join_query = """
    SELECT 
        o.order_id,
        u.name as customer_name,
        u.srn,
        mi.item_name,
        c.category_name,
        oi.quantity,
        oi.unit_price,
        oi.subtotal,
        o.order_status
    FROM Orders o
    JOIN Users u ON o.user_id = u.user_id
    JOIN Order_Items oi ON o.order_id = oi.order_id
    JOIN Menu_Items mi ON oi.item_id = mi.item_id
    JOIN Categories c ON mi.category_id = c.category_id
    ORDER BY o.order_date DESC
    LIMIT 10
    """
    
    st.code(join_query, language='sql')
    
    if st.button("Run JOIN Query", key="run_join"):
        try:
            result = db_utils.fetch_query(join_query)
            if not result.empty:
                st.success(f"Retrieved {len(result)} order items")
                st.dataframe(result, use_container_width=True, hide_index=True)
            else:
                st.info("No results found")
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # Aggregate Query Example
    st.markdown("### 3. Aggregate Query Example")
    st.markdown("**Purpose**: Calculate various statistics using aggregate functions")
    
    aggregate_query = """
    SELECT 
        c.category_name,
        COUNT(DISTINCT mi.item_id) as item_count,
        COUNT(DISTINCT oi.order_id) as order_count,
        SUM(oi.quantity) as total_quantity_sold,
        SUM(oi.subtotal) as total_revenue,
        AVG(mi.price) as avg_item_price,
        MIN(mi.price) as min_price,
        MAX(mi.price) as max_price
    FROM Categories c
    JOIN Menu_Items mi ON c.category_id = mi.category_id
    LEFT JOIN Order_Items oi ON mi.item_id = oi.item_id
    GROUP BY c.category_id, c.category_name
    ORDER BY total_revenue DESC
    """
    
    st.code(aggregate_query, language='sql')
    
    if st.button("Run Aggregate Query", key="run_aggregate"):
        try:
            result = db_utils.fetch_query(aggregate_query)
            if not result.empty:
                st.success(f"Category statistics calculated")
                
                # Format currency columns
                for col in ['total_revenue', 'avg_item_price', 'min_price', 'max_price']:
                    if col in result.columns:
                        result[col] = result[col].apply(lambda x: f"₹{x:.2f}" if pd.notna(x) else "₹0.00")
                
                st.dataframe(result, use_container_width=True, hide_index=True)
            else:
                st.info("No results found")
        except Exception as e:
            st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # Additional complex queries
    st.markdown("### 4. Additional Query Examples")
    
    query_examples = {
        "Top Customers by Orders": """
        SELECT 
            u.name,
            u.user_type,
            COUNT(o.order_id) as order_count,
            SUM(o.total_amount) as total_spent,
            AVG(o.total_amount) as avg_order_value
        FROM Users u
        JOIN Orders o ON u.user_id = o.user_id
        WHERE o.payment_status = 'completed'
        GROUP BY u.user_id, u.name, u.user_type
        ORDER BY order_count DESC
        LIMIT 5
        """,
        
        "Items Never Ordered": """
        SELECT 
            mi.item_name,
            c.category_name,
            mi.price,
            mi.stock
        FROM Menu_Items mi
        JOIN Categories c ON mi.category_id = c.category_id
        LEFT JOIN Order_Items oi ON mi.item_id = oi.item_id
        WHERE oi.item_id IS NULL
        """,
        
        "Daily Revenue Trend": """
        SELECT 
            DATE(order_date) as order_day,
            COUNT(*) as order_count,
            SUM(total_amount) as daily_revenue,
            AVG(total_amount) as avg_order_value
        FROM Orders
        WHERE payment_status = 'completed'
        GROUP BY DATE(order_date)
        ORDER BY order_day DESC
        LIMIT 7
        """
    }
    
    selected_example = st.selectbox("Select Query Example", list(query_examples.keys()))
    
    st.code(query_examples[selected_example], language='sql')
    
    if st.button("Run Selected Query", key="run_example"):
        try:
            result = db_utils.fetch_query(query_examples[selected_example])
            if not result.empty:
                st.success(f"Query executed successfully - {len(result)} rows returned")
                st.dataframe(result, use_container_width=True, hide_index=True)
            else:
                st.info("No results found")
        except Exception as e:
            st.error(f"Error: {e}")