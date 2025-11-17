import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import db_utils
import config

st.set_page_config(
    page_title="Reports & Analytics",
    page_icon="",
    layout="wide"
)

st.title("Reports & Analytics")
st.markdown("Comprehensive insights into canteen operations")
st.markdown("---")

# KPI Section
st.subheader("Key Performance Indicators")

col1, col2, col3, col4, col5 = st.columns(5)

try:
    # Total Revenue
    total_revenue = db_utils.fetch_query("""
        SELECT COALESCE(SUM(total_amount), 0) as revenue 
        FROM Orders 
        WHERE payment_status = 'completed'
    """)['revenue'][0]
    
    # Total Orders
    total_orders = db_utils.fetch_query("SELECT COUNT(*) as count FROM Orders")['count'][0]
    
    # Completed Orders
    completed_orders = db_utils.fetch_query("""
        SELECT COUNT(*) as count 
        FROM Orders 
        WHERE order_status = 'completed'
    """)['count'][0]
    
    # Average Order Value
    avg_order_value = db_utils.fetch_query("""
        SELECT COALESCE(AVG(total_amount), 0) as avg_val 
        FROM Orders 
        WHERE payment_status = 'completed'
    """)['avg_val'][0]
    
    # Total Users
    total_users = db_utils.fetch_query("SELECT COUNT(*) as count FROM Users")['count'][0]
    
    with col1:
        st.metric("Total Revenue", f"₹{total_revenue:.2f}")
    
    with col2:
        st.metric("Total Orders", total_orders)
    
    with col3:
        st.metric("Completed Orders", completed_orders)
    
    with col4:
        st.metric("Avg Order Value", f"₹{avg_order_value:.2f}")
    
    with col5:
        st.metric("Total Users", total_users)

except Exception as e:
    st.error(f"Error loading KPIs: {e}")

st.markdown("---")

# Create tabs for different reports
tab1, tab2, tab3, tab4 = st.tabs(["Popular Items", "Revenue Analysis", "Customer Insights", "Order Analytics"])

# Tab 1: Popular Items
with tab1:
    st.subheader("Most Popular Items")
    
    try:
        # Get popular items from view
        popular_items = db_utils.fetch_query("SELECT * FROM Popular_Items LIMIT 10")
        
        if not popular_items.empty:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Bar chart - Top items by quantity sold
                fig = px.bar(
                    popular_items.head(10),
                    x='item_name',
                    y='total_quantity_sold',
                    title='Top 10 Items by Quantity Sold',
                    labels={'item_name': 'Item', 'total_quantity_sold': 'Quantity Sold'},
                    color='total_quantity_sold',
                    color_continuous_scale='viridis'
                )
                fig.update_layout(xaxis_tickangle=-45, height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Revenue by item
                popular_items['revenue'] = popular_items['price'] * popular_items['total_quantity_sold']
                fig2 = px.bar(
                    popular_items.head(10),
                    x='item_name',
                    y='revenue',
                    title='Top 10 Items by Revenue',
                    labels={'item_name': 'Item', 'revenue': 'Revenue (₹)'},
                    color='revenue',
                    color_continuous_scale='blues'
                )
                fig2.update_layout(xaxis_tickangle=-45, height=400)
                st.plotly_chart(fig2, use_container_width=True)
            
            with col2:
                st.markdown("### Top 10 Items")
                display_df = popular_items.copy()
                display_df['price'] = display_df['price'].apply(lambda x: f"₹{x:.2f}")
                display_df['revenue'] = display_df['revenue'].apply(lambda x: f"₹{x:.2f}")
                
                st.dataframe(
                    display_df[['item_name', 'category_name', 'total_quantity_sold', 'revenue']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "item_name": "Item",
                        "category_name": "Category",
                        "total_quantity_sold": "Qty Sold",
                        "revenue": "Revenue"
                    }
                )
                
                # Export
                csv = popular_items.to_csv(index=False)
                st.download_button(
                    label="Download Report",
                    data=csv,
                    file_name="popular_items_report.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.info("No sales data available yet")
    
    except Exception as e:
        st.error(f"Error loading popular items: {e}")
    
    st.markdown("---")
    
    # Category-wise sales
    st.subheader("Sales by Category")
    
    try:
        category_sales = db_utils.fetch_query("""
            SELECT 
                c.category_name,
                COUNT(DISTINCT oi.order_id) as order_count,
                SUM(oi.quantity) as total_quantity,
                SUM(oi.subtotal) as total_revenue
            FROM Order_Items oi
            JOIN Menu_Items mi ON oi.item_id = mi.item_id
            JOIN Categories c ON mi.category_id = c.category_id
            GROUP BY c.category_id, c.category_name
            ORDER BY total_revenue DESC
        """)
        
        if not category_sales.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Pie chart
                fig = px.pie(
                    category_sales,
                    values='total_revenue',
                    names='category_name',
                    title='Revenue Distribution by Category',
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Table
                display_cat = category_sales.copy()
                display_cat['total_revenue'] = display_cat['total_revenue'].apply(lambda x: f"₹{x:.2f}")
                st.dataframe(display_cat, use_container_width=True, hide_index=True)
    
    except Exception as e:
        st.error(f"Error loading category sales: {e}")

# Tab 2: Revenue Analysis
with tab2:
    st.subheader("Revenue Trends")
    
    try:
        # Daily revenue
        daily_revenue = db_utils.fetch_query("""
            SELECT 
                DATE(order_date) as order_day,
                COUNT(*) as order_count,
                SUM(total_amount) as daily_revenue
            FROM Orders
            WHERE payment_status = 'completed'
            GROUP BY DATE(order_date)
            ORDER BY order_day DESC
            LIMIT 30
        """)
        
        if not daily_revenue.empty:
            daily_revenue = daily_revenue.sort_values('order_day')
            
            # Line chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=daily_revenue['order_day'],
                y=daily_revenue['daily_revenue'],
                mode='lines+markers',
                name='Daily Revenue',
                line=dict(color='#4ECDC4', width=3),
                marker=dict(size=8)
            ))
            fig.update_layout(
                title='Daily Revenue Trend (Last 30 Days)',
                xaxis_title='Date',
                yaxis_title='Revenue (₹)',
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Revenue by payment method
            payment_revenue = db_utils.fetch_query("""
                SELECT 
                    payment_method,
                    COUNT(*) as order_count,
                    SUM(total_amount) as total_revenue
                FROM Orders
                WHERE payment_status = 'completed'
                GROUP BY payment_method
                ORDER BY total_revenue DESC
            """)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if not payment_revenue.empty:
                    fig2 = px.bar(
                        payment_revenue,
                        x='payment_method',
                        y='total_revenue',
                        title='Revenue by Payment Method',
                        labels={'payment_method': 'Payment Method', 'total_revenue': 'Revenue (₹)'},
                        color='payment_method'
                    )
                    st.plotly_chart(fig2, use_container_width=True)
            
            with col2:
                # Summary stats
                st.markdown("### Revenue Summary")
                
                total_rev = daily_revenue['daily_revenue'].sum()
                avg_daily = daily_revenue['daily_revenue'].mean()
                max_daily = daily_revenue['daily_revenue'].max()
                min_daily = daily_revenue['daily_revenue'].min()
                
                st.metric("Total Revenue (Period)", f"₹{total_rev:.2f}")
                st.metric("Average Daily Revenue", f"₹{avg_daily:.2f}")
                st.metric("Highest Daily Revenue", f"₹{max_daily:.2f}")
                st.metric("Lowest Daily Revenue", f"₹{min_daily:.2f}")
            
            # Export
            csv = daily_revenue.to_csv(index=False)
            st.download_button(
                label="Download Revenue Report",
                data=csv,
                file_name="revenue_report.csv",
                mime="text/csv"
            )
        else:
            st.info("No revenue data available")
    
    except Exception as e:
        st.error(f"Error loading revenue data: {e}")

# Tab 3: Customer Insights
with tab3:
    st.subheader("Customer Analysis")
    
    try:
        # Top customers
        top_customers = db_utils.fetch_query("""
            SELECT 
                u.name,
                u.srn,
                u.user_type,
                COUNT(o.order_id) as order_count,
                SUM(o.total_amount) as total_spent
            FROM Users u
            LEFT JOIN Orders o ON u.user_id = o.user_id
            WHERE o.payment_status = 'completed'
            GROUP BY u.user_id, u.name, u.srn, u.user_type
            ORDER BY total_spent DESC
            LIMIT 10
        """)
        
        if not top_customers.empty:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Bar chart
                fig = px.bar(
                    top_customers,
                    x='name',
                    y='total_spent',
                    title='Top 10 Customers by Spending',
                    labels={'name': 'Customer', 'total_spent': 'Total Spent (₹)'},
                    color='user_type',
                    hover_data=['srn', 'order_count']
                )
                fig.update_layout(xaxis_tickangle=-45, height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### Top Customers")
                display_cust = top_customers.copy()
                display_cust['total_spent'] = display_cust['total_spent'].apply(lambda x: f"₹{x:.2f}")
                st.dataframe(display_cust, use_container_width=True, hide_index=True)
        
        # Customer type analysis
        user_type_stats = db_utils.fetch_query("""
            SELECT 
                u.user_type,
                COUNT(DISTINCT u.user_id) as user_count,
                COUNT(o.order_id) as order_count,
                COALESCE(SUM(o.total_amount), 0) as total_spent
            FROM Users u
            LEFT JOIN Orders o ON u.user_id = o.user_id AND o.payment_status = 'completed'
            GROUP BY u.user_type
        """)
        
        if not user_type_stats.empty:
            st.markdown("---")
            st.subheader("Analysis by User Type")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                fig = px.pie(
                    user_type_stats,
                    values='user_count',
                    names='user_type',
                    title='Users by Type'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.pie(
                    user_type_stats,
                    values='order_count',
                    names='user_type',
                    title='Orders by User Type'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col3:
                fig = px.pie(
                    user_type_stats,
                    values='total_spent',
                    names='user_type',
                    title='Revenue by User Type'
                )
                st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error loading customer data: {e}")

# Tab 4: Order Analytics
with tab4:
    st.subheader("Order Statistics")
    
    try:
        # Order status distribution
        status_dist = db_utils.fetch_query("""
            SELECT 
                order_status,
                COUNT(*) as count
            FROM Orders
            GROUP BY order_status
            ORDER BY count DESC
        """)
        
        if not status_dist.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    status_dist,
                    values='count',
                    names='order_status',
                    title='Order Status Distribution',
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(
                    status_dist,
                    x='order_status',
                    y='count',
                    title='Orders by Status',
                    labels={'order_status': 'Status', 'count': 'Count'},
                    color='order_status'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Payment status
        payment_dist = db_utils.fetch_query("""
            SELECT 
                payment_status,
                payment_method,
                COUNT(*) as count,
                SUM(total_amount) as total_amount
            FROM Orders
            GROUP BY payment_status, payment_method
            ORDER BY total_amount DESC
        """)
        
        if not payment_dist.empty:
            st.markdown("---")
            st.subheader("Payment Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.sunburst(
                    payment_dist,
                    path=['payment_status', 'payment_method'],
                    values='count',
                    title='Payment Status & Method Distribution'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                display_payment = payment_dist.copy()
                display_payment['total_amount'] = display_payment['total_amount'].apply(lambda x: f"₹{x:.2f}")
                st.dataframe(display_payment, use_container_width=True, hide_index=True)
        
        # Hourly order pattern (if enough data)
        hourly_pattern = db_utils.fetch_query("""
            SELECT 
                HOUR(order_date) as hour,
                COUNT(*) as order_count
            FROM Orders
            GROUP BY HOUR(order_date)
            ORDER BY hour
        """)
        
        if not hourly_pattern.empty and len(hourly_pattern) > 1:
            st.markdown("---")
            st.subheader("Order Pattern by Hour")
            
            fig = px.line(
                hourly_pattern,
                x='hour',
                y='order_count',
                title='Orders Throughout the Day',
                labels={'hour': 'Hour of Day', 'order_count': 'Number of Orders'},
                markers=True
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error loading order analytics: {e}")

# # Footer section
# st.markdown("---")
# st.markdown("""
# <div style='text-align: center; color: #666; padding: 1rem;'>
#     <p>Reports generated on: {}</p>
#     <p>All data is real-time from the database</p>
# </div>
# """.format(pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
