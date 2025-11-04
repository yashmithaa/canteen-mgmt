import streamlit as st
import pandas as pd
from datetime import datetime
import config
import db_utils

st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout=config.PAGE_LAYOUT,
    initial_sidebar_state=config.INITIAL_SIDEBAR_STATE
)

st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #FF6B6B;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .status-completed { background-color: #4CAF50; color: white; }
    .status-pending { background-color: #FFC107; color: black; }
    .status-preparing { background-color: #2196F3; color: white; }
    .status-ready { background-color: #9C27B0; color: white; }
    .status-cancelled { background-color: #F44336; color: white; }
</style>
""", unsafe_allow_html=True)

def main():
    with st.sidebar:
        st.image("https://via.placeholder.com/150x150.png?text=Canteen", width=150)
        st.title("Navigation")
        st.markdown("---")
        
        # Connection status
        status, msg = db_utils.test_connection()
        if status:
            st.success("Database Connected")
        else:
            st.error("Database Disconnected")
            st.error(msg)
        
        st.markdown("---")
        st.markdown("### Quick Stats")
        
        # Quick stats
        try:
            total_users = db_utils.fetch_query("SELECT COUNT(*) as count FROM Users")['count'][0]
            total_orders = db_utils.fetch_query("SELECT COUNT(*) as count FROM Orders")['count'][0]
            total_items = db_utils.fetch_query("SELECT COUNT(*) as count FROM Menu_Items")['count'][0]
            
            st.metric("Total Users", total_users)
            st.metric("Total Orders", total_orders)
            st.metric("Menu Items", total_items)
        except:
            st.warning("Unable to load stats")
        
        st.markdown("---")
        st.markdown("### System Info")
        st.info(f"Database: {config.DB_NAME}")
        st.info(f"Host: {config.DB_HOST}")
        
    # Main content
    st.markdown('<h1 class="main-header">Canteen Management System</h1>', unsafe_allow_html=True)
    
    # st.markdown("""
    # ### Welcome to the Canteen Management Dashboard
    
    # This comprehensive system helps you manage all aspects of canteen operations including:
    # - **Users Management** - Manage students, faculty, and staff
    # - **Menu Management** - Control menu items, pricing, and inventory
    # - **Orders Processing** - Handle orders and payments
    # - **Reports & Analytics** - Insights and performance metrics
    # - **Admin Tools** - Database management and debugging
    # """)
    
    # st.markdown("---")
    
    # Overview metrics
    st.subheader("Today's Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Total revenue
        revenue_query = """
        SELECT COALESCE(SUM(total_amount), 0) as revenue 
        FROM Orders 
        WHERE DATE(order_date) = CURDATE() AND payment_status = 'completed'
        """
        revenue = db_utils.fetch_query(revenue_query)['revenue'][0]
        
        # Today's orders
        orders_query = """
        SELECT COUNT(*) as count 
        FROM Orders 
        WHERE DATE(order_date) = CURDATE()
        """
        today_orders = db_utils.fetch_query(orders_query)['count'][0]
        
        # Pending orders
        pending_query = """
        SELECT COUNT(*) as count 
        FROM Orders 
        WHERE order_status IN ('pending', 'confirmed', 'preparing')
        """
        pending = db_utils.fetch_query(pending_query)['count'][0]
        
        # Available items
        available_query = """
        SELECT COUNT(*) as count 
        FROM Menu_Items 
        WHERE is_available = TRUE
        """
        available = db_utils.fetch_query(available_query)['count'][0]
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">₹{revenue:.2f}</div>
                <div class="metric-label">Today's Revenue</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{today_orders}</div>
                <div class="metric-label">Today's Orders</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{pending}</div>
                <div class="metric-label">Pending Orders</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{available}</div>
                <div class="metric-label">Available Items</div>
            </div>
            """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Error loading metrics: {e}")
    
    st.markdown("---")
    
    # Recent activity
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Recent Orders")
        try:
            recent_orders = db_utils.fetch_query("""
                SELECT 
                    order_id,
                    customer_name,
                    total_amount,
                    order_status,
                    order_date
                FROM Order_Summary
                ORDER BY order_date DESC
                LIMIT 5
            """)
            
            if not recent_orders.empty:
                st.dataframe(recent_orders, use_container_width=True, hide_index=True)
            else:
                st.info("No recent orders")
        except Exception as e:
            st.error(f"Error loading recent orders: {e}")
    
    with col2:
        st.subheader("Popular Items")
        try:
            popular = db_utils.fetch_query("""
                SELECT * FROM Popular_Items LIMIT 5
            """)
            
            if not popular.empty:
                st.dataframe(popular, use_container_width=True, hide_index=True)
            else:
                st.info("No popular items data")
        except Exception as e:
            st.error(f"Error loading popular items: {e}")
    
    # st.markdown("---")
    
    # Getting started guide
    # with st.expander("Getting Started Guide"):
    #     st.markdown("""
    #     #### Navigation
    #     Use the sidebar or the pages menu to navigate between different sections:
        
    #     1. **Users Management** - Add users, manage wallets, view user information
    #     2. **Menu Management** - Update menu items, manage stock, set prices
    #     3. **Orders** - Create orders, track status, process payments
    #     4. **Reports & Analytics** - View sales reports, popular items, revenue trends
    #     5. **Admin** - Database administration, triggers, procedures, and debugging
        
    #     #### Quick Actions
    #     - Add funds to user wallets
    #     - Create new orders
    #     - Update order status
    #     - Export reports as CSV
        
    #     #### Tips
    #     - All changes are automatically saved to the database
    #     - Use filters to quickly find specific records
    #     - Color-coded status badges help identify order states
    #     - Triggers automatically update wallet balances and stock levels
    #     """)
    
    # Footer
    # st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p>Canteen Management System</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
