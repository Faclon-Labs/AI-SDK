import os
import json
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

import constants as c
import io_connect as io

st.set_page_config(
    layout="wide",
    page_title="FaclonLabs-AI-Studio",
    page_icon="https://storage.googleapis.com/ai-workbench/Data%20Import.svg",
)

st.header("This is a sandbox for testing and development purposes.")

USER_ID = "645a159222722a319ca5f5ad"
# USER_ID = st.context.cookies.get("_id", None) # Enable this for production to make the code dynamic for differnet users.

data_access = io.DataAccess(
    user_id=USER_ID,
    data_url=c.DATA_URL,
    ds_url=c.DS_URL,
    log_time=False,
)

devices = data_access.get_device_details()

# Fetch details of all devices from the API.
# Returns:
#    pd.DataFrame: DataFrame containing details of all devices.
#    devID and devType two columns

devices = devices["devID"].tolist()
selected_device = st.selectbox("Select a data source", devices, key="data_source")

if selected_device:

    sensor = data_access.get_device_metadata(device_id=selected_device)
    # Fetch details of all sensors for the selected device.
    # Returns:
    # dict: Metadata for the specified device.

    sensor = pd.DataFrame(sensor.get("sensors"))["sensorId"].tolist()
    selected_sensor = st.multiselect(
        "Select sensors",
        sensor,
        key="sensors",
    )
    st.markdown("**Note: Defaults to all sensors if not selected. **")

    # Fetch details of all sensors from the API.    
    if len(selected_sensor) == 0:
        selected_sensor = None

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        start_date = st.date_input(
            "Select start date",
            value=datetime.now() - timedelta(days=1),
            key="start_date",
        )

    with col2:
        start_time = st.time_input(
            "Select start time",
            value="now",
            key="start_time",
            )
        
    with col3:
        end_date = st.date_input(
            "Select end date",
            value="today",
            key="end_date",
        )

    with col4:
        end_time = st.time_input(
            "Select end time",
            value="now",
            key="end_time",
        )

    start_time_input = f"{start_date} {str(start_time)}"
    end_time_input = f"{end_date} {str(end_time)}"
    
    if st.button("Fetch data", key="fetch_data", use_container_width=True, type="primary"):
        
        st.write("Last Data Points")
        with st.spinner("Fetching last datapoint..."):
            data = data_access.get_dp(
                device_id=selected_device,
                sensor_list=selected_sensor,
                end_time=end_time_input,
            )

        # Retrieve and process data points (DP) from sensors for a given device.
        # Args:
        #    device_id (str): The ID of the device.
        #    sensor_list (Optional[List], optional): List of sensor IDs. If None, all sensors for the device are used.
        #    end_time (Optional[Union[str, int, datetime, np.int64]], optional): The end time for data retrieval.
        #       Defaults to None.
        #    n (int, optional): Number of data points to retrieve. Defaults to 1.
        #    cal (bool, optional): Whether to apply calibration. Defaults to True.
        #    alias (bool, optional): Whether to apply sensor aliasing. Defaults to False.
        #    unix (bool, optional): Whether to return timestamps in Unix format. Defaults to False.
        #    on_prem (Optional[bool], optional): Whether the data source is on-premise.
        #        If None, the default value from the class attribute is used. Defaults to None.

        # Returns:
        #   pd.DataFrame: DataFrame containing retrieved and processed data points.
        st.write(data)

        st.write("Timeseries Data")
        with st.spinner("Fetching timeseries data..."):
            data = data_access.data_query(
                device_id=selected_device,
                sensor_list=selected_sensor,
                start_time=start_time_input,
                end_time=end_time_input,
            )

            # Queries and retrieves sensor data for a given device within a specified time range.

            # Parameters:
            # - device_id (str): The ID of the device.
            # - start_time (Union[str, int, datetime, np.int64]): The start time for the query (can be a string, integer, or datetime).
            # - end_time (Optional[Union[str, int, datetime, np.int64]]): The end time for the query (can be a string, integer, or datetime). Defaults to None.
            # - sensor_list (Optional[List]): List of sensor IDs to query data for. Defaults to all sensors if not provided.
            # - cal (bool): Flag indicating whether to perform calibration on the data. Defaults to True.
            # - alias (bool): Flag indicating whether to use sensor aliases in the DataFrame. Defaults to False.
            # - unix (bool): Flag indicating whether to return timestamps as Unix timestamps. Defaults to False.
            # - on_prem (Optional[bool]): Indicates if the operation is on-premise. Defaults to class attribute if not provided.
            # - parallel (bool): Flag indicating whether to perform parallel processing. Defaults to True.
            # - metadata : Optional[dict], default=None
            #  Additional metadata related to sensors or calibration parameters.

            # Returns:
            # - pd.DataFrame: The DataFrame containing the queried sensor data.
        st.write(data.head(100))
