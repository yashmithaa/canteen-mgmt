import streamlit as st
import db_utils
import config
from functools import wraps

def require_permission(permission_type):
    """
    Decorator to check if user has specific permission
    
    Args:
        permission_type: 'can_create', 'can_update', 'can_delete', 'can_view_all'
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if db_utils.check_permission(permission_type):
                return func(*args, **kwargs)
            else:
                st.error(f"You don't have permission to perform this action")
                st.info(f"Required permission: {permission_type}")
                return None
        return wrapper
    return decorator

def check_page_access(page_name):
    """Check if current user can access a specific page"""
    current_user, _ = db_utils.get_current_db_user()
    
    # Admin has access to everything
    if current_user in ('admin', 'canteen_admin'):
        return True
    
    allowed_pages = db_utils.get_allowed_pages()
    return page_name in allowed_pages

def render_access_denied(page_name):
    """Render access denied message for a page"""
    st.error(f"**Access Denied to {page_name} Page**")
    st.warning("You do not have permission to access this page with your current user role.")
    
    current_user, _ = db_utils.get_current_db_user()
    
    if current_user in config.DB_USERS:
        user_info = config.DB_USERS[current_user]
        
        allowed_pages = db_utils.get_allowed_pages()
        
        st.markdown(f"""
        ### Your Current Role
        
        **Role:** {user_info['role']}  
        **User:** {current_user}  
        **Description:** {user_info['description']}
        
        ### Pages You Can Access:
        {', '.join(allowed_pages) if allowed_pages else 'None'}
        """)
    
    st.markdown("---")
    
    # Show role comparison
    st.subheader("Role Comparison")
    
    role_data = []
    for user, info in config.DB_USERS.items():
        permissions = config.ROLE_PERMISSIONS[user]
        role_data.append({
            'Role': info['role'],
            'Can Access This Page': 'Yes' if page_name in permissions['pages'] else 'No',
            'Create': 'Yes' if permissions['can_create'] else 'No',
            'Update': 'Yes' if permissions['can_update'] else 'No',
            'Delete': 'Yes' if permissions['can_delete'] else 'No'
        })
    
    import pandas as pd
    st.dataframe(pd.DataFrame(role_data), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.info("**Tip:** Use the sidebar to switch to a different user role with appropriate permissions.")

def render_permission_badge(permission_type):
    """Render a visual badge showing if user has a permission"""
    has_permission = db_utils.check_permission(permission_type)
    
    permission_names = {
        'can_create': 'Create',
        'can_update': 'Update',
        'can_delete': 'Delete',
        'can_view_all': 'View All'
    }
    
    name = permission_names.get(permission_type, permission_type)
    
    if has_permission:
        st.markdown(f"""
        <span style='background-color: #d4edda; color: #155724; padding: 0.3rem 0.8rem; 
                     border-radius: 15px; font-size: 0.85rem; font-weight: 600;'>
            {name} — Allowed
        </span>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <span style='background-color: #f8d7da; color: #721c24; padding: 0.3rem 0.8rem; 
                     border-radius: 15px; font-size: 0.85rem; font-weight: 600;'>
            {name} — Denied
        </span>
        """, unsafe_allow_html=True)

def show_current_role_info():
    """Display current role information banner"""
    current_user, _ = db_utils.get_current_db_user()
    
    if current_user in ('admin', 'canteen_admin'):
        st.info("""
        **Logged in as Administrator**  
        You have full access to all features and pages.
        """)
        return
    
    if current_user in config.DB_USERS:
        user_info = config.DB_USERS[current_user]
        role = db_utils.get_user_role()
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {user_info['color']}22 0%, {user_info['color']}44 100%; 
                padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid {user_info['color']};'>
            <strong>Current Role: {user_info['role']}</strong><br>
            <small>User: {current_user} | {user_info['description']}</small>
        </div>
        """, unsafe_allow_html=True)

def create_permission_protected_button(label, permission_type, key=None, on_click=None, **kwargs):
    """
    Create a button that's disabled if user lacks permission
    
    Args:
        label: Button label
        permission_type: Required permission ('can_create', 'can_update', 'can_delete')
        key: Streamlit widget key
        on_click: Callback function
        **kwargs: Additional button arguments
    """
    has_permission = db_utils.check_permission(permission_type)
    
    if not has_permission:
        # Show disabled button with lock icon
        return st.button(
            f"{label}",
            disabled=True,
            key=key,
            help=f"You don't have {permission_type} permission",
            **kwargs
        )
    else:
        # Show enabled button
        return st.button(
            label,
            key=key,
            on_click=on_click,
            **kwargs
        )

def create_permission_protected_form(form_name, permission_type):
    """
    Create a form context that checks permissions
    
    Usage:
        with create_permission_protected_form("add_user", "can_create"):
            # form contents
    """
    class PermissionProtectedForm:
        def __init__(self, form_key, perm_type):
            self.form_key = form_key
            self.has_permission = db_utils.check_permission(perm_type)
            self.perm_type = perm_type
        
        def __enter__(self):
            if not self.has_permission:
                st.error(f"You don't have {self.perm_type} permission")
                return None
            return st.form(self.form_key).__enter__()
        
        def __exit__(self, *args):
            if self.has_permission:
                return st.form(self.form_key).__exit__(*args)
    
    return PermissionProtectedForm(form_name, permission_type)

def get_filtered_query_based_on_role(base_query, user_filter_field='user_id'):
    """
    Modify query based on user role to limit data visibility
    
    Args:
        base_query: Base SQL query
        user_filter_field: Field name to filter by user (if role requires it)
    
    Returns:
        Modified query string and whether filtering was applied
    """
    current_user, _ = db_utils.get_current_db_user()
    role = db_utils.get_user_role()
    
    # Admin and users with view_all can see everything
    if current_user in ('admin', 'canteen_admin') or role.get('can_view_all', False):
        return base_query, False
    
    # For staff with limited view, could add WHERE clause here
    # This is a placeholder for future implementation
    return base_query, False