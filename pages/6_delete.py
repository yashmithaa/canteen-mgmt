"""
Delete Operations Page
Handle deletion of users, menu items, and orders with proper validation
"""

import streamlit as st
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db_utils
import config

st.set_page_config(
    page_title="Delete Operations",
    page_icon="",
    layout="wide"
)

st.title("Delete Operations")
st.markdown("Safely delete or deactivate records from the database")
st.markdown("---")

# Warning banner
st.error("**Warning**: Deletion operations cannot be easily undone. Please verify before confirming.")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["Delete Orders", "Delete Menu Items", "Delete Users", "Delete History"])

# Tab 1: Delete Orders
with tab1:
    st.subheader("Cancel and Delete Orders")
    
    st.info("""
    **Note**: Deleting an order will:
    - Restore stock for all items in the order
    - Refund wallet balance if payment was completed via wallet
    - Permanently remove the order and all its items
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        try:
            # Get all orders
            orders = db_utils.fetch_query("""
                SELECT 
                    o.order_id,
                    u.name as customer_name,
                    u.srn,
                    o.order_date,
                    o.total_amount,
                    o.order_status,
                    o.payment_method,
                    o.payment_status
                FROM Orders o
                JOIN Users u ON o.user_id = u.user_id
                ORDER BY o.order_date DESC
            """)
            
            if not orders.empty:
                st.dataframe(
                    orders,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "order_id": "Order ID",
                        "customer_name": "Customer",
                        "srn": "SRN",
                        "order_date": st.column_config.DatetimeColumn(
                            "Order Date",
                            format="DD/MM/YYYY HH:mm"
                        ),
                        "total_amount": "Amount",
                        "order_status": "Status",
                        "payment_method": "Payment",
                        "payment_status": "Payment Status"
                    }
                )
                
                st.markdown("---")
                st.markdown("### Delete Order")
                
                order_id_to_delete = st.number_input(
                    "Enter Order ID to Delete",
                    min_value=1,
                    step=1,
                    key="delete_order_id"
                )
                
                # Show order details before deletion
                if order_id_to_delete:
                    order_details = orders[orders['order_id'] == order_id_to_delete]
                    
                    if not order_details.empty:
                        st.warning(f"""
                        **You are about to delete Order #{order_id_to_delete}**
                        - Customer: {order_details.iloc[0]['customer_name']}
                        - Amount: ₹{order_details.iloc[0]['total_amount']:.2f}
                        - Status: {order_details.iloc[0]['order_status']}
                        - Payment: {order_details.iloc[0]['payment_method']} ({order_details.iloc[0]['payment_status']})
                        """)
                        
                        # Show order items
                        order_items = db_utils.fetch_query("""
                            SELECT 
                                mi.item_name,
                                oi.quantity,
                                oi.unit_price,
                                oi.subtotal
                            FROM Order_Items oi
                            JOIN Menu_Items mi ON oi.item_id = mi.item_id
                            WHERE oi.order_id = %s
                        """, (order_id_to_delete,))
                        
                        if not order_items.empty:
                            st.markdown("**Items in this order:**")
                            st.dataframe(order_items, use_container_width=True, hide_index=True)
                        
                        # Confirmation checkbox
                        confirm_delete = st.checkbox(
                            f"I confirm I want to delete Order #{order_id_to_delete}",
                            key="confirm_order_delete"
                        )
                        
                        if st.button("Delete Order", type="primary", disabled=not confirm_delete):
                            try:
                                result = db_utils.call_procedure('delete_order', (order_id_to_delete,))
                                st.success(f"Order #{order_id_to_delete} deleted successfully!")
                                st.balloons()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting order: {e}")
                    else:
                        st.error(f"Order #{order_id_to_delete} not found")
            else:
                st.info("No orders in the database")
        
        except Exception as e:
            st.error(f"Error loading orders: {e}")
    
    with col2:
        st.markdown("### Quick Stats")
        try:
            total_orders = db_utils.fetch_query("SELECT COUNT(*) as count FROM Orders")['count'][0]
            st.metric("Total Orders", total_orders)
            
            pending_orders = db_utils.fetch_query("""
                SELECT COUNT(*) as count FROM Orders 
                WHERE order_status IN ('pending', 'confirmed')
            """)['count'][0]
            st.metric("Pending Orders", pending_orders)
            
            completed_orders = db_utils.fetch_query("""
                SELECT COUNT(*) as count FROM Orders 
                WHERE order_status = 'completed'
            """)['count'][0]
            st.metric("Completed Orders", completed_orders)
        except Exception as e:
            st.error(f"Error loading stats: {e}")

# Tab 2: Delete Menu Items
with tab2:
    st.subheader("Delete Menu Items")
    
    st.info("""
    **Note**: 
    - Items with order history will be marked as unavailable (soft delete)
    - Items never ordered will be permanently deleted (hard delete)
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        try:
            # Get all menu items
            menu_items = db_utils.fetch_query("""
                SELECT 
                    mi.item_id,
                    mi.item_name,
                    c.category_name,
                    mi.price,
                    mi.stock,
                    mi.is_available,
                    COALESCE((SELECT COUNT(*) FROM Order_Items WHERE item_id = mi.item_id), 0) as order_count
                FROM Menu_Items mi
                JOIN Categories c ON mi.category_id = c.category_id
                ORDER BY c.category_name, mi.item_name
            """)
            
            if not menu_items.empty:
                # Add status column
                menu_items['delete_type'] = menu_items['order_count'].apply(
                    lambda x: "Soft Delete" if x > 0 else "Hard Delete"
                )
                
                st.dataframe(
                    menu_items,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "item_id": "ID",
                        "item_name": "Item Name",
                        "category_name": "Category",
                        "price": "Price",
                        "stock": "Stock",
                        "is_available": "Available",
                        "order_count": "Times Ordered",
                        "delete_type": "Delete Type"
                    }
                )
                
                st.markdown("---")
                st.markdown("### Delete Menu Item")
                
                item_id_to_delete = st.number_input(
                    "Enter Item ID to Delete",
                    min_value=1,
                    step=1,
                    key="delete_item_id"
                )
                
                # Show item details before deletion
                if item_id_to_delete:
                    item_details = menu_items[menu_items['item_id'] == item_id_to_delete]
                    
                    if not item_details.empty:
                        order_count = item_details.iloc[0]['order_count']
                        delete_type = "soft delete (mark as unavailable)" if order_count > 0 else "permanently delete"
                        
                        st.warning(f"""
                        **You are about to {delete_type} Item #{item_id_to_delete}**
                        - Item: {item_details.iloc[0]['item_name']}
                        - Category: {item_details.iloc[0]['category_name']}
                        - Price: ₹{item_details.iloc[0]['price']:.2f}
                        - Times Ordered: {order_count}
                        """)
                        
                        # Confirmation checkbox
                        confirm_delete_item = st.checkbox(
                            f"I confirm I want to delete Item #{item_id_to_delete}",
                            key="confirm_item_delete"
                        )
                        
                        if st.button("Delete Menu Item", type="primary", disabled=not confirm_delete_item):
                            try:
                                result = db_utils.call_procedure('delete_menu_item', (item_id_to_delete,))
                                if result:
                                    st.success(result[0][0])
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting item: {e}")
                    else:
                        st.error(f"Item #{item_id_to_delete} not found")
            else:
                st.info("No menu items in the database")
        
        except Exception as e:
            st.error(f"Error loading menu items: {e}")
    
    with col2:
        st.markdown("### Menu Stats")
        try:
            total_items = db_utils.fetch_query("SELECT COUNT(*) as count FROM Menu_Items")['count'][0]
            st.metric("Total Items", total_items)
            
            available_items = db_utils.fetch_query("""
                SELECT COUNT(*) as count FROM Menu_Items WHERE is_available = TRUE
            """)['count'][0]
            st.metric("Available Items", available_items)
            
            unavailable_items = db_utils.fetch_query("""
                SELECT COUNT(*) as count FROM Menu_Items WHERE is_available = FALSE
            """)['count'][0]
            st.metric("Unavailable Items", unavailable_items)
        except Exception as e:
            st.error(f"Error loading stats: {e}")

# Tab 3: Delete Users
with tab3:
    st.subheader("Delete Users")
    
    st.warning("""
    **Important**: 
    - Users with existing orders **cannot** be deleted
    - Cancel all orders first before deleting a user
    - This helps maintain referential integrity
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        try:
            # Get all users with order count
            users = db_utils.fetch_query("""
                SELECT 
                    u.user_id,
                    u.srn,
                    u.name,
                    u.email,
                    u.user_type,
                    u.wallet_balance,
                    COALESCE((SELECT COUNT(*) FROM Orders WHERE user_id = u.user_id), 0) as order_count
                FROM Users u
                ORDER BY u.name
            """)
            
            if not users.empty:
                # Add deletable status
                users['can_delete'] = users['order_count'].apply(lambda x: "Yes" if x == 0 else "No")
                
                st.dataframe(
                    users,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "user_id": "ID",
                        "srn": "SRN",
                        "name": "Name",
                        "email": "Email",
                        "user_type": "Type",
                        "wallet_balance": "Wallet",
                        "order_count": "Orders",
                        "can_delete": "Can Delete"
                    }
                )
                
                st.markdown("---")
                st.markdown("### Delete User")
                
                user_id_to_delete = st.number_input(
                    "Enter User ID to Delete",
                    min_value=1,
                    step=1,
                    key="delete_user_id"
                )
                
                # Show user details before deletion
                if user_id_to_delete:
                    user_details = users[users['user_id'] == user_id_to_delete]
                    
                    if not user_details.empty:
                        order_count = user_details.iloc[0]['order_count']
                        
                        if order_count > 0:
                            st.error(f"""
                            **Cannot delete User #{user_id_to_delete}**
                            - Name: {user_details.iloc[0]['name']}
                            - This user has {order_count} order(s)
                            - Please cancel/delete all orders first
                            """)
                        else:
                            st.warning(f"""
                            **You are about to permanently delete User #{user_id_to_delete}**
                            - Name: {user_details.iloc[0]['name']}
                            - SRN: {user_details.iloc[0]['srn']}
                            - Email: {user_details.iloc[0]['email']}
                            - Wallet Balance: ₹{user_details.iloc[0]['wallet_balance']:.2f}
                            """)
                            
                            # Confirmation checkbox
                            confirm_delete_user = st.checkbox(
                                f"I confirm I want to delete User #{user_id_to_delete}",
                                key="confirm_user_delete"
                            )
                            
                            if st.button("Delete User", type="primary", disabled=not confirm_delete_user):
                                try:
                                    result = db_utils.call_procedure('delete_user', (user_id_to_delete,))
                                    if result:
                                        st.success(result[0][0])
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting user: {e}")
                    else:
                        st.error(f"User #{user_id_to_delete} not found")
            else:
                st.info("No users in the database")
        
        except Exception as e:
            st.error(f"Error loading users: {e}")
    
    with col2:
        st.markdown("### User Stats")
        try:
            total_users = db_utils.fetch_query("SELECT COUNT(*) as count FROM Users")['count'][0]
            st.metric("Total Users", total_users)
            
            users_with_orders = db_utils.fetch_query("""
                SELECT COUNT(DISTINCT user_id) as count FROM Orders
            """)['count'][0]
            st.metric("Users with Orders", users_with_orders)
            
            users_no_orders = total_users - users_with_orders
            st.metric("Users without Orders", users_no_orders)
        except Exception as e:
            st.error(f"Error loading stats: {e}")

# Tab 4: Deletion History
with tab4:
    st.subheader("Recent Deletions & Modifications")
    
    st.info("This section shows recent changes to help track deletions")
    
    # Show recently cancelled orders
    st.markdown("### Recently Cancelled Orders")
    try:
        cancelled_orders = db_utils.fetch_query("""
            SELECT 
                o.order_id,
                u.name as customer_name,
                o.total_amount,
                o.order_status,
                o.updated_at
            FROM Orders o
            JOIN Users u ON o.user_id = u.user_id
            WHERE o.order_status = 'cancelled'
            ORDER BY o.updated_at DESC
            LIMIT 10
        """)
        
        if not cancelled_orders.empty:
            st.dataframe(cancelled_orders, use_container_width=True, hide_index=True)
        else:
            st.info("No cancelled orders")
    except Exception as e:
        st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # Show unavailable items (soft deleted)
    st.markdown("### Unavailable Menu Items (Soft Deleted)")
    try:
        unavailable_items = db_utils.fetch_query("""
            SELECT 
                mi.item_id,
                mi.item_name,
                c.category_name,
                mi.stock,
                mi.updated_at
            FROM Menu_Items mi
            JOIN Categories c ON mi.category_id = c.category_id
            WHERE mi.is_available = FALSE
            ORDER BY mi.updated_at DESC
            LIMIT 10
        """)
        
        if not unavailable_items.empty:
            st.dataframe(unavailable_items, use_container_width=True, hide_index=True)
            
            st.markdown("### Restore Item")
            item_to_restore = st.number_input("Item ID to Restore", min_value=1, step=1)
            
            if st.button("Restore Item Availability"):
                try:
                    query = "UPDATE Menu_Items SET is_available = TRUE WHERE item_id = %s"
                    success = db_utils.execute_query(query, (item_to_restore,))
                    if success:
                        st.success(f"Item #{item_to_restore} restored!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.success("All items are available!")
    except Exception as e:
        st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # Database cleanup utilities
    st.subheader("Database Cleanup Utilities")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Clear Old Data")
        
        if st.button("Delete All Cancelled Orders", type="secondary"):
            try:
                query = "DELETE FROM Orders WHERE order_status = 'cancelled'"
                success = db_utils.execute_query(query)
                if success:
                    st.success("All cancelled orders deleted!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        st.markdown("### Vacuum Operations")
        
        if st.button("Optimize Database Tables", type="secondary"):
            try:
                tables = ['Users', 'Orders', 'Order_Items', 'Menu_Items', 'Categories']
                for table in tables:
                    db_utils.execute_query(f"OPTIMIZE TABLE {table}")
                st.success("All tables optimized!")
            except Exception as e:
                st.error(f"Error: {e}")