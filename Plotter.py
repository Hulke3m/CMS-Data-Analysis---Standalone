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

    st.title('CMS Data Analysis')

    st.sidebar.title('CMS Data Analysis Tools')
    unique_key_file_uploader = f"file_uploader_{time.time()}"
    uploaded_files = st.sidebar.file_uploader("Upload CSV Files", key=unique_key_file_uploader, accept_multiple_files=True)

    with st.sidebar.expander("Filter Options", expanded=True):
        available_months = sorted(merged_data['Month'].unique())
        selected_month = st.selectbox('Select Month', available_months)

    # Calculate and display error percentages for all devices
    error_percentage_data = calculate_error_percentages(merged_data, selected_month)
    st.subheader('Error Percentage Table for All Devices')

    # Apply conditional formatting to highlight cells with different colors based on error percentages
    def highlight_errors(val):
        if val > 49:
            return 'background-color: lightcoral'
        elif 2 <= val <= 48:
            return 'background-color: yellow'
        else:
            return ''

    # Apply formatting and highlighting
    error_percentage_data_styled = error_percentage_data.style.applymap(highlight_errors, subset=pd.IndexSlice[:, ['Battery Error Percentage', 'Signal Error Percentage']]).format({'Battery Error Percentage': "{:.2f}%", 'Signal Error Percentage': "{:.2f}%"})

    # Render the styled DataFrame
    st.write(error_percentage_data_styled)

    with st.sidebar.expander("Device Options", expanded=True):
        available_ids = merged_data['L1#'].unique()
        selected_id = st.selectbox('Select ID', available_ids)

    # Filter data based on selected month and ID
    filtered_data = merged_data[(merged_data['L1#'] == selected_id) & (merged_data['Month'] == selected_month)]

    # Display line graphs
    st.subheader('Line Graphs')
    col1, col2 = st.columns(2)
    with col1:
        # Aggregate battery readings by date and calculate the average
        battery_data = filtered_data.groupby(filtered_data['Last Signal'].dt.date)['Battery'].mean().reset_index()

        fig_battery = px.line(battery_data, x='Last Signal', y='Battery', title='Battery Reading')
        fig_battery.update_xaxes(title_text='Date')
        fig_battery.update_yaxes(title_text='Average Battery Reading')
        fig_battery.update_layout(width=800 * 0.5, height=600 * 0.5)
        st.plotly_chart(fig_battery)

    with col2:
        # Aggregate signal strength readings by date and calculate the average
        signal_strength_data = filtered_data.groupby(filtered_data['Last Signal'].dt.date)['Signal'].mean().reset_index()

        fig_signal_strength = px.line(signal_strength_data, x='Last Signal', y='Signal', title='Signal Strength')
        fig_signal_strength.update_xaxes(title_text='Date')
        fig_signal_strength.update_yaxes(title_text='Average Signal Strength')
        fig_signal_strength.update_layout(width=800 * 0.5, height=600 * 0.5)
        st.plotly_chart(fig_signal_strength)

    # Display bar charts
    st.subheader('Bar Charts')
    col3, _, col4 = st.columns((1, 0.5, 1))
    with col3:
        # Aggregate battery modem counts for the selected ID and month
        battery_modem_counts = filtered_data['Battery Modem'].value_counts()
        fig_battery_modem = px.bar(x=battery_modem_counts.index, y=battery_modem_counts.values, title='Battery Modem Counts', labels={'x':'Status', 'y':'Count'}, color=battery_modem_counts.index, color_discrete_map={'OK': 'green', 'ERROR': 'red'})
        fig_battery_modem.update_traces(texttemplate=None, textposition='inside')
        fig_battery_modem.update_layout(width=800 * 0.5, height=600 * 0.5, bargap=0.3) # Adjust bargap here
        st.plotly_chart(fig_battery_modem)

    with col4:
        # Aggregate signal strength counts for the selected ID and month
        signal_strength_counts = filtered_data['Signal Strength'].value_counts()
        fig_signal_strength_counts = px.bar(x=signal_strength_counts.index, y=signal_strength_counts.values, title='Signal Strength Counts', labels={'x':'Status', 'y':'Count'}, color=signal_strength_counts.index, color_discrete_map={'OK': 'green', 'ERROR': 'red'})
        fig_signal_strength_counts.update_traces(texttemplate=None, textposition='inside')
        fig_signal_strength_counts.update_layout(width=800 * 0.5, height=600 * 0.5, bargap=0.3) # Adjust bargap here
        st.plotly_chart(fig_signal_strength_counts)

    if st.button('Show DataFrame'):
        st.subheader('Filtered Data')
        st.write(filtered_data)

def calculate_error_percentages(merged_data, selected_month):
    # Filter data based on selected month
    filtered_data = merged_data[merged_data['Month'] == selected_month]

    # Calculate error percentages for all devices
    error_percentage_data = filtered_data.groupby('L1#')[['Battery Modem', 'Signal Strength']].apply(lambda x: (x == 'ERROR').mean() * 100).reset_index()
    error_percentage_data.columns = ['Device', 'Battery Error Percentage', 'Signal Error Percentage']
    return error_percentage_data

def main():
    merged_data = pd.DataFrame()
    uploaded_files = st.sidebar.file_uploader("Upload CSV or XLSX Files", accept_multiple_files=True, type=['csv', 'xlsx'], key="file_uploader")
    if uploaded_files:
        merged_data = merge_csv_to_dataframe(uploaded_files)

    if not merged_data.empty:
        display_streamlit_app(merged_data)

if __name__ == "__main__":
    main()

