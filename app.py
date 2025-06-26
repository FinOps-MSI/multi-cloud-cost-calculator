import streamlit as st
import pandas as pd
import re
import uuid
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Cloud Pricing Comparison",
    page_icon="💰",
    layout="wide"
)

# --- Custom CSS for Formal Styling ---
def load_css():
    """Injects custom CSS to style the app to match the reference screenshot."""
    st.markdown("""
        <style>
            /* --- General --- */
            .stApp {
                background-color: #F0F2F6;
            }
            /* --- Cards --- */
            .card {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 8px 0 rgba(0,0,0,0.1);
                transition: 0.3s;
                border: 1px solid #E0E0E0;
            }
            .card:hover {
                box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
            }
            .recommended-card {
                border: 2px solid #28a745; /* Green border for recommendation */
            }
            .card-header {
                font-size: 1.2em;
                font-weight: bold;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            .recommended-badge {
                background-color: #28a745;
                color: white;
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 0.8em;
            }
            .cost-item {
                display: flex;
                justify-content: space-between;
                margin-bottom: 8px;
            }
            .total-cost {
                font-size: 1.5em;
                font-weight: bold;
                color: #007bff; /* Blue for total cost */
                text-align: right;
                margin-top: 15px;
            }
            
            /* --- Savings Analysis --- */
            .savings-card {
                background-color: white;
                border-radius: 10px;
                padding: 25px;
                box-shadow: 0 4px 8px 0 rgba(0,0,0,0.1);
                border: 1px solid #E0E0E0;
            }
            .metric-container {
                text-align: center;
            }
            .metric-value {
                font-size: 2.2em;
                font-weight: 600;
                color: #28a745; /* Green for savings */
            }
            .metric-label {
                font-size: 1em;
                color: #6c757d; /* Gray for labels */
            }
        </style>
    """, unsafe_allow_html=True)


# --- Data Loading and Processing (Same as before, but kept for completeness) ---
GOOGLE_SHEET_URL_EC2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR6nm8tGltr086h1MhnosWrIbP3wJiLEIlEK4ykpvaBhQ7YMzC3X7CNA6MeRKH7WUxHIeDCpASTdYnZ/pub?gid=0&single=true&output=csv"
GOOGLE_SHEET_URL_RDS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR6nm8tGltr086h1MhnosWrIbP3wJiLEIlEK4ykpvaBhQ7YMzC3X7CNA6MeRKH7WUxHIeDCpASTdYnZ/pub?gid=1524734883&single=true&output=csv"
GOOGLE_SHEET_URL_S3 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR6nm8tGltr086h1MhnosWrIbP3wJiLEIlEK4ykpvaBhQ7YMzC3X7CNA6MeRKH7WUxHIeDCpASTdYnZ/pub?gid=1926651960&single=true&output=csv"

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
def load_and_process_data(ec2_url, rds_url, s3_url):
    try:
        ec2_df = pd.read_csv(ec2_url, on_bad_lines='warn')
        ec2_data = []
        for _, row in ec2_df.iterrows():
            if 'vCPUs' not in row or 'Memory' not in row: continue
            vcpu = int(float(row['vCPUs']))
            memory = parse_memory(row['Memory'])
            if pd.notna(row.get('AWS Monthly Cost')) and parse_cost(row.get('AWS Monthly Cost')) > 0:
                ec2_data.append({'cloud': 'aws', 'region': row['Region'], 'meter': row['Instance Type'], 'vcpu': vcpu, 'memory': memory, 'cost': parse_cost(row['AWS Monthly Cost'])})
            if pd.notna(row.get('Azure Monthly Cost')) and parse_cost(row.get('Azure Monthly Cost')) > 0:
                ec2_data.append({'cloud': 'azure', 'region': row['AzureRegion'], 'meter': row['Azure Meter'], 'vcpu': vcpu, 'memory': memory, 'cost': parse_cost(row['Azure Monthly Cost'])})
            if pd.notna(row.get('GCP Monthly Cost')) and row.get('GCP Region') != '#N/A' and parse_cost(row.get('GCP Monthly Cost')) > 0:
                ec2_data.append({'cloud': 'gcp', 'region': row['GCP Region'], 'meter': row['GCP SKU'], 'vcpu': vcpu, 'memory': memory, 'cost': parse_cost(row['GCP Monthly Cost'])})
        
        # NOTE: Processing for RDS and S3 would follow a similar pattern
        # For brevity, this example focuses on the EC2 data shown.
        processed_ec2 = [dict(t) for t in {tuple(d.items()) for d in ec2_data}]
        return {'ec2': processed_ec2, 'rds': [], 's3': []} # Simplified for this example
    except Exception as e:
        st.error(f"An error occurred while loading data. Please check the Google Sheet URLs. Error: {e}")
        return None

def find_equivalent(primary_instance):
    """Finds equivalent instances based on vCPU and Memory."""
    if not primary_instance or not RAW_DATA: return {}
    data = RAW_DATA['ec2']
    
    aws_equiv = next((i for i in data if i['cloud'] == 'aws' and i.get('vcpu') == primary_instance.get('vcpu') and i.get('memory') == primary_instance.get('memory')), None)
    azure_equiv = next((i for i in data if i['cloud'] == 'azure' and i.get('vcpu') == primary_instance.get('vcpu')), None) # Azure matching is often vCPU-based
    gcp_equiv = next((i for i in data if i['cloud'] == 'gcp' and i.get('vcpu') == primary_instance.get('vcpu') and i.get('memory') == primary_instance.get('memory')), None)

    return {'aws': aws_equiv, 'azure': azure_equiv, 'gcp': gcp_equiv}

# --- Main Application ---
load_css()
RAW_DATA = load_and_process_data(GOOGLE_SHEET_URL_EC2, GOOGLE_SHEET_URL_RDS, GOOGLE_SHEET_URL_S3)

st.title("Pricing Comparison")

# --- Session State Initialization ---
if 'comparison_results' not in st.session_state:
    st.session_state.comparison_results = None

# --- Input Configuration Area ---
with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("1. Select Service")
        csp_map = {'AWS': 'aws', 'Azure': 'azure', 'GCP': 'gcp'}
        selected_csp_label = st.selectbox("Cloud Provider", csp_map.keys(), key="csp_select")
        selected_csp = csp_map[selected_csp_label]
        
        # For now, we only support Compute comparison as per the logic refinement
        service_label = st.selectbox("Service Type", ["Compute"]) 
        service_type = 'ec2'

        instances_in_csp = [item for item in RAW_DATA[service_type] if item['cloud'] == selected_csp]
        instance_options = {f"{item['meter']}@{item['region']}": f"{item['meter']} ({item['region']})" for item in instances_in_csp}
        selected_instance_key = st.selectbox("Instance", options=instance_options.keys(), format_func=lambda x: instance_options.get(x, x))

    with col2:
        st.subheader("2. Set Quantity & Discounts")
        quantity = st.number_input("Quantity", min_value=1, value=1, key="quantity")
        aws_discount = st.number_input("AWS Enterprise Discount (%)", min_value=0.0, max_value=100.0, value=25.0, step=1.0)
        azure_discount = st.number_input("Azure Enterprise Discount (%)", min_value=0.0, max_value=100.0, value=15.0, step=1.0)
        gcp_discount = st.number_input("GCP Enterprise Discount (%)", min_value=0.0, max_value=100.0, value=20.0, step=1.0)
    
    with col3:
        st.subheader("3. Generate Comparison")
        st.write("") # Spacer
        st.write("") # Spacer
        if st.button("Add to Comparison", type="primary", use_container_width=True):
            meter, region = selected_instance_key.split('@')
            primary_instance = next((i for i in RAW_DATA[service_type] if i['cloud'] == selected_csp and i['meter'] == meter and i['region'] == region), None)
            
            if primary_instance:
                equivalents = find_equivalent(primary_instance)
                st.session_state.comparison_results = {
                    "equivalents": equivalents,
                    "quantity": quantity,
                    "discounts": {"aws": aws_discount, "azure": azure_discount, "gcp": gcp_discount},
                    "timestamp": datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p")
                }
            else:
                st.warning("Could not find the selected primary instance to start comparison.")

# --- Results Display Area ---
if st.session_state.comparison_results:
    results = st.session_state.comparison_results
    equivalents = results['equivalents']
    
    st.write(f"_Last updated: {results['timestamp']}_")

    # --- 1. Equivalency Table ---
    st.subheader("Technical Specifications")
    tech_data = []
    for cloud in ['aws', 'azure', 'gcp']:
        instance = equivalents.get(cloud)
        if instance:
            tech_data.append({
                "Cloud": cloud.upper(),
                "Instance Name": instance['meter'],
                "vCPUs": instance['vcpu'],
                "Memory (GiB)": instance['memory'],
                "Region": instance['region']
            })
        else:
            tech_data.append({"Cloud": cloud.upper(), "Instance Name": "Not Found", "vCPUs": "N/A", "Memory (GiB)": "N/A", "Region": "N/A"})
    st.dataframe(pd.DataFrame(tech_data).set_index("Cloud"), use_container_width=True)

    # --- 2. Comparison Cards ---
    st.subheader("Cost Comparison")
    
    # Calculate final costs
    costs = {}
    for cloud, data in equivalents.items():
        if data:
            base_cost = data['cost']
            discount_percent = results['discounts'][cloud]
            discount_amount = base_cost * (discount_percent / 100)
            final_cost = (base_cost - discount_amount) * results['quantity']
            costs[cloud] = {
                "base_price": base_cost,
                "discount_percent": discount_percent,
                "discount_amount": discount_amount,
                "total_monthly_cost": final_cost
            }
    
    lowest_cost = min(c['total_monthly_cost'] for c in costs.values()) if costs else 0
    
    card_cols = st.columns(3)
    cloud_logos = {'aws': '⚫', 'azure': '🔵', 'gcp': '🟢'} # Simple emoji logos
    cloud_names = {'aws': 'Amazon AWS', 'azure': 'Microsoft Azure', 'gcp': 'Google Cloud'}
    
    for i, cloud in enumerate(['azure', 'aws', 'gcp']): # Order from screenshot
        with card_cols[i]:
            instance = equivalents.get(cloud)
            cost_data = costs.get(cloud)
            is_recommended = cost_data and cost_data['total_monthly_cost'] == lowest_cost
            
            card_class = "recommended-card" if is_recommended else "card"
            
            html = f'<div class="{card_class}">'
            
            # Header with optional badge
            header_html = f'<div class="card-header">{cloud_logos[cloud]} {cloud_names[cloud]}'
            if is_recommended:
                header_html += '<span class="recommended-badge">RECOMMENDED</span>'
            header_html += '</div>'
            html += header_html

            if instance and cost_data:
                html += f"<div>{instance['meter']}</div><small>{instance['region']}</small><hr>"
                html += f'<div class="cost-item"><span>Base Price (Monthly):</span> <span>${cost_data["base_price"]:,.2f}</span></div>'
                html += f'<div class="cost-item"><span>Enterprise Discount ({cost_data["discount_percent"]}%):</span> <span style="color: #dc3545;">-${cost_data["discount_amount"]:,.2f}</span></div>'
                html += f'<div class="cost-item"><span>Quantity ({results["quantity"]}x):</span> <span></span></div>' # No value for this row
                html += f'<div class="total-cost">${cost_data["total_monthly_cost"]:,.2f}</div>'
            else:
                html += "<p>Equivalent not found or no pricing data available.</p>"
                
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)
            
    # --- 3. Savings Analysis ---
    st.subheader("Cost Summary & Savings Analysis")
    
    with st.container():
        st.markdown('<div class="savings-card">', unsafe_allow_html=True)
        metric_cols = st.columns(4)
        valid_costs = [c['total_monthly_cost'] for c in costs.values()]
        
        if valid_costs:
            average_cost = sum(valid_costs) / len(valid_costs)
            monthly_savings = average_cost - lowest_cost
            annual_savings = monthly_savings * 12

            with metric_cols[0]:
                st.markdown(f'<div class="metric-container"><div class="metric-value">${lowest_cost:,.2f}</div><div class="metric-label">Lowest Cost</div></div>', unsafe_allow_html=True)
            with metric_cols[1]:
                st.markdown(f'<div class="metric-container"><div class="metric-value">${average_cost:,.2f}</div><div class="metric-label">Average Cost</div></div>', unsafe_allow_html=True)
            with metric_cols[2]:
                st.markdown(f'<div class="metric-container"><div class="metric-value">${monthly_savings:,.2f}</div><div class="metric-label">Monthly Savings</div></div>', unsafe_allow_html=True)
            with metric_cols[3]:
                st.markdown(f'<div class="metric-container"><div class="metric-value">${annual_savings:,.2f}</div><div class="metric-label">Annual Savings</div></div>', unsafe_allow_html=True)
        else:
            st.write("Not enough data to perform savings analysis.")
        st.markdown('</div>', unsafe_allow_html=True)
