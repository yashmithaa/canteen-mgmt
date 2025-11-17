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
    .role-badge {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        display: inline-block;
        margin: 0.5rem 0;
    }
    .permission-item {
        padding: 0.3rem 0.8rem;
        margin: 0.2rem;
        border-radius: 15px;
        display: inline-block;
        font-size: 0.85rem;
    }
    .permission-granted {
        background-color: #d4edda;
        color: #155724;
    }
    .permission-denied {
        background-color: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

def render_user_switcher():
    """Render user role switcher in sidebar"""
    
    st.sidebar.markdown("### Database User Role")
    
    # Get current user
    current_user, _ = db_utils.get_current_db_user()
    
    # Display current role badge
    if current_user in config.DB_USERS:
        user_info = config.DB_USERS[current_user]
        st.sidebar.markdown(f"""
        <div style='background-color: {user_info['color']}; padding: 1rem; margin: 1rem; border-radius: 10px; color: white; text-align: center;'>
            <div style='font-weight: bold; font-size: 1.1rem;'>{user_info['role']}</div>
            <div style='font-size: 0.85rem; opacity: 0.9;'>{current_user}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

    # User switcher
    with st.sidebar.expander("Switch User Role", expanded=False):
        st.markdown("**Select Database User:**")
        
        # Use configured DB users only (remove separate root admin option)
        user_options = list(config.DB_USERS.keys())
        user_display = [f"{config.DB_USERS[u]['role']}" for u in user_options]

        # Default index should prefer the canteen_admin user
        default_index = 0
        if current_user in user_options:
            default_index = user_options.index(current_user)
        else:
            try:
                default_index = user_options.index('canteen_admin')
            except ValueError:
                default_index = 0

        selected_idx = st.selectbox(
            "User",
            range(len(user_options)),
            format_func=lambda x: user_display[x],
            index=default_index,
            key="user_selector"
        )

        selected_user = user_options[selected_idx]

        # Show user description and password input
        st.info(f"**Access Level:** {config.DB_USERS[selected_user]['description']}")

        pwd_input = st.text_input("Enter password to switch (required)", type="password", key="switch_pwd")

        # Switch button: verify credentials before actually switching session user
        if st.button("Switch to This User", use_container_width=True):
            if not pwd_input:
                st.error("Please enter the password for the selected user to switch.")
            else:
                ok, msg = db_utils.verify_db_credentials(selected_user, pwd_input)
                if ok:
                    db_utils.set_db_user(selected_user, pwd_input)
                    st.success(f"Switched to {selected_user}!")
                    st.rerun()
                else:
                    st.error(f"Failed to switch: {msg}")
                    st.info("You remain connected as the view-only user until valid credentials are provided.")
    
    # Show permissions for current role
    with st.sidebar.expander("My Permissions", expanded=False):
        role = db_utils.get_user_role()
        
        if role:
            st.markdown("**Allowed Pages:**")
            for page in role.get('pages', []):
                st.markdown(f"- {page}")
            
            st.markdown("**Operations:**")
            
            permissions = [
                ('Create', 'can_create'),
                ('Update', 'can_update'),
                ('Delete', 'can_delete'),
                ('View All', 'can_view_all')
            ]

            for perm_name, perm_key in permissions:
                if role.get(perm_key, False):
                    st.markdown(f"- {perm_name}: Yes")
                else:
                    st.markdown(f"- {perm_name}: No")
        else:
            st.info("Full administrator access")

def check_page_access(page_name):
    """Check if current user can access a page"""
    current_user, _ = db_utils.get_current_db_user()
    
    # Admin has access to everything
    if current_user in ('admin', 'canteen_admin'):
        return True
    
    allowed_pages = db_utils.get_allowed_pages()
    return page_name in allowed_pages

def render_access_denied():
    """Render access denied message"""
    st.error("**Access Denied**")
    st.warning("You do not have permission to access this page with your current user role.")
    
    current_user, _ = db_utils.get_current_db_user()
    if current_user in config.DB_USERS:
        user_info = config.DB_USERS[current_user]
        st.info(f"""
        **Current Role:** {user_info['role']}
        
        **Your Allowed Pages:**
        {', '.join(db_utils.get_allowed_pages())}
        """)
    
    st.markdown("---")
    st.info("**Tip:** Switch to a different user role from the sidebar to access more features.")

def main():
    # Render user switcher in sidebar
    render_user_switcher()
    
    with st.sidebar:
        st.markdown("### Quick Stats")
        
        # Connection status
        status, msg = db_utils.test_connection()
        if status:
            st.success("Connected")
            st.caption(msg)
        else:
            st.error("Disconnected")
            st.error(msg)
        
        st.markdown("---")
        
        # Quick stats (if user has access)
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
    
    # Show role-based welcome message
    current_user, _ = db_utils.get_current_db_user()
    
    if current_user in config.DB_USERS:
        user_info = config.DB_USERS[current_user]
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {user_info['color']}22 0%, {user_info['color']}44 100%); 
                    padding: 1.5rem; border-radius: 10px; border-left: 4px solid {user_info['color']};'>
            <h3>{user_info['icon']} Welcome, {user_info['role']}!</h3>
            <p><strong>Current User:</strong> {current_user}</p>
            <p><strong>Access Level:</strong> {user_info['description']}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #e74c3c22 0%, #e74c3c44 100%); 
                    padding: 1.5rem; border-radius: 10px; border-left: 4px solid #e74c3c;'>
            <h3>👑 Welcome, Administrator!</h3>
            <p><strong>Current User:</strong> {current_user}</p>
            <p><strong>Access Level:</strong> Full system administrator with all privileges</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
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
    
    st.markdown("---")
    
    # Role-based quick actions
    st.subheader("Quick Actions")
    
    role = db_utils.get_user_role()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if role.get('can_create', False) or current_user in ('admin', 'canteen_admin'):
            if st.button("Add New User", use_container_width=True):
                st.info("Navigate to Users → Add New User tab")
        else:
            st.button("Add New User", disabled=True, use_container_width=True)
    
    with col2:
        if 'Orders' in db_utils.get_allowed_pages() or current_user in ('admin', 'canteen_admin'):
            if st.button("Create Order", use_container_width=True):
                st.info("Navigate to Orders → New Order tab")
        else:
            st.button("Create Order", disabled=True, use_container_width=True)
    
    with col3:
        if 'Analytics' in db_utils.get_allowed_pages() or current_user in ('admin', 'canteen_admin'):
            if st.button("View Reports", use_container_width=True):
                st.info("Navigate to Analytics page")
        else:
            st.button("View Reports", disabled=True, use_container_width=True)
    
    with col4:
        if role.get('can_update', False) or current_user in ('admin', 'canteen_admin'):
            if st.button("Manage Wallets", use_container_width=True):
                st.info("Navigate to Users → Wallet Management tab")
        else:
            st.button("Manage Wallets", disabled=True, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p><strong>Canteen Management System</strong></p>
        <p style='font-size: 0.85rem;'>Role-Based Access Control Enabled</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()