import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import pyodbc

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="TallyPrime ODBC Intelligence Hub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .metric-card {
        background: #1e222d;
        border-radius: 10px;
        padding: 16px;
        border-left: 5px solid #29b5e8;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        margin-bottom: 12px;
    }
    .metric-title {
        color: #9aa0a6;
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-value {
        color: #ffffff;
        font-size: 1.6rem;
        font-weight: 700;
        margin-top: 4px;
    }
    .metric-delta {
        font-size: 0.8rem;
        font-weight: 500;
        margin-top: 4px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        border-radius: 6px;
        padding-left: 16px;
        padding-right: 16px;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Synthetic Mock Data Generator (Offline / Fallback Mode)
# ---------------------------------------------------------
def generate_mock_tally_data():
    """Generates realistic Tally ERP / Prime data for offline testing."""
    ledgers_data = [
        # Revenue / Profit Centers
        {"Name": "Domestic Sales - North Zone", "Parent": "Sales Accounts", "ClosingBalance": -14500000.0, "IsRevenue": "Yes"},
        {"Name": "Domestic Sales - West Zone", "Parent": "Sales Accounts", "ClosingBalance": -18200000.0, "IsRevenue": "Yes"},
        {"Name": "Export Software Services", "Parent": "Sales Accounts", "ClosingBalance": -26400000.0, "IsRevenue": "Yes"},
        {"Name": "Consulting & Advisory Fees", "Parent": "Direct Incomes", "ClosingBalance": -5800000.0, "IsRevenue": "Yes"},
        {"Name": "Interest & Dividend Income", "Parent": "Indirect Incomes", "ClosingBalance": -950000.0, "IsRevenue": "Yes"},
        
        # Direct Cost / Cost Centers
        {"Name": "Raw Material Consumption - Grade A", "Parent": "Direct Expenses", "ClosingBalance": 12800000.0, "IsRevenue": "No"},
        {"Name": "Raw Material Consumption - Grade B", "Parent": "Direct Expenses", "ClosingBalance": 7400000.0, "IsRevenue": "No"},
        {"Name": "Direct Factory Wages & Overtime", "Parent": "Direct Expenses", "ClosingBalance": 4600000.0, "IsRevenue": "No"},
        {"Name": "Freight & Inward Carriage", "Parent": "Direct Expenses", "ClosingBalance": 1850000.0, "IsRevenue": "No"},
        {"Name": "Sub-Contracting & Job Work", "Parent": "Direct Expenses", "ClosingBalance": 3200000.0, "IsRevenue": "No"},

        # Expense Centers (Indirect Overheads)
        {"Name": "Executive & Staff Salaries", "Parent": "Indirect Expenses", "ClosingBalance": 8900000.0, "IsRevenue": "No"},
        {"Name": "Corporate Office Rent", "Parent": "Indirect Expenses", "ClosingBalance": 2400000.0, "IsRevenue": "No"},
        {"Name": "Cloud Infrastructure & AWS Hosting", "Parent": "Indirect Expenses", "ClosingBalance": 1750000.0, "IsRevenue": "No"},
        {"Name": "Marketing & Digital Advertising", "Parent": "Indirect Expenses", "ClosingBalance": 2900000.0, "IsRevenue": "No"},
        {"Name": "Legal & Audit Compliance Fees", "Parent": "Indirect Expenses", "ClosingBalance": 850000.0, "IsRevenue": "No"},
        {"Name": "Electricity & Power Charges", "Parent": "Indirect Expenses", "ClosingBalance": 1100000.0, "IsRevenue": "No"},
        {"Name": "Travel & Business Conveyance", "Parent": "Indirect Expenses", "ClosingBalance": 940000.0, "IsRevenue": "No"},
        {"Name": "Depreciation on Assets", "Parent": "Indirect Expenses", "ClosingBalance": 1350000.0, "IsRevenue": "No"},
        {"Name": "Software Subscriptions & SaaS Tools", "Parent": "Indirect Expenses", "ClosingBalance": 620000.0, "IsRevenue": "No"},
        {"Name": "Telephone & Bandwidth Charges", "Parent": "Indirect Expenses", "ClosingBalance": 380000.0, "IsRevenue": "No"},

        # Balance Sheet Ledgers
        {"Name": "HDFC Bank Current Account", "Parent": "Bank Accounts", "ClosingBalance": 4500000.0, "IsRevenue": "No"},
        {"Name": "ICICI Bank Operating Account", "Parent": "Bank Accounts", "ClosingBalance": 2800000.0, "IsRevenue": "No"},
        {"Name": "Sundry Debtors - Domestic", "Parent": "Sundry Debtors", "ClosingBalance": 11200000.0, "IsRevenue": "No"},
        {"Name": "Sundry Creditors - Vendors", "Parent": "Sundry Creditors", "ClosingBalance": -6400000.0, "IsRevenue": "No"},
    ]
    df_ledgers = pd.DataFrame(ledgers_data)

    cost_centres_data = [
        {"Name": "North Sales Hub", "Category": "Branches", "Parent": "Primary", "AllocatedExpense": 2800000.0, "AllocatedRevenue": 14500000.0, "Type": "Profit Center"},
        {"Name": "West Sales Hub", "Category": "Branches", "Parent": "Primary", "AllocatedExpense": 3200000.0, "AllocatedRevenue": 18200000.0, "Type": "Profit Center"},
        {"Name": "Global Delivery Unit", "Category": "Divisions", "Parent": "Primary", "AllocatedExpense": 5400000.0, "AllocatedRevenue": 26400000.0, "Type": "Profit Center"},
        {"Name": "Fintech Client Engagements", "Category": "Projects", "Parent": "Primary", "AllocatedExpense": 2100000.0, "AllocatedRevenue": 5800000.0, "Type": "Profit Center"},
        {"Name": "Corporate HQ Administration", "Category": "Departments", "Parent": "Primary", "AllocatedExpense": 3400000.0, "AllocatedRevenue": 0.0, "Type": "Cost Center"},
        {"Name": "IT & DevOps Infrastructure", "Category": "Departments", "Parent": "Primary", "AllocatedExpense": 2370000.0, "AllocatedRevenue": 0.0, "Type": "Expense Center"},
        {"Name": "HR & Talent Acquisition", "Category": "Departments", "Parent": "Primary", "AllocatedExpense": 1450000.0, "AllocatedRevenue": 0.0, "Type": "Expense Center"},
        {"Name": "Plant 1 - Manufacturing", "Category": "Production Units", "Parent": "Primary", "AllocatedExpense": 18200000.0, "AllocatedRevenue": 0.0, "Type": "Cost Center"},
        {"Name": "R&D AI Innovations", "Category": "Departments", "Parent": "Primary", "AllocatedExpense": 1950000.0, "AllocatedRevenue": 0.0, "Type": "Cost Center"},
    ]
    df_cost_centers = pd.DataFrame(cost_centres_data)

    months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
    np.random.seed(42)
    vouchers_data = []
    for i, m in enumerate(months):
        vouchers_data.append({
            "Month": m,
            "MonthIndex": i + 1,
            "Revenue": np.random.uniform(4.5, 6.2) * 1000000,
            "DirectExpense": np.random.uniform(2.1, 3.2) * 1000000,
            "IndirectExpense": np.random.uniform(1.4, 2.0) * 1000000,
            "VoucherCount": int(np.random.uniform(180, 320))
        })
    df_monthly = pd.DataFrame(vouchers_data)

    return df_ledgers, df_cost_centers, df_monthly


# ---------------------------------------------------------
# Tally ODBC Extraction Engine
# ---------------------------------------------------------
def clean_numeric_col(series):
    """Parses Tally string balances into clean signed floats."""
    def _parse(val):
        if pd.isna(val):
            return 0.0
        val_str = str(val).strip()
        is_credit = "Cr" in val_str or "cr" in val_str
        clean_num = val_str.replace("Dr", "").replace("dr", "").replace("Cr", "").replace("cr", "").replace(",", "").strip()
        try:
            amt = float(clean_num)
            return -abs(amt) if is_credit else amt
        except Exception:
            return 0.0
    return series.apply(_parse)


def connect_tally_odbc(dsn_name="TallyODBC64_9000", host="localhost", port=9000, mode="DSN"):
    """Creates a connection object to Tally ODBC driver."""
    try:
        if mode == "DSN":
            conn_str = f"DSN={dsn_name};"
        else:
            conn_str = f"DRIVER={{Tally ODBC Driver64}};SERVER={host};PORT={port};"
        
        conn = pyodbc.connect(conn_str, timeout=5)
        return conn, None
    except Exception as e:
        return None, str(e)


def extract_tally_tables(conn):
    """Executes SQL statements on Tally ODBC Collections."""
    # 1. Fetch Ledgers
    ledger_sql = "SELECT $Name,$Parent, $ClosingBalance,$IsRevenue FROM Ledger"
    try:
        df_ledgers = pd.read_sql(ledger_sql, conn)
        # Normalize columns
        df_ledgers.columns = [col.lstrip("$_").strip() for col in df_ledgers.columns]
        if "ClosingBalance" in df_ledgers.columns:
            df_ledgers["ClosingBalance"] = clean_numeric_col(df_ledgers["ClosingBalance"])
    except Exception:
        df_ledgers = pd.DataFrame()

    # 2. Fetch Cost Centres
    cc_sql = "SELECT $Name, $Parent,$CategoryName FROM CostCentre"
    try:
        df_cost_centers = pd.read_sql(cc_sql, conn)
        df_cost_centers.columns = [col.lstrip("$_").strip() for col in df_cost_centers.columns]
    except Exception:
        df_cost_centers = pd.DataFrame()

    # 3. Fetch Vouchers summary
    vch_sql = "SELECT TOP 1000 $Date,$VoucherTypeName, $VoucherNumber,$Amount FROM Voucher"
    try:
        df_vouchers = pd.read_sql(vch_sql, conn)
        df_vouchers.columns = [col.lstrip("$_").strip() for col in df_vouchers.columns]
    except Exception:
        df_vouchers = pd.DataFrame()

    return df_ledgers, df_cost_centers, df_vouchers


def classify_ledger(row):
    """Classifies ledgers into financial centers and reporting heads."""
    parent = str(row.get("Parent", "")).lower()
    name = str(row.get("Name", "")).lower()

    if any(k in parent for k in ["sales", "direct income", "revenue", "income (direct)"]):
        return "Profit Center (Direct Revenue)", "Revenue"
    elif any(k in parent for k in ["indirect income", "other income"]):
        return "Profit Center (Other Income)", "Revenue"
    elif any(k in parent for k in ["direct expense", "purchase", "job work", "wages", "freight"]):
        return "Cost Center (Direct Cost / COGS)", "Direct Expense"
    elif any(k in parent for k in ["indirect expense", "administrative", "selling", "operating"]):
        return "Expense Center (Overheads)", "Indirect Expense"
    elif any(k in parent for k in ["bank", "cash", "debtor", "current asset", "fixed asset"]):
        return "Asset Center", "Balance Sheet"
    elif any(k in parent for k in ["creditor", "loan", "capital", "duties", "provisions"]):
        return "Liability Center", "Balance Sheet"
    else:
        return "General Ledger", "Unclassified"


# ---------------------------------------------------------
# Sidebar: Controls & Connection Management
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/database--v1.png", width=64)
    st.title("Tally ODBC Settings")
    st.caption("Direct SQL Bridge for TallyPrime / Tally.ERP 9")

    conn_type = st.radio("Connection Interface", ["DSN Name", "Direct Driver"], horizontal=True)

    if conn_type == "DSN Name":
        dsn_name = st.text_input("ODBC DSN", value="TallyODBC64_9000", help="Configured DSN in Windows ODBC Data Sources")
        host_val, port_val = "localhost", 9000
    else:
        dsn_name = ""
        host_val = st.text_input("Server Host", value="localhost")
        port_val = st.number_input("Tally ODBC Port", value=9000, step=1)

    use_demo_data = st.checkbox("Force Demo / Offline Data", value=False)
    btn_sync = st.button("🔄 Sync Live Tally Data", use_container_width=True, type="primary")

    with st.expander("📌 Tally ODBC Setup Checklist"):
        st.markdown("""
        1. Open **TallyPrime**.
        2. Press `F1` (Help) > **Settings** > **Connectivity**.
        3. Set **Client/Server configuration** to `Both` or `Server`.
        4. Set **Port** to `9000`.
        5. Accept and restart TallyPrime.
        6. Open your company before syncing.
        """)

    st.markdown("---")
    st.markdown("### Dashboard Filters")


# ---------------------------------------------------------
# Data Acquisition Pipeline
# ---------------------------------------------------------
data_source_label = "Demo Dataset"
df_ledgers = pd.DataFrame()
df_cost_centers = pd.DataFrame()
df_monthly = pd.DataFrame()

if not use_demo_data:
    conn, err = connect_tally_odbc(dsn_name=dsn_name, host=host_val, port=port_val, mode=conn_type)
    if conn:
        with st.spinner("Extracting Collections via Tally ODBC..."):
            df_ledgers, df_cost_centers, df_vch = extract_tally_tables(conn)
            data_source_label = "Live TallyPrime (Port 9000)"
            st.sidebar.success(" Connected to TallyPrime ODBC")
            conn.close()
    else:
        st.sidebar.warning("⚠️ Live Tally ODBC unavailable. Loaded demo model.")
        df_ledgers, df_cost_centers, df_monthly = generate_mock_tally_data()
else:
    df_ledgers, df_cost_centers, df_monthly = generate_mock_tally_data()
    st.sidebar.info("Using Built-in Analytical Demo Model")


# ---------------------------------------------------------
# Data Transformation & Business Classification
# ---------------------------------------------------------
if not df_ledgers.empty:
    if "ClosingBalance" not in df_ledgers.columns:
        df_ledgers["ClosingBalance"] = 0.0
    
    # Apply accounting classifications
    classes = df_ledgers.apply(classify_ledger, axis=1)
    df_ledgers["CenterClassification"] = [c[0] for c in classes]
    df_ledgers["ReportType"] = [c[1] for c in classes]

    # Absolute amounts for magnitude comparisons
    df_ledgers["AbsoluteBalance"] = df_ledgers["ClosingBalance"].abs()

    # Aggregations
    total_revenue = df_ledgers[df_ledgers["ReportType"] == "Revenue"]["AbsoluteBalance"].sum()
    total_direct_exp = df_ledgers[df_ledgers["ReportType"] == "Direct Expense"]["AbsoluteBalance"].sum()
    total_indirect_exp = df_ledgers[df_ledgers["ReportType"] == "Indirect Expense"]["AbsoluteBalance"].sum()
    gross_profit = total_revenue - total_direct_exp
    net_profit = gross_profit - total_indirect_exp
    gp_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0.0
    np_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0.0
else:
    total_revenue = total_direct_exp = total_indirect_exp = gross_profit = net_profit = gp_margin = np_margin = 0.0


# Additional filter widgets in sidebar based on loaded data
if not df_ledgers.empty:
    with st.sidebar:
        parent_groups = ["All"] + sorted(list(df_ledgers["Parent"].dropna().unique()))
        selected_parent = st.selectbox("Filter by Ledger Group", parent_groups)
        
        if selected_parent != "All":
            filtered_ledgers = df_ledgers[df_ledgers["Parent"] == selected_parent]
        else:
            filtered_ledgers = df_ledgers
else:
    filtered_ledgers = df_ledgers


# ---------------------------------------------------------
# Top Header & Metadata Banner
# ---------------------------------------------------------
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("TallyPrime Executive Analytics")
    st.caption(f"Financial Cost, Profit & Expense Center Intelligence | Source: **{data_source_label}**")
with col_h2:
    st.markdown(f"<div style='text-align: right; padding-top: 15px; color: #888;'>Refreshed: {datetime.now().strftime('%d-%b-%Y %H:%M')}</div>", unsafe_allow_html=True)


# ---------------------------------------------------------
# Executive KPI Row
# ---------------------------------------------------------
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #00d084;">
        <div class="metric-title">Total Revenue</div>
        <div class="metric-value">₹ {total_revenue/1e5:,.2f} L</div>
        <div class="metric-delta" style="color: #00d084;">Turnover & Incomes</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #ff9800;">
        <div class="metric-title">Direct Costs (COGS)</div>
        <div class="metric-value">₹ {total_direct_exp/1e5:,.2f} L</div>
        <div class="metric-delta" style="color: #ff9800;">Production & Direct Costs</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #29b5e8;">
        <div class="metric-title">Gross Profit</div>
        <div class="metric-value">₹ {gross_profit/1e5:,.2f} L</div>
        <div class="metric-delta" style="color: #29b5e8;">Margin: {gp_margin:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #f44336;">
        <div class="metric-title">Indirect Overheads</div>
        <div class="metric-value">₹ {total_indirect_exp/1e5:,.2f} L</div>
        <div class="metric-delta" style="color: #f44336;">Expense Centers</div>
    </div>
    """, unsafe_allow_html=True)

with kpi5:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #9c27b0;">
        <div class="metric-title">Net Operating Profit</div>
        <div class="metric-value">₹ {net_profit/1e5:,.2f} L</div>
        <div class="metric-delta" style="color: {'#00d084' if net_profit >= 0 else '#f44336'};">Net Margin: {np_margin:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")


# ---------------------------------------------------------
# Main Analytical Tabs
# ---------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Executive P&L & Margins",
    "🏢 Cost & Profit Centers",
    "💸 Expense Center Deep Dive",
    "📋 Ledger Master & Data Explorer"
])


# ---------------------------------------------------------
# TAB 1: Executive P&L and Margin Overview
# ---------------------------------------------------------
with tab1:
    st.subheader("Financial Performance Architecture")
    
    col_t1_1, col_t1_2 = st.columns([3, 2])
    
    with col_t1_1:
        # Waterfall Chart of P&L Breakdown
        waterfall_fig = go.Figure(go.Waterfall(
            name="P&L Breakdown",
            orientation="v",
            measure=["absolute", "relative", "total", "relative", "total"],
            x=["Gross Revenue", "Direct Costs", "Gross Profit", "Indirect Overheads", "Net Profit"],
            textposition="outside",
            text=[f"₹{v/1e5:,.1f}L" for v in [total_revenue, -total_direct_exp, gross_profit, -total_indirect_exp, net_profit]],
            y=[total_revenue, -total_direct_exp, 0, -total_indirect_exp, 0],
            connector={"line": {"color": "#6c757d"}},
            decreasing={"marker": {"color": "#e63946"}},
            increasing={"marker": {"color": "#2a9d8f"}},
            totals={"marker": {"color": "#457b9d"}}
        ))
        waterfall_fig.update_layout(
            title="Revenue to Net Profit Bridge",
            height=380,
            template="plotly_dark",
            margin=dict(l=30, r=30, t=50, b=30)
        )
        st.plotly_chart(waterfall_fig, use_container_width=True)

    with col_t1_2:
        # Cost-to-Income Distribution
        pie_data = pd.DataFrame({
            "Head": ["Direct Costs", "Indirect Expenses", "Net Profit Retention"],
            "Amount": [total_direct_exp, total_indirect_exp, max(0.0, net_profit)]
        })
        fig_pie = px.pie(
            pie_data,
            values="Amount",
            names="Head",
            title="Revenue Allocation Distribution",
            color="Head",
            color_discrete_map={
                "Direct Costs": "#ff9800",
                "Indirect Expenses": "#e63946",
                "Net Profit Retention": "#2a9d8f"
            },
            hole=0.45,
            template="plotly_dark"
        )
        fig_pie.update_layout(height=380, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_pie, use_container_width=True)

    # Monthly Trends (if available)
    if not df_monthly.empty:
        st.subheader("Monthly Revenue vs Operating Cost Velocity")
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=df_monthly["Month"],
            y=df_monthly["Revenue"],
            name="Revenue",
            marker_color="#2a9d8f"
        ))
        fig_trend.add_trace(go.Bar(
            x=df_monthly["Month"],
            y=df_monthly["DirectExpense"],
            name="Direct Cost",
            marker_color="#e76f51"
        ))
        fig_trend.add_trace(go.Bar(
            x=df_monthly["Month"],
            y=df_monthly["IndirectExpense"],
            name="Indirect Overheads",
            marker_color="#f4a261"
        ))
        fig_trend.update_layout(
            barmode="group",
            template="plotly_dark",
            height=340,
            margin=dict(l=30, r=30, t=30, b=30),
            yaxis_title="Amount (₹)"
        )
        st.plotly_chart(fig_trend, use_container_width=True)


# ---------------------------------------------------------
# TAB 2: Cost & Profit Center Intelligence
# ---------------------------------------------------------
with tab2:
    st.subheader("Cost, Profit & Expense Center Breakdown")

    if not df_cost_centers.empty and "AllocatedExpense" in df_cost_centers.columns:
        col_c1, col_c2 = st.columns([3, 2])

        with col_c1:
            # Horizontal bar comparison for Cost vs Profit Centers
            df_cc_sorted = df_cost_centers.sort_values(by="AllocatedExpense", ascending=True)
            fig_cc = go.Figure()
            fig_cc.add_trace(go.Bar(
                y=df_cc_sorted["Name"],
                x=df_cc_sorted["AllocatedExpense"],
                name="Expenses Incurred",
                orientation="h",
                marker_color="#e63946"
            ))
            fig_cc.add_trace(go.Bar(
                y=df_cc_sorted["Name"],
                x=df_cc_sorted["AllocatedRevenue"],
                name="Revenue Generated",
                orientation="h",
                marker_color="#2a9d8f"
            ))
            fig_cc.update_layout(
                title="Center-Wise Revenue Contribution vs Incurred Cost",
                barmode="group",
                template="plotly_dark",
                height=420,
                xaxis_title="Amount (₹)",
                margin=dict(l=50, r=30, t=50, b=30)
            )
            st.plotly_chart(fig_cc, use_container_width=True)

        with col_c2:
            # Treemap by Category & Type
            fig_tm = px.treemap(
                df_cost_centers,
                path=["Category", "Type", "Name"],
                values="AllocatedExpense",
                color="Type",
                color_discrete_map={"Profit Center": "#2a9d8f", "Cost Center": "#e76f51", "Expense Center": "#f4a261"},
                title="Expense Distribution Hierarchy by Category",
                template="plotly_dark"
            )
            fig_tm.update_layout(height=420, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_tm, use_container_width=True)

        # Cost Center Efficiency Table
        st.write("#### Center Profitability & Margin Ledger")
        df_cc_display = df_cost_centers.copy()
        df_cc_display["Net Contribution"] = df_cc_display["AllocatedRevenue"] - df_cc_display["AllocatedExpense"]
        df_cc_display["Cost Efficiency %"] = np.where(
            df_cc_display["AllocatedRevenue"] > 0,
            ((df_cc_display["AllocatedRevenue"] - df_cc_display["AllocatedExpense"]) / df_cc_display["AllocatedRevenue"]) * 100,
            0.0
        )
        
        # Formatting for presentation
        styled_df = df_cc_display.style.format({
            "AllocatedExpense": "₹ {:,.2f}",
            "AllocatedRevenue": "₹ {:,.2f}",
            "Net Contribution": "₹ {:,.2f}",
            "Cost Efficiency %": "{:.1f}%"
        })
        st.dataframe(styled_df, use_container_width=True, height=280)

    else:
        # Fallback view if Tally CostCentre master has no direct allocation table
        st.info("Direct CostCentre tables detected from Tally. Displaying registered masters hierarchy:")
        st.dataframe(df_cost_centers, use_container_width=True)


# ---------------------------------------------------------
# TAB 3: Expense Center Deep Dive
# ---------------------------------------------------------
with tab3:
    st.subheader("Expense Center Head-Wise Analytics")

    df_expenses = df_ledgers[df_ledgers["ReportType"].isin(["Direct Expense", "Indirect Expense"])].copy()

    if not df_expenses.empty:
        col_exp1, col_exp2 = st.columns(2)

        with col_exp1:
            # Top 10 Expense Drivers (Pareto View)
            top_expenses = df_expenses.sort_values(by="AbsoluteBalance", ascending=False).head(10)
            fig_top_exp = px.bar(
                top_expenses,
                x="AbsoluteBalance",
                y="Name",
                orientation="h",
                color="ReportType",
                color_discrete_map={"Direct Expense": "#e76f51", "Indirect Expense": "#f4a261"},
                title="Top 10 Expense Ledgers by Volume",
                labels={"AbsoluteBalance": "Total Incurred (₹)", "Name": "Ledger Head"},
                template="plotly_dark"
            )
            fig_top_exp.update_layout(yaxis={"autorange": "reversed"}, height=400)
            st.plotly_chart(fig_top_exp, use_container_width=True)

        with col_exp2:
            # Expense classification breakdown
            exp_group_summary = df_expenses.groupby("Parent")["AbsoluteBalance"].sum().reset_index()
            fig_group_pie = px.pie(
                exp_group_summary,
                names="Parent",
                values="AbsoluteBalance",
                title="Expense Distribution by Grouping Parent",
                hole=0.4,
                template="plotly_dark"
            )
            fig_group_pie.update_layout(height=400)
            st.plotly_chart(fig_group_pie, use_container_width=True)

        st.write("#### Detailed Expense Ledger Register")
        st.dataframe(
            df_expenses[["Name", "Parent", "ReportType", "AbsoluteBalance"]].sort_values(by="AbsoluteBalance", ascending=False).style.format({
                "AbsoluteBalance": "₹ {:,.2f}"
            }),
            use_container_width=True,
            height=300
        )
    else:
        st.warning("No expense ledgers found under current selection.")


# ---------------------------------------------------------
# TAB 4: Ledger Master & Raw Data Explorer
# ---------------------------------------------------------
with tab4:
    st.subheader("Ledger Master Registry & Data Export")
    
    col_f1, col_f2 = st.columns([3, 1])
    with col_f1:
        search_query = st.text_input("🔍 Search Ledger by Name or Category", "")
    with col_f2:
        st.write("")
        st.write("")
        csv = filtered_ledgers.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export Ledger Data to CSV",
            data=csv,
            file_name=f"tally_ledger_data_{date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )

    view_df = filtered_ledgers
    if search_query:
        view_df = view_df[view_df["Name"].str.contains(search_query, case=False, na=False)]

    st.dataframe(
        view_df.style.format({
            "ClosingBalance": "₹ {:,.2f}",
            "AbsoluteBalance": "₹ {:,.2f}"
        }),
        use_container_width=True,
        height=450
    )

    # Custom Query Console for Tally ODBC
    with st.expander("🛠️ Advanced: Direct TDL SQL Console"):
        st.caption("Execute custom SQL queries directly against Tally ODBC Server.")
        custom_sql = st.text_area("SQL Query", value="SELECT $Name,$Parent, $ClosingBalance FROM Ledger WHERE$$IsDr:$ClosingBalance")
        if st.button("Run Query"):
            conn_run, err_run = connect_tally_odbc(dsn_name=dsn_name, host=host_val, port=port_val, mode=conn_type)
            if conn_run:
                try:
                    df_custom = pd.read_sql(custom_sql, conn_run)
                    st.dataframe(df_custom, use_container_width=True)
                    conn_run.close()
                except Exception as q_err:
                    st.error(f"SQL Execution Error: {q_err}")
            else:
                st.error(f"Cannot execute query: ODBC connection failed ({err_run})")