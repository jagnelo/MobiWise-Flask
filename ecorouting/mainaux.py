import numpy as np
from MobiGraph import *

from SUMOinout import *
#from TrafficGenerator import *

import glob, ntpath
import os, shutil

import time


    
"""
    Corre o SUMO (a variavel global _sumocmd define se e' usada a versao
    grafica ou nao).
    testcase:       nome do caso de teste
    trafficName:    sufixo do ficheiro de trafego usado como input
    inFolder:       pasta de input que contem uma pasta com o nome do testcase,
                    pasta essa que contem o ficheiro da rede .net.xml com o mesmo
                    nome que o testcase
    outFolder:      pasta de output que contem uma pasta com o nome do testcase,
                    pasta essa que contem o ficheiro de trafego .rou.xml com o
                    nome cujo prefixo e' o testcase e o sufixo e' o trafficname.
                    E' nesta pasta que vao ser guardados os ficheiros gerados pelo
                    SUMO, dois ficheiros com o testcase com mesmo nome que o
                    ficheiro do trafego e com sufixo "-emission" e "-tripinfo"
"""
def runSUMO(netfile, roufile, obname, guiversion=True):
    sumocmd = "sumo-gui --gui-settings-file gui-settings.xml" if guiversion else "sumo"
    
    cmd = sumocmd+" --net-file "+netfile+" --route-files "+roufile+" --tripinfo-output "+obname+"-tripinfo --device.emissions.probability 1.0 --emission-output.precision 6 --additional-files moreOutputInfo.xml --collision.action warn -S --quit-on-end --time-to-teleport -1"

    startt = time.time()
    os.system(cmd)
    endt = time.time()
    print("\nSUMO Simulation time: %.3f seconds" % (endt-startt))
    
    shutil.move("basecars-emission-by-edges-out.xml", obname+"-emissions.xml")
    shutil.move("edge-data-out.xml", obname+"-edgdata.xml")
    #shutil.move("ecocars-emission-by-edges-out.xml", obname+"-ecocars-emissions.xml")
    

def readAllRoutes(fname):
    f = open(fname, "r")
    routes = [line.split() for line in f]
    f.close()
    return routes



""" Get traffic info of sdemand for a given set of routes
    sdemand - list of pairs (deptime, routeid, arcid)
    routes -  available routes
"""
def sdemandToSmartTraffic(sdemand, routes):
    ncars = len(sdemand)
    nr = len(routes)
    
    zeroRoot = [i for i in range(len(sdemand)) if sdemand[i][2] == 0]
    otherRoot = [i for i in range(len(sdemand)) if sdemand[i][2] != 0]
    
    vehicles = []

    nv = 0    
    if len(otherRoot) == 0:
        sroutes = routes

        nr = len(zeroRoot)
        for (dt, r, a) in sdemand:
            rid = zeroRoot[int(r) % nr] #id in routes
    
            nv += 1
            vehicles.append((dt, nv, rid))
    else:
        np.random.seed(1)
        sroutes = []
        sroutesd = {}
        vehicles = []
        nsr = 0 #number of routes in sroutes
        
        maxid = max([max(map(int, r)) for r in routes])
        count = np.zeros(maxid+1)
        
        for r in routes:
            for arc in r:
                count[int(arc)] += 1
        ev = np.array([sum(count[map(int, r)]) for r in routes])
    
            
        ix = np.argsort(ev)
        routes = [routes[i] for i in ix]
        ev = ev[ix]
        ixr = map(int, np.random.beta(1,3, size=ncars)*nr)
        
        nv = 0
        count = np.zeros(nr) #statistics
        for (dt, r, a) in sdemand:
            rid = ixr[nv]
            count[rid] += 1
            na = len(routes[rid]) - 2 #para nao ser nem o primeiro nem o ultimo
        
            aid = 0
    
            route = routes[rid][aid:]
            routestr = "#".join(map(str, route))
            
            if routestr in sroutesd:
                srid = sroutesd[routestr] #id in sroutes
            else:
                srid = nsr
                sroutesd[routestr] = srid
                sroutes.append(route)
                nsr += 1
            nv += 1
            vehicles.append((dt, nv, srid))
    return sroutes, vehicles
        
    

def getSolutions(ibname, ofolder, fcostWeights, fcostLabels, dynamicTypes=["Car"], onlyExtremalSols=True):
    
    testcase = ibname.split("/")[-1]
    outFolder = ofolder + "/" + "-".join(fcostLabels)
    
    #get demands
    sourcedestf = ibname+"-source-destiny.in"
    demandf = ibname+"-demand.in"
    sdemandf = ibname+"-sdemand.in"
    
    #select graph
    rfile =  ibname +"-routes.dat" #all routes
    nfile =  ibname +".edg.csv" #arcs info
    cstfile = ibname +".edg-costs.csv" #arcs info
    pfile =  ibname +".nod.csv" #node position info
    
    arcs, link2Nodes, linkData, nodePosition = SUMOToMWGraphData(nfile, cstfile, pfile)
    stopCosts = {}
    
    allroutes = readAllRoutes(rfile)
    
    #create base graph
    speedcapl = "onePerSec" # "maxspeed"
    mwgraph = MWGraph(arcs, link2Nodes, linkData, nodePosition=nodePosition, speedcapl=speedcapl)
    
    #static routes
    #sdemand = np.loadtxt(sdemandf, dtype=int)
    sdemand = np.loadtxt(sdemandf, dtype=float)
    sroutes, svehicles = sdemandToSmartTraffic(sdemand, allroutes) #generate Traffic
    sroutes, svehicles, sflowd = mwgraph.trafficFlow(sroutes, svehicles, mode=2)
    
    demandstr = ntpath.basename(demandf)[7:-3]
    demand = [(1, d) for d in np.loadtxt(demandf).ravel()]
    sourcedest = np.genfromtxt(sourcedestf, dtype=str, comments=None) #assume, for now, that there is a single source and destiny
    
    if len(sourcedest.shape) == 1:
        nodes, nodet = sourcedest
        sourcedest = sourcedest[np.newaxis,:]
    else:
        nodes, nodet = sourcedest[:,0], sourcedest[:,1]
    
    
    #--------- OPTIMIZE ON THE ORIGINAL GRAPH ---------------#
    

    evbase = SUMOToMWEvaluation(ibname+"-tripinfo.csv", vTypes=dynamicTypes)
    base_eval = np.array([[evbase[fcostLabels[j]] for j in range(len(fcostLabels))]])
    
    
    startt = time.time()
    flowsc, flowsd = mwgraph.minCostStaticMOP(demand, nodes, nodet, fcostLabels, fcostWeights=fcostWeights, sflow=sflowd, fixCapacity=1000000, onlyExtremalSols=onlyExtremalSols, fnamemop="minCostFlowMOP")
    endt = time.time()
    print("Solver runtime: %.3f seconds" % (endt-startt))
    

    n = len(flowsc)
    d = len(fcostLabels)
    pred_eval = np.zeros((n,d))
    sim_eval = np.zeros((n,d))
    
    
    #dictionaries with evals
    predevals = []
    simevals = []
    i = 0
    
    sols = []
    solsFolder = []
    solsBName = []
    for flowc, flowd in zip(flowsc, flowsd):
        ev = mwgraph.evaluateFlow(flowd)
        
        solsFolder.append(outFolder+"/solution"+str(i+1))
        if not os.path.exists(solsFolder[-1]):
            os.makedirs(solsFolder[-1])
        
        fname = solsFolder[-1]+ "/" + testcase
        solsBName.append(fname)
        saveEvaluation(ev, fname+"-pred.ev")
        printEvaluation(ev)
        
        for j in range(len(fcostLabels)):
            pred_eval[i,j] = ev[fcostLabels[j]]
            
        predevals.append(ev)
        simevals.append({})
        sols.append((flowc, flowd, ev, pred_eval[i]))
            
        print("objs: %r" % flowc)
        i += 1
        
    print("pred: %r" % pred_eval)
    #print "sim:", sim_eval
    print("base: %r" % base_eval)
    saveResultsMOP(predevals, fcostLabels, outFolder+"/pred.eval")
    saveResultsMOP([evbase], fcostLabels, outFolder+"/base.eval")
    
    
    commoninfo = (mwgraph, demand, sourcedest, sroutes, svehicles, dynamicTypes, outFolder, base_eval)
    solsinfo = (sols, sim_eval, simevals, pred_eval, solsBName)
    return commoninfo, solsinfo


def saveEvaluation(ev, fname):
    f = open(fname, "w")
    ls = ev.keys()
    ls = sorted(ls)
    for l in ls:
        f.write(l+"\t"+str(ev[l])+"\n")
    f.close()


#print output
def printEvaluation(ev):
    
    print("evaluation:")
    labels = ev.keys()
    labels = sorted(labels)
    for l in labels:
        print("%r:\t%.2f" % (l,ev[l]))



"""
    Guarda a avaliacao (todos os custos) de um conjunto de solucoes
    evalsd:         Uma lista de dicionarios. Todos os dicionarios na lista tem
                    as mesmas chaves. As chaves indicam o custo (ex.: ttime, length, cost_co,...).
    fcostLabels:    Lista das labels usadas na optimizao (por exemplo, ["ttime", "cost_co"]).
                    Na pratica, esta lista so e usada para dar o nome 'a pasta
                    onde vao ser guardados os resultados e por isso e apenas uma recomendacao,
                    pois pode-se colocar outros nomes na lista.
    prefix:         prefixo do nome do ficheiro gerado (deve identificar
                    a que caso se referem os dados evalsd)
"""
def saveResultsMOP(evalsd, fcostLabels, fname):
    
    ix = np.argmax([len(evalsd[i]) for i in range(len(evalsd))])
    clabels = list(evalsd[ix].keys())
    clabels.sort()
    
    n = len(evalsd)
    d = len(clabels)
    evals = np.zeros((n,d))
    for i in range(n):
        if len(evalsd[i]) >= len(fcostLabels):
            for j in range(d):
                evals[i,j] = evalsd[i][clabels[j]]
            
    labelsstr = " ".join(clabels)
    
    np.savetxt(fname, evals, header=labelsstr)
    
    
    
    
def runSolution(netfile, commoninfo, solsinfo, sel, fcostLabels, guiversion=True, comments=""):
    
    (mwgraph, demand, sourcedest, sroutes, svehicles, dynamicTypes, outFolder, base_eval) = commoninfo
    (sols, sim_eval, simevalsd, pred_eval, solsBName) = solsinfo
    
    flowc, flowd, ev, predev = sols[sel]
    obname = solsBName[sel]
    
    roufile = obname+".rou.xml"
    #flow -> routes and traffic info
    routes, vehicles = mwgraph.getFlowDescription(flowd, demand, sourcedest, mode=2)
    
    #Traffic summary
    printTrafficSummary(routes, vehicles)
    
    fname = obname +".simev.perVeh.csv"
    printPredictedEvPerVehicle([mwgraph.evaluateRoute(routes[r]) for (_,_,r) in vehicles], vehicles, fname)

    comments +="\n" + "\n".join(map(str, ev.items()))

    printSUMORoutes(routes, vehicles, obname+".rou.xml", sroutes=sroutes, svehicles=svehicles, comments=comments)
    saveEvaluation(ev, obname+"-pred.ev")
    
    runSUMO(netfile, roufile, obname, guiversion=guiversion)
    
    SUMOSummaries_ToCSV_OptInput(netfile, roufile, obname, getNetworkData=False)
    
    evsumo = SUMOToMWEvaluation(obname+"-tripinfo.csv", vTypes=dynamicTypes)
    
    #os.system("rm "+obname+ "*emission*")
    printEvaluation(ev)
    printEvaluation(evsumo)
    saveEvaluation(evsumo, fname+"-sim.ev")
    
    
    for j in range(len(fcostLabels)):
        sim_eval[sel,j] = evsumo[fcostLabels[j]]
        
    simevalsd[sel] = evsumo
    
    print("predicted values: %r\n" % pred_eval)
    print("simulation values: %r\n" % sim_eval)
    
    saveResultsMOP(simevalsd, fcostLabels, outFolder+"/sim.eval")
    
    return evsumo




def printTrafficSummary(routes, vehicles):
    countPerRoute = {r: 0 for r in routes.keys()}
    for _, _, rid in vehicles:
        countPerRoute[rid] += 1
    print("\nTraffic summary:")
    for r, c in countPerRoute.items():
        print("\troute %d: %d" % (r, c))
    print("\nroutes:")
    for rid, r in routes.items():
        print("\troute %d: %s" % (rid, " ".join(r)))
