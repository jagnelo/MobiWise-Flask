import os


class NoInit:
    def __init__(self):
        raise RuntimeError


class Globals(NoInit):

    SCENARIO_SEPARATOR = "."
    OBJECTIVE_SEPARATOR = "-"
    SOLUTION_SEPARATOR = "."

    ECOROUTING_DIR = os.path.join("..", "ecorouting")
    ECOROUTING_GUI_SETTINGS_FILE_NAME = "gui-settings.xml"
    ECOROUTING_ADDITIONAL_FILES_FILE_NAME = "moreOutputInfo.xml"
    ECOROUTING_METRICS = {
        "ttime": {"unit": "s", "pretty": "Travel time"},
        "length": {"unit": "km", "pretty": "Travel distance"},
        "cost_co": {"unit": "g", "pretty": "CO"},
        "cost_co2": {"unit": "g", "pretty": "CO2"},
        "cost_PMx": {"unit": "g", "pretty": "PMx"},
        "cost_hc": {"unit": "g", "pretty": "HC"},
        "cost_nox": {"unit": "g", "pretty": "NOx"}
    }

    TEMA_DIR = os.path.join("..", "tema", "bin")
    TEMA_ADDITIONAL_FILES_FILE_NAME = "Additional_Files.add.xml"
    TEMA_ROUTING_VEHICLES_EDGE_DATA_FILE_NAME = "edges_Routing_data.xml"
    TEMA_ALL_VEHICLES_EDGE_DATA_FILE_NAME = "edges_All_vehicles.xml"
    TEMA_NOISE_EDGE_DATA_FILE_NAME = "edge_noise_data.xml"
    TEMA_FILE_NAME_BASE_SUFFIX = "baseline.xml"
    TEMA_FILE_NAME_SIM_SUFFIX_FORMAT = "optimal_solution%d.xml"
    TEMA_RESULTS_FILE_NAME = "TEMA-results.res"
    TEMA_TRACI_BASE_PORT = 8813
    TEMA_HEATMAPS_METRICS = {
        "co2": {"unit": "g/km/vehicle", "pretty": "CO2"},
        "eco_indicator": {"unit": "€ cents/vehicle", "pretty": "Eco-indicator"},
        "emissions_indicator": {"unit": "€ cents/vehicle", "pretty": "Emissions indicator"},
        "travel_time": {"unit": "s", "pretty": "Travel time"}
    }
    TEMA_RESULTS_METRICS = {
        "ttime": {"unit": "h", "pretty": "Travel time"},
        "length": {"unit": "km", "pretty": "Travel distance"},
        "cost_co2": {"unit": "ton", "pretty": "CO2"},
        "cost_co2_veh": {"unit": "g/vehicle km", "pretty": "CO2"},
        "cost_co": {"unit": "kg", "pretty": "CO"},
        "cost_PMx": {"unit": "kg", "pretty": "PMx"},
        "cost_nox": {"unit": "kg", "pretty": "NOx"},
        "cost_eco_indicator": {"unit": "€", "pretty": "Eco-indicator"}
    }

    MATLAB_LIB_DIR = os.path.join("..", "lib", "MATLAB")
    MATLAB_RUNTIME_DIR = os.path.abspath(os.path.join(os.sep, "usr", "local", "MATLAB", "MATLAB_Runtime", "v99"))

    XML_COMMENT_TAGS = ("<!--", "-->")
    XML_PROLOG_TAGS = ("<\\?xml", "\\?>")

    SUMO_EDGE_DATA_XML_TAG = "edgeData"

    TASK_MANAGER_MAX_TIMEOUT = 60 * 60 * 2
    TASK_MANAGER_MAX_THREADS = os.cpu_count()

    LOGS_OLD_NAME = "old logs"
    LOGS_DIR = os.path.join("..", "logs")
    LOGS_LEVEL_INFO = "INFO"
    LOGS_LEVEL_DEBUG = "DEBUG"
    LOGS_LEVEL_WARN = "WARN"
    LOGS_LEVEL_ERROR = "ERROR"
    LOGS_FILE_TYPE = "log"

    SNAPSHOTS_DIR = "snapshots"
    SNAPSHOTS_COUNT = 200_000
    SNAPSHOTS_FILE_TYPE = "png"
    SNAPSHOTS_FILE_NAME = "snapshot%d." + SNAPSHOTS_FILE_TYPE
    SNAPSHOTS_XML_ELEMENT = "\t<snapshot file=\"%s\" time=\"%d\"/>"

    VIDEOS_DIR = os.path.join("..", "media", "videos")
    VIDEOS_TARGZ_DIR = os.path.join("..", "media", "videos.tar.gz")
    VIDEOS_FILE_TYPE = "mp4"
    VIDEOS_TARGZ_FILE_TYPE = "tar.gz"
    FFMPEG_CMD = 'ffmpeg -y -r 30 -i %s -vcodec libx264 -crf 32 -pix_fmt yuv420p %s.' + VIDEOS_FILE_TYPE
    VIDEOS_RESOLUTION = {
        "width": 1280,
        "height": 960
    }

    HEATMAPS_DIR = os.path.join("..", "media", "heatmaps")
    HEATMAPS_FILE_TYPE = "png"
    HEATMAPS_RESOLUTION = {
        "width": 1920,
        "height": 1080
    }
    HEATMAP_EXPECTED_COUNT = 8  # 2 of each type (full, routes) for each of the 4 TEMA_METRICS

    VNC_MANAGER_API = "http://localhost:5001/api/"
