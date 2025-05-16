import pytz


UTC = pytz.utc
# Get the timezone for India
IST = pytz.timezone("Asia/Kolkata")
VERSION = "0.6.0"

"""ALERTS HANDLER"""

MAIL_URL = "http://{ds_url}/ds/internal/messenger/send-mail"
TEAMS_URL = "http://{ds_url}/ds/internal/messenger/teamsAlerts"

"""BRUCE HANDLER"""

ADD_INSIGHT_RESULT = "{protocol}://{data_url}/api/bruce/insightResult/add"
GET_INSIGHT_RESULT = (
    "{protocol}://{data_url}/api/bruce/insightResult/fetch/count/{count}"
)

"""MQTT HANDLER"""

MAX_CHUNK_SIZE = 1000
SLEEP_TIME = 1

"""DATA ACCESS"""

GET_USER_INFO_URL = "{protocol}://{data_url}/api/metaData/user"
GET_DEVICE_DETAILS_URL = "{protocol}://{data_url}/api/metaData/allDevices"
GET_DEVICE_METADATA_URL = "{protocol}://{data_url}/api/metaData/device/{device_id}"
GET_DP_URL = "{protocol}://{data_url}/api/apiLayer/getLimitedDataMultipleSensors/"
GET_FIRST_DP = "{protocol}://{data_url}/api/apiLayer/getMultipleSensorsDPAfter"
GET_LOAD_ENTITIES = "{protocol}://{data_url}/api/metaData/getAllClusterData"
INFLUXDB_URL = "{protocol}://{data_url}/api/apiLayer/getAllData"
GET_CURSOR_BATCHES_URL = "{protocol}://{data_url}/api/apiLayer/getCursorOfBatches"
CONSUMPTION_URL = "{protocol}://{data_url}/api/apiLayer/getStartEndDPV2"
TRIGGER_URL = "{protocol}://{data_url}/api/expression-schedular/user-trigger-with-title"
CLUSTER_AGGREGATION = "{protocol}://{data_url}/api/widget/clusterData"
GET_FILTERED_OPERATION_DATA = (
    "{protocol}://{data_url}/api/consumption/getOperationDataWithTime"
)

MAX_RETRIES = 15
RETRY_DELAY = [2, 4]
CURSOR_LIMIT = 25000


"""EVENTS HANDLER"""

PUBLISH_EVENT_URL = "{protocol}://{data_url}/api/eventTag/publishEvent"
GET_EVENTS_IN_TIMESLOT_URL = "{protocol}://{data_url}/api/eventTag/fetchEvents/timeslot"
GET_EVENT_DATA_COUNT_URL = "{protocol}://{data_url}/api/eventTag/fetchEvents/count"
GET_EVENT_CATEGORIES_URL = "{protocol}://{data_url}/api/eventTag"
GET_DETAILED_EVENT_URL = "{protocol}://{data_url}/api/eventTag/eventLogger"
GET_MONGO_DATA = "{protocol}://{data_url}/api/table/getRows3"
GET_MAINTENANCE_MODULE_DATA = (
    "{protocol}://{data_url}/api/widget/getMaintenanceModuleData"
)
GET_DEVICE_DATA = "{protocol}://{data_url}/api/table/getRowsByDevices"

"""WEATHER HANDLER"""
WEATHER_API = "https://api.openweathermap.org/energy/1.0/solar/data"
WEATHERBIT_API = "https://api.weatherbit.io/v2.0/forecast/hourly"
