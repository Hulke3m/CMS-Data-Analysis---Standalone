import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import time

# Function to merge CSV data into Pandas DataFrame
def merge_csv_to_dataframe(csv_files):
    merged_data = []

    for csv_file in csv_files:
        if csv_file.name.endswith(".csv"):
            df_csv = pd.read_csv(csv_file)
            df_csv['Last Signal'] = pd.to_datetime(df_csv['Last Signal'], format='%d/%m/%Y, %H:%M:%S')
            merged_data.append(df_csv)

    merged_data = pd.concat(merged_data, ignore_index=True)
    return merged_data

# Function to display Streamlit app
def display_streamlit_app(merged_data):
    merged_data['Month'] = merged_data['Last Signal'].dt.strftime("%B")
    merged_data['Battery Modem'] = np.where((merged_data['Battery'] > 0) & (merged_data['Battery'] < 3), 'ERROR', 'OK')
    merged_data['Signal Strength'] = np.where((merged_data['Signal'] > 0) & (merged_data['Signal'] < 20), 'ERROR', 'OK')
    merged_data['Analysis'] = np.where((merged_data['Battery Modem'] == 'OK') & (merged_data['Signal Strength'] == 'OK'), 'GOOD', 'REPLACE')

    st.sidebar.title('CMS Data Analysis Tools')
    unique_key_file_uploader = f"file_uploader_{time.time()}"
    uploaded_files = st.sidebar.file_uploader("Upload CSV Files", key=unique_key_file_uploader, accept_multiple_files=True)

    with st.sidebar.expander("Filter Options", expanded=True):
        available_ids = merged_data['L1#'].unique()
        selected_id = st.selectbox('Select ID', available_ids)

        available_months = sorted(merged_data['Month'].unique())
        selected_month = st.selectbox('Select Month', available_months)

    # Filter data based on selected month
    filtered_data = merged_data[merged_data['Month'] == selected_month]

    # Aggregate battery readings by date and calculate the average
    battery_data = filtered_data.groupby(filtered_data['Last Signal'].dt.date)['Battery'].mean().reset_index()

    fig_battery = px.line(battery_data, x='Last Signal', y='Battery', title='Battery Reading')
    fig_battery.update_xaxes(title_text='Date')
    fig_battery.update_yaxes(title_text='Average Battery Reading')

    # Aggregate signal strength readings by date and calculate the average
    signal_strength_data = filtered_data.groupby(filtered_data['Last Signal'].dt.date)['Signal'].mean().reset_index()

    fig_signal_strength = px.line(signal_strength_data, x='Last Signal', y='Signal', title='Signal Strength')
    fig_signal_strength.update_xaxes(title_text='Date')
    fig_signal_strength.update_yaxes(title_text='Average Signal Strength')

    # Calculate percentage of 'Battery Modem' errors for each ID in the selected month
    battery_error_percentages = filtered_data.groupby('L1#')['Battery Modem'].apply(lambda x: (x == 'ERROR').mean() * 100).reset_index()
    battery_error_percentages.columns = ['Device', 'Battery Error Percentage']

    # Calculate percentage of 'Signal Strength' errors for each ID in the selected month
    signal_error_percentages = filtered_data.groupby('L1#')['Signal Strength'].apply(lambda x: (x == 'ERROR').mean() * 100).reset_index()
    signal_error_percentages.columns = ['Device', 'Signal Error Percentage']
    
    # Calculate percentage of devices to replace for each ID in the selected month
    replace_percentage = filtered_data.groupby('L1#')['Analysis'].apply(lambda x: (x == 'REPLACE').mean() * 100).reset_index()
    replace_percentage.columns = ['Device', 'Percentage of REPLACE']

    # Merge all calculated percentages into a single DataFrame
    result_df = pd.merge(replace_percentage, battery_error_percentages, on='Device', how='left')
    result_df = pd.merge(result_df, signal_error_percentages, on='Device', how='left')
    
    # Reset the index to start from 1
    result_df.index += 1
    
    st.subheader(f'Devices to Replace along with Error Percentages for {selected_month}')
    st.write(result_df)

    if st.button('Show DataFrame'):
        st.subheader('Filtered Data')
        st.write(filtered_data)

    # Display line graphs horizontally
    st.subheader('Line Graphs')
    col1, col2 = st.columns(2)
    col1.plotly_chart(fig_battery, use_container_width=True)
    col2.plotly_chart(fig_signal_strength, use_container_width=True)

def main():
    st.title('CMS Data Analysis')
    merged_data = pd.DataFrame()
    uploaded_files = st.sidebar.file_uploader("Upload CSV or XLSX Files", accept_multiple_files=True, type=['csv', 'xlsx'], key="file_uploader")
    if uploaded_files:
        merged_data = merge_csv_to_dataframe(uploaded_files)

    if not merged_data.empty:
        display_streamlit_app(merged_data)


if __name__ == "__main__":
    main()
