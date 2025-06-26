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
            /* --- General --- */
            .stApp { background-color: #F0F2F6; }
            h1, h3 { font-weight: 600; }
            /* --- Cards --- */
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
            /* --- Savings Analysis --- */
            .savings-card { background-color: white; border-radius: 10px; padding: 25px; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.1); border: 1px solid #E0E0E0; }
            .metric-container { text-align: center; }
            .metric-value { font-size: 2.2em; font-weight: 600; color: #28a745; }
            .metric-label { font-size: 1em; color: #6c757d; }
        </style>
    """, unsafe_allow_html=True)

# --- Data Loading and Processing ---
GOOGLE_SHEET_URL_EC2 = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR6nm8tGltr086h1MhnosWrIbP3wJiLEIlEK4ykpvaBhQ7YMzC3X7CNA6MeRKH7WUxHIeDCpASTdYnZ/pub?gid=0&single=true&output=csv"

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
    """Loads the CSV data directly into a DataFrame without transformation."""
    try:
        df = pd.read_csv(url, on_bad_lines='warn')
        return df
    except Exception as e:
        st.error(f"An error occurred while loading data. Please check the Google Sheet URL. Error: {e}")
        return None

def get_comparison_from_row(df, primary_cloud, primary_meter, primary_region):
    """
    Finds the specified primary instance and returns the data for all three clouds
    from that single row.
    """
    row = None
    # Find the correct row in the DataFrame based on the user's selection
    if primary_cloud == 'aws':
        row_df = df.loc[(df['Instance Type'] == primary_meter) & (df['Region'] == primary_region)]
    elif primary_cloud == 'azure':
        row_df = df.loc[(df['Azure Meter'] == primary_meter) & (df['AzureRegion'] == primary_region)]
    elif primary_cloud == 'gcp':
        row_df = df.loc[(df['GCP SKU'] == primary_meter) & (df['GCP Region'] == primary_region)]
    
    if not row_df.empty:
        row = row_df.iloc[0] # Get the first (and only) row as a Series
    else:
        return None # Return None if no matching row is found

    # Build the equivalents dictionary from this one row
    equivalents = {}
    # Extract AWS data if present in the row
    if pd.notna(row.get('Instance Type')) and pd.notna(row.get('AWS Monthly Cost')):
        equivalents['aws'] = {
            'meter': row['Instance Type'], 'region': row['Region'], 
            'vcpu': int(float(row['vCPUs'])), 'memory': parse_memory(row['Memory']),
            'cost': parse_cost(row['AWS Monthly Cost'])
        }
    # Extract Azure data if present in the row
    if pd.notna(row.get('Azure Meter')) and pd.notna(row.get('Azure Monthly Cost')):
         equivalents['azure'] = {
            'meter': row['Azure Meter'], 'region': row['AzureRegion'], 
            'vcpu': int(float(row['vCPUs'])), 'memory': parse_memory(row['Memory']),
            'cost': parse_cost(row['Azure Monthly Cost'])
        }
    # Extract GCP data if present in the row
    if pd.notna(row.get('GCP SKU')) and pd.notna(row.get('GCP Monthly Cost')):
        equivalents['gcp'] = {
            'meter': row['GCP SKU'], 'region': row['GCP Region'],
            'vcpu': int(float(row['vCPUs.1'])), 'memory': parse_memory(row['Memory.1']),
            'cost': parse_cost(row['GCP Monthly Cost'])
        }
    return equivalents

# --- Main Application ---
load_css()
RAW_DF = load_data(GOOGLE_SHEET_URL_EC2)

st.title("Pricing Comparison")

if RAW_DF is None:
    st.stop()

if 'comparison_results' not in st.session_state:
    st.session_state.comparison_results = None

with st.container(border=True):
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("1. Select Service")
        csp_map = {'AWS': 'aws', 'Azure': 'azure', 'GCP': 'gcp'}
        selected_csp = csp_map[st.selectbox("Cloud Provider", csp_map.keys())]
        
        # Define columns for the selected cloud
        col_map = {
            'aws': {'meter': 'Instance Type', 'region': 'Region'},
            'azure': {'meter': 'Azure Meter', 'region': 'AzureRegion'},
            'gcp': {'meter': 'GCP SKU', 'region': 'GCP Region'}
        }
        meter_col = col_map[selected_csp]['meter']
        region_col = col_map[selected_csp]['region']

        # Filter the DataFrame to get valid instances for the dropdown
        filtered_df = RAW_DF.dropna(subset=[meter_col, region_col])
        instance_options = {
            f"{row[meter_col]}@{row[region_col]}": f"{row[meter_col]} ({row[region_col]})"
            for index, row in filtered_df.iterrows()
        }
        selected_key = st.selectbox("Instance", options=instance_options.keys(), format_func=lambda x: instance_options.get(x, x))

    with col2:
        st.subheader("2. Set Quantity")
        quantity = st.number_input("Quantity", min_value=1, value=1)
        
        st.write("")
        if st.button("Compare Prices", type="primary", use_container_width=True):
            meter, region = selected_key.split('@')
            equivalents = get_comparison_from_row(RAW_DF, selected_csp, meter, region)
            
            if equivalents:
                st.session_state.comparison_results = {
                    "equivalents": equivalents,
                    "quantity": quantity,
                    "timestamp": datetime.now().strftime("%m/%d/%Y, %I:%M:%S %p")
                }
            else:
                st.warning("Could not find the selected instance to start comparison.")
                st.session_state.comparison_results = None

# --- Results Display Area ---
if st.session_state.comparison_results:
    results = st.session_state.comparison_results
    equivalents = results['equivalents']
    
    st.divider()
    st.write(f"_Comparison generated: {results['timestamp']}_")

    # --- Technical Specifications Table ---
    st.subheader("Technical Specifications")
    tech_data = []
    for cloud in ['aws', 'azure', 'gcp']:
        instance = equivalents.get(cloud)
        tech_data.append({
            "Cloud": cloud.upper(),
            "Instance Name": instance.get('meter', "N/A") if instance else "N/A",
            "vCPUs": instance.get('vcpu', "N/A") if instance else "N/A",
            "Memory (GiB)": instance.get('memory', "N/A") if instance else "N/A",
            "Region": instance.get('region', "N/A") if instance else "N/A"
        })
    st.dataframe(pd.DataFrame(tech_data).set_index("Cloud"), use_container_width=True)

    # --- Cost Comparison Cards ---
    st.subheader("Cost Comparison")
    costs = {cloud: {'base_price': data['cost'], 'total_monthly_cost': data['cost'] * results['quantity']} 
             for cloud, data in equivalents.items()}
    lowest_cost = min((c['total_monthly_cost'] for c in costs.values()), default=0)
    
    card_cols = st.columns(3)
    cloud_logos = {'aws': 'Amazon AWS', 'azure': 'Microsoft Azure', 'gcp': 'Google Cloud'}
    
    for i, cloud in enumerate(['aws', 'azure', 'gcp']):
        with card_cols[i]:
            instance = equivalents.get(cloud)
            cost_data = costs.get(cloud)
            is_recommended = cost_data and cost_data['total_monthly_cost'] == lowest_cost and lowest_cost > 0
            
            card_class = "card recommended-card" if is_recommended else "card"
            header_html = f'<div class="card-header">{cloud_logos[cloud]}'
            if is_recommended: header_html += '<span class="recommended-badge">RECOMMENDED</span>'
            header_html += '</div>'

            html_body = ""
            if instance and cost_data:
                html_body = f"""
                    <div class="card-body">
                        <div>{instance['meter']}</div><small>{instance['region']}</small><hr>
                        <div class="cost-item"><span>Unit Price (Monthly):</span> <span>${cost_data["base_price"]:,.2f}</span></div>
                        <div class="cost-item"><span>Quantity:</span><span>{results["quantity"]}x</span></div>
                    </div>
                    <div class="total-cost">${cost_data["total_monthly_cost"]:,.2f}</div>
                """
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
