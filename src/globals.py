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

    objective_separator = "-"
    scenario_separator = "."

    SNAPSHOTS_DIR = os.path.join("..", "snapshots")
    VIDEOS_DIR = os.path.join("..", "videos")
    HEATMAPS_DIR = os.path.join("..", "heatmaps")

    FFMPEG_CMD = 'ffmpeg -framerate 30 -i "%s" -filter:v "crop=in_w/2:in_h:in_w/4:in_h" -pix_fmt yuv420p "%s.mp4"'

    VNC_MANAGER_API = "http://localhost:8002/api/"
