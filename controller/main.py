import argparse
import os
import numpy as np

import mainaux
import SUMOinout
from ecorouting.testcases import testcases
import pickle
from flask import Flask, send_file
from flask_cors import CORS
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "*"}})


TTIME = "ttime"
LENGTH = "length"
COST_CO = "cost_co"
COST_CO2 = "cost_co2"
COST_PMX = "cost_PMx"
COST_HC = "cost_hc"
COST_NOX = "cost_nox"
# COST_FUEL = "cost_fuel"     # esta opção não consta do código original da Andreia
metrics = [TTIME, LENGTH, COST_CO, COST_CO2, COST_PMX, COST_HC, COST_NOX]   # , COST_FUEL]

TTIME_PRTY = "Time"
LENGTH_PRTY = "Length"
COST_CO_PRTY = "Cost CO"
COST_CO2_PRTY = "Cost CO2"
COST_PMX_PRTY = "Cost PMx"
COST_HC_PRTY = "Cost HC"
COST_NOX_PRTY = "Cost NOx"
# COST_FUEL_PRTY = "Cost fuel"
metrics_pretty = [TTIME_PRTY, LENGTH_PRTY, COST_CO_PRTY, COST_CO2_PRTY, COST_PMX_PRTY, COST_HC_PRTY, COST_NOX_PRTY]   # , COST_FUEL_PRTY]


PICKLE_NAME = "data.pkl"


def format_objective_names(objective1, objective2):
    o = sorted([objective1, objective2])
    return "%s-%s" % (o[0], o[1])


def format_db_entry_key(scenario, objective1, objective2):
    return "%s:%s" % (scenario, format_objective_names(objective1, objective2))


# duplicate from ecorouting.main-interactive.setupRecords
def setup_records(tc):
    expPath = tc["ofolder"]

    if not os.path.exists(expPath + "/inputdata"):
        os.makedirs(expPath + "/inputdata")


# adjusted duplicate from ecorouting.main-interactive.readArguments
def read_arguments(default_args=None):
    tcnames = testcases.keys()

    parser = argparse.ArgumentParser(description='EcoRouting.')
    parser.add_argument('--mode', type=int, choices=[1 ,2 ,3], default=1,
                        help='choose mode: 1) run base case; 2) optimize and simulate solutions - interactive mode; 3) optimize and simulate all solutions')
    parser.add_argument("-t", type=str, choices=tcnames, default="ang-est")
    parser.add_argument("--obj1", type=str, choices=metrics, default="ttime", help="Objective 1")
    parser.add_argument("--obj2", type=str, choices=metrics, default="length", help="Objective 2")
    parser.add_argument("--w1", type=int, default=1, help="Weight 1")
    parser.add_argument("--w2", type=int, default=1, help="Weight 2")
    parser.add_argument("--gui", default=False, action="store_true", help="Run the graphical version of SUMO")
    parser.add_argument("--plot", default=False, action="store_true", help="Plot the (Pareto-)optimal solutions. Available only for mode 3")

    args = parser.parse_args(default_args) if default_args is not None else parser.parse_args()

    return args


@app.route('/api/scenarios', methods=['GET'])
def scenarios():
    return {"success": True, "scenarios": [h for h in testcases]}, 200


@app.route('/api/objectives', methods=['GET'])
def objectives():
    return {"success": True, "objectives": metrics, "pretty_names": metrics_pretty}, 200


@app.route('/api/preload', methods=['GET'])
def run_all():
    print("Pre-calculating all simulations")
    for scenario in testcases:
        print("Scenario: %s" % scenario)
        for m1 in metrics:
            for m2 in metrics:
                if m1 != m2:
                    print("Objectives: %s - %s" % (m1, m2))
                    simulation_run_base(scenario, m1, m2)
                    optimization_calc_solutions(scenario, m1, m2)
                    simulation_run_optimized(scenario, m1, m2)

    return {"success": True}, 200


@app.route('/api/<scenario>/<objective1>/<objective2>/simulate/base', methods=['GET'])
def simulation_run_base(scenario, objective1, objective2):
    data = read_pickle()
    key = format_db_entry_key(scenario, objective1, objective2)

    args = ["-t", scenario, "--obj1", objective1, "--obj2", objective2]

    args = read_arguments(args)
    tc = testcases[args.t]  # test case

    # if the data created by this step already exists, return immediately rather than re-running
    if key in data and "args" in data[key] and "tc" in data[key] and "stage" in data[key] and data[key]["stage"] >= 1:
        if os.path.exists(data[key]["tc"]["ofolder"]) and os.path.exists(os.path.join(data[key]["tc"]["ofolder"], "inputdata")):
            return {
                       "success": True,
                       "data":
                           {
                               "objective1": objective1,
                               "objective2": objective2
                           }
                   }, 200

    setup_records(tc)

    # gera os ficheiros -routes.dat, -source-destiny.in, -demand.in, -sdemand.in (trafego estatico e dinamico)
    # e o -base.rou.xml (versao base usada que garante que os veiculos
    # sao do mesmo tipo que os usados na experiencia)
    # Nota: E' nesta funcao que se define que veiculos devem ser considerados estaticos (ou dinamicos)

    ifolder = tc["ifolder"]  # input folder
    ofolder = tc["ofolder"] + "/inputdata"  # output folder
    netfile = ifolder + "/" + tc["netfile"]  # net file
    roufile = ifolder + "/" + tc["roufile"]  # inital route file
    obname = ofolder + "/" + tc["bname"]  # output base name
    dynamicVTypes = tc["dynamicTypes"]  # possiveis ids dos veiculos dinamicos

    # gera ficheiros com informacao estatica do grafo, e ficheiros com os dados do trafego estatico e dinamico
    broufile = obname + "-base" + ".rou.xml"
    SUMOinout.SUMOToCSV_routes(netfile, roufile, obname, oroufile=broufile, dynamicVTypes=dynamicVTypes)

    # gera os ficheiros -tripinfo e o -emission (obter custos do SUMO)
    mainaux.runSUMO(netfile, broufile, obname, guiversion=False)

    # gera os ficheiros CSV -tripinfo.csv, .edg.csv, nod.csv, -emission.csv e .edg-costs.csv
    SUMOinout.SUMOSummaries_ToCSV_OptInput(netfile, roufile, obname, getNetworkData=True)

    data[key] = {"args": args, "tc": tc, "stage": 1}
    write_pickle(data)

    return {
               "success": True,
               "data":
                   {
                       "objective1": objective1,
                       "objective2": objective2
                   }
           }, 200


@app.route('/api/<scenario>/<objective1>/<objective2>/optimize', methods=['GET'])
def optimization_calc_solutions(scenario, objective1, objective2):
    data = read_pickle()
    key = format_db_entry_key(scenario, objective1, objective2)
    args = data[key]["args"]
    tc = data[key]["tc"]

    # if the data created by this step already exists, return immediately rather than re-running
    if key in data and "args" in data[key] and "tc" in data[key] and "stage" in data[key] and data[key]["stage"] >= 2:
        if "fcostLabels" in data[key] and "fcostWeights" in data[key] and "commoninfo" in data[key] and "solsinfo" in data[key]:
            if os.path.exists(data[key]["tc"]["ofolder"]) and os.path.exists(os.path.join(data[key]["tc"]["ofolder"], "inputdata")):
                if os.path.exists(os.path.join(data[key]["tc"]["ofolder"], format_objective_names(objective1, objective2))):
                    base_file = os.path.join(tc["ofolder"], format_objective_names(objective1, objective2), "base.eval")
                    pred_file = os.path.join(tc["ofolder"], format_objective_names(objective1, objective2), "pred.eval")
                    if os.path.exists(base_file) and os.path.exists(pred_file):
                        base = read_eval_file(base_file)
                        base = {h: base[h] for h in base if h in metrics}

                        pred = read_eval_file(pred_file)
                        pred = {h: pred[h] for h in pred if h in metrics}

                        return {
                                   "success": True,
                                   "data":
                                       {
                                           "objective1": objective1,
                                           "objective2": objective2,
                                           "base": {"num_sols": len(base[metrics[0]]), **base},
                                           "pred": {"num_sols": len(pred[metrics[0]]), **pred}
                                       }
                               }, 200

    fcostLabels = np.array([args.obj1, args.obj2])
    fcostWeights = np.array([args.w1, args.w2])

    ix = np.argsort(fcostLabels)
    fcostLabels, fcostWeights = fcostLabels[ix], fcostWeights[ix]

    ibname = tc["ofolder"] + "/inputdata/" + tc["bname"]
    ofolder = tc["ofolder"]
    dynamicTypes = tc["dynamicTypes"]
    onlyExtremalSols = tc["onlyExtremalSols"]

    commoninfo, solsinfo = mainaux.getSolutions(ibname, ofolder, fcostWeights, fcostLabels, dynamicTypes,
                                                onlyExtremalSols)

    data[key]["fcostLabels"] = fcostLabels
    data[key]["fcostWeights"] = fcostWeights
    data[key]["commoninfo"] = commoninfo
    data[key]["solsinfo"] = solsinfo
    data[key]["stage"] = 2
    write_pickle(data)

    base = read_eval_file(os.path.join(tc["ofolder"], format_objective_names(objective1, objective2), "base.eval"))
    base = {h: base[h] for h in base if h in metrics}

    pred = read_eval_file(os.path.join(tc["ofolder"], format_objective_names(objective1, objective2), "pred.eval"))
    pred = {h: pred[h] for h in pred if h in metrics}

    return {
               "success": True,
               "data":
                   {
                       "objective1": objective1,
                       "objective2": objective2,
                       "base": {"num_sols": len(base[metrics[0]]), **base},
                       "pred": {"num_sols": len(pred[metrics[0]]), **pred}
                   }
           }, 200


@app.route('/api/<scenario>/<objective1>/<objective2>/simulate/optimized', methods=['GET'])
def simulation_run_optimized(scenario, objective1, objective2):
    data = read_pickle()
    key = format_db_entry_key(scenario, objective1, objective2)
    tc = data[key]["tc"]
    fcostWeights = data[key]["fcostWeights"]
    fcostLabels = data[key]["fcostLabels"]
    commoninfo = data[key]["commoninfo"]
    solsinfo = data[key]["solsinfo"]

    # if the data created by this step already exists, return immediately rather than re-running
    if key in data and "args" in data[key] and "tc" in data[key] and "stage" in data[key] and data[key]["stage"] >= 3:
        if "fcostLabels" in data[key] and "fcostWeights" in data[key] and "commoninfo" in data[key] and "solsinfo" in data[key]:
            if os.path.exists(data[key]["tc"]["ofolder"]) and os.path.exists(os.path.join(data[key]["tc"]["ofolder"], "inputdata")):
                if os.path.exists(os.path.join(data[key]["tc"]["ofolder"], format_objective_names(objective1, objective2))):
                    sim_file = os.path.join(tc["ofolder"], format_objective_names(objective1, objective2), "sim.eval")
                    if os.path.exists(sim_file):
                        sim = read_eval_file(sim_file)
                        sim = {h: sim[h] for h in sim if h in metrics}

                        return {
                                   "success": True,
                                   "data":
                                       {
                                           "objective1": objective1,
                                           "objective2": objective2,
                                           "sim": {"num_sols": len(sim[metrics[0]]), **sim}
                                       }
                               }, 200

    ifolder = tc["ifolder"]  # input folder
    netfile = ifolder + "/" + tc["netfile"]  # net file

    comments = "objective functions: (" + ", ".join(
        map(lambda a: (str(a[0]) + "*" + str(a[1])), zip(fcostWeights, fcostLabels))) + ")"

    sols = solsinfo[0]

    for i in range(len(sols)):
        mainaux.runSolution(netfile, commoninfo, solsinfo, i, fcostLabels, guiversion=False, comments=comments)

    data[key]["stage"] = 3
    write_pickle(data)

    sim = read_eval_file(os.path.join(tc["ofolder"], format_objective_names(objective1, objective2), "sim.eval"))
    sim = {h: sim[h] for h in sim if h in metrics}

    return {
               "success": True,
               "data":
                   {
                       "objective1": objective1,
                       "objective2": objective2,
                       "sim": {"num_sols": len(sim[metrics[0]]), **sim}
                   }
           }, 200


@app.route('/api/<scenario>/<objective1>/<objective2>/view/<solution>', methods=['GET'])
def simulation_view_base(scenario, objective1, objective2, solution):
    data = read_pickle()
    key = format_db_entry_key(scenario, objective1, objective2)
    tc = data[key]["tc"]

    ifolder = tc["ifolder"]  # input folder
    ofolder = tc["ofolder"] + "/inputdata"  # output folder
    netfile = ifolder + "/" + tc["netfile"]  # net file
    roufile = ifolder + "/" + tc["roufile"]  # inital route file
    obname = ofolder + "/" + tc["bname"]  # output base name

    sumocmd = "sumo-gui --gui-settings-file gui-settings.xml"

    cmd_base = "DISPLAY=:1 " + sumocmd + " --net-file " + netfile + " --route-files " + roufile +\
               " --tripinfo-output " + obname + "-tripinfo --device.emissions.probability 1.0 " \
                                                "--emission-output.precision 6 " \
                                                "--additional-files moreOutputInfo.xml " \
                                                "--collision.action warn " \
                                                "-S " \
                                                "--quit-on-end " \
                                                "--time-to-teleport -1 " \
                                                "-G"

    fcostWeights = data[key]["fcostWeights"]
    fcostLabels = data[key]["fcostLabels"]
    commoninfo = data[key]["commoninfo"]
    solsinfo = data[key]["solsinfo"]

    (mwgraph, demand, sourcedest, sroutes, svehicles, dynamicTypes, outFolder, base_eval) = commoninfo
    (sols, sim_eval, simevalsd, pred_eval, solsBName) = solsinfo

    sol = int(solution)

    flowc, flowd, ev, predev = sols[sol]
    obname = solsBName[sol]

    roufile = obname + ".rou.xml"
    routes, vehicles = mwgraph.getFlowDescription(flowd, demand, sourcedest, mode=2)

    comments = "objective functions: (" + ", ".join(
        map(lambda a: (str(a[0]) + "*" + str(a[1])), zip(fcostWeights, fcostLabels))) + ")"
    comments += "\n" + "\n".join(map(str, ev.items()))

    SUMOinout.printSUMORoutes(routes, vehicles, roufile, sroutes=sroutes, svehicles=svehicles, comments=comments)

    cmd_optimized = "DISPLAY=:2 " + sumocmd + " --net-file " + netfile + " --route-files " + roufile +\
                    " --tripinfo-output " + obname + "-tripinfo --device.emissions.probability 1.0 " \
                                                     "--emission-output.precision 6 " \
                                                     "--additional-files moreOutputInfo.xml " \
                                                     "--collision.action warn " \
                                                     "-S " \
                                                     "--quit-on-end " \
                                                     "--time-to-teleport -1 " \
                                                     "-G"

    os.system(cmd_base + " & " + cmd_optimized + " & wait")

    return {"success": True}, 200


def read_eval_file(file_name):
    f = open(file_name, "r")
    line = f.readline()
    line = line.replace("#", "").strip()
    headers = [h.strip() for h in line.split(" ")]
    lines = [l for l in f.readlines() if len(l.strip()) > 0]
    f.close()

    ev = {h: [] for h in headers}
    for i in range(len(lines)):
        line = lines[i]
        values = [float(v.strip()) for v in line.split(" ")]
        for j in range(len(values)):
            ev[headers[j]].append(values[j])

    return ev


def write_pickle(data):
    f = open(PICKLE_NAME, "wb")
    pickle.dump(data, f)
    f.close()


def read_pickle():
    if not os.path.exists(PICKLE_NAME):
        return {}
    f = open(PICKLE_NAME, "rb")
    data = pickle.load(f)
    f.close()
    return data


@app.route('/api/heatmap/base', methods=['GET'])
def heatmap_base_simulation():
    return send_file("base_heatmap.jpg", mimetype='image/jpeg')


@app.route('/api/heatmap/optimized', methods=['GET'])
def heatmap_optimized_simulation():
    return send_file("sim_heatmap.jpg", mimetype='image/jpeg')


if __name__ == '__main__':
    app.run(port=8001)
