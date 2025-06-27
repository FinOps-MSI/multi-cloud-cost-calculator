import streamlit as st
import pandas as pd
import re
import uuid
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Cross Examine",
    page_icon="⚖️",
    layout="wide"
)

# --- Custom CSS for Polished Styling ---
def load_css():
    """Injects custom CSS for the application's formal look."""
    st.markdown("""
        <style>
            .stApp { background-color: #FFFFFF; }
            h1, h3 { font-weight: 600; }
            .card {
                background-color: white; border-radius: 10px; padding: 20px;
                box-shadow: 0 4px 8px 0 rgba(0,0,0,0.08); border: 1px solid #E0E0E0;
                height: 100%; display: flex; flex-direction: column;
            }
            .card-body { flex-grow: 1; }
            .recommended-card { border: 2px solid #28a745; }
            .card-header { font-size: 1.5em; font-weight: bold; margin-bottom: 15px; color: #0052CC; }
            .recommended-badge { background-color: #28a745; color: white; padding: 5px 10px; border-radius: 5px; font-size: 0.8em; }
            .total-cost { font-size: 2em; font-weight: bold; color: #333; text-align: right; margin-top: 20px; }
            .savings-card {
                background-color: white; border-radius: 10px; padding: 25px;
                box-shadow: 0 4px 8px 0 rgba(0,0,0,0.08); border: 1px solid #E0E0E0;
            }
            .metric-row {
                display: flex;
                justify-content: space-around;
                align-items: center;
            }
            .metric-container { text-align: center; flex: 1; }
            .metric-value { font-size: 2.2em; font-weight: 600; color: #28a745; }
            .metric-label { font-size: 1em; color: #6c757d; }
            .st-expander { border: 1px solid #E0E0E0 !important; border-radius: 10px !important; }
        </style>
    """, unsafe_allow_html=True)

# --- Data Loading and Processing Functions ---
GOOGLE_SHEET_URL_EC2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR6nm8tGltr086h1MhnosWrIbP3wJiLEIlEK4ykpvaBhQ7YMzC3X7CNA6MeRKH7WUxHIeDCpASTdYnZ/pub?gid=0&single=true&output=csv"
GOOGLE_SHEET_URL_RDS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR6nm8tGltr086h1MhnosWrIbP3wJiLEIlEK4ykpvaBhQ7YMzC3X7CNA6MeRKH7WUxHIeDCpASTdYnZ/pub?gid=1524734883&single=true&output=csv"
GOOGLE_SHEET_URL_S3 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR6nm8tGltr086h1MhnosWrIbP3wJiLEIlEK4ykpvaBhQ7YMzC3X7CNA6MeRKH7WUxHIeDCpASTdYnZ/pub?gid=1926651960&single=true&output=csv"

@st.cache_data(ttl="1h")
def load_and_filter_data():
    """Loads and filters data for all services to ensure equivalency."""
    
    # Define column mappings for each service to check for completeness
    vm_compute_map = {'aws': {'meter': 'Instance Type', 'cost': 'AWS Monthly Cost'}, 'azure': {'meter': 'Azure Meter', 'cost': 'Azure Monthly Cost'}, 'gcp': {'meter': 'GCP SKU', 'cost': 'GCP Monthly Cost'}}
    vm_db_map = {'aws': {'meter': 'Meter', 'cost': 'AWS- On Demand Monthly Cost'}, 'azure': {'meter': 'Meter.1', 'cost': 'Azure Monthly Cost'}, 'gcp': {'meter': 'GCP SKU', 'cost': 'GCP Ondemand Cost/month'}}
    storage_map = {'aws': {'meter': 'Meter', 'cost': 'AWS Ondemand Cost'}, 'azure': {'meter': 'Meter.1', 'cost': 'Azure Ondemand Cost'}, 'gcp': {'meter': 'Meter.2', 'cost': 'GCP Ondemand Cost'}}
    
    data_sources = {
        'Compute': (load_data(GOOGLE_SHEET_URL_EC2), vm_compute_map),
        'Database': (load_data(GOOGLE_SHEET_URL_RDS), vm_db_map),
        'Storage': (load_data(GOOGLE_SHEET_URL_S3), storage_map)
    }
    
    filtered_dfs = {}
    for service, (df, col_map) in data_sources.items():
        if df is not None:
            # Drop rows where any of the providers are missing a meter name or a cost.
            required_cols = [col_map[p]['meter'] for p in col_map] + [col_map[p]['cost'] for p in col_map]
            filtered_dfs[service] = df.dropna(subset=required_cols)
            
    return filtered_dfs

@st.cache_data
def load_data(url):
    try: return pd.read_csv(url, on_bad_lines='warn')
    except Exception: return None

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

def get_vm_comparison_from_row(df, primary_cloud, primary_meter, primary_region, col_map):
    primary_meter_col, primary_region_col = col_map[primary_cloud]['meter'], col_map[primary_cloud]['region']
    row_df = df.loc[(df[primary_meter_col] == primary_meter) & (df[primary_region_col] == primary_region)]
    if row_df.empty: return None
    row = row_df.iloc[0]
    equivalents = {}
    equivalents['aws'] = {'meter': row[col_map['aws']['meter']], 'region': row[col_map['aws']['region']], 'vcpu': int(float(row[col_map['shared']['vcpu']])), 'memory': parse_memory(row[col_map['shared']['memory']]), 'cost': parse_cost(row[col_map['aws']['cost']])}
    equivalents['azure'] = {'meter': row[col_map['azure']['meter']], 'region': row[col_map['azure']['region']], 'vcpu': int(float(row[col_map['shared']['vcpu']])), 'memory': parse_memory(row[col_map['shared']['memory']]), 'cost': parse_cost(row[col_map['azure']['cost']])}
    equivalents['gcp'] = {'meter': row[col_map['gcp']['meter']], 'region': row[col_map['gcp']['region']], 'vcpu': int(float(row[col_map['gcp']['vcpu']])), 'memory': parse_memory(row[col_map['gcp']['memory']]), 'cost': parse_cost(row[col_map['gcp']['cost']])}
    return equivalents

def get_storage_comparison(df, primary_cloud, primary_tier):
    col_map = {'aws': 'Meter', 'azure': 'Meter.1', 'gcp': 'Meter.2'}
    cost_map = {'aws': 'AWS Ondemand Cost', 'azure': 'Azure Ondemand Cost', 'gcp': 'GCP Ondemand Cost'}
    region_map = {'aws': 'Region', 'azure': 'Region.1', 'gcp': 'Region.2'}
    row_df = df.loc[df[col_map[primary_cloud]] == primary_tier]
    if row_df.empty: return None
    row = row_df.iloc[0]
    equivalents = {}
    for cloud in ['aws', 'azure', 'gcp']:
        equivalents[cloud] = {'tier': row[col_map[cloud]], 'region': row[region_map[cloud]], 'cost_per_gb': parse_cost(row[cost_map[cloud]])}
    return equivalents

# --- Main Application ---
load_css()

if 'bucket' not in st.session_state:
    st.session_state.bucket = []

st.title("Cross Examine")
st.caption("Expose. Compare. Decide")

FILTERED_DFS = load_and_filter_data()

with st.container(border=True):
    st.subheader("1. Add a Resource to Your Bucket")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        csp_map = {'AWS': 'aws', 'Azure': 'azure', 'GCP': 'gcp'}
        selected_csp = csp_map[st.selectbox("Cloud Provider", csp_map.keys())]
        service_type = st.selectbox("Service Type", FILTERED_DFS.keys())
    
    with col2:
        df = FILTERED_DFS.get(service_type)
        if df is None or df.empty:
            st.warning(f"No configurations with full cross-cloud equivalents found for {service_type}."); st.stop()
        
    if service_type in ['Compute', 'Database']:
        col_maps = {
            'Compute': {'aws': {'meter': 'Instance Type', 'region': 'Region', 'cost': 'AWS Monthly Cost'}, 'azure': {'meter': 'Azure Meter', 'region': 'AzureRegion', 'cost': 'Azure Monthly Cost'}, 'gcp': {'meter': 'GCP SKU', 'region': 'GCP Region', 'cost': 'GCP Monthly Cost', 'vcpu': 'vCPUs', 'memory': 'Memory'}, 'shared': {'vcpu': 'vCPUs', 'memory': 'Memory'}},
            'Database': {'aws': {'meter': 'Meter', 'region': 'Region', 'cost': 'AWS- On Demand Monthly Cost'}, 'azure': {'meter': 'Meter.1', 'region': 'AzureRegion', 'cost': 'Azure Monthly Cost'}, 'gcp': {'meter': 'GCP SKU', 'region': 'GCP Region', 'cost': 'GCP Ondemand Cost/month', 'vcpu': 'vCPUs.1', 'memory': 'Memory.1'}, 'shared': {'vcpu': 'vCPUs', 'memory': 'Memory'}}
        }
        current_map, meter_col, region_col = col_maps[service_type], col_maps[service_type][selected_csp]['meter'], col_maps[service_type][selected_csp]['region']
        
        instance_options = {f"{row[meter_col]}@{row[region_col]}": f"{row[meter_col]} ({row[region_col]})" for _, row in df.iterrows()}
        with col2:
            selected_key = st.selectbox("Instance", options=instance_options.keys(), format_func=lambda x: instance_options.get(x, x), key=f"instance_{selected_csp}_{service_type}")
        with col3:
            quantity = st.number_input("Quantity", min_value=1, value=1, key=f"qty_{selected_csp}_{service_type}")
            if st.button("Add to Bucket", type="primary", use_container_width=True, key=f"add_{selected_csp}_{service_type}"):
                if selected_key:
                    meter, region = selected_key.split('@')
                    equivalents = get_vm_comparison_from_row(df, selected_csp, meter, region, current_map)
                    if equivalents:
                        st.session_state.bucket.append({"id": str(uuid.uuid4()), "service_type": service_type, "description": f"{quantity}x {meter} ({region})", "equivalents": equivalents, "quantity": quantity})
                        st.success(f"Added {meter} to bucket!")
    
    elif service_type == 'Storage':
        tier_col_map = {'aws': 'Meter', 'azure': 'Meter.1', 'gcp': 'Meter.2'}
        tier_col = tier_col_map[selected_csp]
        with col2:
            selected_tier = st.selectbox("Storage Tier", options=df[tier_col].unique(), key=f"tier_{selected_csp}")
        with col3:
            storage_gb = st.number_input("Storage (GB)", min_value=1, value=1000, key=f"gb_{selected_csp}")
            if st.button("Add to Bucket", type="primary", use_container_width=True, key=f"add_{selected_csp}_storage"):
                equivalents = get_storage_comparison(df, selected_csp, selected_tier)
                if equivalents:
                    st.session_state.bucket.append({"id": str(uuid.uuid4()), "service_type": service_type, "description": f"{storage_gb} GB of {selected_tier}", "equivalents": equivalents, "storage_gb": storage_gb})
                    st.success(f"Added {selected_tier} to bucket!")

if st.session_state.bucket:
    st.divider()
    st.subheader("Your Bucket")
    for i, item in enumerate(st.session_state.bucket):
        with st.expander(f"**{item['service_type']}:** {item['description']}"):
            tech_data = []
            if item['service_type'] in ['Compute', 'Database']:
                for cloud, data in item['equivalents'].items(): tech_data.append({"Cloud": cloud.upper(), "Instance": data['meter'], "vCPUs": data['vcpu'], "Memory (GiB)": data['memory'], "Region": data['region']})
            else:
                for cloud, data in item['equivalents'].items(): tech_data.append({"Cloud": cloud.upper(), "Tier": data['tier'], "Cost/GB": f"${data['cost_per_gb']:.5f}", "Region": data['region']})
            st.dataframe(pd.DataFrame(tech_data).set_index("Cloud"), use_container_width=True)
            if st.button("Remove", key=f"remove_{item['id']}", type="secondary"):
                st.session_state.bucket.pop(i)
                st.rerun()

    total_costs = {'aws': 0, 'azure': 0, 'gcp': 0}
    for item in st.session_state.bucket:
        for cloud, data in item['equivalents'].items():
            if item['service_type'] in ['Compute', 'Database']:
                total_costs[cloud] += data.get('cost', 0) * item.get('quantity', 1)
            else:
                total_costs[cloud] += data.get('cost_per_gb', 0) * item.get('storage_gb', 0)
    
    st.subheader("Total Bucket Cost Comparison")
    lowest_cost = min((cost for cost in total_costs.values() if cost > 0), default=0)
    card_cols = st.columns(3)
    cloud_names = {'aws': 'Amazon AWS', 'azure': 'Microsoft Azure', 'gcp': 'Google Cloud'}
    for i, cloud in enumerate(['aws', 'azure', 'gcp']):
        with card_cols[i]:
            is_recommended = total_costs[cloud] == lowest_cost and lowest_cost > 0
            card_class = "card recommended-card" if is_recommended else "card"
            header_html = f'<div class="card-header">{cloud_names[cloud]}'
            if is_recommended: header_html += '<span class="recommended-badge">RECOMMENDED</span>'
            header_html += '</div>'
            body_html = f"<div class='card-body'><div class='total-cost'>${total_costs[cloud]:,.0f}</div></div>"
            st.markdown(f'<div class="{card_class}">{header_html}{body_html}</div>', unsafe_allow_html=True)

    st.subheader("Cost Summary & Savings Analysis")
    valid_costs = [cost for cost in total_costs.values() if cost > 0]
    if len(valid_costs) > 1:
        highest_cost = max(valid_costs)
        monthly_savings = highest_cost - lowest_cost
        annual_savings = monthly_savings * 12

        metrics_html = f"""
            <div class="savings-card">
                <div class="metric-row">
                    <div class="metric-container">
                        <div class="metric-value">${lowest_cost:,.0f}</div>
                        <div class="metric-label">Lowest Cost</div>
                    </div>
                    <div class="metric-container">
                        <div class="metric-value">${highest_cost:,.0f}</div>
                        <div class="metric-label">Highest Cost</div>
                    </div>
                    <div class="metric-container">
                        <div class="metric-value">${monthly_savings:,.0f}</div>
                        <div class="metric-label">Monthly Savings</div>
                    </div>
                    <div class="metric-container">
                        <div class="metric-value">${annual_savings:,.0f}</div>
                        <div class="metric-label">Annual Savings</div>
                    </div>
                </div>
            </div>
        """
        st.markdown(metrics_html, unsafe_allow_html=True)
    else:
        st.info("Add items to your bucket to see a savings analysis.")

else:
    st.info("Your bucket is empty. Add a resource above to begin your cost comparison.")
