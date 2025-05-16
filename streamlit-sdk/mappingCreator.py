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
dump_path = "deviceMapping.json"  # Change path as needed

selected_device = st.multiselect("Select a data source", devices, key="data_source")

deviceMapping = {}

if selected_device and st.button("Edit Metadata") and "deviceMapping" not in st.session_state:
    st.session_state.deviceMapping = {}
    for temp_device in selected_device:
        sensor = data_access.get_device_metadata(device_id=temp_device)

        dev_id = sensor.get("devID")
        dev_name = sensor.get("devName")
        sensors = sensor.get("sensors", [])

        st.session_state.deviceMapping[temp_device] = {
            "devID": dev_id,
            "devName": dev_name,
            "description": "",
            "sensors": [
                {"sensorid": s.get("sensorId", ""), "description": s.get("description", ""),  "sensorName": s.get("sensorName", "")}
                for s in sensors
            ]
        }

# Now loop through session_state.deviceMapping to render UI for updates
if "deviceMapping" in st.session_state:
    for dev_id, device_info in st.session_state.deviceMapping.items():
        st.markdown("---")
        st.subheader(f"Device: {device_info['devName']} ({dev_id})")

        # Editable device description
        device_description = st.text_input(
            f"Device Description ({dev_id})",
            value=device_info.get("description", ""),
            key=f"device_desc_{dev_id}"
        )
        st.session_state.deviceMapping[dev_id]["description"] = device_description

        # Editable table for sensors
        updated_sensors = []
        st.markdown("#### Sensors Metadata")
        for i, sensor in enumerate(device_info["sensors"]):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.text(f"{sensor['sensorid']} ({sensor['sensorName']})")
            with col2:
                new_desc = st.text_input(
                    f"Description for {sensor['sensorid']}",
                    value=sensor.get("description", ""),
                    key=f"{dev_id}_sensor_desc_{i}"
                )
            updated_sensors.append({
                "sensorid": sensor["sensorid"],
                "sensorName": sensor["sensorName"],
                "description": new_desc
            })

        # Save updated sensors back
        st.session_state.deviceMapping[dev_id]["sensors"] = updated_sensors

    # Final save button
    if st.button("Save All Changes"):
        with open(dump_path, "w") as f:
            json.dump(st.session_state.deviceMapping, f, indent=4)
        st.success("All metadata saved to deviceMapping.json")
