import os
import requests

import utils
import ecorouting_connector as eco
from flask import Flask, send_file
from flask_cors import CORS
from dotenv import load_dotenv, find_dotenv

from globals import Globals

load_dotenv(find_dotenv())

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "*"}})


@app.route("/api/scenarios", methods=["GET"])
def scenarios():
    testcases = eco.get_test_cases()
    return {
               "success": True,
               "scenarios": [h for h in testcases],
               "pretty_names": [testcases[h]["prettyName"] for h in testcases]
           }, 200


@app.route("/api/objectives", methods=["GET"])
def objectives():
    return {
               "success": True,
               "objectives": [h for h in Globals.METRICS],
               "pretty_names": [Globals.METRICS[h]["pretty"] for h in Globals.METRICS],
               "units": [Globals.METRICS[h]["unit"] for h in Globals.METRICS]
           }, 200


@app.route("/api/<scenario>/<objective1>/<objective2>/data", methods=["GET"])
def data(scenario, objective1, objective2):
    testcases = eco.get_test_cases()
    tc = testcases[scenario]
    path = utils.format_objective_names(objective1, objective2)

    base = utils.read_eval_file(os.path.join(tc["ofolder"], path, "base.eval"))
    base = {h: base[h] for h in base if h in [h for h in Globals.METRICS]}

    pred = utils.read_eval_file(os.path.join(tc["ofolder"], path, "pred.eval"))
    pred = {h: pred[h] for h in pred if h in [h for h in Globals.METRICS]}

    sim = utils.read_eval_file(os.path.join(tc["ofolder"], path, "sim.eval"))
    sim = {h: sim[h] for h in sim if h in [h for h in Globals.METRICS]}

    return {
               "success": True,
               "data": {
                       "objective1": objective1,
                       "objective2": objective2,
                       "base": {**base},
                       "pred": {**pred},
                       "sim": {**sim}
                   }
           }, 200


@app.route("/api/<scenario>/base/view", methods=["GET"])
def base_view(scenario):
    testcases = eco.get_test_cases()
    tc = testcases[scenario]
    netfile = os.path.join(tc["ifolder"], tc["netfile"])
    roufile = os.path.join(tc["ofolder"], "inputdata", tc["bname"]) + "-base.rou.xml"
    files = utils.get_simulation_files(netfile, roufile)
    response = requests.post(Globals.VNC_MANAGER_API + "vnc/request", files=files)
    return {"success": True, "data": response.json()["data"]}, 200


@app.route("/api/<scenario>/optimized/<objective1>/<objective2>/view/<solution>", methods=["GET"])
def optimized_view(scenario, objective1, objective2, solution):
    testcases = eco.get_test_cases()
    tc = testcases[scenario]
    netfile = os.path.join(tc["ifolder"], tc["netfile"])
    objs = utils.format_objective_names(objective1, objective2)
    sol = "solution%d" % (int(solution) + 1)
    roufile = os.path.join(tc["ofolder"], objs, sol, tc["bname"]) + ".rou.xml"
    files = utils.get_simulation_files(netfile, roufile)
    response = requests.post(Globals.VNC_MANAGER_API + "vnc/request", files=files)
    return {"success": True, **response.json()}, 200


@app.route("/api/<scenario>/base/heatmap", methods=["GET"])
def base_heatmap(scenario):
    image_name = utils.format_file_name_base(scenario)
    return send_file(utils.get_file_path_or_default(Globals.HEATMAPS_DIR, image_name, "jpg"), mimetype="image/jpeg")


@app.route("/api/<scenario>/optimized/<objective1>/<objective2>/heatmap/<solution>", methods=["GET"])
def optimized_heatmap(scenario, objective1, objective2, solution):
    image_name = utils.format_file_name_sim(scenario, objective1, objective2, int(solution))
    return send_file(utils.get_file_path_or_default(Globals.HEATMAPS_DIR, image_name, "jpg"), mimetype="image/jpeg")


@app.route("/api/<scenario>/base/video", methods=["GET"])
def base_video(scenario):
    video_name = utils.format_file_name_base(scenario)
    return send_file(utils.get_file_path_or_default(Globals.VIDEOS_DIR, video_name, "mp4"), mimetype="video/mp4")


@app.route("/api/<scenario>/optimized/<objective1>/<objective2>/video/<solution>", methods=["GET"])
def optimized_video(scenario, objective1, objective2, solution):
    video_name = utils.format_file_name_sim(scenario, objective1, objective2, int(solution))
    return send_file(utils.get_file_path_or_default(Globals.VIDEOS_DIR, video_name, "mp4"), mimetype="video/mp4")


if __name__ == "__main__":
    # app.run(port=8001)
