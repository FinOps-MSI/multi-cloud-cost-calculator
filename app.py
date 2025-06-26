import streamlit as st
import pandas as pd
import re
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Cloud Pricing Comparison",
    page_icon="💰",
    layout="wide"
)

# --- Custom CSS for Formal Styling ---
def load_css():
    """Injects custom CSS to style the app."""
    st.markdown("""
        <style>
            .stApp { background-color: #F0F2F6; }
            h1, h3 { font-weight: 600; }
            .card {
                background-color: white; border-radius: 10px; padding: 20px;
                box-shadow: 0 4px 8px 0 rgba(0,0,0,0.1); border: 1px solid #E0E0E0;
                height: 100%; display: flex; flex-direction: column;
            }
            .card-body { flex-grow: 1; }
            .recommended-card { border: 2px solid #28a745; }
            .card-header { font-size: 1.2em; font-weight: bold; margin-bottom: 15px; display: flex; align-items: center; justify-content: space-between; }
            .recommended-badge { background-color: #28a745; color: white; padding: 5px 10px; border-radius: 5px; font-size: 0.8em; }
            .cost-item { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.95em; }
            .total-cost { font-size: 1.7em; font-weight: bold; color: #0052CC; text-align: right; margin-top: 20px; }
            .savings-card { background-color: white; border-radius: 10px; padding: 25px; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.1); border: 1px solid #E0E0E0; }
            .metric-container { text-align: center; }
            .metric-value { font-size: 2.2em; font-weight: 600; color: #28a745; }
            .metric-label { font-size: 1em; color: #6c757d; }
        </style>
    """, unsafe_allow_html=True)

# --- Data Loading and Processing ---
# URLs for all three services
GOOGLE_SHEET_URL_EC2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR6nm8tGltr086h1MhnosWrIbP3wJiLEIlEK4ykpvaBhQ7YMzC3X7CNA6MeRKH7WUxHIeDCpASTdYnZ/pub?gid=0&single=true&output=csv"
GOOGLE_SHEET_URL_RDS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR6nm8tGltr086h1MhnosWrIbP3wJiLEIlEK4ykpvaBhQ7YMzC3X7CNA6MeRKH7WUxHIeDCpASTdYnZ/pub?gid=1524734883&single=true&output=csv"
GOOGLE_SHEET_URL_S3 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR6nm8tGltr086h1MhnosWrIbP3wJiLEIlEK4ykpvaBhQ7YMzC3X7CNA6MeRKH7WUxHIeDCpASTdYnZ/pub?gid=1926651960&single=true&output=csv"

# Helper functions for parsing
def parse_memory(mem_str):
    if isinstance(mem_str, (int, float)): return mem_str
    if isinstance(mem_str, str):
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", mem_str)
        if numbers: return float(numbers[0])
    return 0

def parse_cost(cost_str):
    if isinstance(cost_str, (int, float)): return float(cost_str)
    if isinstance(cost_str, str):
        try: return float(str(cost_str).replace('$', '').replace(',', '').strip())
        except (ValueError, TypeError): return 0.0
    return 0.0

@st.cache_data(ttl="1h")
def load_data(url):
    """Loads a single CSV into a DataFrame."""
    try:
        return pd.read_csv(url, on_bad_lines='warn')
    except Exception as e:
        st.error(f"Error loading data from {url}. Please check the URL. Error: {e}")
        return None

def get_vm_comparison_from_row(df, primary_cloud, primary_meter, primary_region, col_map):
    """Handles comparison for Compute and Database services."""
    row = None
    primary_meter_col = col_map[primary_cloud]['meter']
    primary_region_col = col_map[primary_cloud]['region']
    row_df = df.loc[(df[primary_meter_col] == primary_meter) & (df[primary_region_col] == primary_region)]
    
    if not row_df.empty:
        row = row_df.iloc[0]
    else:
        return None

    equivalents = {}
    if pd.notna(row.get(col_map['aws']['meter'])) and pd.notna(row.get(col_map['aws']['cost'])):
        equivalents['aws'] = {'meter': row[col_map['aws']['meter']], 'region': row[col_map['aws']['region']], 'vcpu': int(float(row[col_map['shared']['vcpu']])), 'memory': parse_memory(row[col_map['shared']['memory']]), 'cost': parse_cost(row[col_map['aws']['cost']])}
    if pd.notna(row.get(col_map['azure']['meter'])) and pd.notna(row.get(col_map['azure']['cost'])):
        equivalents['azure'] = {'meter': row[col_map['azure']['meter']], 'region': row[col_map['azure']['region']], 'vcpu': int(float(row[col_map['shared']['vcpu']])), 'memory': parse_memory(row[col_map['shared']['memory']]), 'cost': parse_cost(row[col_map['azure']['cost']])}
    if pd.notna(row.get(col_map['gcp']['meter'])) and pd.notna(row.get(col_map['gcp']['cost'])):
        equivalents['gcp'] = {'meter': row[col_map['gcp']['meter']], 'region': row[col_map['gcp']['region']], 'vcpu': int(float(row[col_map['gcp']['vcpu']])), 'memory': parse_memory(row[col_map['gcp']['memory']]), 'cost': parse_cost(row[col_map['gcp']['cost']])}
    return equivalents

def get_storage_comparison(df, primary_cloud, primary_tier):
    """Handles comparison for Storage services."""
    col_map = {'aws': 'Meter', 'azure': 'Meter.1', 'gcp': 'Meter.2'}
    cost_map = {'aws': 'AWS Ondemand Cost', 'azure': 'Azure Ondemand Cost', 'gcp': 'GCP Ondemand Cost'}
    region_map = {'aws': 'Region', 'azure': 'Region.1', 'gcp': 'Region.2'}

    row_df = df.loc[df[col_map[primary_cloud]] == primary_tier]
    if row_df.empty: return None
    row = row_df.iloc[0]

    equivalents = {}
    for cloud in ['aws', 'azure', 'gcp']:
        if pd.notna(row.get(col_map[cloud])) and pd.notna(row.get(cost_map[cloud])):
            equivalents[cloud] = {'tier': row[col_map[cloud]], 'region': row[region_map[cloud]], 'cost_per_gb': parse_cost(row[cost_map[cloud]])}
    return equivalents

# --- Main Application ---
load_css()

# Load all data sources
RAW_DFS = {
    'Compute': load_data(GOOGLE_SHEET_URL_EC2),
    'Database': load_data(GOOGLE_SHEET_URL_RDS),
    'Storage': load_data(GOOGLE_SHEET_URL_S3),
}

st.title("Pricing Comparison")

if 'comparison_results' not in st.session_state:
    st.session_state.comparison_results = None

with st.container(border=True):
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("1. Select Service")
        service_type = st.selectbox("Service Type", RAW_DFS.keys())
        
        # Select the correct DataFrame based on service type
        df = RAW_DFS[service_type]
        if df is None:
            st.error(f"Data for {service_type} could not be loaded. Please check the source.")
            st.stop()
        
        csp_map = {'AWS': 'aws', 'Azure': 'azure', 'GCP': 'gcp'}
        selected_csp = csp_map[st.selectbox("Cloud Provider", csp_map.keys())]

    with col2:
        st.subheader("2. Configure & Compare")
        # --- Dynamic UI based on Service Type ---
        if service_type in ['Compute', 'Database']:
            # Column mappings for Compute and Database services
            col_maps = {
                'Compute': {'aws': {'meter': 'Instance Type', 'region': 'Region', 'cost': 'AWS Monthly Cost'}, 'azure': {'meter': 'Azure Meter', 'region': 'AzureRegion', 'cost': 'Azure Monthly Cost'}, 'gcp': {'meter': 'GCP SKU', 'region': 'GCP Region', 'cost': 'GCP Monthly Cost', 'vcpu': 'vCPUs', 'memory': 'Memory'}, 'shared': {'vcpu': 'vCPUs', 'memory': 'Memory'}},
                'Database': {'aws': {'meter': 'Meter', 'region': 'Region', 'cost': 'AWS- On Demand Monthly Cost'}, 'azure': {'meter': 'Meter.1', 'region': 'AzureRegion', 'cost': 'Azure Monthly Cost'}, 'gcp': {'meter': 'GCP SKU', 'region': 'GCP Region', 'cost': 'GCP Ondemand Cost/month', 'vcpu': 'vCPUs.1', 'memory': 'Memory.1'}, 'shared': {'vcpu': 'vCPUs', 'memory': 'Memory'}}
            }
            current_map = col_maps[service_type]
            meter_col = current_map[selected_csp]['meter']
            region_col = current_map[selected_csp]['region']

            filtered_df = df.dropna(subset=[meter_col, region_col])
            instance_options = {f"{row[meter_col]}@{row[region_col]}": f"{row[meter_col]} ({row[region_col]})" for _, row in filtered_df.iterrows()}
            selected_key = st.selectbox("Instance", options=instance_options.keys(), format_func=lambda x: instance_options.get(x, x))
            quantity = st.number_input("Quantity", min_value=1, value=1)

            if st.button("Compare Prices", type="primary", use_container_width=True):
                meter, region = selected_key.split('@')
                equivalents = get_vm_comparison_from_row(df, selected_csp, meter, region, current_map)
                if equivalents:
                    st.session_state.comparison_results = {"service_type": service_type, "equivalents": equivalents, "quantity": quantity, "timestamp": datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p")}
                else:
                    st.warning("Could not find the selected instance."); st.session_state.comparison_results = None

        elif service_type == 'Storage':
            tier_col_map = {'aws': 'Meter', 'azure': 'Meter.1', 'gcp': 'Meter.2'}
            tier_col = tier_col_map[selected_csp]
            
            filtered_df = df.dropna(subset=[tier_col])
            tier_options = filtered_df[tier_col].unique()
            selected_tier = st.selectbox("Storage Tier", options=tier_options)
            storage_gb = st.number_input("Storage (GB)", min_value=1, value=1000)

            if st.button("Compare Prices", type="primary", use_container_width=True):
                equivalents = get_storage_comparison(df, selected_csp, selected_tier)
                if equivalents:
                    st.session_state.comparison_results = {"service_type": service_type, "equivalents": equivalents, "storage_gb": storage_gb, "timestamp": datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p")}
                else:
                    st.warning("Could not find the selected tier."); st.session_state.comparison_results = None


# --- Results Display Area ---
if st.session_state.comparison_results:
    results = st.session_state.comparison_results
    equivalents = results['equivalents']
    service_type = results['service_type']
    
    st.divider()
    st.write(f"_Comparison generated: {results['timestamp']}_")

    # --- Dynamic Technical Specifications Table ---
    st.subheader("Technical Specifications")
    tech_data = []
    if service_type in ['Compute', 'Database']:
        for cloud in ['aws', 'azure', 'gcp']:
            instance = equivalents.get(cloud)
            tech_data.append({"Cloud": cloud.upper(), "Instance Name": instance.get('meter', "N/A") if instance else "N/A", "vCPUs": instance.get('vcpu', "N/A") if instance else "N/A", "Memory (GiB)": instance.get('memory', "N/A") if instance else "N/A", "Region": instance.get('region', "N/A") if instance else "N/A"})
    elif service_type == 'Storage':
        for cloud in ['aws', 'azure', 'gcp']:
            instance = equivalents.get(cloud)
            tech_data.append({"Cloud": cloud.upper(), "Storage Tier": instance.get('tier', "N/A") if instance else "N/A", "Cost per GB": f"${instance.get('cost_per_gb', 0):.5f}" if instance else "N/A", "Region": instance.get('region', "N/A") if instance else "N/A"})
    
    st.dataframe(pd.DataFrame(tech_data).set_index("Cloud"), use_container_width=True)

    # --- Dynamic Cost Comparison Cards ---
    st.subheader("Cost Comparison")
    costs = {}
    if service_type in ['Compute', 'Database']:
        costs = {cloud: {'base_price': data['cost'], 'total_monthly_cost': data['cost'] * results['quantity']} for cloud, data in equivalents.items()}
    elif service_type == 'Storage':
        costs = {cloud: {'base_price': data['cost_per_gb'], 'total_monthly_cost': data['cost_per_gb'] * results['storage_gb']} for cloud, data in equivalents.items()}

    lowest_cost = min((c['total_monthly_cost'] for c in costs.values()), default=0)
    
    card_cols = st.columns(3)
    cloud_names = {'aws': 'Amazon AWS', 'azure': 'Microsoft Azure', 'gcp': 'Google Cloud'}
    
    for i, cloud in enumerate(['aws', 'azure', 'gcp']):
        with card_cols[i]:
            instance = equivalents.get(cloud)
            cost_data = costs.get(cloud)
            is_recommended = cost_data and cost_data['total_monthly_cost'] == lowest_cost and lowest_cost > 0
            
            card_class = "card recommended-card" if is_recommended else "card"
            header_html = f'<div class="card-header">{cloud_names[cloud]}'
            if is_recommended: header_html += '<span class="recommended-badge">RECOMMENDED</span>'
            header_html += '</div>'

            html_body = ""
            if instance and cost_data:
                if service_type in ['Compute', 'Database']:
                    html_body = f"""<div class="card-body"><div>{instance['meter']}</div><small>{instance['region']}</small><hr><div class="cost-item"><span>Unit Price (Monthly):</span> <span>${cost_data["base_price"]:,.2f}</span></div><div class="cost-item"><span>Quantity:</span><span>{results["quantity"]}x</span></div></div><div class="total-cost">${cost_data["total_monthly_cost"]:,.2f}</div>"""
                elif service_type == 'Storage':
                    html_body = f"""<div class="card-body"><div>{instance['tier']}</div><small>{instance['region']}</small><hr><div class="cost-item"><span>Price per GB (Monthly):</span> <span>${cost_data["base_price"]:,.5f}</span></div><div class="cost-item"><span>Storage:</span><span>{results["storage_gb"]} GB</span></div></div><div class="total-cost">${cost_data["total_monthly_cost"]:,.2f}</div>"""
            else:
                html_body = "<div class='card-body' style='text-align: center; padding-top: 50px;'>Not available in this row.</div>"
                
            st.markdown(f'<div class="{card_class}">{header_html}{html_body}</div>', unsafe_allow_html=True)
    
    # --- Savings Analysis ---
    st.subheader("Cost Summary & Savings Analysis")
    with st.container():
        st.markdown('<div class="savings-card">', unsafe_allow_html=True)
        metric_cols = st.columns(4)
        valid_costs = list(costs.values())
        
        if len(valid_costs) > 1:
            total_costs = [c['total_monthly_cost'] for c in valid_costs]
            average_cost = sum(total_costs) / len(total_costs)
            monthly_savings = average_cost - lowest_cost
            annual_savings = monthly_savings * 12

            with metric_cols[0]: st.markdown(f'<div class="metric-container"><div class="metric-value">${lowest_cost:,.2f}</div><div class="metric-label">Lowest Cost</div></div>', unsafe_allow_html=True)
            with metric_cols[1]: st.markdown(f'<div class="metric-container"><div class="metric-value">${average_cost:,.2f}</div><div class="metric-label">Average Cost</div></div>', unsafe_allow_html=True)
            with metric_cols[2]: st.markdown(f'<div class="metric-container"><div class="metric-value">${monthly_savings:,.2f}</div><div class="metric-label">Monthly Savings</div></div>', unsafe_allow_html=True)
            with metric_cols[3]: st.markdown(f'<div class="metric-container"><div class="metric-value">${annual_savings:,.2f}</div><div class="metric-label">Annual Savings</div></div>', unsafe_allow_html=True)
        else:
            st.info("Not enough data to perform a savings analysis. At least two cloud options are needed.")
        st.markdown('</div>', unsafe_allow_html=True)
