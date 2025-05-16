from datetime import datetime, timezone
from operator import itemgetter

import pandas as pd
import numpy as np
import requests
import urllib3
import pytz
import time
import concurrent.futures
import logging
import io_connect.constants as c
from typing import List, Optional, Union, Tuple, Dict, Literal
from typeguard import typechecked
from io_connect.utilities.store import ERROR_MESSAGE, Logger

from dateutil import parser

# Disable pandas' warning about chained assignment
pd.options.mode.chained_assignment = None

# Disable urllib3's warning about insecure requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@typechecked
class DataAccess:
    __version__ = c.VERSION

    def __init__(
        self,
        user_id: str,
        data_url: str,
        ds_url: str,
        on_prem: Optional[bool] = False,
        tz: Optional[Union[pytz.BaseTzInfo, timezone]] = c.UTC,
        log_time: Optional[bool] = False,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize a DataAccess instance.

        Args:
            user_id (str): The API key or user ID for accessing the API.
            data_url (str): The URL of the data server.
            ds_url (str): The URL of the data source.
            on_prem (Optional[bool], optional): Specifies whether the data server is on-premises. Defaults to False.
            tz (Optional[Union[pytz.BaseTzInfo, timezone]], optional): The timezone for timestamp conversions.
                    Accepts a pytz timezone object or a datetime.timezone object.
                    Defaults to UTC.
        """
        self.user_id = user_id
        self.data_url = data_url
        self.ds_url = ds_url
        self.on_prem = on_prem
        self.tz = tz
        self.log_time = log_time
        self.logger = Logger(logger)

    def get_user_info(self, on_prem: Optional[bool] = None) -> dict:
        """
        Fetches user information from the API.

        Args:
            on_prem (bool, optional): Specifies whether to use on-premises data server. If not provided, uses the class default.

        Returns:
            dict: A dictionary containing user information.

        Example:
            >>> data_access = DataAccess(user_id="my_user_id", data_url="data.url.com", ds_url="example_ds.com")
            >>> user_info = data_access.get_user_info(on_prem=True)
            >>> print(user_info)

        Raises:
            requests.exceptions.RequestException: If an error occurs during the HTTP request, such as a network issue or timeout.
            Exception: If an unexpected error occurs during metadata retrieval, such as parsing JSON data or other unexpected issues.
        """
        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Construct the URL based on the on_prem flag
            protocol = "http" if on_prem else "https"
            url = c.GET_USER_INFO_URL.format(protocol=protocol, data_url=self.data_url)

            with Logger(self.logger, f"API {url} response time:", self.log_time):
                # Make the request
                response = requests.get(
                    url, headers={"userID": self.user_id}, verify=False
                )

            # Check the response status code
            response.raise_for_status()

            # Parse the JSON response
            response_content = response.json()

            if "data" not in response_content:
                raise requests.exceptions.RequestException()

            return response_content["data"]

        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"[EXCEPTION] {type(e).__name__}: {ERROR_MESSAGE(response, url)}"
            )
            return {}

        except (TypeError, ValueError) as e:
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {e}")
            return {}

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return {}

    def get_device_details(self, on_prem: Optional[bool] = None) -> pd.DataFrame:
        """
        Fetch details of all devices from the API.

        Args:
            on_prem (bool, optional): Specifies whether to use on-premises data server. If not provided, uses the class default.

        Returns:
            pd.DataFrame: DataFrame containing details of all devices.

        Example:
            >>> data_access = DataAccess(user_id="my_user_id", data_url="data.url.com", ds_url="example_ds.com")
            >>> device_details_df = data_access.get_device_details(on_prem=True)
            >>> print(device_details_df)

        Raises:
            requests.exceptions.RequestException: If an error occurs during the HTTP request, such as a network issue or timeout.
            Exception: If an unexpected error occurs during metadata retrieval, such as parsing JSON data or other unexpected issues.
        """
        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Construct the URL based on the on_prem flag
            protocol = "http" if on_prem else "https"
            url = c.GET_DEVICE_DETAILS_URL.format(
                protocol=protocol, data_url=self.data_url
            )

            with Logger(self.logger, f"API {url} response time:", self.log_time):
                # Make the request
                response = requests.get(
                    url, headers={"userID": self.user_id}, verify=False
                )

            # Check the response status code
            response.raise_for_status()

            # Parse the JSON response
            response_content = response.json()

            if "data" not in response_content:
                raise requests.exceptions.RequestException()

            # Convert data to DataFrame
            df = pd.DataFrame(response_content["data"])

            return df

        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"[EXCEPTION] {type(e).__name__}: {ERROR_MESSAGE(response, url)}"
            )
            return pd.DataFrame()

        except (TypeError, ValueError) as e:
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {e}")
            return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return pd.DataFrame()

    def get_device_metadata(
        self, device_id: str, on_prem: Optional[bool] = None
    ) -> dict:
        """
        Fetches metadata for a specific device.

        Args:
            device_id (str): The identifier of the device.
            on_prem (bool, optional): Specifies whether to use on-premises data server. If not provided, uses the class default.

        Returns:
            dict: Metadata for the specified device.

        Example:
            >>> data_access = DataAccess(user_id="my_user_id", data_url="data.url.com", ds_url="example_ds.com")
            >>> metadata = data_access.get_device_metadata(device_id="device123", on_prem=True)
            >>> print(metadata)
            {'id': 'device123', 'name': 'Device XYZ', 'location': 'Room A', ...}

        Raises:
            requests.exceptions.RequestException: If an error occurs during the HTTP request, such as a network issue or timeout.
            Exception: If an unexpected error occurs during metadata retrieval, such as parsing JSON data or other unexpected issues.
        """
        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Construct the URL based on the on_prem flag
            protocol = "http" if on_prem else "https"
            url = c.GET_DEVICE_METADATA_URL.format(
                protocol=protocol, data_url=self.data_url, device_id=device_id
            )

            with Logger(self.logger, f"API {url} response time:", self.log_time):
                # Make the request
                response = requests.get(
                    url, headers={"userID": self.user_id}, verify=False
                )

            # Check the response status code
            response.raise_for_status()

            # Parse the JSON response
            response_content = response.json()

            if "data" not in response_content:
                raise requests.exceptions.RequestException()

            return response_content["data"]

        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"[EXCEPTION] {type(e).__name__}: {ERROR_MESSAGE(response, url)}"
            )
            return {}

        except (TypeError, ValueError) as e:
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {e}")
            return {}

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return {}

    def time_to_unix(
        self, time: Optional[Union[str, int, datetime, np.int64]] = None
    ) -> int:
        """
        Convert a given time to Unix timestamp in milliseconds.

        Parameters:
        ----------
        time : Optional[Union[str, int, datetime, np.int64]]
            The time to be converted. It can be a string in ISO 8601 format, a Unix timestamp in milliseconds, or a datetime object.
            If None, the current time in the specified timezone (`self.tz`) is used.

        Returns:
        -------
        int
            The Unix timestamp in milliseconds.

        Raises:
        ------
        ValueError
            If the provided Unix timestamp is not in milliseconds or if there are mismatched offset times between `time` timezone and `self.tz`.

        Notes:
        -----
        - If `time` is not provided, the method uses the current time in the timezone specified by `self.tz`.
        - If `time` is already in Unix timestamp format (in milliseconds), it is validated and returned directly.
        - If `time` is provided as a string, it is parsed into a datetime object.
        - If the datetime object doesn't have timezone information, it is assumed to be in the timezone specified by `self.tz`.
        - The method ensures consistency in timezone information between `time` and `self.tz` before converting to Unix timestamp.
        - Unix timestamps must be provided in milliseconds format (> 10 digits).

        Example:
        -------
        >>> data_access = DataAccess(user_id="my_user_id", data_url="data.url.com", ds_url="example_ds.com")
        >>> unix_time = data_access.time_to_unix('2023-06-14T12:00:00Z')
        >>> print(unix_time)
            1686220800000
        """
        # If time is not provided, use the current time in the specified timezone
        if time is None:
            return int(datetime.now(self.tz).timestamp() * 1000)

        # If time is already in Unix timestamp format
        if isinstance(time, (int, np.int64)):
            if time <= 0 or len(str(time)) <= 10:
                raise ValueError(
                    "Unix timestamp must be a positive integer in milliseconds, not seconds."
                )
            return int(time)

        # If time is in string format, convert it to a datetime object
        if isinstance(time, str):
            time = parser.parse(time, dayfirst=False, yearfirst=True)

        # If the datetime object doesn't have timezone information, assume it's in self.tz timezone
        if time.tzinfo is None:
            if isinstance(self.tz, pytz.BaseTzInfo):
                # If tz is a pytz timezone, localize the datetime
                time = self.tz.localize(time)

            else:
                # If tz is a datetime.timezone object, replace tzinfo
                time = time.replace(tzinfo=self.tz)

        elif self.tz.utcoffset(time.replace(tzinfo=None)) != time.tzinfo.utcoffset(
            time
        ):
            raise ValueError(
                f"Mismatched offset times between time: ({time.tzinfo.utcoffset(time)}) and self.tz:({self.tz.utcoffset(time.replace(tzinfo=None))})"
            )

        # Return datetime object after converting to Unix timestamp
        return int(time.timestamp() * 1000)

    def __get_cleaned_table(
        self,
        df: pd.DataFrame,
        alias: bool,
        cal: bool,
        device_id: str,
        sensor_list: list,
        on_prem: bool,
        unix: bool,
        metadata: Optional[dict] = None,
        pivot_table: Optional[bool] = True,
    ) -> pd.DataFrame:
        """
        Clean and preprocess a DataFrame containing time-series sensor data.

        Parameters:
        ----------
        df : pd.DataFrame
            The input DataFrame containing sensor data with columns 'time', 'sensor', and 'value'.

        alias : bool
            Flag indicating whether to apply sensor aliasing based on device configuration.

        cal : bool
            Flag indicating whether to apply calibration to sensor values.

        device_id : str
            The identifier for the device from which sensor data is collected.

        sensor_list : list
            A list of sensor IDs or names to filter and process from the DataFrame.

        on_prem : bool
            Flag indicating whether the data is retrieved from an on-premises server or not.

        unix : bool
            Flag indicating whether to convert 'time' column to Unix timestamp format in milliseconds.

        metadata : Optional[dict], default=None
            Additional metadata related to sensors or calibration parameters.

        Returns:
        -------
        pd.DataFrame
            A cleaned and preprocessed DataFrame with columns adjusted based on the provided parameters.

        Notes:
        -----
        - The method assumes the input DataFrame (`df`) has columns 'time', 'sensor', and 'value'.
        - It converts the 'time' column to datetime format and sorts the DataFrame by 'time'.
        - The DataFrame is pivoted to have sensors as columns, indexed by 'time'.
        - Sensor list is filtered to include only sensors present in the DataFrame.
        - Calibration (`cal=True`) adjusts sensor values based on calibration parameters fetched from the server.
        - Sensor aliasing (`alias=True`) replaces sensor IDs or names with user-friendly aliases.
        - If `unix=True`, the 'time' column is converted to Unix timestamp format in milliseconds.
        - Timezone conversion is applied to 'time' column if `unix=False`, using the timezone (`self.tz`) specified during class initialization.
        - The method returns the cleaned and processed DataFrame suitable for further analysis or export.

        """

        if pivot_table:
            # Ensure time column is in datetime format
            df["time"] = pd.to_datetime(df["time"], errors="coerce")
            df = df.sort_values("time").reset_index(drop=True)

            # Pivot DataFrame
            df = df.pivot(index="time", columns="sensor", values="value").reset_index(
                drop=False
            )

            # Filter sensor list to include only present sensors
            sensor_list = [sensor for sensor in sensor_list if sensor in df.columns]

        with Logger(self.logger, "Calibration and Alias time:", self.log_time):
            # Apply calibration if required
            if cal:
                df, metadata = self.__get_calibration(
                    device_id=device_id,
                    sensor_list=sensor_list,
                    metadata=metadata,
                    df=df,
                    on_prem=on_prem,
                )

            # Apply sensor alias if required
            if alias:
                df, metadata = self.get_sensor_alias(
                    device_id=device_id,
                    df=df,
                    sensor_list=sensor_list,
                    on_prem=on_prem,
                    metadata=metadata,
                )

        # Convert time to Unix timestamp if required
        if unix:
            df["time"] = (df["time"]).apply(lambda x: int(x.timestamp() * 1000))

        else:
            # Convert time column to timezone
            df["time"] = df["time"].dt.tz_convert(self.tz)

        return df

    def get_sensor_alias(
        self,
        device_id: str,
        df: pd.DataFrame,
        on_prem: Optional[bool] = None,
        sensor_list: Optional[list] = None,
        metadata: Optional[dict] = None,
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Applies sensor aliasing to the DataFrame columns.

        This method retrieves sensor aliases from metadata and renames DataFrame columns
        accordingly, appending the sensor ID to the alias for clarity.

        Args:
            device_id (str): The ID of the device.
            df (pd.DataFrame): DataFrame containing sensor data.
            on_prem (bool): Whether the data is on-premise.
            sensor_list (list): List of sensor IDs.
            metadata (Optional[dict]): Metadata containing sensor information.

        Example:
            >>> data_access = DataAccess(user_id="my_user_id", data_url="data.url.com", ds_url="example_ds.com")
            >>> device_details_df = data_access.get_sensor_alias(df=df,device_id="TEST_DEVICE")
            >>> print(device_details_df)

        Returns:
            pd.DataFrame: DataFrame with renamed columns.
            dict: Updated metadata with sensor information.

        """
        # If on_prem is not provided, use the default value from the class attribute
        if on_prem is None:
            on_prem = self.on_prem

        # If metadata is not provided, fetch it
        if metadata is None:
            metadata = self.get_device_metadata(device_id=device_id, on_prem=on_prem)

        if sensor_list is None:
            sensor_list = df.columns.tolist()

        # Create a dictionary mapping sensor IDs to sensor names
        sensor_map = {
            item["sensorId"]: "{} ({})".format(item["sensorName"], item["sensorId"])
            for item in metadata["sensors"]
            if item["sensorId"] in sensor_list
        }

        # Rename the DataFrame columns using the constructed mapping
        df.rename(columns=sensor_map, inplace=True)

        return df, metadata

    def __get_calibration(
        self,
        device_id: str,
        sensor_list: list,
        df: pd.DataFrame,
        on_prem: bool = False,
        metadata: Optional[dict] = None,
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Applies calibration to sensor data in the DataFrame.

        This method extracts calibration parameters from metadata and applies them to the
        corresponding sensor data in the DataFrame.

        Args:
            device_id (str): The ID of the device.
            sensor_list (list): List of sensor IDs.
            df (pd.DataFrame): DataFrame containing sensor data.
            on_prem (bool): Whether the data is on-premise. Defaults to False.
            metadata (Optional[dict]): Metadata containing calibration parameters.

        Returns:
            pd.DataFrame: DataFrame with calibrated sensor data.
            dict: Updated metadata with calibration information.

        """
        # If metadata is not provided, fetch it
        if metadata is None:
            metadata = self.get_device_metadata(device_id=device_id, on_prem=on_prem)

        # Define default calibration values
        default_values = {"m": 1.0, "c": 0.0, "min": float("-inf"), "max": float("inf")}

        # Extract sensor calibration data from metadata
        data = metadata.get("params", {})

        # Iterate over sensor_list to apply calibration
        for sensor in sensor_list:
            # Extract calibration parameters for the current sensor
            params = {
                param["paramName"]: param["paramValue"]
                for param in data.get(sensor, [])
            }
            cal_values = {}

            # Populate cal_values with extracted parameters or defaults if not available
            for key in default_values:
                try:
                    cal_values[key] = float(params.get(key, default_values[key]))
                except Exception:
                    cal_values[key] = default_values[key]

            # Convert column to numeric
            numeric_col = pd.to_numeric(df[sensor], errors="coerce")

            if cal_values != default_values and not numeric_col.isna().all():
                # Vectorized operation for performance improvement
                df[sensor] = np.clip(
                    cal_values["m"] * numeric_col + cal_values["c"],
                    cal_values["min"],
                    cal_values["max"],
                )

        return df, metadata

    def get_dp(
        self,
        device_id: str,
        sensor_list: Optional[List] = None,
        n: int = 1,
        cal: bool = True,
        end_time: Optional[Union[str, int, datetime, np.int64]] = None,
        alias: bool = False,
        unix: bool = False,
        on_prem: Optional[bool] = None,
    ) -> pd.DataFrame:
        """
        Retrieve and process data points (DP) from sensors for a given device.

        Args:
            device_id (str): The ID of the device.
            sensor_list (Optional[List], optional): List of sensor IDs. If None, all sensors for the device are used.
            end_time (Optional[Union[str, int, datetime, np.int64]], optional): The end time for data retrieval.
                Defaults to None.
            n (int, optional): Number of data points to retrieve. Defaults to 1.
            cal (bool, optional): Whether to apply calibration. Defaults to True.
            alias (bool, optional): Whether to apply sensor aliasing. Defaults to False.
            unix (bool, optional): Whether to return timestamps in Unix format. Defaults to False.
            on_prem (Optional[bool], optional): Whether the data source is on-premise.
                If None, the default value from the class attribute is used. Defaults to None.

        Returns:
            pd.DataFrame: DataFrame containing retrieved and processed data points.

        Example:
            >>> data_access = DataAccess(user_id="my_user_id", data_url="data.url.com", ds_url="example_ds.com")
            >>> df = data_access.get_dp("XYZ",sensor_list= ['X'],n=1,alias=True,cal=True,end_time=1685767732710,unix=False)
            >>> print(df)

        Raises:
            ValueError: If parameter 'n' is less than 1.
            Exception: If no sensor data is available.
            Exception: If max retries for data fetching from api-layer are exceeded.
            TypeError: If an unexpected type error occurs during execution.
            requests.exceptions.RequestException: If an error occurs during HTTP request.
            Exception: For any other unexpected exceptions raised during execution.

        """
        try:
            metadata = None

            # Validate input parameters
            if n < 1:
                raise ValueError("Parameter 'n' must be greater than or equal to 1")

            df_devices = self.get_device_details(on_prem=on_prem)

            # Check if the device is added in the account
            if device_id not in df_devices["devID"].values:
                raise Exception(f"Message: Device {device_id} not added in account")

            # Fetch metadata if sensor_list is not provided
            if sensor_list is None:
                metadata = self.get_device_metadata(device_id, on_prem)
                sensor_list = list(map(itemgetter("sensorId"), metadata["sensors"]))

            # Ensure sensor_list is not empty
            if not sensor_list:
                raise Exception("No sensor data available.")

            # Convert end_time to Unix timestamp
            end_time = self.time_to_unix(end_time)

            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem
            protocol = "http" if on_prem else "https"

            # Construct API URL for data retrieval
            url = c.GET_DP_URL.format(protocol=protocol, data_url=self.data_url)

            df = pd.DataFrame()

            retry = 0
            with Logger(self.logger, "Total Data Polling time:", self.log_time):
                for sensor in sensor_list:
                    cursor = {"end": end_time, "limit": n}

                    while cursor["end"]:
                        try:
                            params = {
                                "device": device_id,
                                "sensor": sensor,
                                "eTime": cursor["end"],
                                "lim": cursor["limit"],
                                "cursor": "true",
                            }
                            with Logger(
                                self.logger, f"API {url} response time:", self.log_time
                            ):
                                # Make the API request
                                response = requests.get(url, params=params)

                            # Check the response status code
                            response.raise_for_status()

                            # Parse the JSON response
                            response_content = response.json()

                            # Check for errors in the API response
                            if "success" in response_content:
                                raise requests.exceptions.RequestException()

                            data = response_content["data"]

                            df = pd.concat([df, pd.DataFrame(data)])

                            cursor = response_content["cursor"]

                        except Exception as e:
                            retry += 1
                            self.logger.error(
                                f"[{type(e).__name__}] Retry Count: {retry}, {e}"
                                + ERROR_MESSAGE(response, url)
                            )

                            # Retry with exponential backoff
                            if retry < c.MAX_RETRIES:
                                sleep_time = (
                                    c.RETRY_DELAY[1] if retry > 5 else c.RETRY_DELAY[0]
                                )
                                time.sleep(sleep_time)
                            else:
                                raise Exception(
                                    "Max retries for data fetching from api-layer exceeded."
                                    + ERROR_MESSAGE(response, url)
                                )

            # Process retrieved data if DataFrame is not empty
            if not df.empty:
                df = self.__get_cleaned_table(
                    df=df,
                    alias=alias,
                    cal=cal,
                    device_id=device_id,
                    sensor_list=sensor_list,
                    on_prem=on_prem,
                    unix=unix,
                    metadata=metadata,
                )

            return df

        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"[EXCEPTION] {type(e).__name__}: {ERROR_MESSAGE(response, url)}"
            )
            return pd.DataFrame()

        except (TypeError, ValueError) as e:
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {e}")
            return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return pd.DataFrame()

    def get_firstdp(
        self,
        device_id: str,
        sensor_list: Optional[List] = None,
        cal: bool = True,
        start_time: Union[str, int, datetime, np.int64] = None,
        n: Optional[int] = 1,
        alias: bool = False,
        unix: bool = False,
        on_prem: Optional[bool] = None,
    ) -> pd.DataFrame:
        """
        Fetches the first data point after a specified start time for a given device and sensor list.

        Parameters:
        - start_time (Union[str, int, datetime, np.int64]): The start time for the query (can be a string, integer, or datetime).
        - device_id (str): The ID of the device.
        - sensor_list (Optional[List]): List of sensor IDs to query data for. Defaults to all sensors if not provided.
        - n (Optional[int]): Number of data points to retrieve. Defaults to 1.
        - cal (bool): Flag indicating whether to perform calibration on the data. Defaults to True.
        - alias (bool): Flag indicating whether to use sensor aliases in the DataFrame. Defaults to False.
        - unix (bool): Flag indicating whether to return timestamps as Unix timestamps. Defaults to False.
        - on_prem (Optional[bool]): Indicates if the operation is on-premise. Defaults to class attribute if not provided.

        Returns:
        - pd.DataFrame: The DataFrame containing the retrieved data points.

        Example:
            >>> data_access = DataAccess(user_id="my_user_id", data_url="data.url.com", ds_url="example_ds.com")
            >>> df = data_access.get_firstdp(device_id="XYZ",sensor_list= ['X'],alias=True,cal=True,start_time=1685767732710,unix=False)
            >>> print(df)

        Exceptions Handled:
        - TypeError: Raised when there is a type mismatch in the input parameters.
        - requests.exceptions.RequestException: Raised when there is an issue with the HTTP request.
        - Exception: General exception handling for other errors.
        """
        try:
            # Validate input parameters
            if n < 1:
                raise ValueError("Parameter 'n' must be greater than or equal to 1")

            df_devices = self.get_device_details(on_prem=on_prem)

            # Check if the device is added in the account
            if device_id not in df_devices["devID"].values:
                raise Exception(f"Message: Device {device_id} not added in account")

            metadata = None
            # Fetch metadata if sensor_list is not provided
            if sensor_list is None:
                metadata = self.get_device_metadata(device_id, on_prem)
                sensor_list = list(map(itemgetter("sensorId"), metadata["sensors"]))

            # Ensure sensor_list is not empty
            if not sensor_list:
                raise Exception("No sensor data available.")

            # Convert end_time to Unix timestamp
            start_time = self.time_to_unix(start_time)

            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem
            protocol = "http" if on_prem else "https"

            # Construct API URL for data retrieval
            url = c.GET_FIRST_DP.format(protocol=protocol, data_url=self.data_url)

            sensor_values = ",".join(sensor_list)

            df = pd.DataFrame()

            params = {
                "device": device_id,
                "sensor": sensor_values,
                "time": start_time // 1000,
            }
            with Logger(self.logger, f"API {url} response time:", self.log_time):
                # Make the API request
                response = requests.get(url, params=params)

            # Check the response status code
            response.raise_for_status()

            # Parse the JSON response
            response_content = response.json()

            # Check for errors in the API response
            if "success" in response_content:
                raise ValueError(ERROR_MESSAGE(response, url))

            data = response_content[0]
            # Initialize an empty list to hold formatted data
            formatted_data = []

            # Check the structure of the data and format accordingly
            for sensor_data in data.values():
                if isinstance(sensor_data, dict):
                    formatted_data.append(
                        {
                            "time": sensor_data["time"],
                            "sensor": sensor_data["sensor"],
                            "value": sensor_data["value"],
                        }
                    )
                elif isinstance(sensor_data, list):
                    formatted_data.extend(
                        [
                            {
                                "time": entry["time"],
                                "sensor": entry["sensor"],
                                "value": entry["value"],
                            }
                            for entry in sensor_data
                        ]
                    )

            # Create DataFrame
            df = pd.DataFrame(formatted_data)

            # Process retrieved data if DataFrame is not empty
            if not df.empty:
                df = self.__get_cleaned_table(
                    df=df,
                    alias=alias,
                    cal=cal,
                    device_id=device_id,
                    sensor_list=sensor_list,
                    on_prem=on_prem,
                    unix=unix,
                    metadata=metadata,
                )
            return df

        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"[EXCEPTION] {type(e).__name__}: {ERROR_MESSAGE(response, url)}"
            )
            return pd.DataFrame()

        except (TypeError, ValueError) as e:
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {e}")
            return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return pd.DataFrame()

    def data_query(
        self,
        device_id: str,
        sensor_list: Optional[List] = None,
        start_time: Union[str, int, datetime, np.int64] = None,
        end_time: Optional[Union[str, int, datetime, np.int64]] = None,
        cal: bool = True,
        alias: bool = False,
        unix: bool = False,
        on_prem: Optional[bool] = None,
        parallel: bool = False,
    ) -> pd.DataFrame:
        """
        Queries and retrieves sensor data for a given device within a specified time range.

        Parameters:
        - device_id (str): The ID of the device.
        - start_time (Union[str, int, datetime, np.int64]): The start time for the query (can be a string, integer, or datetime).
        - end_time (Optional[Union[str, int, datetime, np.int64]]): The end time for the query (can be a string, integer, or datetime). Defaults to None.
        - sensor_list (Optional[List]): List of sensor IDs to query data for. Defaults to all sensors if not provided.
        - cal (bool): Flag indicating whether to perform calibration on the data. Defaults to True.
        - alias (bool): Flag indicating whether to use sensor aliases in the DataFrame. Defaults to False.
        - unix (bool): Flag indicating whether to return timestamps as Unix timestamps. Defaults to False.
        - on_prem (Optional[bool]): Indicates if the operation is on-premise. Defaults to class attribute if not provided.
        - parallel (bool): Flag indicating whether to perform parallel processing. Defaults to True.
        - metadata : Optional[dict], default=None
            Additional metadata related to sensors or calibration parameters.

        Returns:
        - pd.DataFrame: The DataFrame containing the queried sensor data.

        Example:
            >>> data_access = DataAccess(user_id="my_user_id", data_url="data.url.com", ds_url="example_ds.com")
            >>> df = data_access.data_query("XYZ",sensor_list = ["X","Y"],end_time=1717419975210,start_time=1685767732000,alias=True)
            >>> print(df)

        Exceptions Handled:
        - TypeError: Raised when there is a type mismatch in the input parameters.
        - requests.exceptions.RequestException: Raised when there is an issue with the HTTP request.
        - Exception: General exception handling for other errors.
        """
        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Convert start_time and end_time to Unix timestamps
            start_time_unix = self.time_to_unix(start_time)
            end_time_unix = self.time_to_unix(end_time)

            # Validate that the start time is before the end time
            if end_time_unix < start_time_unix:
                raise ValueError(
                    f"Invalid time range: start_time({start_time}) should be before end_time({end_time})."
                )

            #  Initialise the df
            df = pd.DataFrame()

            # Check if the device is added in the account
            df_devices = self.get_device_details(on_prem=on_prem)
            if device_id not in df_devices["devID"].values:
                raise Exception(f"Message: Device {device_id} not added in account")

            metadata = None
            # Fetch metadata if sensor_list is not provided
            if sensor_list is None:
                metadata = self.get_device_metadata(device_id, on_prem)
                sensor_list = list(map(itemgetter("sensorId"), metadata["sensors"]))

            # Ensure sensor_list is not empty
            if not sensor_list:
                raise Exception("No sensor data available.")

            if parallel:
                payload = self.get_cursor_batches(
                    device_id=device_id,
                    start_time=start_time_unix,
                    end_time=end_time_unix,
                    sensor_list=sensor_list,
                    on_prem=on_prem,
                    metadata=metadata,
                )

                # Fetch from influx API in case of an error raised from get_cursor_batches
                if len(payload) == 0:
                    # Fetch and process data from InfluxDB through single request
                    df = self.__influxdb(
                        device_id=device_id,
                        sensor_list=sensor_list,
                        start_time=start_time_unix,
                        end_time=end_time_unix,
                        on_prem=on_prem,
                        metadata=metadata,
                        alias=alias,
                        cal=cal,
                        unix=unix,
                    )
                elif len(payload["counts"]) == 0:
                    df = pd.DataFrame()
                else:
                    results = []
                    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                        futures = [
                            executor.submit(
                                self.__influxdb,
                                device_id=device_id,
                                start_time=time_range["firstDPTime"],
                                end_time=time_range["lastDPTime"],
                                sensor_list=sensor_list,
                                alias=alias,
                                cal=cal,
                                unix=unix,
                                on_prem=on_prem,
                                metadata=metadata,
                            )
                            for time_range in payload["timeStamps"]
                        ]

                        # Collect results as they complete
                        for future in concurrent.futures.as_completed(futures):
                            results.append(future.result())

                    df = pd.concat(results, ignore_index=True)
                    df = df.sort_values(by="time").reset_index(drop=True)
                    df = df.drop_duplicates()

            else:
                # Fetch and process data from InfluxDB
                df = self.__influxdb(
                    device_id=device_id,
                    sensor_list=sensor_list,
                    start_time=start_time_unix,
                    end_time=end_time_unix,
                    on_prem=on_prem,
                    metadata=metadata,
                    alias=alias,
                    cal=cal,
                    unix=unix,
                )

            return df

        except (TypeError, ValueError, requests.exceptions.RequestException) as e:
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {e}")
            return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return pd.DataFrame()

    def __influxdb(
        self,
        device_id: str,
        start_time: int,
        end_time: int,
        alias: bool,
        cal: bool,
        unix: bool,
        sensor_list: Optional[List] = None,
        metadata: Optional[dict] = None,
        on_prem: Optional[bool] = None,
    ) -> pd.DataFrame:
        """
        Fetches and processes data from the InfluxDB based on the provided parameters.

        Parameters:
        - device_id (str): The ID of the device.
        - start_time (int): The start time for data retrieval (Unix timestamp).
        - end_time (int): The end time for data retrieval (Unix timestamp).
        - alias (bool): Whether to use sensor aliases in the DataFrame.
        - cal (bool): Whether to perform calibration on the data.
        - unix (bool): Whether to return timestamps as Unix timestamps.
        - sensor_list (Optional[List]): List of sensor IDs to retrieve data for. Defaults to all sensors if not provided.
        - on_prem (Optional[bool]): Indicates if the operation is on-premise. Defaults to class attribute if not provided.

        Returns:
        - pd.DataFrame: The DataFrame containing the fetched and processed data.
        """

        # Fetch metadata if sensor_list is not provided
        if sensor_list is None:
            if metadata is None:
                metadata = self.get_device_metadata(device_id, on_prem)
            sensor_list = list(map(itemgetter("sensorId"), metadata["sensors"]))

        # Ensure sensor_list is not empty
        if not sensor_list:
            raise Exception("No sensor data available.")

        df = pd.DataFrame()

        # Determine the protocol based on the on_prem flag
        protocol = "http" if on_prem else "https"

        # Construct API URL for data retrieval
        url = c.INFLUXDB_URL.format(protocol=protocol, data_url=self.data_url)

        # Initialize cursor for data retrieval
        cursor = {"start": start_time, "end": end_time}

        sensor_values = ",".join(sensor_list)
        retry = 0

        with Logger(self.logger, "Total Data Polling time:", self.log_time):
            while cursor["start"] and cursor["end"]:
                try:
                    # Set the request parameters
                    params = {
                        "device": device_id,
                        "sensor": sensor_values,
                        "sTime": cursor["start"],
                        "eTime": cursor["end"],
                        "cursor": "true",
                        "limit": c.CURSOR_LIMIT,
                    }

                    with Logger(
                        self.logger, f"API {url} response time:", self.log_time
                    ):
                        # Make the API request
                        response = requests.get(url, params=params)

                    # Check the response status code
                    response.raise_for_status()

                    # Parse the response JSON
                    response_content = response.json()

                    # Check for errors in the API response
                    if "success" in response_content:
                        raise requests.exceptions.RequestException()

                    data = response_content["data"]
                    cursor = response_content["cursor"]

                    # Append the fetched data to the DataFrame
                    df = pd.concat([df, pd.DataFrame(data)])

                    self.logger.display_log(f"[INFO] {len(df)} data points fetched.")

                except Exception as e:
                    retry += 1
                    self.logger.error(
                        f"[{type(e).__name__}] Retry Count: {retry}, {e}"
                        + ERROR_MESSAGE(response, url)
                    )

                    # Retry with exponential backoff
                    if retry < c.MAX_RETRIES:
                        sleep_time = c.RETRY_DELAY[1] if retry > 5 else c.RETRY_DELAY[0]
                        time.sleep(sleep_time)
                    else:
                        raise Exception(
                            "Max retries for data fetching from api-layer exceeded."
                            + ERROR_MESSAGE(response, url)
                        )

        # Process the DataFrame if it's not empty
        if not df.empty:
            self.logger.info("")
            df = self.__get_cleaned_table(
                df=df,
                alias=alias,
                cal=cal,
                device_id=device_id,
                sensor_list=sensor_list,
                on_prem=on_prem,
                unix=unix,
                metadata=metadata,
            )

        return df

    def consumption(
        self,
        device_id: str,
        sensor: str,
        interval: Optional[int] = None,
        start_time: Union[str, int, datetime, np.int64] = None,
        end_time: Optional[Union[str, int, datetime, np.int64]] = None,
        cal: bool = True,
        alias: bool = False,
        unix: bool = False,
        on_prem: Optional[bool] = None,
        disable_interval: bool = False,
    ) -> pd.DataFrame:
        """
        Fetch consumption data for a specified device and sensor within a given time range.

        This method retrieves consumption data for a device's sensor, applies optional calibration
        and alias adjustments, handles time conversion (Unix or datetime), and supports custom intervals
        for data aggregation. Data is retrieved via an API call, with a retry mechanism to handle potential failures.

        Args:
        - device_id (str): The unique identifier for the device.
        - sensor (str): The name of the sensor for which data is to be retrieved.
        - interval (int, optional): Custom time interval (in seconds) for data aggregation. Defaults to None.
        - start_time (Union[str, int, datetime, np.int64], optional): The start time of the data retrieval period.
          Can be provided as a string, integer timestamp, or datetime object.
        - end_time (Union[str, int, datetime, np.int64], optional): The end time of the data retrieval period.
          Can be provided as a string, integer timestamp, or datetime object.
        - cal (bool, optional): If True, applies calibration adjustments to the sensor data. Defaults to True.
        - alias (bool, optional): If True, applies sensor alias mapping. Defaults to False.
        - unix (bool, optional): If True, output times are in Unix milliseconds. Defaults to False (returns datetime).
        - on_prem (bool, optional): Overrides on-premises data access. If None, uses the default instance attribute.
          Defaults to None.
        - disable_interval (bool, optional): Disables custom interval and uses the default data frequency. Defaults to False.

        Returns:
        - pd.DataFrame: A DataFrame containing the time and sensor values within the specified time range.

        Raises:
        - ValueError: If the provided `start_time` is later than the `end_time`.
        - Exception: If the device is not found in the user's account or if maximum retries for data fetching are exceeded.
        - requests.exceptions.RequestException: For issues with the HTTP request to fetch the data.

        Example:
            >>> data_access = DataAccess(user_id="my_user_id", data_url="data.url.com", ds_url="example_ds.com")
            >>> df = data_access.consumption("XYZ", sensor="D99", end_time=1720308782000, start_time=1719790382000, alias=True, cal=True, unix=False)

        Notes:
        - A retry mechanism is implemented with exponential backoff. If data fetching fails after
          exceeding the maximum number of retries (`c.MAX_RETRIES`), an exception is raised.
        - Timestamps are internally converted to Unix milliseconds for API compatibility unless
          `unix=False`, in which case timestamps are converted back to datetime with the appropriate timezone.
        - If the `cal` flag is set, calibration data is applied based on the device and sensor metadata.
        - The `alias` flag allows applying a sensor alias mapping to the data, based on predefined sensor aliases.

        """
        try:
            metadata = None
            time_stamp = {}

            # Convert start_time and end_time to Unix timestamps
            time_stamp["startTime"] = self.time_to_unix(start_time)
            time_stamp["endTime"] = self.time_to_unix(end_time)

            # Validate that the start time is before the end time
            if time_stamp["endTime"] < time_stamp["startTime"]:
                raise ValueError(
                    f"Invalid time range: start_time({start_time}) should be before end_time({end_time})."
                )

            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem
            protocol = "http" if on_prem else "https"

            # Fetch device details to verify if the device exists in the account
            df_devices = self.get_device_details(on_prem=on_prem)

            # Check if the device is added in the account
            if device_id not in df_devices["devID"].values:
                raise Exception(f"Message: Device {device_id} not added in account")

            # Construct API URL for data retrieval
            url = c.CONSUMPTION_URL.format(protocol=protocol, data_url=self.data_url)

            retry = 0
            payload = {
                "device": device_id,
                "sensor": sensor,
                "startTime": time_stamp["startTime"],
                "endTime": time_stamp["endTime"],
                "disableThreshold": str(disable_interval).lower(),
            }

            if not disable_interval:
                payload["interval"] = interval

            # Retry mechanism for fetching data from API
            while True:
                try:
                    with Logger(
                        self.logger, f"API {url} response time:", self.log_time
                    ):
                        # Make the API request
                        response = requests.get(url, params=payload)

                    response.raise_for_status()

                    # Parse the JSON response
                    response_data = response.json()

                    if "errors" in response_data:
                        raise ValueError()

                    break

                except Exception as e:
                    retry += 1
                    self.logger.error(
                        f"[{type(e).__name__}] Retry Count: {retry}, {e}"
                        + ERROR_MESSAGE(response, url)
                    )
                    if retry < c.MAX_RETRIES:
                        sleep_time = c.RETRY_DELAY[1] if retry > 5 else c.RETRY_DELAY[0]
                        time.sleep(sleep_time)
                    else:
                        raise Exception(
                            "Max retries for data fetching from api-layer exceeded."
                            + ERROR_MESSAGE(response, url)
                        )

            # Initialize lists to store time and sensor values
            time_list = []
            sensor_list = []

            # Iterate through the dictionary to populate the lists
            for key, value in response_data.items():
                if isinstance(value, dict):
                    time_list.append(value.get("time", time_stamp[key]))
                    sensor_list.append(value.get("value", np.nan))
                else:
                    time_list.append(time_stamp[key])
                    sensor_list.append(np.nan)

            # Create the DataFrame
            df = pd.DataFrame({"time": time_list, sensor: sensor_list})

            # Process the DataFrame if it's not empty
            if not df.empty:
                # Ensure time column is in datetime format
                df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)

                df = self.__get_cleaned_table(
                    df=df,
                    alias=alias,
                    cal=cal,
                    device_id=device_id,
                    sensor_list=[sensor],
                    on_prem=on_prem,
                    unix=unix,
                    metadata=metadata,
                    pivot_table=False,
                )

            return df

        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"[EXCEPTION] {type(e).__name__}: {ERROR_MESSAGE(response, url)}"
            )
            return pd.DataFrame()

        except (TypeError, ValueError) as e:
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {e}")
            return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return pd.DataFrame()

    def get_load_entities(
        self, on_prem: Optional[bool] = None, clusters: Optional[list] = None
    ) -> list:
        """
        Fetches load entities from an API, handling pagination and optional filtering by cluster names.

        Args:
            on_prem (Optional[bool]): Specifies whether to use on-premise settings for the request.
                                      Defaults to None, which uses the class attribute `self.on_prem`.
            clusters (Optional[list]): A list of cluster names to filter the results by.
                                       Defaults to None, which returns all clusters.

        Returns:
            list: A list of load entities. If clusters are provided, only entities belonging to the specified clusters are returned.

        Raises:
            Exception: If no clusters are provided or if the maximum retry limit is reached.
            TypeError, ValueError, requests.exceptions.RequestException: For other request-related exceptions.

        Example:
            >>> data_access = DataAccess(user_id="my_user_id", data_url="data.url.com", ds_url="example_ds.com")

            >>> # Fetch all load entities using on-premise settings
            >>> all_entities = data_access.get_load_entities()

            >>> # Fetch load entities and filter by specific cluster names
            >>> specific_clusters = data_access.get_load_entities(clusters=["cluster1", "cluster2"])

            >>> # Fetch load entities using on-premise settings, but no specific clusters
            >>> on_prem_entities = data_access.get_load_entities(on_prem=True)

        """
        try:
            # Validate clusters input
            if clusters is not None and len(clusters) == 0:
                raise Exception("No clusters provided.")
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem
            protocol = "http" if on_prem else "https"

            page_count = 1
            cluster_count = None
            retry = 0

            result = []

            # Construct API URL for data retrieval
            url = c.GET_LOAD_ENTITIES.format(
                protocol=protocol,
                data_url=self.data_url,
            )
            headers = {"userID": self.user_id}

            while True:
                try:
                    with Logger(
                        self.logger, f"API {url} response time:", self.log_time
                    ):
                        response = requests.get(
                            url + f"/{self.user_id}/{page_count}/{cluster_count}",
                            headers=headers,
                            verify=False,
                        )

                    # Check the response status code
                    response.raise_for_status()

                    # Parse the JSON response
                    response_data = response.json()
                    if "error" in response_data:
                        self.logger.error(ERROR_MESSAGE(response, url))
                        return []

                    # Extend result with retrieved response_data
                    result.extend(response_data["data"])

                    total_count = response_data["totalCount"]
                    clusters_recieved = len(result)

                    # Break the loop if all clusters have been received
                    if clusters_recieved == total_count:
                        break

                    # Update for next page
                    page_count += 1
                    cluster_count = total_count - clusters_recieved

                except Exception as e:
                    retry += 1
                    self.logger.error(
                        f"[{type(e).__name__}] Retry Count: {retry}, {e}"
                        + ERROR_MESSAGE(response, url)
                    )
                    if retry < c.MAX_RETRIES:
                        sleep_time = c.RETRY_DELAY[1] if retry > 5 else c.RETRY_DELAY[0]
                        time.sleep(sleep_time)
                    else:
                        raise Exception(
                            "Max retries for data fetching from api-layer exceeded."
                            + ERROR_MESSAGE(response, url)
                        )
            # Filter results by cluster names if provided
            if clusters is not None:
                return [item for item in result if item["name"] in clusters]

            return result

        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"[EXCEPTION] {type(e).__name__}: {ERROR_MESSAGE(response, url)}"
            )
            return []

        except (TypeError, ValueError) as e:
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {e}")
            return []

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return []

    def trigger_paramter(
        self, title_list: list, on_prem: Optional[bool] = None
    ) -> list:
        """
        Triggers a parameter-based operation on the server by sending a list of titles.

        This method sends a request to the API with the provided list of titles, triggering
        a server-side operation. The method retries in case of failure, up to a maximum retry limit.

        Args:
            title_list (list): A list of titles to be used for triggering the operation.
            on_prem (bool, optional): Whether the operation is performed on-premises.
                If not provided, the class attribute value is used.

        Returns:
            list: The data returned from the server after triggering the operation, or an empty list in case of an error.

        Raises:
            Exception: If the maximum retries for data fetching are exceeded.
            ValueError: If there is an issue with the input values.

        Example usage:

        ```python
        data_access = DataAccess(user_id="my_user_id", data_url="data.url.com", ds_url="example_ds.com")

        # Example: Trigger a parameter operation with a list of titles
        result = data_access.trigger_paramter(
            title_list=["Title1", "Title2", "Title3"]
        )
        ```
        """
        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem
            protocol = "http" if on_prem else "https"

            # Construct API URL for data retrieval
            url = c.TRIGGER_URL.format(
                protocol=protocol,
                data_url=self.data_url,
            )
            retry = 0

            headers = {"Content-Type": "application/json"}

            payload = {"userID": self.user_id, "title": title_list}
            while True:
                try:
                    with Logger(
                        self.logger, f"API {url} response time:", self.log_time
                    ):
                        response = requests.put(url, headers=headers, json=payload)

                    # Check the response status code
                    response.raise_for_status()

                    # Parse the JSON response
                    response_data = response.json()

                    if "error" in response_data:
                        raise ValueError()

                    break

                except Exception as e:
                    retry += 1
                    self.logger.error(
                        f"[{type(e).__name__}] Retry Count: {retry}, {e}"
                        + ERROR_MESSAGE(response, url)
                    )
                    if retry < c.MAX_RETRIES:
                        sleep_time = c.RETRY_DELAY[1] if retry > 5 else c.RETRY_DELAY[0]
                        time.sleep(sleep_time)
                    else:
                        raise Exception(
                            "Max retries for data fetching from api-layer exceeded."
                            + ERROR_MESSAGE(response, url)
                        )

            return response_data["data"]

        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"[EXCEPTION] {type(e).__name__}: {ERROR_MESSAGE(response, url)}"
            )
            return []

        except (TypeError, ValueError) as e:
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {e}")
            return []

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return []

    def get_filtered_operation_data(
        self,
        device_id: str,
        sensor_list: Optional[list] = None,
        operation: Optional[Literal["min", "max", "last", "first"]] = None,
        filter_operator: Optional[
            Literal[">", "<", "<=", ">=", "!=", "==", "><", "<>"]
        ] = None,
        threshold: Optional[str] = None,
        start_time: Union[str, int, datetime, np.int64] = None,
        end_time: Optional[Union[str, int, datetime, np.int64]] = None,
        df: Optional[pd.DataFrame] = None,
        cal: bool = True,
        alias: bool = False,
        unix: bool = False,
        on_prem: Optional[bool] = None,
    ) -> pd.DataFrame:
        """
        Retrieves filtered operation data for a specific device over a specified time range.

        This method fetches sensor data by communicating with a data API, applying various
        operations like min, max, first, last, or filter operators with thresholds, and returns
        the data in a cleaned DataFrame format.

        Args:
            device_id (str): The ID of the device for which data is to be fetched.
            sensor_list (list, optional): List of sensors to retrieve data from. Defaults to None.
            operation (Literal["min", "max", "last", "first"], optional): Operation to apply to the data.
            filter_operator (Literal[">", "<", "<=", ">=", "!=", "==", "><", "<>"], optional): Filter operator.
            threshold (str, optional): Threshold value for filtering sensor data.
            start_time (Union[str, int, datetime, np.int64]): The start time for data retrieval.
            end_time (Union[str, int, datetime, np.int64], optional): The end time for data retrieval.
            df (pd.DataFrame, optional): A DataFrame containing sensor configurations (sensor, operation, filter_operator, threshold).
            cal (bool, optional): Whether to apply calibration to the data. Default is True.
            alias (bool, optional): Whether to return sensor names as aliases. Default is False.
            unix (bool, optional): Whether to return time in Unix format. Default is False.
            on_prem (bool, optional): Whether to fetch data from an on-premises system. If None, uses class-level setting.

        Returns:
            pd.DataFrame: A DataFrame containing the retrieved sensor data, or an empty DataFrame if an error occurs.

        Raises:
            ValueError: If time ranges are invalid, columns in the DataFrame are missing or inconsistent, or if operations or filters are not properly set.
            Exception: If the device is not found in the account, or if the maximum retries for data fetching are exceeded.

        Example usage:

        ```python
        data_access = DataAccess(user_id="my_user_id", data_url="data.url.com", ds_url="example_ds.com")

        # Example 1: Fetch the minimum value for sensors on device 'device_123' between two timestamps
        df = data_access.get_filtered_operation_data(
            device_id="device_123",
            sensor_list=["sensor_1", "sensor_2"],
            operation="min",
            start_time="2024-09-01T00:00:00Z",
            end_time="2024-09-10T23:59:59Z"
        )

        # Example 2: Fetch data using a DataFrame with sensors, operations, and filters
        import pandas as pd

        sensor_df = pd.DataFrame({
            "sensor": ["sensor_1", "sensor_2"],
            "operation": ["last", "max"],
            "filter_operator": [">", "<"],
            "threshold": ["50", "100"]
        })

        df_filtered = data_access.get_filtered_operation_data(
            device_id="device_123",
            df=sensor_df,
            start_time=1693771200,  # Unix timestamp
            end_time=1694359200  # Unix timestamp
        )
        ```
        """
        try:
            metadata = None

            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem
            protocol = "http" if on_prem else "https"

            # Convert start_time and end_time to Unix timestamps
            start_time_unix = self.time_to_unix(start_time)
            end_time_unix = self.time_to_unix(end_time)

            # Validate that the start time is before the end time
            if end_time_unix < start_time_unix:
                raise ValueError(
                    f"Invalid time range: start_time({start_time}) should be before end_time({end_time})."
                )
            df_devices = self.get_device_details(on_prem=on_prem)

            # Check if the device is added in the account
            if device_id not in df_devices["devID"].values:
                raise Exception(f"Message: Device {device_id} not added in account")

            # Initialize the request body with userID, startTime, and endTime
            request_body = {
                "userID": self.user_id,
                "startTime": start_time_unix,
                "endTime": end_time_unix,
                "devConfig": [],
            }

            if df is not None:
                # Check if all required columns are present in the DataFrame
                required_columns = {"sensor", "operation"}
                if not required_columns.issubset(df.columns):
                    raise ValueError(
                        f"DataFrame must contain the following columns: {required_columns}"
                    )

                # Check for duplicates in the 'sensor' column
                if df["sensor"].duplicated().any():
                    raise ValueError(
                        "Duplicate values detected in the 'sensor' column. Please ensure all sensor entries are unique."
                    )

                # Check if filter_operator and threshold columns are both present or both absent
                if ("filter_operator" in df.columns) != ("threshold" in df.columns):
                    raise ValueError(
                        "Both 'filter_operator' and 'threshold' columns must be present together or not at all."
                    )
                elif ("filter_operator" in df.columns) and ("threshold" in df.columns):
                    if not all(
                        df["filter_operator"].notna() == df["threshold"].notna()
                    ):
                        raise ValueError(
                            "Inconsistent null values: If 'filter_operator' is present in a row, 'threshold' must also be present in that row, and vice versa."
                        )

                sensor_list = []
                # Replace np.nan with None
                df = df.replace({np.nan: None})

                # Iterate through each row in the DataFrame to build the request body
                for _, row in df.iterrows():
                    sensor_list.append(row["sensor"])
                    # Basic sensor configuration with mandatory fields
                    sensor_config = {
                        "devID": device_id,
                        "sensorID": row["sensor"],
                        "operation": row["operation"],
                    }

                    # Conditionally add filter_operator and threshold if they are present and not empty
                    filter_operator = row.get("filter_operator", None)
                    threshold = row.get("threshold", None)

                    if pd.notna(filter_operator) and pd.notna(
                        threshold
                    ):  # Both should not be NaN/None
                        sensor_config["operator"] = filter_operator
                        sensor_config["operatorValue"] = threshold

                    # Append the sensor configuration to devConfig
                    request_body["devConfig"].append(sensor_config)

            else:
                if operation is None:
                    raise ValueError("The 'operation' variable must be set.")

                # Validate that both filter_operator and threshold are either both present or both absent
                if (filter_operator is None) != (threshold is None):
                    raise ValueError(
                        "Both filter_operator and threshold must be provided together or not at all."
                    )
                # Fetch metadata if sensor_list is not provided
                if sensor_list is None:
                    metadata = self.get_device_metadata(device_id, on_prem)
                    sensor_list = list(map(itemgetter("sensorId"), metadata["sensors"]))

                # Iterate through the sensor_list to populate devConfig
                for sensor_id in sensor_list:
                    # Create the configuration dictionary for each sensor
                    sensor_config = {
                        "devID": device_id,
                        "sensorID": sensor_id,
                        "operation": operation,
                    }

                    # Add filter_operator and operatorValue only if they are both present
                    if filter_operator is not None and threshold is not None:
                        sensor_config["operator"] = filter_operator
                        sensor_config["operatorValue"] = threshold

                    # Append the configuration to devConfig
                    request_body["devConfig"].append(sensor_config)

            # Construct API URL for data retrieval
            url = c.GET_FILTERED_OPERATION_DATA.format(
                protocol=protocol,
                data_url=self.data_url,
            )
            retry = 0

            while True:
                try:
                    with Logger(
                        self.logger, f"API {url} response time:", self.log_time
                    ):
                        response = requests.put(
                            url, json=request_body, headers={"userID": self.user_id}
                        )

                    # Check the response status code
                    response.raise_for_status()

                    # Parse the JSON response
                    response_data = response.json()

                    if "errors" in response_data:
                        raise requests.exceptions.RequestException()
                    break

                except Exception as e:
                    retry += 1
                    self.logger.error(
                        f"[{type(e).__name__}] Retry Count: {retry}, {e}"
                        + ERROR_MESSAGE(response, url)
                    )

                    # Retry with exponential backoff
                    if retry < c.MAX_RETRIES:
                        sleep_time = c.RETRY_DELAY[1] if retry > 5 else c.RETRY_DELAY[0]
                        time.sleep(sleep_time)
                    else:
                        raise Exception(
                            "Max retries for data fetching from api-layer exceeded."
                            + ERROR_MESSAGE(response, url)
                        )

            retrieved_sensors = []
            time_list = []
            value = []
            for sensor in sensor_list:
                if df is not None:
                    operation = df[df["sensor"] == sensor]["operation"].values[0]

                info = response_data["data"][f"{device_id}_{sensor}_{operation}"]
                if info:
                    retrieved_sensors.append(sensor)
                    time_list.append(info["time"])
                    value.append(info["value"])
            df = pd.DataFrame()
            if value:
                df = pd.DataFrame(
                    {"sensor": retrieved_sensors, "time": time_list, "value": value}
                )
            if not df.empty:
                df = self.__get_cleaned_table(
                    df=df,
                    alias=alias,
                    cal=cal,
                    device_id=device_id,
                    sensor_list=sensor_list,
                    on_prem=on_prem,
                    unix=unix,
                    metadata=metadata,
                )

            return df

        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"[EXCEPTION] {type(e).__name__}: {ERROR_MESSAGE(response, url)}"
            )
            return pd.DataFrame()

        except (TypeError, ValueError) as e:
            self.logger.error(f"[EXCEPTION] {type(e).__name__}: {e}")
            return pd.DataFrame()

        except Exception as e:
            self.logger.error(f"[EXCEPTION] {e}")
            return pd.DataFrame()
