import os
import requests
from ecorouting.testcases import testcases
from flask import Flask, send_file
from flask_cors import CORS
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "*"}})

METRICS = {
    "ttime": {"unit": "s", "pretty": "Time"},
    "length": {"unit": "km", "pretty": "Length"},
    "cost_co": {"unit": "g", "pretty": "CO"},
    "cost_co2": {"unit": "g", "pretty": "CO2"},
    "cost_PMx": {"unit": "g", "pretty": "PMx"},
    "cost_hc": {"unit": "g", "pretty": "HC"},
    "cost_nox": {"unit": "g", "pretty": "NOx"}
}

SNAPSHOTS_DIR = os.path.join("..", "snapshots")
VIDEOS_DIR = os.path.join("..", "videos")
HEATMAPS_DIR = os.path.join("..", "heatmaps")

FFMPEG_CMD = 'ffmpeg -framerate 30 -i "%s" -filter:v "crop=in_w/2:in_h:in_w/4:in_h" -pix_fmt yuv420p "%s.mp4"'

VNC_MANAGER_API = "http://localhost:8002/api/"


def format_objective_names(objective1, objective2):
    o = sorted([objective1, objective2])
    return "%s-%s" % (o[0], o[1])


def format_db_entry_key(scenario, objective1, objective2):
    return "%s.%s" % (scenario, format_objective_names(objective1, objective2))


def format_file_name_base(scenario):
    return "%s.base" % scenario


def format_file_name_sim(scenario, objective1, objective2, solution):
    return "%s.sim%d" % (format_db_entry_key(scenario, objective1, objective2), solution)


def get_file_path_or_default(path, name, extension):
    file_path = os.path.join(path, "%s.%s" % (name, extension))
    if not os.path.exists(file_path):
        file_path = os.path.join(path, "default.%s" % extension)
    return file_path


def get_video_cmd(video_name):
    return FFMPEG_CMD % (os.path.join(SNAPSHOTS_DIR, "snapshot%d.png"), os.path.join(VIDEOS_DIR, video_name))


def setup_snapshots_dir():
    if not os.path.exists(SNAPSHOTS_DIR):
        os.mkdir(SNAPSHOTS_DIR)


def clear_snapshots():
    for file in os.listdir(SNAPSHOTS_DIR):
        os.remove(os.path.join(SNAPSHOTS_DIR, file))


def read_eval_file(file_name):
    f = open(file_name, "r")
    line = f.readline()
    line = line.replace("#", "").strip()
    headers = [h.strip() for h in line.split(" ")]
    lines = [l for l in f.readlines() if l.strip()]
    f.close()

    ev = {h: [] for h in headers}
    for i in range(len(lines)):
        line = lines[i]
        values = [float(v.strip()) for v in line.split(" ")]
        for j in range(len(values)):
            ev[headers[j]].append(values[j])

    return ev


def get_simulation_files(netfile, roufile):
    return {
        "gui-settings": open("gui-settings.xml", "rb"),
        "additional-files": open("moreOutputInfo.xml", "rb"),
        "net-file": open(netfile, "rb"),
        "route-files": open(roufile, "rb"),
        "edge-data-out": open("edge-data-out.xml", "rb"),
        "basecars-emission-by-edges-out": open("basecars-emission-by-edges-out.xml", "rb")
    }


@app.route("/api/scenarios", methods=["GET"])
def scenarios():
    return {
               "success": True,
               "scenarios": [h for h in testcases],
               "pretty_names": [testcases[h]["prettyName"] for h in testcases]
           }, 200


@app.route("/api/objectives", methods=["GET"])
def objectives():
    return {
               "success": True,
               "objectives": [h for h in METRICS],
               "pretty_names": [METRICS[h]["pretty"] for h in METRICS],
               "units": [METRICS[h]["unit"] for h in METRICS]
           }, 200


@app.route("/api/<scenario>/<objective1>/<objective2>/data", methods=["GET"])
def data(scenario, objective1, objective2):
    tc = testcases[scenario]

    base = read_eval_file(os.path.join(tc["ofolder"], format_objective_names(objective1, objective2), "base.eval"))
    base = {h: base[h] for h in base if h in [h for h in METRICS]}

    pred = read_eval_file(os.path.join(tc["ofolder"], format_objective_names(objective1, objective2), "pred.eval"))
    pred = {h: pred[h] for h in pred if h in [h for h in METRICS]}

    sim = read_eval_file(os.path.join(tc["ofolder"], format_objective_names(objective1, objective2), "sim.eval"))
    sim = {h: sim[h] for h in sim if h in [h for h in METRICS]}

    return {
               "success": True,
               "data":
                   {
                       "objective1": objective1,
                       "objective2": objective2,
                       "base": {**base},
                       "pred": {**pred},
                       "sim": {**sim}
                   }
           }, 200


@app.route("/api/<scenario>/base/view", methods=["GET"])
def base_view(scenario):
    tc = testcases[scenario]
    netfile = os.path.join(tc["ifolder"], tc["netfile"])
    roufile = os.path.join(tc["ofolder"], "inputdata", tc["bname"]) + "-base.rou.xml"
    response = requests.post(VNC_MANAGER_API + "vnc/request", files=get_simulation_files(netfile, roufile))
    return {"success": True, "data": response.json()["data"]}, 200


@app.route("/api/<scenario>/optimized/<objective1>/<objective2>/view/<solution>", methods=["GET"])
def optimized_view(scenario, objective1, objective2, solution):
    tc = testcases[scenario]
    netfile = os.path.join(tc["ifolder"], tc["netfile"])
    objs = format_objective_names(objective1, objective2)
    sol = "solution%d" % (int(solution) + 1)
    roufile = os.path.join(tc["ofolder"], objs, sol, tc["bname"]) + ".rou.xml"
    response = requests.post(VNC_MANAGER_API + "vnc/request", files=get_simulation_files(netfile, roufile))
    return {"success": True, **response.json()}, 200


@app.route("/api/<scenario>/base/heatmap", methods=["GET"])
def base_heatmap(scenario):
    image_name = format_file_name_base(scenario)
    return send_file(get_file_path_or_default(HEATMAPS_DIR, image_name, "jpg"), mimetype="image/jpeg")


@app.route("/api/<scenario>/optimized/<objective1>/<objective2>/heatmap/<solution>", methods=["GET"])
def optimized_heatmap(scenario, objective1, objective2, solution):
    image_name = format_file_name_sim(scenario, objective1, objective2, int(solution))
    return send_file(get_file_path_or_default(HEATMAPS_DIR, image_name, "jpg"), mimetype="image/jpeg")


@app.route("/api/<scenario>/base/video", methods=["GET"])
def base_video(scenario):
    video_name = format_file_name_base(scenario)
    return send_file(get_file_path_or_default(VIDEOS_DIR, video_name, "mp4"), mimetype="video/mp4")


@app.route("/api/<scenario>/optimized/<objective1>/<objective2>/video/<solution>", methods=["GET"])
def optimized_video(scenario, objective1, objective2, solution):
    video_name = format_file_name_sim(scenario, objective1, objective2, int(solution))
    return send_file(get_file_path_or_default(VIDEOS_DIR, video_name, "mp4"), mimetype="video/mp4")


if __name__ == "__main__":
    app.run(port=8001)
