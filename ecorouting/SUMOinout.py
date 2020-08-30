import numpy as np
#from MobiGraph import *
import xml.etree.ElementTree as ET


def filterNodeName(name):
    if name.startswith("J-"):
        return name.split("-")[1]
    return name


def routes2Graph(netfile, roufile, excludeRoadTypes=[]):
    routes = []
    
    tree = ET.parse(roufile)
    root = tree.getroot()
    nr = 0
    
    #read successors from routes' file
    for child in root:
        if child.tag == "route":
            route = child
            edges = route.attrib.get("edges").split()
            routes.append(edges)
            
    edgsuccessors = {}
    for r in routes:
        for i in range(len(r)-1):
            if r[i] in edgsuccessors:
                if r[i+1] not in edgsuccessors[r[i]]:
                    edgsuccessors[r[i]].append(r[i+1])
            else:
                edgsuccessors[r[i]] = [r[i+1]]
                
    alledges = set(edgsuccessors.keys())
    for edge in edgsuccessors.keys():
        alledges.update(edgsuccessors[edge])
        
    nodesd = {}
    edgesd = {}
    jintedges = {}
    
    #read node and arc info from net file
    tree = ET.parse(netfile)
    root = tree.getroot()
    for child in root:
        #get info of normal arcs
        if child.tag == "edge" and (child.attrib.get("id") in alledges or child.attrib.get("id").startswith(":")): 
            lane = child.findall("lane")[0]
            etype = child.attrib.get("type")
            if lane is not None and etype not in excludeRoadTypes:
                edgesd[child.attrib.get("id")] = {"from": child.attrib.get("from"), "to": child.attrib.get("to"), "speed": lane.attrib.get("speed"), "length": lane.attrib.get("length"), "lanes": str(len(child.findall("lane")))}
                
        elif child.tag == "junction":
            nid = child.attrib.get("id")
            nodesd[nid] = {'x': child.attrib.get("x"), 'y': child.attrib.get("y")}
            jintedges[nid] = list(map((lambda intlane: intlane[:intlane.rfind("_")]), child.attrib.get("intLanes").split()))
    
    return edgesd, nodesd, edgsuccessors, jintedges


#16/12/2019
# Cada arco que entra num no N, passa a ter como no de chegada o no N-i-F (i e' o i-nesimo arco
# a entrar no no' N.
# Cada arco que sai de um no M, passa a ter como no de partida o no M-j-T (j e' o j-nesimo arco
# a sair do no M.
# Sao criados arcos do tipo N-i-F -> N-j-T se o j-nesimo arco a sair de N for um arco sucessor
# do inesimo arco a entrar em N (se existir uma rota que comprove essa sucessao)
def expandNodes(edgesd, nodesd, edgsuccessors):

    edgesk = edgesd.keys()
    nodesk = nodesd.keys()
    n = len(nodesd)
    
    inarcs = {}
    outarcs = {}
    nodecount = {}
    newedges = {}
    viaArcs = {}
    for e in edgesk:
        if not e.startswith(":"):
            if edgesd[e]["from"] not in outarcs:
                outarcs[edgesd[e]["from"]] = 1
            else:
                outarcs[edgesd[e]["from"]] += 1
                
            nd = edgesd[e]["from"]
            x, y = nodesd[nd]['x'], nodesd[nd]['y']
            node2 = "J-"+edgesd[e]["from"]+"-"+str(outarcs[edgesd[e]["from"]])+"T"
            edgesd[e]["from"] = node2
            
            nodesd[node2] = {'x': x, 'y': y}
            
            if edgesd[e]["to"] not in inarcs:
                inarcs[edgesd[e]["to"]] = 1
            else:
                inarcs[edgesd[e]["to"]] += 1
                
            nd = edgesd[e]["to"]
            x, y = nodesd[nd]['x'], nodesd[nd]['y']
            node1 = "J-"+edgesd[e]["to"]+"-"+str(inarcs[edgesd[e]["to"]])+"F"
            edgesd[e]["to"] = node1
            nodesd[node1] = {'x': x, 'y': y}
            
            
    for e1 in edgsuccessors.keys():
            
        for e2 in edgsuccessors[e1]:
            nd = edgesd[e1]["to"]
            if nd.startswith("J-"):
                nd = nd.split("-")[1]
            if nd not in nodecount:
                nodecount[nd] = 1
            else:
                nodecount[nd] += 1
            i = nodecount[nd]
                
            x, y = nodesd[nd]['x'], nodesd[nd]['y']
            baseid = "J-"+nd+"-"+str(i)

            if edgesd[e1]["to"].startswith("J-"):
                node1 = edgesd[e1]["to"]
            else:
                node1 = baseid+"F"

            if edgesd[e2]["from"].startswith("J-"):
                node2 = edgesd[e2]["from"]

            else:
                node2 = baseid+"T"

            edgesd[e1]["to"] = node1
            edgesd[e2]["from"] = node2
            newedges[baseid] = {"from": node1, "to": node2, "speed": 100, "length":0, "lanes":1}
            viaArcs[(e1, e2)] = baseid
            
    edgesd.update(newedges)
    for node in nodecount.keys():
        del(nodesd[node])
        
    return edgesd, nodesd, viaArcs
    


def SUMOToCSV_networkNnodes(netfile, roufile, obname):

    edgesd, nodesd, edgsuccessors, jintedges = routes2Graph(netfile, roufile)
    edgesd, nodesd, fixedges = expandNodes(edgesd, nodesd, edgsuccessors)

    jlengths = {}
    for node in jintedges.keys():
        ni = len(jintedges[node])
        ws = np.zeros(ni)
        i = 0
        baselink = "J-"+node
        data = {}
        
        cs = []
        i = 0
        for edge in jintedges[node]:
            
            if edge in edgesd:
                cs.append(float(edgesd[edge]["length"]))
                i += 1
        n = len(cs)
        cs = sum(cs)/n if n > 0 else 0
        jlengths["J-"+node] = cs


    #save to files
    nfile = open(obname+".nod.csv", "w")
    nfile.write("node_id\tx\ty\n")
    for nd in nodesd.keys():
        nfile.write("%s\t%s\t%s\n" % (nd, nodesd[nd]['x'], nodesd[nd]['y']))
    nfile.close()
    
    efile = open(obname+".edg.csv", "w")
    efile.write("link\tnlanes\tfrom\tto\tmaxspeed\tlength\n")
    for edge in edgesd.keys():
        if edge.startswith("J-"):
            edgesd[edge]["length"] = jlengths[edge[:edge.rfind("-")]]
        efile.write("%s\t%s\t%s\t%s\t%s\t%s\n" % (edge, edgesd[edge]["lanes"], edgesd[edge]["from"], edgesd[edge]["to"], edgesd[edge]["speed"], edgesd[edge]["length"]))
    efile.close()
    
    jfile = open(obname+".jintedges.csv", "w")
    jfile.write("junction\tedge\n")
    for edge in jintedges.keys():
        for intedge in jintedges[edge]:
            jfile.write("%s\t%s\n" % (edge, intedge))
    jfile.close()
    
    return edgesd, nodesd, {}, jintedges



#routes: dict (routeID, list_of_arc_ids)
#vehicles: list of (dep_time, vehicle_id, routeID)
#maxspeed (m/s) - default: 100km/h ~ 27.7 m/s
def printSUMORoutes(routes, vehicles, fname, sroutes=None, svehicles=[], comments="", maxspeed=27.7, depTimeFactor=1):
    f = open(fname, "w")
    
    f.write("<routes>\n")

    #angeja_estarreja
    #f.write("\t<vType id=\"SCar\" accel=\"2.5\" decel=\"4.0\" apparentDecel=\"3.8\" emergencyDecel=\"4.0\" sigma=\"0.7\" length=\"4.6\" tau=\"1.1\" minGap=\"3.3\" width=\"1.9\" maxSpeed=\"33.33\" speedFactor=\"0.95\" speedDev=\"0.2\" vClass=\"passenger\" />\n")
    #f.write("\t<vType id=\"Car\" accel=\"2.5\" decel=\"4.0\" apparentDecel=\"3.8\" emergencyDecel=\"4.0\" sigma=\"0.7\" length=\"4.6\" tau=\"1.1\" minGap=\"3.3\" width=\"1.9\" maxSpeed=\"33.33\" speedFactor=\"0.95\" speedDev=\"0.2\" vClass=\"passenger\" />\n")
    
    #Novo Porto (11/2019)
    f.write("<vType id=\"SCar\" length=\"4.75\" minGap=\"1.20\" maxSpeed=\"22.22\" vClass=\"private\" color=\"yellow\" decel=\"5.5\"/>")
    f.write("<vType id=\"Car\" length=\"4.75\" minGap=\"1.20\" maxSpeed=\"22.22\" vClass=\"private\" color=\"240,230,2\" decel=\"5.5\"/>")
    
    for rid, arcSeq in routes.items():
        arcs = []
        for a in arcSeq:
            if not a.startswith(":") and not a.startswith("J-"):
                arcs.append(a)
        arcSeq = arcs
        f.write("\t<route id=\"route%s\" edges=\"%s\"/>\n" % (rid, " ".join(arcSeq)))
    f.write("\n")
    
    if sroutes is not None:
        for rid, arcSeq in zip(range(len(sroutes)), sroutes):
            arcs = []
            for a in arcSeq:
                if not a.startswith(":") and not a.startswith("J-"):
                    arcs.append(a)
            arcSeq = arcs
            f.write("\t<route id=\"sroute%s\" edges=\"%s\"/>\n" % (rid, " ".join(arcSeq)))
        f.write("\n")
    
    nd = len(vehicles)
    ns = len(svehicles)
    
    vehicles.extend(svehicles)
    depTimes = np.array([dt for dt,_,_ in vehicles])
    ix = np.argsort(depTimes)
    for i in ix:
        dpt, carid, rid = vehicles[i]
        if i < nd:
            f.write("\t<vehicle depart=\"%.1f\" id=\"veh%s\" route=\"route%s\" type=\"Car\" color=\"1,0,0\" departSpeed=\"max\" />\n" % (depTimeFactor*dpt, carid, rid))
        else:
            f.write("\t<vehicle depart=\"%.1f\" id=\"sveh%s\" route=\"sroute%s\" type=\"SCar\" departSpeed=\"max\" />\n" % (depTimeFactor*dpt, carid, rid))
    
    f.write("\n\n<!--\n %s \n-->\n\n" % comments)

    f.write("\n</routes>\n")
    f.close()
    
    
    
    

#ROUTES
def SUMOToCSV_routes(netfile, roufile, obname, oroufile, dynamicVTypes=["EcoRoutingSN"]):
    
    edgesd, _, viad, _ = SUMOToCSV_networkNnodes(netfile, roufile, obname)
    pathsd = {}
    pathsdedge = {}
    
    rfile = open(obname+'-routes.dat', 'w')
    sdfile = open(obname+'-sdemand.in', 'w')
    dfile = open(obname+'-demand.in', 'w')
    sdefile = open(obname+'-source-destiny.in', 'w') #source and destiny edges
    drfile = open(obname+'-dyn-initial-routes-nodes.txt', 'w')
    
    vehicles, svehicles = [], []
    routes, sroutes = {}, {}
    sroutesl = []
    allroutes = {}
    nsv, ndv = 0, 0
    
    tree = ET.parse(roufile)
    root = tree.getroot()
    nr = 0
    for child in root:

        if child.tag == "route":
            route = child

            edges = route.attrib.get("edges").split()
            fixedges = [edges[0]]
            for i in range(len(edges)-1):
                if (edges[i], edges[i+1]) in viad:
                    fixedges.append(viad[(edges[i], edges[i+1])])
                fixedges.append(edges[i+1])
            edges = fixedges
            
            allroutes[route.attrib.get("id")] = edges
            

            nodes = [edgesd[edges[0]]["from"]]
            for edge in edges:
                nodes.append(edgesd[edge]["to"])

            pathsd[route.attrib.get("id")] = (nr, nodes)
            pathsdedge[route.attrib.get("id")] = (nr, edges)
            nr += 1
            rfile.write("%s\n" % " ".join(map(filterNodeName, nodes)))

        elif child.tag == "vehicle":

            vehicle = child

            if vehicle.attrib.get("type") not in dynamicVTypes:

                sdfile.write("%s\t%d\t%d\n" % (vehicle.attrib.get("depart").replace(",","."), pathsd[vehicle.attrib.get("route")][0], 0))
                
                #get static routes and vehicles
                srouteid = vehicle.attrib.get("route")
                srid = sroutes[srouteid][0] if srouteid in sroutes else len(sroutes)
                sroutes[srouteid] = (srid, allroutes[srouteid])
                
                svehicles.append((float(vehicle.attrib.get("depart").replace(",",".")), nsv, srid))
                if srid == len(sroutesl):
                    sroutesl.append(allroutes[srouteid])
                nsv += 1
                
            else:
                dfile.write("%s\n" % vehicle.attrib.get("depart").replace(",","."))
                
                path = pathsd[vehicle.attrib.get("route")][1]
                pathe = pathsdedge[vehicle.attrib.get("route")][1]
                sdefile.write("%s %s\n" % (path[0], path[-1]))
                
                drfile.write("%s\n" % " ".join(pathe))
                
                #get dynamic routes and vehicles
                routeid = vehicle.attrib.get("route")
                rid = routes[routeid][0] if routeid in routes else len(routes)
                routes[routeid] = (rid, allroutes[routeid])
                vehicles.append((float(vehicle.attrib.get("depart").replace(",",".")), ndv, rid))
                ndv += 1
                
                
                
    routes = {r[0]: r[1] for r in routes.values()}
    sroutes = sroutesl
    
    #save base routes
    printSUMORoutes(routes, vehicles, oroufile, sroutes=sroutes, svehicles=svehicles)
                
    rfile.close()
    sdfile.close()
    dfile.close()
    sdefile.close()
    drfile.close()
    
    


               
def SUMOToCSV_tripinfo(bname):
    
    tree = ET.parse(bname + '-tripinfo')
    root = tree.getroot()
    with open(bname+'-tripinfo.csv', 'w') as file:

        file.write("vType\tveh_id\tdepart\tdepart_edge\tdepart_delay\tarrival\tarrival_edge\tduration\troute_length\tCO\tCO2\tHC\tPMx\tNOx"
                   "\tfuel\n")
        for child in root:
            for emission in child.findall("emissions"):
                file.write(""+child.attrib.get("vType")+"\t"+child.attrib.get("id")+"\t"+child.attrib.get("depart")+"\t"
                           +child.attrib.get("departLane").split("_")[0]+"\t"+child.attrib.get("departDelay")
                           +"\t"+child.attrib.get("arrival")+"\t"
                           + child.attrib.get("arrivalLane").split("_")[0] + "\t" + child.attrib.get("duration")+"\t"
                           + child.attrib.get("routeLength") + "\t" + emission.get("CO_abs") + "\t"
                           + emission.get("CO2_abs") + "\t" + emission.get("HC_abs") + "\t"
                           + emission.get("PMx_abs") + "\t" + emission.get("NOx_abs") + "\t"
                           + emission.get("fuel_abs") + "\t" 
                           )
                file.write('\n')



#EDGE-BASED EMISSIONS, AVG SPEED and, AVG TRAVELTIME
def SUMO_Emissions_ToCSV(bname, jintedges):
    name = bname + "-edgdata"
    
    tree = ET.parse(name + '.xml')
    root = tree.getroot()
    data = {}
    for child in root:
        for edge in child.findall("edge"):
            data[edge.attrib.get("id")] = {
                "speed": edge.get("speed", default="0"),
                "sampsecs": edge.get("sampledSeconds", default="0"),
                "entered": edge.get("entered", default="0"),
                "waitingTime": edge.get("waitingTime", default="0"),
                "overlapTraveltime": edge.get("overlapTraveltime", default="0"),
                "left": edge.get("left", default="0")
                }
    
    tree = ET.parse(bname + '-emissions.xml')
    root = tree.getroot()
    
    co = 0
    
    for child in root:
        for edge in child.findall("edge"):
            link = edge.attrib.get("id")
            data[link]["ttime"] = float(edge.get("traveltime", default="0"))
            data[link]["cost_co"] = float(edge.get("CO_perVeh", default="0"))
            data[link]["cost_co2"] = float(edge.get("CO2_perVeh", default="0"))
            data[link]["cost_hc"] = float(edge.get("HC_perVeh", default="0"))
            data[link]["cost_PMx"] = float(edge.get("PMx_perVeh", default="0"))
            data[link]["cost_nox"] = float(edge.get("NOx_perVeh", default="0"))
            data[link]["cost_fuel"] = float(edge.get("fuel_perVeh", default="0"))
            
            co += float(edge.get("CO_perVeh", default="0"))
                
    #lidar com arcos internos (agregar info)
    for node in jintedges.keys():
        ni = len(jintedges[node])
        ws = np.zeros(ni)
        i = 0
        for edge in jintedges[node]:
            ws[i] = data[edge]["left"]
            i += 1
        ws = ws/ws.sum() if ws.sum() > 0 else np.zeros(ni)
        baselink = "J-"+node
        data[baselink] = {}
        for label in ["ttime", "speed", "sampsecs", "entered", "left", "cost_co", "cost_co2", "cost_hc", "cost_PMx", "cost_nox", "cost_fuel"]:
            cs = np.zeros(ni)
            i = 0
 
            for edge in jintedges[node]:
                cs[i] = float(data[edge][label])
                i += 1
            if(ws.sum() <= 0): # se nao houver info dos custos nesta junction
                data[baselink][label] = 0 #1e9
            else:
                data[baselink][label] = (ws*cs).sum()
            
                
    with open(bname+'.edg-costs.csv', 'w') as file:
        file.write("link\tttime\tavgspeed\tsampledSeconds\tentered\tleft\tcost_co\tcost_co2\tcost_hc\tcost_PMx\tcost_nox\tcost_fuel\n")
        links = data.keys()
        links = sorted(links)
        for link in links:
            file.write(""+link+"\t"
                        +str(data[link]["ttime"])+"\t"
                        +str(data[link]["speed"])+"\t"
                        +str(data[link]["sampsecs"])+"\t"
                        +str(data[link]["entered"])+"\t"
                        #+str(data[link]["waitingTime"])+"\t"
                        +str(data[link]["left"])+"\t"
                        +str(data[link]["cost_co"])+"\t"
                        +str(data[link]["cost_co2"])+"\t"
                        +str(data[link]["cost_hc"])+"\t"
                        +str(data[link]["cost_PMx"])+"\t"
                        +str(data[link]["cost_nox"])+"\t"
                        +str(data[link]["cost_fuel"])
                        )
            file.write('\n')
            


# Para obter os dados da rede (opcional - so e preciso para inicializar a optimizacao) e do trafego
def SUMOSummaries_ToCSV_OptInput(netfile, roufile, bname, trafficname="-initdata-onePerRoute", getNetworkData=True, jintedges={}):
    if getNetworkData:
        _, _, _, jintedges = SUMOToCSV_networkNnodes(netfile, roufile, bname)
    SUMOToCSV_tripinfo(bname)
    SUMO_Emissions_ToCSV(bname, jintedges)

    return jintedges







    
#import data from SUMO (networkData and trafficData) and export to MWGraph data
def SUMOToMWGraphData(networkFile, networkCostFile, posFile=None):
    
    network = np.genfromtxt(networkFile, dtype=str, comments=None) #deixa de ignorar os comentarios porque os ids das edges podem ter cardinais
    nlabels, network = network[0], network[1:]
    
    networkcosts = np.genfromtxt(networkCostFile, dtype=str, comments=None)
    clabels, costs = networkcosts[0], networkcosts[1:]
    
    #get arcs
    ixf = np.where(nlabels == "from")[0][0]
    ixt = np.where(nlabels == "to")[0][0]
    arcs = {}
    
    for row in network:
        if row[ixf] in arcs:
            arcs[row[ixf]].append(row[ixt])
        else:
            arcs[row[ixf]]  = [row[ixt]]
        if row[ixt] not in arcs: #so that terminal nodes are in the adjacency list
            arcs[row[ixt]] = []
    
    #get link2Nodes
    ixl = np.where(nlabels == "link")[0][0]
    link2Nodes = {row[ixl]: (row[ixf], row[ixt]) for row in network}
    
    #get (static info of) linkData
    ixnl = np.where(nlabels == "nlanes")[0][0]
    ixlen = np.where(nlabels == "length")[0][0]
    ixms = np.where(nlabels == "maxspeed")[0][0]
    linkData = {row[ixl]: {"nlanes": int(row[ixnl]), "length": float(row[ixlen]), "maxspeed": float(row[ixms]), "minttime": float(row[ixlen])/float(row[ixms])} for row in network}
    
    #get (traffic info of) linkData 
    ixl = np.where(clabels == "link")[0][0]
    ixtt = np.where(clabels == "ttime")[0][0]
    ixavgs = np.where(clabels == "avgspeed")[0][0]
    
    costLabels = [label for label in clabels if label.startswith("cost")]
    ixsc = [np.where(clabels == costl)[0][0] for costl in costLabels]
    
    
    for link in link2Nodes.keys():
        linkname = link[:link.rfind("-")] if link.startswith("J-") else link
        ixs = np.where(costs[:, ixl] == linkname)[0]
    
        if len(ixs) > 0:
            linkData[link]["avgspeed"] = float(costs[ixs, ixavgs][0])
            linkData[link]["ttime"] = float(costs[ixs, ixtt][0])
        else: #TODO(14/12): Fix this! e suposto os J-...-? terem informacao no linkData (nem que seja zero)
            linkData[link] = {"avgspeed": 100, "ttime": 0, "length": 0, "maxspeed": 0}

        #print "ixsc:", ixsc
        for i in range(len(costLabels)):
            costl = costLabels[i]
            if len(ixs) > 0:
                linkData[link][costl] = float(costs[ixs, ixsc[i]][0])
            else: #TODO(14/12): Fix this! e suposto os J-...-? terem informacao no costs (nem que seja zero)
                linkData[link][costl] = 0
            
    if posFile is None:
        nodePosition = None
    else:
        data = np.genfromtxt(posFile, dtype=str, comments=None)[1:]
        nodePosition = {row[0]: row[1:].astype(float) for row in data}
            
    return arcs, link2Nodes, linkData, nodePosition




#fname indica qual o ficheiro -tripinfo.csv que deve ser avaliado"
def SUMOToMWEvaluation(fname, vTypes=["Car"]):
    data = np.genfromtxt(fname, dtype=str, comments=None)
    sumols = ["duration", "route_length", "CO", "CO2", "PMx", "NOx", "HC", "fuel"]
    mwls = ["ttime", "length", "cost_co", "cost_co2", "cost_PMx", "cost_nox", "cost_hc", "cost_fuel", "cost_hc"]

    ixvid = np.where(data[0,:] == "vType")[0]

    ixdyn = [i for i in range(1, len(data)) if data[i,ixvid][0] in vTypes]

    ev = {}
    for sl, mwl in zip(sumols, mwls):
        ix = np.where(data[0,:] == sl)[0]
        ev[mwl] = np.sum(data[ixdyn,ix[0]].astype(float))
    
    ev["delay_ttime"] = 0
    ix = np.where(data[0,:] == "depart_delay")[0]
    ev["delay_ttime"] += np.sum(data[ixdyn,ix[0]].astype(float))

    return ev




def printPredictedEvPerVehicle(evs, vehicles, fname):
    print("evs, veh size: %d %d\n" % (len(evs), len(vehicles)))
    labels = evs[0].keys()
    with open(fname, "w") as f:
        f.write("carid\t%s\n" % "\t".join(labels))
        for ev, veh in zip(evs, vehicles):
            f.write(str(veh[1])+"\t")
            f.write("%s\n" % "\t".join(map(str, [ev[label] for label in labels])))
