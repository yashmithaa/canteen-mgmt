import streamlit as st
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db_utils
import config

st.set_page_config(
    page_title="Menu Management",
    page_icon="🍔",
    layout="wide"
)

st.title("Menu Management")
st.markdown("Manage menu items, categories, pricing, and inventory")
st.markdown("---")

# Create tabs
tab1, tab2, tab3 = st.tabs(["View Menu", "Add Menu Item", "Stock Management"])

# Tab 1: View Menu
with tab1:
    st.subheader("Menu Items")
    
    # Filters
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        search_item = st.text_input("Search Item", "")
    
    with col2:
        # Get categories
        categories = db_utils.fetch_query("SELECT category_id, category_name FROM Categories WHERE is_active = TRUE")
        category_options = ["All"] + categories['category_name'].tolist()
        category_filter = st.selectbox("Filter by Category", category_options)
    
    with col3:
        availability_filter = st.selectbox("Availability", ["All", "Available", "Unavailable"])
    
    with col4:
        st.write("")
        st.write("")
        refresh_menu = st.button("Refresh", use_container_width=True)
    
    # Build query
    query = """
    SELECT 
        mi.item_id,
        mi.item_name,
        c.category_name,
        mi.description,
        mi.price,
        mi.stock,
        mi.is_available,
        mi.preparation_time_minutes,
        mi.created_at
    FROM Menu_Items mi
    JOIN Categories c ON mi.category_id = c.category_id
    WHERE 1=1
    """
    params = []
    
    if search_item:
        query += " AND mi.item_name LIKE %s"
        params.append(f"%{search_item}%")
    
    if category_filter != "All":
        query += " AND c.category_name = %s"
        params.append(category_filter)
    
    if availability_filter == "Available":
        query += " AND mi.is_available = TRUE"
    elif availability_filter == "Unavailable":
        query += " AND mi.is_available = FALSE"
    
    query += " ORDER BY c.category_name, mi.item_name"
    
    # Fetch menu items
    try:
        if params:
            menu_df = db_utils.fetch_query(query, tuple(params))
        else:
            menu_df = db_utils.fetch_query(query)
        
        if not menu_df.empty:
            st.success(f"Found {len(menu_df)} items")
            
            # Format display
            menu_df['price'] = menu_df['price'].apply(lambda x: f"₹{x:.2f}")
            menu_df['is_available'] = menu_df['is_available'].apply(lambda x: "Yes" if x else "No")
            
            # Color code stock levels
            def stock_color(val):
                if val <= 0:
                    return '🔴 Out of Stock'
                elif val <= 5:
                    return f'🟡 Low ({val})'
                else:
                    return f'🟢 Good ({val})'
            
            menu_df['stock_status'] = menu_df['stock'].apply(stock_color)
            
            # Display dataframe
            st.dataframe(
                menu_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "item_id": "ID",
                    "item_name": "Item Name",
                    "category_name": "Category",
                    "description": "Description",
                    "price": "Price",
                    "stock": "Stock Qty",
                    "stock_status": "Stock Status",
                    "is_available": "Available",
                    "preparation_time_minutes": "Prep Time (min)",
                    "created_at": st.column_config.DatetimeColumn(
                        "Added On",
                        format="DD/MM/YYYY"
                    )
                }
            )
            
            # Export option
            # csv = menu_df.to_csv(index=False)
            # st.download_button(
            #     label="📥 Download Menu as CSV",
            #     data=csv,
            #     file_name="menu_export.csv",
            #     mime="text/csv"
            # )
            
            # Sales insights
            st.markdown("---")
            st.subheader("Sales Insights")
            
            col1, col2, col3 = st.columns(3)
            
            # Get top selling items
            with col1:
                st.markdown("#### Top 5 Items by Revenue")
                top_items = db_utils.fetch_query("""
                    SELECT 
                        mi.item_name,
                        SUM(oi.subtotal) as total_sales
                    FROM Order_Items oi
                    JOIN Menu_Items mi ON oi.item_id = mi.item_id
                    GROUP BY mi.item_id, mi.item_name
                    ORDER BY total_sales DESC
                    LIMIT 5
                """)
                
                if not top_items.empty:
                    top_items['total_sales'] = top_items['total_sales'].apply(lambda x: f"₹{x:.2f}")
                    st.dataframe(top_items, hide_index=True, use_container_width=True)
                else:
                    st.info("No sales data available")
            
            with col2:
                st.markdown("#### Low Stock Alert")
                low_stock = db_utils.fetch_query("""
                    SELECT item_name, stock 
                    FROM Menu_Items 
                    WHERE stock <= 5 AND stock > 0
                    ORDER BY stock ASC
                    LIMIT 5
                """)
                
                if not low_stock.empty:
                    st.dataframe(low_stock, hide_index=True, use_container_width=True)
                else:
                    st.success("All items well stocked!")
            
            with col3:
                st.markdown("#### Out of Stock")
                out_of_stock = db_utils.fetch_query("""
                    SELECT item_name, category_name
                    FROM Menu_Items mi
                    JOIN Categories c ON mi.category_id = c.category_id
                    WHERE mi.stock = 0
                    LIMIT 5
                """)
                
                if not out_of_stock.empty:
                    st.dataframe(out_of_stock, hide_index=True, use_container_width=True)
                else:
                    st.success("No items out of stock!")
        
        else:
            st.info("No menu items found matching the criteria")
    
    except Exception as e:
        st.error(f"Error loading menu: {e}")

# Tab 2: Add Menu Item
with tab2:
    st.subheader("Add New Menu Item")
    
    with st.form("add_menu_item_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            item_name = st.text_input("Item Name *", placeholder="e.g., Masala Dosa")
            
            # Get categories for dropdown
            categories = db_utils.fetch_query("SELECT category_id, category_name FROM Categories WHERE is_active = TRUE")
            if not categories.empty:
                category_names = categories['category_name'].tolist()
                category_ids = categories['category_id'].tolist()
                
                selected_category_idx = st.selectbox(
                    "Category *",
                    range(len(category_names)),
                    format_func=lambda x: category_names[x]
                )
                selected_category_id = category_ids[selected_category_idx]
            else:
                st.error("No categories available")
                selected_category_id = None
            
            description = st.text_area("Description", placeholder="Brief description of the item")
        
        with col2:
            price = st.number_input("Price (₹) *", min_value=1.0, value=50.0, step=5.0)
            stock = st.number_input("Initial Stock Quantity", min_value=0, value=10, step=1)
            prep_time = st.number_input("Preparation Time (minutes)", min_value=1, value=10, step=1)
            is_available = st.checkbox("Available for Order", value=True)
        
        submitted_item = st.form_submit_button("Add Menu Item", use_container_width=True)
        
        if submitted_item:
            if not item_name or selected_category_id is None:
                st.error("Please fill in all required fields marked with *")
            else:
                query = """
                INSERT INTO Menu_Items (
                    category_id, item_name, description, price, 
                    stock, is_available, preparation_time_minutes
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    selected_category_id, item_name, description, 
                    price, stock, is_available, prep_time
                )
                
                success = db_utils.execute_query(query, params)
                
                if success:
                    st.success(f"Menu item '{item_name}' added successfully!")
                else:
                    st.error("Failed to add menu item")

# Tab 3: Stock Management
with tab3:
    st.subheader("Stock Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Update Stock")
        
        # Get all menu items
        try:
            items = db_utils.fetch_query("""
                SELECT mi.item_id, mi.item_name, c.category_name, mi.stock, mi.is_available
                FROM Menu_Items mi
                JOIN Categories c ON mi.category_id = c.category_id
                ORDER BY c.category_name, mi.item_name
            """)
            
            if not items.empty:
                item_options = [f"{row['item_name']} ({row['category_name']}) - Current: {row['stock']}" 
                               for _, row in items.iterrows()]
                item_ids = items['item_id'].tolist()
                
                selected_item_idx = st.selectbox(
                    "Select Item",
                    range(len(item_options)),
                    format_func=lambda x: item_options[x]
                )
                
                selected_item_id = item_ids[selected_item_idx]
                current_stock = items.iloc[selected_item_idx]['stock']
                item_name = items.iloc[selected_item_idx]['item_name']
                
                st.info(f"Current Stock: {current_stock} units")
                
                # Stock update options
                update_type = st.radio("Update Type", ["Add Stock", "Set Stock", "Reduce Stock"])
                
                if update_type == "Add Stock":
                    quantity = st.number_input("Quantity to Add", min_value=1, value=10, step=1)
                    new_stock = current_stock + quantity
                elif update_type == "Set Stock":
                    new_stock = st.number_input("New Stock Quantity", min_value=0, value=current_stock, step=1)
                else:  # Reduce Stock
                    quantity = st.number_input("Quantity to Reduce", min_value=1, max_value=current_stock, value=1, step=1)
                    new_stock = current_stock - quantity
                
                st.info(f"New Stock will be: {new_stock} units")
                
                if st.button("🔄 Update Stock", use_container_width=True):
                    try:
                        query = "UPDATE Menu_Items SET stock = %s WHERE item_id = %s"
                        success = db_utils.execute_query(query, (new_stock, selected_item_id))
                        
                        if success:
                            st.success(f"Stock updated for '{item_name}'")
                            
                            # Check if item was auto-disabled
                            if new_stock <= 0:
                                st.warning("Item automatically marked as unavailable (stock = 0)")
                            
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error updating stock: {e}")
            else:
                st.warning("No menu items found")
        
        except Exception as e:
            st.error(f"Error loading items: {e}")
    
    with col2:
        st.markdown("### Quick Stats")
        
        try:
            # Total items
            total_items = db_utils.fetch_query("SELECT COUNT(*) as count FROM Menu_Items")['count'][0]
            st.metric("Total Items", total_items)
            
            # Available items
            available_items = db_utils.fetch_query(
                "SELECT COUNT(*) as count FROM Menu_Items WHERE is_available = TRUE"
            )['count'][0]
            st.metric("Available Items", available_items)
            
            # Low stock items
            low_stock_count = db_utils.fetch_query(
                "SELECT COUNT(*) as count FROM Menu_Items WHERE stock <= 5 AND stock > 0"
            )['count'][0]
            st.metric("Low Stock Alert", low_stock_count, delta="⚠️" if low_stock_count > 0 else None)
            
            # Out of stock
            out_of_stock_count = db_utils.fetch_query(
                "SELECT COUNT(*) as count FROM Menu_Items WHERE stock = 0"
            )['count'][0]
            st.metric("Out of Stock", out_of_stock_count, delta="🔴" if out_of_stock_count > 0 else None)
        
        except Exception as e:
            st.error(f"Error loading stats: {e}")
    
    st.markdown("---")
    
    # Bulk stock update
    # st.subheader("Bulk Stock Operations")
    
    # col1, col2 = st.columns(2)
    
    # with col1:
    #     if st.button("Restock All Low Stock Items (+10)", use_container_width=True):
    #         try:
    #             query = "UPDATE Menu_Items SET stock = stock + 10 WHERE stock <= 5"
    #             success = db_utils.execute_query(query)
                
    #             if success:
    #                 st.success("All low stock items restocked!")
    #                 st.rerun()
    #         except Exception as e:
    #             st.error(f"Error: {e}")
    
    # with col2:
    #     if st.button("Enable All Items with Stock > 0", use_container_width=True):
    #         try:
    #             query = "UPDATE Menu_Items SET is_available = TRUE WHERE stock > 0"
    #             success = db_utils.execute_query(query)
                
    #             if success:
    #                 st.success("All items with stock enabled!")
    #                 st.rerun()
    #         except Exception as e:
    #             st.error(f"Error: {e}")
