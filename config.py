DB_HOST = "localhost"
DB_USER = "user'"
DB_PASSWORD = "pass"  # Update with your MariaDB password
DB_NAME = "canteen"
DB_PORT = 3306

APP_TITLE = "Canteen Management System"
APP_ICON = ""
PAGE_LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "expanded"

PRIMARY_COLOR = "#FF6B6B"
SECONDARY_COLOR = "#4ECDC4"
SUCCESS_COLOR = "#95E1D3"
WARNING_COLOR = "#F38181"

# Database User Roles and Credentials
DB_USERS = {
    'canteen_admin': {
        'password': 'admin_pass_123',
        'role': 'Administrator',
        'description': 'Full database control and management',
        'color': '#e74c3c',
        'icon': ''
    },
    'canteen_manager': {
        'password': 'manager_pass_123',
        'role': 'Manager',
        'description': 'Data manipulation and reporting',
        'color': '#3498db',
        'icon': ''
    },
    'canteen_staff': {
        'password': 'staff_pass_123',
        'role': 'Staff Member',
        'description': 'Limited CRUD operations',
        'color': '#2ecc71',
        'icon': ''
    },
    'canteen_readonly': {
        'password': 'readonly_pass_123',
        'role': 'Read-Only User',
        'description': 'View-only access for reporting',
        'color': '#95a5a6',
        'icon': ''
    }
}

# Role-based page access control
ROLE_PERMISSIONS = {
    'canteen_admin': {
        'pages': ['Users', 'Menu', 'Orders', 'Analytics', 'Admin', 'Delete'],
        'can_create': True,
        'can_update': True,
        'can_delete': True,
        'can_view_all': True
    },
    'canteen_manager': {
        'pages': ['Users', 'Menu', 'Orders', 'Analytics'],
        'can_create': True,
        'can_update': True,
        'can_delete': True,
        'can_view_all': True
    },
    'canteen_staff': {
        'pages': ['Users', 'Orders', 'Analytics'],
        'can_create': True,
        'can_update': True,
        'can_delete': False,
        'can_view_all': False
    },
    'canteen_readonly': {
        'pages': ['Analytics'],
        'can_create': False,
        'can_update': False,
        'can_delete': False,
        'can_view_all': True
    }
}