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
    SNAPSHOTS_DIR = os.path.join("..", "snapshots")
    VIDEOS_DIR = os.path.join("..", "videos")
    HEATMAPS_DIR = os.path.join("..", "heatmaps")
    LOGS_DIR = os.path.join("..", "logs")

    SNAPSHOTS_COUNT = 200_000
    SNAPSHOTS_FILE_TYPE = "png"
    SNAPSHOTS_NAME = "snapshot%d." + SNAPSHOTS_FILE_TYPE

    SUMO_MAX_TIMEOUT = 4*60*60

    VIDEOS_FILE_TYPE = "mp4"

    HEATMAPS_FILE_TYPE = "png"

    # -filter:v "crop=in_w/2:in_h:in_w/4:in_h" ' \
    FFMPEG_CMD = 'ffmpeg -y -framerate 30 -i "%s" ' \
                 '-pix_fmt yuv420p "%s.' + VIDEOS_FILE_TYPE + '"'

    VNC_MANAGER_API = "http://localhost:8002/api/"
