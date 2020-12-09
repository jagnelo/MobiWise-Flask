import os
import shutil
import threading
import time
from datetime import datetime

import requests
from apscheduler.schedulers.background import BackgroundScheduler

import eval_file_fixer
import heatmap_organizer
import utils
import ecorouting_connector as eco
from flask import Flask, send_file
from flask_cors import CORS
from dotenv import load_dotenv, find_dotenv

import video_generator
from globals import Globals
from logger import logger

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


@app.route("/api/objectives/ecorouting", methods=["GET"])
def objectives():
    return {
               "success": True,
               "objectives": [h for h in Globals.ECOROUTING_METRICS],
               "pretty_names": [Globals.ECOROUTING_METRICS[h]["pretty"] for h in Globals.ECOROUTING_METRICS],
               "units": [Globals.ECOROUTING_METRICS[h]["unit"] for h in Globals.ECOROUTING_METRICS]
           }, 200


@app.route("/api/objectives/tema", methods=["GET"])
def TEMA_objectives():
    return {
               "success": True,
               "objectives": [h for h in Globals.TEMA_METRICS],
               "pretty_names": [Globals.TEMA_METRICS[h]["pretty"] for h in Globals.TEMA_METRICS],
               "units": [Globals.TEMA_METRICS[h]["unit"] for h in Globals.TEMA_METRICS]
           }, 200


@app.route("/api/<scenario>/<objective1>/<objective2>/data", methods=["GET"])
def data(scenario, objective1, objective2):
    testcases = eco.get_test_cases()
    tc = testcases[scenario]
    path = utils.format_objective_names(objective1, objective2)

    base = utils.read_eval_file(os.path.join(tc["ofolder"], path, "base.eval"))
    base = {h: base[h] for h in base if h in [h for h in Globals.ECOROUTING_METRICS]}

    pred = utils.read_eval_file(os.path.join(tc["ofolder"], path, "pred.eval"))
    pred = {h: pred[h] for h in pred if h in [h for h in Globals.ECOROUTING_METRICS]}

    if os.path.exists(os.path.join(tc["ofolder"], path, "sim_fixed.eval")):
        sim = utils.read_eval_file(os.path.join(tc["ofolder"], path, "sim_fixed.eval"))
        sim = {h: sim[h] for h in sim if h in [h for h in Globals.ECOROUTING_METRICS]}
    else:
        sim = utils.read_eval_file(os.path.join(tc["ofolder"], path, "sim.eval"))
        sim = {h: sim[h] for h in sim if h in [h for h in Globals.ECOROUTING_METRICS]}

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


@app.route("/api/<scenario>/base/heatmap/<metric>/<type>", methods=["GET"])
def base_heatmap(scenario, metric, type):
    image_dir_name = utils.format_file_name_base(scenario)
    if type == "routes":
        file_name = metric + "_routes." + Globals.HEATMAPS_FILE_TYPE
    else:
        file_name = metric + "." + Globals.HEATMAPS_FILE_TYPE
    return send_file(os.path.join(Globals.HEATMAPS_DIR, image_dir_name, file_name), mimetype="image/png")


@app.route("/api/<scenario>/optimized/<objective1>/<objective2>/heatmap/<solution>/<metric>/<type>", methods=["GET"])
def optimized_heatmap(scenario, objective1, objective2, solution, metric, type):
    image_dir_name = utils.format_file_name_sim(scenario, objective1, objective2, int(solution))
    if type == "routes":
        file_name = metric + "_routes." + Globals.HEATMAPS_FILE_TYPE
    else:
        file_name = metric + "." + Globals.HEATMAPS_FILE_TYPE
    return send_file(os.path.join(Globals.HEATMAPS_DIR, image_dir_name, file_name), mimetype="image/png")


@app.route("/api/<scenario>/base/video", methods=["GET"])
def base_video(scenario):
    video_name = utils.format_file_name_base(scenario) + "." + Globals.VIDEOS_FILE_TYPE
    return send_file(os.path.join(Globals.VIDEOS_DIR, video_name), mimetype="video/mp4")


@app.route("/api/<scenario>/optimized/<objective1>/<objective2>/video/<solution>", methods=["GET"])
def optimized_video(scenario, objective1, objective2, solution):
    video_name = utils.format_file_name_sim(scenario, objective1, objective2, int(solution))
    video_name = video_name + "." + Globals.VIDEOS_FILE_TYPE
    return send_file(os.path.join(Globals.VIDEOS_DIR, video_name), mimetype="video/mp4")


def setup():
    threading.current_thread().name = "Main"
    if os.path.exists(Globals.LOGS_DIR):
        old_logs = []
        log_files = []
        for file in os.listdir(Globals.LOGS_DIR):
            if os.path.isdir(os.path.join(Globals.LOGS_DIR, file)) and file.startswith(Globals.LOGS_OLD_NAME):
                old_logs.append(file)
            elif file.endswith(".%s" % Globals.LOGS_FILE_TYPE):
                log_files.append(file)
        old_logs_num = len(old_logs) + 1
        old_logs_dir = os.path.join(Globals.LOGS_DIR, "%s %d" % (Globals.LOGS_OLD_NAME, old_logs_num))
        utils.ensure_dir_exists(old_logs_dir)
        for file in log_files:
            shutil.move(os.path.join(Globals.LOGS_DIR, file), os.path.join(old_logs_dir, file))
    else:
        utils.ensure_dir_exists(Globals.LOGS_DIR)
    utils.ensure_dir_exists(Globals.VIDEOS_TARGZ_DIR)
    utils.ensure_dir_exists(Globals.VIDEOS_DIR)
    utils.ensure_dir_exists(Globals.HEATMAPS_DIR)


def main():
    logger.info("Main", "---------------------- MobiWise backend starting ----------------------")

    def update_tasks(silent=True):
        for _, task in eco.check_content(silent=silent).items():
            task_manager.add_task(task)

    scheduler = BackgroundScheduler()
    scheduler.start()
    scheduler.add_job(eval_file_fixer.run, 'interval', seconds=60*15)
    scheduler.add_job(heatmap_organizer.run, 'interval', seconds=60*15)
    scheduler.add_job(video_generator.run, 'interval', seconds=60*15)

    task_manager = eco.EcoRoutingTaskManager(Globals.TASK_MANAGER_MAX_THREADS, update_tasks)
    update_tasks(silent=False)
    task_manager.start()
    last_status = datetime.now()
    try:
        while task_manager.running:
            print_status = (datetime.now() - last_status).total_seconds() >= 300
            update_tasks(silent=not print_status)
            if print_status:
                task_manager.status()
                last_status = datetime.now()
            logger.flush()
            time.sleep(60)
    except:
        pass
    finally:
        logger.flush()
        task_manager.stop(wait=True)
        eco.check_content(silent=False)
        scheduler.shutdown()
        task_manager.status()
        logger.info("Main", "---------------------- MobiWise backend stopping ----------------------")
        logger.flush()


if __name__ == "__main__":
    setup()
    main()
    # app.run(port=5000)
