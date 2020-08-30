import argparse
import os
import numpy as np
from mainaux import runSUMO, getSolutions, runSolution
from SUMOinout import SUMOToCSV_routes, SUMOSummaries_ToCSV_OptInput

from plotSummarizedData import plotExample

# ------------------------ Test cases -------------------------------- #
from testcases import testcases
# -------------------------------------------------------------------- #

_guiversion = False



def getTestcase(name):
    return testcases[name]

def setupRecords(tc):
    expPath = tc["ofolder"]
    
    if not os.path.exists(expPath+"/inputdata"):
        os.makedirs(expPath+"/inputdata")



def readArguments():

    global _version
    tcnames = testcases.keys()
    objs = ["ttime", "length", "cost_co", "cost_co2", "cost_PMx", "cost_hc", "cost_nox"]

    parser = argparse.ArgumentParser(description='EcoRouting.')
    parser.add_argument('--mode', type=int, choices=[1,2,3], default=1,
                    help='choose mode: 1) run base case; 2) optimize and simulate solutions - interactive mode; 3) optimize and simulate all solutions')
    parser.add_argument("-t", type=str, choices=tcnames, default="ang-est")
    #TODO: Receber objectivos e weights
    parser.add_argument("--obj1", type=str, choices=objs, default="ttime", help="Objective 1")
    parser.add_argument("--obj2", type=str, choices=objs, default="length", help="Objective 2")
    parser.add_argument("--w1", type=int, default=1, help="Weight 1")
    parser.add_argument("--w2", type=int, default=1, help="Weight 2")
    parser.add_argument("--gui", default=False, action="store_true", help="Run the graphical version of SUMO")
    parser.add_argument("--plot", default=False, action="store_true", help="Plot the (Pareto-)optimal solutions. Available only for mode 3")
    
    args = parser.parse_args()
    _guiversion = args.gui
    
    return args

    
def runBaseCase(tc):
    print("Welcome to base case mode!\n")

    #gera os ficheiros -routes.dat, -source-destiny.in, -demand.in, -sdemand.in (trafego estatico e dinamico) e o -base.rou.xml (versao base usada que garante que os veiculos
    #sao do mesmo tipo que os usados na experiencia)
    #Nota: E' nesta funcao que se define que veiculos devem ser considerados estaticos (ou dinamicos)
    
    ifolder = tc["ifolder"]                     #input folder
    ofolder = tc["ofolder"] + "/inputdata"      #output folder
    netfile = ifolder + "/" + tc["netfile"]     #net file
    roufile = ifolder + "/" + tc["roufile"]     #inital route file
    obname  = ofolder + "/" + tc["bname"]      #output base name
    dynamicVTypes = tc["dynamicTypes"]         # possiveis ids dos veiculos dinamicos
    
    # gera ficheiros com informacao estatica do grafo, e ficheiros com os dados do trafego estatico e dinamico
    broufile = obname+"-base"+".rou.xml"
    SUMOToCSV_routes(netfile, roufile, obname, oroufile=broufile, dynamicVTypes=dynamicVTypes)


    #gera os ficheiros -tripinfo e o -emission (obter custos do SUMO)    
    runSUMO(netfile, broufile, obname, _guiversion)

    #gera os ficheiros CSV -tripinfo.csv, .edg.csv, nod.csv, -emission.csv e .edg-costs.csv
    SUMOSummaries_ToCSV_OptInput(netfile, roufile, obname, getNetworkData=True)




def interactive(tc, fcostWeights, fcostLabels, guiversion=False):
    print("Welcome to interactive mode!\n")
    print("Computing solutions...\n")
    
    netfile = tc["ifolder"] + "/" + tc["netfile"]     #net file
    ibname = tc["ofolder"] + "/inputdata/" + tc["bname"]
    ofolder = tc["ofolder"]
    dynamicTypes = tc["dynamicTypes"]
    onlyExtremalSols = tc["onlyExtremalSols"]
    
    commoninfo, solsinfo = getSolutions(ibname, ofolder, fcostWeights, fcostLabels, dynamicTypes, onlyExtremalSols)
    base_eval = commoninfo[-1]
    sols = solsinfo[0]
    
    comments = "objective functions: (" + ", ".join(map(lambda a: (str(a[0])+"*"+str(a[1])), zip(fcostWeights,fcostLabels))) + ")"
    
    sel = 0
    while sel >= 0:
        print("Base solution: %s\n" % str(base_eval[0]))
        print("Solutions (%d):" % len(sols))
        for i in range(len(sols)):
            print("%d) %s\n" % (i+1, str(sols[i][3])))
        
        sel = int(input("Enter solution number or -1 to exit\n"))
        if sel > 0:
            runSolution(netfile, commoninfo, solsinfo, sel-1, fcostLabels, guiversion=guiversion, comments=comments)
    
    
    
def runAll(tc, fcostWeights, fcostLabels, guiversion=False, plot=False):
    print("Run all mode!\n")
    print("Compute (Pareto-optimal) solutions...\n")
    
    netfile = tc["ifolder"] + "/" + tc["netfile"]     #net file
    ibname = tc["ofolder"] + "/inputdata/" + tc["bname"]
    ofolder = tc["ofolder"]
    dynamicTypes = tc["dynamicTypes"]
    onlyExtremalSols = tc["onlyExtremalSols"]
    
    commoninfo, solsinfo = getSolutions(ibname, ofolder, fcostWeights, fcostLabels, dynamicTypes, onlyExtremalSols)
    
    sols = solsinfo[0]
    base_eval = commoninfo[-1]
    
    comments = "objective functions: (" + ", ".join(map(lambda a: (str(a[0])+"*"+str(a[1])), zip(fcostWeights,fcostLabels))) + ")"
    
    print("Base solution: %s\n" % str(base_eval[0]))
    print("Solutions (%d):" % len(sols))
    for i in range(len(sols)):
        print("Solution %d) %s\n" % (i+1, str(sols[i][3])))

        runSolution(netfile, commoninfo, solsinfo, i, fcostLabels, guiversion=guiversion, comments=comments)
    
    if plot:
        outFolder = commoninfo[-2]
        plotExample(outFolder, fcostLabels)
    
    
if __name__ == "__main__":
    args = readArguments()
    tc = getTestcase(args.t) # test case
    setupRecords(tc)
    
    fcostLabels = np.array([args.obj1, args.obj2])
    fcostWeights = np.array([args.w1, args.w2])
    
    ix = np.argsort(fcostLabels)
    fcostLabels, fcostWeights = fcostLabels[ix], fcostWeights[ix]
    
    if args.mode == 1:
        runBaseCase(tc)
    elif args.mode == 2:
        interactive(tc, fcostWeights, fcostLabels, guiversion=args.gui)
    elif args.mode == 3:
        runAll(tc, fcostWeights, fcostLabels, guiversion=args.gui, plot=args.plot)
