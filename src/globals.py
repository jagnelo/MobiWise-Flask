import os


class NoInit:
    def __init__(self):
        raise RuntimeError


class Globals(NoInit):
    METRICS = {
        "ttime": {"unit": "s", "pretty": "Time"},
        "length": {"unit": "km", "pretty": "Length"},
        "cost_co": {"unit": "g", "pretty": "CO"},
        "cost_co2": {"unit": "g", "pretty": "CO2"},
        "cost_PMx": {"unit": "g", "pretty": "PMx"},
        "cost_hc": {"unit": "g", "pretty": "HC"},
        "cost_nox": {"unit": "g", "pretty": "NOx"}
    }

    SCENARIO_SEPARATOR = "."
    OBJECTIVE_SEPARATOR = "-"
    SOLUTION_SEPARATOR = "."

    ECOROUTING_DIR = os.path.join("..", "ecorouting")
    ECOROUTING_GUI_SETTINGS_FILE_NAME = "gui-settings.xml"
    ECOROUTING_ADDITIONAL_FILES_FILE_NAME = "moreOutputInfo.xml"

    TEMA_DIR = os.path.join("..", "tema", "bin")
    TEMA_ADDITIONAL_FILES_FILE_NAME = "Additional_Files.add.xml"
    TEMA_ROUTING_VEHICLES_EDGE_DATA_FILE_NAME = "edges_Routing_data.xml"
    TEMA_ALL_VEHICLES_EDGE_DATA_FILE_NAME = "edges_All_vehicles.xml"
    TEMA_NOISE_EDGE_DATA_FILE_NAME = "edge_noise_data.xml"
    TEMA_FILE_NAME_BASE_SUFFIX = "baseline.xml"
    TEMA_FILE_NAME_SIM_SUFFIX_FORMAT = "optimal_solution%d.xml"
    TEMA_TRACI_BASE_PORT = 8813

    MATLAB_RUNTIME_DIR = os.path.abspath(os.path.join(os.sep, "usr", "local", "MATLAB", "MATLAB_Runtime", "v99"))

    XML_COMMENT_TAGS = ("<!--", "-->")
    XML_PROLOG_TAGS = ("<\\?xml", "\\?>")

    SUMO_EDGE_DATA_XML_TAG = "edgeData"

    TASK_MANAGER_MAX_TIMEOUT = 60 * 60 * 2
    TASK_MANAGER_MAX_THREADS = 8

    LOGS_DIR = os.path.join("..", "logs")
    LOGS_LEVEL_INFO = "INFO"
    LOGS_LEVEL_WARN = "WARN"
    LOGS_LEVEL_ERROR = "ERROR"

    SNAPSHOTS_DIR = "snapshots"
    SNAPSHOTS_COUNT = 200_000
    SNAPSHOTS_FILE_TYPE = "png"
    SNAPSHOTS_FILE_NAME = "snapshot%d." + SNAPSHOTS_FILE_TYPE
    SNAPSHOTS_XML_ELEMENT = "\t<snapshot file=\"%s\" time=\"%d\"/>"

    VIDEOS_DIR = os.path.join("..", "media", "videos")
    VIDEOS_TARGZ_DIR = os.path.join("..", "media", "videos.tar.gz")
    VIDEOS_FILE_TYPE = "mp4"
    VIDEOS_TARGZ_FILE_TYPE = "tar.gz"
    FFMPEG_CMD = 'ffmpeg -y -framerate 30 -i "%s" -pix_fmt yuv420p "%s.' + VIDEOS_FILE_TYPE + '"'
    VIDEOS_RESOLUTION = {
        "width": 400,   # 1280,
        "height": 300   # 960
    }

    HEATMAPS_DIR = os.path.join("..", "media", "heatmaps")
    HEATMAPS_FILE_TYPE = "png"
    HEATMAPS_RESOLUTION = {
        "width": 1920,
        "height": 1080
    }

    VNC_MANAGER_API = "http://localhost:8002/api/"
