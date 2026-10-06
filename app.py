import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="Rust Summary Dashboard", layout="wide")
st.title("Rust Summary Interactive Dashboard")

# 2. Secure File Upload Functionality
st.sidebar.header("Update Data (Admin Only)")
upload_password = st.sidebar.text_input("Enter password to upload file", type="password")

# Set default file or uploaded file
data_source = "SUM rust BRG.xlsx"

if upload_password == "admin123": # คุณสามารถเปลี่ยนรหัสผ่านตรงนี้ได้
    uploaded_file = st.sidebar.file_uploader("Upload new Excel file (.xlsx)", type=["xlsx"])
    if uploaded_file is not None:
        data_source = uploaded_file
        st.sidebar.success("File uploaded successfully!")
elif upload_password != "":
    st.sidebar.error("Incorrect password. Upload restricted.")

# 3. Load Data Function
@st.cache_data
def load_data(file):
    try:
        # Skip the first 4 rows to get to the actual header
        df = pd.read_excel(file, skiprows=4)
        # Drop rows where 'Year' is missing
        df = df.dropna(subset=['Year'])
        
        # Convert columns to appropriate types
        df['Year'] = df['Year'].astype(str).str.replace(r'\.0', '', regex=True)
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return pd.DataFrame()

df = load_data(data_source)

if df.empty:
    st.warning("No data available. Please check the file.")
    st.stop()

# 4. Global Filters
st.sidebar.header("Global Filters")
years = st.sidebar.multiselect("Select Year", options=df['Year'].unique(), default=df['Year'].unique())
months = st.sidebar.multiselect("Select Month", options=df['Month'].unique(), default=df['Month'].unique())
divisions = st.sidebar.multiselect("Select Division", options=df['Division'].unique(), default=df['Division'].unique())
samples = st.sidebar.multiselect("Select Sample", options=df['Sample'].unique(), default=df['Sample'].unique())

# Apply Filters
filtered_df = df[
    (df['Year'].isin(years)) & 
    (df['Month'].isin(months)) & 
    (df['Division'].isin(divisions)) &
    (df['Sample'].isin(samples))
]

# 5. Dashboard Metrics
st.markdown("### Key Statistics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Requests", len(filtered_df))
col2.metric("Total Amount (Pcs)", int(filtered_df['Amount (Pcs)'].sum()) if not filtered_df.empty else 0)
col3.metric("Total Rusty Cases", filtered_df['Rusty'].sum() if 'Rusty' in filtered_df else 0)
col4.metric("Divisions Involved", filtered_df['Division'].nunique())

st.markdown("---")

# 6. Charts & Trends
col_chart1, col_chart2 = st.columns(2)

# Trend Analysis: Monthly Requests
with col_chart1:
    st.markdown("#### Monthly Request Trend")
    if not filtered_df.empty:
        trend_df = filtered_df.groupby(['Month', 'Year']).size().reset_index(name='Count')
        fig_trend = px.line(trend_df, x='Month', y='Count', color='Year', markers=True, title="Number of Requests by Month")
        st.plotly_chart(fig_trend, use_container_width=True)

# Division Distribution
with col_chart2:
    st.markdown("#### Requests by Division")
    if not filtered_df.empty:
        div_df = filtered_df['Division'].value_counts().reset_index()
        div_df.columns = ['Division', 'Count']
        fig_div = px.pie(div_df, names='Division', values='Count', hole=0.4, title="Proportion of Requests by Division")
        st.plotly_chart(fig_div, use_container_width=True)

# Rust & Defect Breakdown
st.markdown("#### Defect Types Breakdown")
# Summing all the defect columns dynamically
defect_cols = ['Rusty, Corroded surface', 'Rusty', 'Corroded surface', 'Oxidized surface', 
               ' Inclusion', 'Metal sludge/ Sludge contamination', 'Corrosion surface', 
               'Damaged surface', 'Rusty contamination', 'Grain boundary corrosion', 'Pitting corrosion']

existing_defect_cols = [col for col in defect_cols if col in filtered_df.columns]
if existing_defect_cols:
    defect_sums = filtered_df[existing_defect_cols].sum().reset_index()
    defect_sums.columns = ['Defect Type', 'Total Count']
    defect_sums = defect_sums[defect_sums['Total Count'] > 0] # Show only those > 0
    
    fig_defects = px.bar(defect_sums, x='Defect Type', y='Total Count', color='Defect Type', title="Total Count of Various Defects")
    fig_defects.update_layout(showlegend=False)
    st.plotly_chart(fig_defects, use_container_width=True)

# 7. Raw Data Table
st.markdown("### Detailed Data")
st.dataframe(filtered_df, use_container_width=True)