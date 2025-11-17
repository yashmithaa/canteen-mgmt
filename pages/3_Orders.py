"""
Orders Management Page
Handle orders, payments, and order tracking
"""

import streamlit as st
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db_utils
import config

st.set_page_config(
    page_title="Orders Management",
    page_icon="",
    layout="wide"
)

st.title("Orders Management")
st.markdown("Create orders, track status, and process payments")
st.markdown("---")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["View Orders", "New Order", "Manage Orders", "Order Details"])

# Tab 1: View Orders
with tab1:
    st.subheader("All Orders")
    
    # Filters
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        search_customer = st.text_input("Search Customer", "")
    
    with col2:
        status_filter = st.selectbox(
            "Order Status",
            ["All", "pending", "confirmed", "preparing", "ready", "completed", "cancelled"]
        )
    
    with col3:
        payment_filter = st.selectbox(
            "Payment Status",
            ["All", "pending", "completed", "failed", "refunded"]
        )
    
    with col4:
        st.write("")
        st.write("")
        refresh_orders = st.button("Refresh", use_container_width=True)
    
    # Build query
    query = "SELECT * FROM Order_Summary WHERE 1=1"
    params = []
    
    if search_customer:
        query += " AND (customer_name LIKE %s OR srn LIKE %s)"
        params.extend([f"%{search_customer}%", f"%{search_customer}%"])
    
    if status_filter != "All":
        query += " AND order_status = %s"
        params.append(status_filter)
    
    if payment_filter != "All":
        query += " AND payment_status = %s"
        params.append(payment_filter)
    
    query += " ORDER BY order_date DESC"
    
    # Fetch orders
    try:
        if params:
            orders_df = db_utils.fetch_query(query, tuple(params))
        else:
            orders_df = db_utils.fetch_query(query)
        
        if not orders_df.empty:
            st.success(f"Found {len(orders_df)} orders")
            
            # Format display
            orders_df['total_amount'] = orders_df['total_amount'].apply(lambda x: f"₹{x:.2f}")
            
            # Status badges with colors
            def status_badge(status):
                # Return a plain-text status label without emoji
                return status.upper()
            
            orders_df['status_display'] = orders_df['order_status'].apply(status_badge)
            
            # Display dataframe
            st.dataframe(
                orders_df,
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
                    "total_amount": "Total Amount",
                    "status_display": "Order Status",
                    "payment_method": "Payment Method",
                    "payment_status": "Payment Status"
                }
            )
            
            # Export option
            csv = orders_df.to_csv(index=False)
            st.download_button(
                label="Download Orders as CSV",
                data=csv,
                file_name="orders_export.csv",
                mime="text/csv"
            )
        else:
            st.info("No orders found matching the criteria")
    
    except Exception as e:
        st.error(f"Error loading orders: {e}")

# Tab 2: New Order
with tab2:
    st.subheader("Create New Order")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Select customer
        try:
            users = db_utils.fetch_query("SELECT user_id, name, srn, wallet_balance FROM Users ORDER BY name")
            
            if not users.empty:
                user_options = [f"{row['name']} ({row['srn']}) - Wallet: ₹{row['wallet_balance']:.2f}" 
                               for _, row in users.iterrows()]
                user_ids = users['user_id'].tolist()
                
                selected_user_idx = st.selectbox(
                    "Select Customer",
                    range(len(user_options)),
                    format_func=lambda x: user_options[x]
                )
                
                selected_user_id = user_ids[selected_user_idx]
                customer_name = users.iloc[selected_user_idx]['name']
                customer_balance = users.iloc[selected_user_idx]['wallet_balance']
                
                # Select item
                items = db_utils.fetch_query("""
                    SELECT mi.item_id, mi.item_name, c.category_name, mi.price, mi.stock, mi.is_available
                    FROM Menu_Items mi
                    JOIN Categories c ON mi.category_id = c.category_id
                    WHERE mi.is_available = TRUE AND mi.stock > 0
                    ORDER BY c.category_name, mi.item_name
                """)
                
                if not items.empty:
                    item_options = [f"{row['item_name']} ({row['category_name']}) - ₹{row['price']:.2f} (Stock: {row['stock']})" 
                                   for _, row in items.iterrows()]
                    item_ids = items['item_id'].tolist()
                    
                    selected_item_idx = st.selectbox(
                        "Select Item",
                        range(len(item_options)),
                        format_func=lambda x: item_options[x]
                    )
                    
                    selected_item_id = item_ids[selected_item_idx]
                    item_name = items.iloc[selected_item_idx]['item_name']
                    item_price = items.iloc[selected_item_idx]['price']
                    max_stock = items.iloc[selected_item_idx]['stock']
                    
                    # Quantity
                    quantity = st.number_input(
                        "Quantity",
                        min_value=1,
                        max_value=max_stock,
                        value=1,
                        step=1
                    )
                    
                    # Payment method
                    payment_method = st.selectbox(
                        "Payment Method",
                        ["wallet", "cash", "upi", "card"]
                    )
                    
                    # Calculate total
                    total = item_price * quantity
                    st.info(f"Order Total: ₹{total:.2f}")
                    
                    # Wallet warning
                    if payment_method == "wallet" and customer_balance < total:
                        st.error(f"Insufficient wallet balance! Customer has ₹{customer_balance:.2f}, needs ₹{total:.2f}")
                    
                    if st.button("Place Order", use_container_width=True):
                        if payment_method == "wallet" and customer_balance < total:
                            st.error("Cannot place order: Insufficient wallet balance")
                        else:
                            try:
                                # Call stored procedure
                                result = db_utils.call_procedure(
                                    'place_new_order',
                                    (selected_user_id, payment_method, selected_item_id, quantity)
                                )
                                
                                if result:
                                    st.success(f"Order placed successfully for {customer_name}!")
                                    st.success(f"Order ID: {result[0][0]}, Total: ₹{result[0][1]:.2f}")
                                else:
                                    st.error("Failed to place order")
                            except Exception as e:
                                st.error(f"Error placing order: {e}")
                else:
                    st.warning("No available items with stock")
            else:
                st.warning("No users found")
        
        except Exception as e:
            st.error(f"Error loading data: {e}")
    
    with col2:
        st.markdown("### Quick Stats")
        try:
            # Today's orders
            today_orders = db_utils.fetch_query("""
                SELECT COUNT(*) as count 
                FROM Orders 
                WHERE DATE(order_date) = CURDATE()
            """)['count'][0]
            st.metric("Today's Orders", today_orders)
            
            # Pending orders
            pending_orders = db_utils.fetch_query("""
                SELECT COUNT(*) as count 
                FROM Orders 
                WHERE order_status IN ('pending', 'confirmed', 'preparing')
            """)['count'][0]
            st.metric("Pending Orders", pending_orders)
            
            # Today's revenue
            today_revenue = db_utils.fetch_query("""
                SELECT COALESCE(SUM(total_amount), 0) as revenue 
                FROM Orders 
                WHERE DATE(order_date) = CURDATE() AND payment_status = 'completed'
            """)['revenue'][0]
            st.metric("Today's Revenue", f"₹{today_revenue:.2f}")
        except Exception as e:
            st.error(f"Error loading stats: {e}")

# Tab 3: Manage Orders
with tab3:
    st.subheader("Manage Existing Orders")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Add Item to Order")
        
        try:
            # Get pending/confirmed orders
            pending_orders = db_utils.fetch_query("""
                SELECT o.order_id, u.name, o.order_status, o.total_amount
                FROM Orders o
                JOIN Users u ON o.user_id = u.user_id
                WHERE o.order_status IN ('pending', 'confirmed')
                ORDER BY o.order_date DESC
            """)
            
            if not pending_orders.empty:
                order_options = [f"Order #{row['order_id']} - {row['name']} - ₹{row['total_amount']:.2f}" 
                               for _, row in pending_orders.iterrows()]
                order_ids = pending_orders['order_id'].tolist()
                
                selected_order_idx = st.selectbox(
                    "Select Order",
                    range(len(order_options)),
                    format_func=lambda x: order_options[x],
                    key="add_item_order"
                )
                
                selected_order_id = order_ids[selected_order_idx]
                current_total = pending_orders.iloc[selected_order_idx]['total_amount']
                
                # Select item to add
                items = db_utils.fetch_query("""
                    SELECT mi.item_id, mi.item_name, mi.price, mi.stock
                    FROM Menu_Items mi
                    WHERE mi.is_available = TRUE AND mi.stock > 0
                    ORDER BY mi.item_name
                """)
                
                if not items.empty:
                    item_options_add = [f"{row['item_name']} - ₹{row['price']:.2f}" 
                                       for _, row in items.iterrows()]
                    item_ids_add = items['item_id'].tolist()
                    
                    selected_item_add_idx = st.selectbox(
                        "Select Item to Add",
                        range(len(item_options_add)),
                        format_func=lambda x: item_options_add[x],
                        key="item_to_add"
                    )
                    
                    selected_item_add_id = item_ids_add[selected_item_add_idx]
                    item_price_add = items.iloc[selected_item_add_idx]['price']
                    max_stock_add = items.iloc[selected_item_add_idx]['stock']
                    
                    quantity_add = st.number_input(
                        "Quantity to Add",
                        min_value=1,
                        max_value=max_stock_add,
                        value=1,
                        step=1,
                        key="qty_add"
                    )
                    
                    new_total = current_total + (item_price_add * quantity_add)
                    st.info(f"New Order Total: ₹{new_total:.2f}")
                    
                    if st.button("Add Item to Order", use_container_width=True):
                        try:
                            db_utils.call_procedure(
                                'add_item_to_order',
                                (selected_order_id, selected_item_add_id, quantity_add)
                            )
                            st.success("Item added to order successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.warning("No available items")
            else:
                st.info("No pending/confirmed orders to modify")
        
        except Exception as e:
            st.error(f"Error: {e}")
    
    with col2:
        st.markdown("### Update Order Status")
        
        try:
            # Get orders
            orders = db_utils.fetch_query("""
                SELECT o.order_id, u.name, o.order_status, o.payment_status
                FROM Orders o
                JOIN Users u ON o.user_id = u.user_id
                WHERE o.order_status != 'completed' AND o.order_status != 'cancelled'
                ORDER BY o.order_date DESC
            """)
            
            if not orders.empty:
                order_status_options = [f"Order #{row['order_id']} - {row['name']} ({row['order_status']})" 
                                       for _, row in orders.iterrows()]
                order_status_ids = orders['order_id'].tolist()
                
                selected_status_order_idx = st.selectbox(
                    "Select Order",
                    range(len(order_status_options)),
                    format_func=lambda x: order_status_options[x],
                    key="update_status_order"
                )
                
                selected_status_order_id = order_status_ids[selected_status_order_idx]
                current_order_status = orders.iloc[selected_status_order_idx]['order_status']
                current_payment_status = orders.iloc[selected_status_order_idx]['payment_status']
                
                # New status
                new_order_status = st.selectbox(
                    "New Order Status",
                    ["pending", "confirmed", "preparing", "ready", "completed", "cancelled"],
                    index=["pending", "confirmed", "preparing", "ready", "completed", "cancelled"].index(current_order_status)
                )
                
                new_payment_status = st.selectbox(
                    "New Payment Status",
                    ["pending", "completed", "failed", "refunded"],
                    index=["pending", "completed", "failed", "refunded"].index(current_payment_status)
                )
                
                if st.button("Update Status", use_container_width=True):
                    try:
                        query = """
                        UPDATE Orders 
                        SET order_status = %s, payment_status = %s
                        WHERE order_id = %s
                        """
                        success = db_utils.execute_query(
                            query,
                            (new_order_status, new_payment_status, selected_status_order_id)
                        )
                        
                        if success:
                            st.success("Order status updated successfully!")
                            if new_payment_status == 'completed':
                                st.info("Wallet balance will be auto-deducted if payment method is 'wallet'")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.info("No orders to update")
        
        except Exception as e:
            st.error(f"Error: {e}")

# Tab 4: Order Details
with tab4:
    st.subheader("View Order Details")
    
    try:
        # Get all orders
        all_orders = db_utils.fetch_query("""
            SELECT o.order_id, u.name, o.order_date, o.total_amount, o.order_status
            FROM Orders o
            JOIN Users u ON o.user_id = u.user_id
            ORDER BY o.order_date DESC
        """)
        
        if not all_orders.empty:
            order_detail_options = [f"Order #{row['order_id']} - {row['name']} - ₹{row['total_amount']:.2f}" 
                                   for _, row in all_orders.iterrows()]
            order_detail_ids = all_orders['order_id'].tolist()
            
            selected_detail_order_idx = st.selectbox(
                "Select Order to View",
                range(len(order_detail_options)),
                format_func=lambda x: order_detail_options[x]
            )
            
            selected_detail_order_id = order_detail_ids[selected_detail_order_idx]
            
            # Get order header
            order_header = db_utils.fetch_query(
                "SELECT * FROM Order_Summary WHERE order_id = %s",
                (selected_detail_order_id,)
            )
            
            # Get order items
            order_items = db_utils.fetch_query("""
                SELECT 
                    oi.order_item_id,
                    mi.item_name,
                    c.category_name,
                    oi.quantity,
                    oi.unit_price,
                    oi.subtotal,
                    oi.special_requests
                FROM Order_Items oi
                JOIN Menu_Items mi ON oi.item_id = mi.item_id
                JOIN Categories c ON mi.category_id = c.category_id
                WHERE oi.order_id = %s
            """, (selected_detail_order_id,))
            
            # Display order header
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                **Order ID:** #{order_header.iloc[0]['order_id']}  
                **Customer:** {order_header.iloc[0]['customer_name']}  
                **SRN:** {order_header.iloc[0]['srn']}
                """)
            
            with col2:
                st.markdown(f"""
                **Order Status:** {order_header.iloc[0]['order_status'].upper()}  
                **Payment Method:** {order_header.iloc[0]['payment_method'].upper()}  
                **Payment Status:** {order_header.iloc[0]['payment_status'].upper()}
                """)
            
            with col3:
                st.markdown(f"""
                **Order Date:** {order_header.iloc[0]['order_date']}  
                **Total Amount:** ₹{order_header.iloc[0]['total_amount']:.2f}
                """)
            
            st.markdown("---")
            
            # Display order items
            st.subheader("Order Items")
            
            if not order_items.empty:
                order_items['unit_price'] = order_items['unit_price'].apply(lambda x: f"₹{x:.2f}")
                order_items['subtotal'] = order_items['subtotal'].apply(lambda x: f"₹{x:.2f}")
                
                st.dataframe(
                    order_items,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "order_item_id": "Item ID",
                        "item_name": "Item Name",
                        "category_name": "Category",
                        "quantity": "Quantity",
                        "unit_price": "Unit Price",
                        "subtotal": "Subtotal",
                        "special_requests": "Special Requests"
                    }
                )
                
                # Calculate order total using function
                calculated_total = db_utils.call_function('get_order_total', (selected_detail_order_id,))
                st.success(f"**Calculated Total (via function):** ₹{calculated_total:.2f}")
            else:
                st.info("No items in this order")
        
        else:
            st.info("No orders found")
    
    except Exception as e:
        st.error(f"Error loading order details: {e}")
