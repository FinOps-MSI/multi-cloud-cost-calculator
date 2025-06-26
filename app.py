import streamlit as st
import pandas as pd
import re
from io import StringIO
import uuid

# --- Page Configuration ---
st.set_page_config(
    page_title="Multi-Cloud Cost Calculator",
    page_icon="☁️",
    layout="wide"
)

# --- Live Data Loading from Google Sheets ---
# IMPORTANT: Replace these with your own Google Sheet URLs
# How to get the URL:
# 1. In your Google Sheet, click 'File' -> 'Share' -> 'Publish to web'.
# 2. In the dialog, select the sheet you want to share.
# 3. Choose 'Comma-separated values (.csv)' as the format.
# 4. Click 'Publish' and copy the generated link.
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

@st.cache_data(ttl="1h") # Cache the data for 1 hour
def load_and_process_data(ec2_url, rds_url, s3_url):
    """Loads and normalizes data from Google Sheets URLs."""
    try:
        # --- Process EC2 Data ---
        ec2_df = pd.read_csv(ec2_url)
        ec2_data = []
        for _, row in ec2_df.iterrows():
            vcpu = int(float(row['vCPUs']))
            memory = parse_memory(row['Memory'])
            if pd.notna(row['AWS Monthly Cost']) and parse_cost(row['AWS Monthly Cost']) > 0:
                ec2_data.append({'cloud': 'aws', 'region': row['Region'], 'meter': row['Instance Type'], 'vcpu': vcpu, 'memory': memory, 'cost': parse_cost(row['AWS Monthly Cost'])})
            if pd.notna(row['Azure Monthly Cost']) and parse_cost(row['Azure Monthly Cost']) > 0:
                ec2_data.append({'cloud': 'azure', 'region': row['AzureRegion'], 'meter': row['Azure Meter'], 'vcpu': vcpu, 'memory': memory, 'cost': parse_cost(row['Azure Monthly Cost'])})
            if pd.notna(row.get('GCP Monthly Cost')) and row.get('GCP Region') != '#N/A' and parse_cost(row.get('GCP Monthly Cost')) > 0:
                ec2_data.append({'cloud': 'gcp', 'region': row['GCP Region'], 'meter': row['GCP SKU'], 'vcpu': vcpu, 'memory': memory, 'cost': parse_cost(row['GCP Monthly Cost'])})

        # --- Process RDS Data ---
        rds_df = pd.read_csv(rds_url)
        rds_data = []
        for _, row in rds_df.iterrows():
            if pd.notna(row['AWS- On Demand Monthly Cost']) and parse_cost(row['AWS- On Demand Monthly Cost']) > 0:
                rds_data.append({'cloud': 'aws', 'meter': row['Meter'], 'region': row['Region'], 'vcpu': int(float(row['vCPUs'])), 'memory': parse_memory(row['Memory']), 'cost': parse_cost(row['AWS- On Demand Monthly Cost'])})
            if pd.notna(row['Azure Monthly Cost']) and parse_cost(row['Azure Monthly Cost']) > 0:
                rds_data.append({'cloud': 'azure', 'meter': row['Meter.1'], 'region': row['AzureRegion'], 'vcpu': int(float(row['vCPUs'])), 'memory': parse_memory(row['Memory']), 'cost': parse_cost(row['Azure Monthly Cost'])})
            if pd.notna(row.get('GCP SKU')) and pd.notna(row.get('GCP Ondemand Cost/month')) and parse_cost(row.get('GCP Ondemand Cost/month')) > 0:
                 rds_data.append({'cloud': 'gcp', 'meter': row['GCP SKU'], 'region': row['GCP Region'], 'vcpu': int(float(row['vCPUs.1'])), 'memory': parse_memory(row['Memory.1']), 'cost': parse_cost(row['GCP Ondemand Cost/month'])})

        # --- Process S3 Data ---
        s3_df = pd.read_csv(s3_url)
        s3_data = []
        for _, row in s3_df.iterrows():
            if parse_cost(row['AWS Ondemand Cost']) > 0:
                s3_data.append({'cloud': 'aws', 'tier': row['Meter'], 'region': row['Region'], 'costPerGB': parse_cost(row['AWS Ondemand Cost'])})
            if parse_cost(row['Azure Ondemand Cost']) > 0:
                s3_data.append({'cloud': 'azure', 'tier': row['Meter.1'], 'region': row['Region.1'], 'costPerGB': parse_cost(row['Azure Ondemand Cost'])})
            if parse_cost(row['GCP Ondemand Cost']) > 0:
                s3_data.append({'cloud': 'gcp', 'tier': row['Meter.2'], 'region': row['Region.2'], 'costPerGB': parse_cost(row['GCP Ondemand Cost'])})
        
        # Remove duplicates and clean up
        processed_ec2 = [dict(t) for t in {tuple(d.items()) for d in ec2_data}]
        processed_rds = [dict(t) for t in {tuple(d.items()) for d in rds_data}]
        processed_s3 = [dict(t) for t in {tuple(d.items()) for d in s3_data}]

        return {'ec2': processed_ec2, 'rds': processed_rds, 's3': processed_s3}
    except Exception as e:
        st.error(f"An error occurred while processing the data. Please check that the Google Sheet URLs are correct and publicly accessible. Error: {e}")
        return None


# --- Main App Logic ---
RAW_DATA = load_and_process_data(GOOGLE_SHEET_URL_EC2, GOOGLE_SHEET_URL_RDS, GOOGLE_SHEET_URL_S3)

def find_equivalent(primary_instance, service_type):
    if not primary_instance or not RAW_DATA: return {}
    data = RAW_DATA[service_type]
    aws_equiv = next((i for i in data if i['cloud'] == 'aws' and i.get('vcpu') == primary_instance.get('vcpu') and i.get('memory') == primary_instance.get('memory')), None)
    azure_equiv = next((i for i in data if i['cloud'] == 'azure' and i.get('vcpu') == primary_instance.get('vcpu')), None)
    gcp_equiv = next((i for i in data if i['cloud'] == 'gcp' and i.get('vcpu') == primary_instance.get('vcpu') and i.get('memory') == primary_instance.get('memory')), None)
    return {'aws': aws_equiv, 'azure': azure_equiv, 'gcp': gcp_equiv}

def get_s3_equivalents(primary_tier, storage_gb):
    if not RAW_DATA: return {}
    equivalents = {}
    aws_tier = next((t for t in RAW_DATA['s3'] if t['cloud'] == 'aws' and t.get('tier') == primary_tier), None)
    azure_tier = next((t for t in RAW_DATA['s3'] if t['cloud'] == 'azure' and primary_tier.split(' ')[0] in t.get('tier', '')), None)
    gcp_tier = next((t for t in RAW_DATA['s3'] if t['cloud'] == 'gcp' and primary_tier.split(' ')[0] in t.get('tier', '')), None)

    if aws_tier: equivalents['aws'] = {**aws_tier, 'cost': aws_tier['costPerGB'] * storage_gb}
    if azure_tier: equivalents['azure'] = {**azure_tier, 'cost': azure_tier['costPerGB'] * storage_gb}
    if gcp_tier: equivalents['gcp'] = {**gcp_tier, 'cost': gcp_tier['costPerGB'] * storage_gb}
    return equivalents

# --- Session State Initialization ---
if 'basket' not in st.session_state:
    st.session_state.basket = []

# --- UI Rendering ---
st.title("☁️ Multi-Cloud Cost Calculator")
st.write("Compare costs for a group of resources across AWS, Azure, and GCP.")

if not RAW_DATA:
    st.error("Data could not be loaded. Please check the script's data strings.")
    st.stop()

with st.container(border=True):
    st.header("Service Configuration")
    
    cols = st.columns(4)
    with cols[0]:
        csp_map = {'AWS': 'aws', 'Azure': 'azure', 'GCP': 'gcp'}
        selected_csp_label = st.selectbox("Cloud Provider", csp_map.keys())
        selected_csp = csp_map[selected_csp_label]

    with cols[1]:
        service_map = {'Compute': 'ec2', 'Database': 'rds', 'Storage': 's3'}
        service_label = st.selectbox("Service Type", service_map.keys())
        service_type = service_map[service_label]
        
    # Dynamic UI for parameters
    if service_type in ['ec2', 'rds']:
        with cols[2]:
            instances_in_csp = [item for item in RAW_DATA[service_type] if item['cloud'] == selected_csp]
            instance_options = {f"{item['meter']}@{item['region']}": f"{item['meter']} ({item['region']})" for item in instances_in_csp}
            selected_instance_key = st.selectbox("Instance", options=instance_options.keys(), format_func=lambda x: instance_options.get(x, x))
    elif service_type == 's3':
        with cols[2]:
            tiers_in_csp = sorted(list(set(item['tier'] for item in RAW_DATA['s3'] if item['cloud'] == selected_csp)))
            selected_tier = st.selectbox("Storage Tier", tiers_in_csp)
            storage_amount = st.number_input("Storage (GB)", min_value=1, value=1000)

    with cols[3]:
        st.write("")
        st.write("")
        if st.button("Add to Basket", type="primary", use_container_width=True):
            item_id = str(uuid.uuid4())
            new_item = {'id': item_id, 'equivalents': {}}

            if service_type in ['ec2', 'rds']:
                meter, region = selected_instance_key.split('@')
                primary_instance = next((i for i in RAW_DATA[service_type] if i['cloud'] == selected_csp and i['meter'] == meter and i['region'] == region), None)
                new_item['description'] = f"{selected_csp_label} {service_label}: {primary_instance['meter']}"
                new_item['equivalents'] = find_equivalent(primary_instance, service_type)

            elif service_type == 's3':
                new_item['description'] = f"{selected_csp_label} {service_label}: {selected_tier} ({storage_amount} GB)"
                new_item['equivalents'] = get_s3_equivalents(selected_tier, storage_amount)

            st.session_state.basket.append(new_item)

# --- Display Basket and Totals ---
if st.session_state.basket:
    with st.container(border=True):
        st.header("Resource Basket")
        total_costs = {'aws': 0, 'azure': 0, 'gcp': 0}
        
        for i, item in enumerate(st.session_state.basket):
            cols = st.columns([4, 1])
            with cols[0]:
                st.write(item['description'])
            with cols[1]:
                if st.button("Remove", key=f"remove_{item['id']}", use_container_width=True):
                    st.session_state.basket.pop(i)
                    st.rerun()

            for cloud in ['aws', 'azure', 'gcp']:
                if item['equivalents'].get(cloud) and pd.notna(item['equivalents'][cloud].get('cost')):
                    total_costs[cloud] += item['equivalents'][cloud]['cost']
    
    with st.container(border=True):
        st.header("Total Monthly Cost Comparison")
        cost_cols = st.columns(3)
        valid_costs = {cloud: cost for cloud, cost in total_costs.items() if cost > 0}
        lowest_cost_cloud = min(valid_costs, key=valid_costs.get) if valid_costs else None

        cloud_map = {'aws': cost_cols[0], 'azure': cost_cols[1], 'gcp': cost_cols[2]}
        cloud_names = {'aws': 'Amazon AWS', 'azure': 'Microsoft Azure', 'gcp': 'Google Cloud'}
        
        for cloud, col in cloud_map.items():
            with col:
                st.subheader(cloud_names[cloud])
                st.metric(label="Total Monthly Cost for Basket", value=f"${total_costs[cloud]:,.2f}")
                if cloud == lowest_cost_cloud:
                    st.success("✅ Recommended")
