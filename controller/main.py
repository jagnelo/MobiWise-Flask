import argparse
import os
import numpy as np
import mainaux
import SUMOinout
from ecorouting.testcases import testcases
import pickle


# configs for running 2 side-by-side sumo-gui windows (resolution: 1920x950, on Ubuntu)
# left screen half
# --window-pos 0,0 --window-size 923,950
# right screen half
# --window-pos 1920,0 --window-size 923,950


TTIME = "ttime"
LENGTH = "length"
COST_CO = "cost_co"
COST_CO2 = "cost_co2"
COST_PMX = "cost_PMx"
COST_HC = "cost_hc"
COST_NOX = "cost_nox"
# COST_FUEL = "cost_fuel"     # esta opção não consta do código original da Andreia

ANG_EST = "ang-est"
PORTO_8AM9_FEWER = "portoSB_8AM9AM_fewerv"
PORTO_8AM9 = "portoSB_8AM9AM"


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
    objs = [TTIME, LENGTH, COST_CO, COST_CO2, COST_PMX, COST_HC, COST_NOX]  # , COST_FUEL]

    parser = argparse.ArgumentParser(description='EcoRouting.')
    parser.add_argument('--mode', type=int, choices=[1 ,2 ,3], default=1,
                        help='choose mode: 1) run base case; 2) optimize and simulate solutions - interactive mode; 3) optimize and simulate all solutions')
    parser.add_argument("-t", type=str, choices=tcnames, default="ang-est")
    parser.add_argument("--obj1", type=str, choices=objs, default="ttime", help="Objective 1")
    parser.add_argument("--obj2", type=str, choices=objs, default="length", help="Objective 2")
    parser.add_argument("--w1", type=int, default=1, help="Weight 1")
    parser.add_argument("--w2", type=int, default=1, help="Weight 2")
    parser.add_argument("--gui", default=False, action="store_true", help="Run the graphical version of SUMO")
    parser.add_argument("--plot", default=False, action="store_true", help="Plot the (Pareto-)optimal solutions. Available only for mode 3")

    args = parser.parse_args(default_args) if default_args is not None else parser.parse_args()

    return args


def simulation_run_base(scenario, objective1, objective2):
    data = read_pickle()
    key = format_db_entry_key(scenario, objective1, objective2)

    args = ["-t", scenario, "--obj1", objective1, "--obj2", objective2, "--gui"]

    args = read_arguments(args)
    tc = testcases[args.t]  # test case
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
    mainaux.runSUMO(netfile, broufile, obname, guiversion=True) # , extra_args="--window-pos 0,0 --window-size 923,950")

    # gera os ficheiros CSV -tripinfo.csv, .edg.csv, nod.csv, -emission.csv e .edg-costs.csv
    SUMOinout.SUMOSummaries_ToCSV_OptInput(netfile, roufile, obname, getNetworkData=True)

    data[key] = {"args": args, "tc": tc, "stage": 1}
    write_pickle(data)


def optimization_calc_solutions(scenario, objective1, objective2):
    data = read_pickle()
    key = format_db_entry_key(scenario, objective1, objective2)
    args = data[key]["args"]
    tc = data[key]["tc"]

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


def simulation_run_optimized(scenario, objective1, objective2, sol_num):
    data = read_pickle()
    key = format_db_entry_key(scenario, objective1, objective2)
    tc = data[key]["tc"]
    fcostWeights = data[key]["fcostWeights"]
    fcostLabels = data[key]["fcostLabels"]
    commoninfo = data[key]["commoninfo"]
    solsinfo = data[key]["solsinfo"]

    ifolder = tc["ifolder"]  # input folder
    netfile = ifolder + "/" + tc["netfile"]  # net file

    comments = "objective functions: (" + ", ".join(
        map(lambda a: (str(a[0]) + "*" + str(a[1])), zip(fcostWeights, fcostLabels))) + ")"

    mainaux.runSolution(netfile, commoninfo, solsinfo, sol_num, fcostLabels, guiversion=True, comments=comments)# ,
                        # extra_args="--window-pos 1920,0 --window-size 923,950")

    data[key]["stage"] = 3
    write_pickle(data)


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


test_name = ANG_EST
obj1 = TTIME
obj2 = LENGTH
sol = 0


simulation_run_base(test_name, obj1, obj2)
optimization_calc_solutions(test_name, obj1, obj2)
simulation_run_optimized(test_name, obj1, obj2, sol)


metrics = [TTIME, LENGTH, COST_CO, COST_CO2, COST_PMX, COST_HC, COST_NOX]
base = read_eval_file(os.path.join(testcases[test_name]["ofolder"], format_objective_names(obj1, obj2), "base.eval"))
pred = read_eval_file(os.path.join(testcases[test_name]["ofolder"], format_objective_names(obj1, obj2), "pred.eval"))
sim = read_eval_file(os.path.join(testcases[test_name]["ofolder"], format_objective_names(obj1, obj2), "sim.eval"))
base = {h:base[h] for h in base if h in metrics}
pred = {h:pred[h] for h in pred if h in metrics}
sim = {h:sim[h] for h in sim if h in metrics}

