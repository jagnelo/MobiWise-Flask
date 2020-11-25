import os


class Globals:
    METRICS = {
        "ttime": {"unit": "s", "pretty": "Time"},
        "length": {"unit": "km", "pretty": "Length"},
        "cost_co": {"unit": "g", "pretty": "CO"},
        "cost_co2": {"unit": "g", "pretty": "CO2"},
        "cost_PMx": {"unit": "g", "pretty": "PMx"},
        "cost_hc": {"unit": "g", "pretty": "HC"},
        "cost_nox": {"unit": "g", "pretty": "NOx"}
    }

    OBJECTIVE_SEPARATOR = "-"
    SCENARIO_SEPARATOR = "."

    ECOROUTING_DIR = os.path.join("..", "ecorouting")

    SUMO_GUI_SETTINGS_FILE_NAME = "gui-settings.xml"
    SUMO_MAX_TIMEOUT = 4 * 60 * 60
    SUMO_MAX_THREADS = 8

    LOGS_DIR = os.path.join("..", "logs")

    SNAPSHOTS_DIR = "snapshots"
    SNAPSHOTS_COUNT = 200_000
    SNAPSHOTS_FILE_TYPE = "png"
    SNAPSHOTS_FILE_NAME = "snapshot%d." + SNAPSHOTS_FILE_TYPE
    SNAPSHOTS_XML_ELEMENT = "\t<snapshot file=\"%s\" time=\"%d\"/>"

    VIDEOS_DIR = os.path.join("..", "videos")
    VIDEOS_FILE_TYPE = "mp4"
    FFMPEG_CMD = 'ffmpeg -y -framerate 30 -i "%s" -pix_fmt yuv420p "%s.' + VIDEOS_FILE_TYPE + '"'
    VIDEOS_RESOLUTION = {
        "width": 640,   # 1280,
        "height": 480   # 960
    }

    HEATMAPS_DIR = os.path.join("..", "heatmaps")
    HEATMAPS_FILE_TYPE = "png"

    VNC_MANAGER_API = "http://localhost:8002/api/"
