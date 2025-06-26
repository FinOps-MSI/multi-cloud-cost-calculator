import streamlit as st
import pandas as pd

# --- Page Configuration ---
st.set_page_config(
    page_title="Multi-Cloud Cost Calculator",
    page_icon="☁️",
    layout="wide"
)

# --- Live Data Loading from Google Sheets ---
# IMPORTANT: Replace this with your own Google Sheet URL
# How to get the URL:
# 1. In your Google Sheet, click 'File' -> 'Share' -> 'Publish to web'.
# 2. In the dialog, select the sheet you want to share.
# 3. Choose 'Comma-separated values (.csv)' as the format.
# 4. Click 'Publish' and copy the generated link.
GOOGLE_SHEET_URL_S3 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTlDPF1wgX6e4bGmLb6zGRVXmH9vb-s2JsahLAnMewli9Dn7r9PtAZn1wUHUL47UjCPL_vPBirOtFNh/pub?gid=0&single=true&output=csv" # Replace with your S3 data URL
GOOGLE_SHEET_URL_RDS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTlDPF1wgX6e4bGmLb6zGRVXmH9vb-s2JsahLAnMewli9Dn7r9PtAZn1wUHUL47UjCPL_vPBirOtFNh/pub?gid=1778892103&single=true&output=csv" # Replace with your RDS data URL


@st.cache_data(ttl="1h") # Cache the data for 1 hour
def load_and_process_data():
    """Loads and normalizes data from Google Sheets URLs."""
    try:
        # Load the raw data
        s3_df = pd.read_csv(GOOGLE_SHEET_URL_S3)
        rds_df = pd.read_csv(GOOGLE_SHEET_URL_RDS)
        
        # --- Process S3 Data ---
        s3_data = []
        for _, row in s3_df.iterrows():
            # AWS
            s3_data.append({'cloud': 'aws', 'tier': row['Meter'], 'region': row['Region'], 'costPerGB': float(str(row['AWS Ondemand Cost']).replace('$', ''))})
            # Azure
            s3_data.append({'cloud': 'azure', 'tier': row['Meter.1'], 'region': row['Region.1'], 'costPerGB': float(str(row['Azure Ondemand Cost']).replace('$', ''))})
            # GCP
            s3_data.append({'cloud': 'gcp', 'tier': row['Meter.2'], 'region': row['Region.2'], 'costPerGB': float(str(row['GCP Ondemand Cost']).replace('$', ''))})

        # --- Process RDS Data ---
        rds_data = []
        for _, row in rds_df.iterrows():
            # AWS
            rds_data.append({'cloud': 'aws', 'meter': row['Meter'], 'region': row['Region'], 'vcpu': row['vCPUs'], 'memory': row['Memory'], 'cost': float(str(row['AWS- On Demand Monthly Cost']).replace(',', ''))})
            # Azure
            rds_data.append({'cloud': 'azure', 'meter': row['Meter.1'], 'region': row['AzureRegion'], 'vcpu': row['vCPUs'], 'memory': row['Memory'], 'cost': float(str(row['Azure Monthly Cost']).replace(',', ''))})
            # GCP
            rds_data.append({'cloud': 'gcp', 'meter': row['GCP SKU'], 'region': row['GCP Region'], 'vcpu': row['vCPUs.1'], 'memory': row['Memory.1'], 'cost': float(str(row['GCP Ondemand Cost/month']).replace(',', '').replace('$', ''))})
        
        # Remove duplicates and clean up
        processed_s3 = [dict(t) for t in {tuple(d.items()) for d in s3_data if pd.notna(d['tier'])}]
        processed_rds = [dict(t) for t in {tuple(d.items()) for d in rds_data if pd.notna(d['meter'])}]

        return {'s3': processed_s3, 'rds': processed_rds}
    except Exception as e:
        st.error(f"Failed to load data from Google Sheets. Please check the URL and sheet format. Error: {e}")
        return None

# Load the data
RAW_DATA = load_and_process_data()

# --- Helper Functions ---
def get_rds_equivalents(primary_instance):
    """Finds equivalent RDS instances based on vCPU and memory."""
    if not primary_instance or not RAW_DATA:
        return {}
    
    aws_equiv = next((i for i in RAW_DATA['rds'] if i['cloud'] == 'aws' and i['vcpu'] == primary_instance['vcpu'] and i['memory'] == primary_instance['memory']), None)
    azure_equiv = next((i for i in RAW_DATA['rds'] if i['cloud'] == 'azure' and i['vcpu'] == primary_instance['vcpu']), None)
    gcp_equiv = next((i for i in RAW_DATA['rds'] if i['cloud'] == 'gcp' and i['vcpu'] == primary_instance['vcpu'] and i['memory'] == primary_instance['memory']), None)
    
    return {'aws': aws_equiv, 'azure': azure_equiv, 'gcp': gcp_equiv}

def get_s3_equivalents(primary_tier_name, storage_gb):
    """Finds equivalent S3 tiers and calculates cost."""
    if not RAW_DATA: return {}
    equivalents = {}
    
    aws_tier = next((t for t in RAW_DATA['s3'] if t['cloud'] == 'aws' and t['tier'] == primary_tier_name), None)
    azure_tier = next((t for t in RAW_DATA['s3'] if t['cloud'] == 'azure' and primary_tier_name.split(' ')[0] in t['tier']), None)
    gcp_tier = next((t for t in RAW_DATA['s3'] if t['cloud'] == 'gcp' and primary_tier_name.split(' ')[0] in t['tier']), None)

    if aws_tier: equivalents['aws'] = {**aws_tier, 'cost': aws_tier['costPerGB'] * storage_gb}
    if azure_tier: equivalents['azure'] = {**azure_tier, 'cost': azure_tier['costPerGB'] * storage_gb}
    if gcp_tier: equivalents['gcp'] = {**gcp_tier, 'cost': gcp_tier['costPerGB'] * storage_gb}
    
    return equivalents

# --- Main App UI ---
st.title("☁️ Multi-Cloud Cost Calculator")
st.write("Compare costs for equivalent services across AWS, Azure, and GCP.")

# Stop if data loading failed
if not RAW_DATA:
    st.stop()

# Initialize session state to store results
if 'comparison_set' not in st.session_state:
    st.session_state.comparison_set = None

with st.container(border=True):
    st.header("Service Configuration")
    cols = st.columns(4)
    with cols[0]:
        service_type = st.selectbox(
            "Service Type",
            ('Managed Database (RDS)', 'Object Storage (S3)'),
            key='service_type'
        )

    # Dynamic UI based on service type
    if service_type == 'Managed Database (RDS)':
        with cols[1]:
            available_regions = sorted(list(set(item['region'] for item in RAW_DATA['rds'])))
            selected_region = st.selectbox("Region", available_regions, key='rds_region')
        
        with cols[2]:
            instances_in_region = [item for item in RAW_DATA['rds'] if item['region'] == selected_region]
            instance_options = {item['meter']: f"{item['meter']} ({item['vcpu']} vCPU, {item['memory']} GiB)" for item in instances_in_region}
            selected_instance_meter = st.selectbox("Instance", options=instance_options.keys(), format_func=lambda x: instance_options[x], key='rds_instance')
            
    elif service_type == 'Object Storage (S3)':
        with cols[1]:
            available_tiers = sorted(list(set(item['tier'] for item in RAW_DATA['s3'])))
            selected_tier = st.selectbox("Storage Tier", available_tiers, key='s3_tier')
        with cols[2]:
            storage_amount = st.number_input("Storage (GB)", min_value=1, value=1000, key='s3_gb')

    with cols[3]:
        st.write("") 
        st.write("") 
        if st.button("Compare Pricing", type="primary", use_container_width=True):
            if service_type == 'Managed Database (RDS)':
                primary_instance = next((i for i in RAW_DATA['rds'] if i['region'] == selected_region and i['meter'] == selected_instance_meter), None)
                st.session_state.comparison_set = get_rds_equivalents(primary_instance)
            elif service_type == 'Object Storage (S3)':
                st.session_state.comparison_set = get_s3_equivalents(selected_tier, storage_amount)


# --- Display Results ---
if st.session_state.comparison_set:
    results = st.session_state.comparison_set
    
    with st.container(border=True):
        st.header("Service Equivalency Mapping")
        display_data = {'Specification': [], 'AZURE': [], 'AWS': [], 'GCP': []}
        
        if service_type == 'Managed Database (RDS)':
            specs = ['Instance Type', 'vCPU', 'Memory', 'Region']
            for spec in specs:
                display_data['Specification'].append(f"**{spec}**")
                display_data['AZURE'].append(results.get('azure', {}).get({'Instance Type': 'meter', 'vCPU': 'vcpu', 'Memory': 'memory', 'Region': 'region'}[spec], 'N/A'))
                display_data['AWS'].append(results.get('aws', {}).get({'Instance Type': 'meter', 'vCPU': 'vcpu', 'Memory': 'memory', 'Region': 'region'}[spec], 'N/A'))
                display_data['GCP'].append(results.get('gcp', {}).get({'Instance Type': 'meter', 'vCPU': 'vcpu', 'Memory': 'memory', 'Region': 'region'}[spec], 'N/A'))
        else: # S3
            specs = ['Storage Tier', 'Region']
            for spec in specs:
                display_data['Specification'].append(f"**{spec}**")
                display_data['AZURE'].append(results.get('azure', {}).get(spec.lower().replace(' ', ''), 'N/A'))
                display_data['AWS'].append(results.get('aws', {}).get(spec.lower().replace(' ', ''), 'N/A'))
                display_data['GCP'].append(results.get('gcp', {}).get(spec.lower().replace(' ', ''), 'N/A'))

        st.table(display_data)

    with st.container(border=True):
        st.header("Pricing Comparison")
        cost_cols = st.columns(3)
        valid_costs = {cloud: data['cost'] for cloud, data in results.items() if data and 'cost' in data and pd.notna(data['cost'])}
        lowest_cost_cloud = min(valid_costs, key=valid_costs.get) if valid_costs else None
        cloud_map = {'azure': cost_cols[0], 'aws': cost_cols[1], 'gcp': cost_cols[2]}
        cloud_names = {'azure': 'Microsoft Azure', 'aws': 'Amazon AWS', 'gcp': 'Google Cloud'}
        
        for cloud, col in cloud_map.items():
            with col:
                data = results.get(cloud)
                if data and 'cost' in data and pd.notna(data['cost']):
                    st.subheader(cloud_names[cloud])
                    st.markdown(f"*{data.get('meter') or data.get('tier')}*")
                    st.metric(label="Total Monthly Cost", value=f"${data['cost']:.2f}")
                    if cloud == lowest_cost_cloud:
                        st.success("✅ Recommended")
                else:
                    st.subheader(cloud_names[cloud])
                    st.markdown("*N/A*")
                    st.metric(label="Total Monthly Cost", value="N/A")
    
    with st.container(border=True):
        st.header("Cost Summary & Savings Analysis")
        summary_cols = st.columns(4)
        if valid_costs:
            costs = list(valid_costs.values())
            lowest = min(costs) if costs else 0
            average = sum(costs) / len(costs) if costs else 0
            monthly_savings = average - lowest
            
            with summary_cols[0]: st.metric("Lowest Cost", f"${lowest:.2f}")
            with summary_cols[1]: st.metric("Average Cost", f"${average:.2f}")
            with summary_cols[2]: st.metric("Monthly Savings", f"${monthly_savings:.2f}")
            with summary_cols[3]: st.metric("Annual Savings", f"${monthly_savings * 12:.2f}")