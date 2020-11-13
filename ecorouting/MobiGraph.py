import numpy as np
import time
import os


def _filterNodeName(name):
    if name.startswith("J-"):
        return name.split("-")[1]
    return name

def _updateCap(linkData, speedl="avgspeed", vSize=5, mindist=10):
    for link in linkData.keys():
        if speedl == "onePerSec":
            linkData[link]["_cap"] = 1
        else:
            linkData[link]["_cap"] = max(1,_iround(linkData[link]["nlanes"] * (linkData[link][speedl]/(vSize+mindist))))


def _iround(a):
    return int(round(a))


class MWGraph(object):
    __name__ = "MobiGraph"
    arcs = {}       #dict (k,v):  nodeA : [node1, node2,...noden] #arcos que saiem de cada no
    link2Nodes = {} #dict (k,v): "link" : (nodeA, nodeB)          #o "link" corresponde ao arco
                                                                  #do nodeA para o nodeB
    linkData = {}    #dict (k,v): "link" : {"attr1": valor, "attr2": valor, etc}
                                 # "attr" e um dos labels pre-definidos ou opciais (atributos de custo)
        
    def __init__(self, arcs, link2Nodes, linkData, nodePosition=None, vSize=5, speedcapl="maxspeed"):
        
        self.arcs, self.link2Nodes, self.linkData, self.nodePosition = arcs, link2Nodes, linkData, nodePosition
        self.vSize = vSize
        self.nodes2Link = {(nodes[0], nodes[1]): link for link, nodes in link2Nodes.items()}
        
        self.labels = list(linkData[list(linkData.keys())[0]].keys()) 
        
        self.costlabels = list(filter(lambda x: x.startswith("cost_"), self.labels)) 
        
        self.speedcapl = speedcapl
        if "_cap" not in linkData[list(linkData.keys())[0]]:
            _updateCap(linkData, speedl=speedcapl, vSize=self.vSize)
            
            
            
    """
        Get the flow corresponding to the routes and vehicles given
    """
    def trafficFlow(self, routes, vehicles, mode=1):
        
        nrs = len(routes)
        
        routes = [[arc for arc in route] for route in routes]
        routes = list(map(self.sumoRoute, routes))
        
        counts = np.zeros(nrs)
        for _, _, rid, _ in vehicles:
            counts[rid] += 1
                
        sflowd = {node: {} for node in self.arcs.keys()}
        for rid in range(nrs):
            c = counts[rid]
            if c > 0:
                route = routes[rid]
                                   
                for i in range(len(route)-1):
                    nodeA = route[i]
                    nodeB = route[i+1]
                    
                    if (nodeA, nodeB) in self.nodes2Link:
                        link = self.nodes2Link[(nodeA, nodeB)]
                        sflowd[nodeA][nodeB] = c if nodeB not in sflowd[nodeA] else sflowd[nodeA][nodeB] + c
        
        if mode == 2:
            routesA = []
            for r in routes:
                routesA.append(self.nodePathToArcPath(r))
            routes = routesA
                
        return routes, vehicles, sflowd
    
    
    def sumoRoute(self, route):
        sumoroute = []
        for i in range(len(route)-1):
            nodeA = route[i]
            nodeB = route[i+1]
            
            if (nodeA, nodeB) not in self.nodes2Link:
                pairs = [(ndA, ndB) for (ndA, ndB) in self.nodes2Link.keys() if _filterNodeName(ndA) == nodeA and _filterNodeName(ndB) == nodeB]
                link = self.nodes2Link[pairs[0]]

                if len(sumoroute) == 0:
                    if pairs[0][0].startswith("J-"):
                        pass
                    else:
                        sumoroute.append(pairs[0][0])

                if pairs[0][0].startswith("J-"):
                    sumoroute.append(pairs[0][0])

                sumoroute.append(pairs[0][1])

                if sumoroute[-1] == nodeA or len(pairs) > 1:
                    raw_input("something is wrong...")

        return sumoroute
    
    
    
    #convert sequence of nodes to sequence of arcs
    def nodePathToArcPath(self, path):
        arcs = []
        for i in range(1, len(path)):
            if (path[i-1], path[i]) in self.nodes2Link: #este e um fix around... pode nao funcionar sempre...
                arcs.append(self.nodes2Link[(path[i-1], path[i])])
        return arcs



    
    def minCostStaticMOP(self, demand, nodes, nodet, fcostLabels, fcostWeights=None, sflow=None, fixCapacity=-1, onlyExtremalSols=True, fnamemop="moProblem"):
        
        if fcostWeights is None:
            fcostWeights = [1] * len(fcostLabels)
        
        ixToNodes = list(self.arcs.keys())
        nodesToix = {ixToNodes[i]: i for i in range(len(ixToNodes))}
        links = list(self.linkData.keys())
        
        start_nodes = [nodesToix[self.link2Nodes[link][0]] for link in links]
        end_nodes = [nodesToix[self.link2Nodes[link][1]] for link in links]
        maxcapacities = [self.linkData[link]["_cap"] for link in links]
        
        #"static" traffic prediction
        capacities = maxcapacities
        
        if fixCapacity > 0:
            capacities = [fixCapacity for c in capacities] #reduce capacity
        else:
            if sflow is not None:
                capacities = [max(0, maxcapacities[i]-sflow[ixToNodes[start_nodes[i]]][ixToNodes[end_nodes[i]]]) if ixToNodes[start_nodes[i]] in sflow and ixToNodes[end_nodes[i]] in sflow[ixToNodes[start_nodes[i]]] else maxcapacities[i] for i in range(len(start_nodes))]
            #else:
                capacities = maxcapacities

        #supply
        supplies = [0] * len(ixToNodes)

        if isinstance(demand, int):
            if isinstance(self, TEMWGraph):
                nodes = str(nodes)+".0"
                nodet = str(nodet)+"."+str(self.ntstamps)
        
            supplies[nodesToix[nodes]] = demand
            supplies[nodesToix[nodet]] = -demand
        
        else: #demand is a list of trios (demand, timeunit, vtype)
            tdemand = 0
            if isinstance(nodes, str) or len(nodes) == 1:
                nodes = [nodes] * len(demand)
                nodet = [nodet] * len(demand)
                
            for (dem, depTime, _), source, target in zip(demand, nodes, nodet):
                supplies[nodesToix[str(source)]] += dem
                supplies[nodesToix[str(target)]] -= dem
        
        ixnotzero = np.where(np.array(supplies) != 0)[0]
        
        writeMOPFile(self.linkData, ixToNodes, links, start_nodes, end_nodes, supplies, capacities, fcostWeights, fcostLabels, fname=fnamemop+".mop")
        
        opts = "-x" if onlyExtremalSols else ""
        runMOP(fnamemop+".mop", opts=opts) #-x
        flowsCost, flowsDict =  readMOPfile(self.link2Nodes, ixToNodes, "solutions_"+fnamemop+".txt")
        
        vflowsCost, vflowsDict = [], []
        for flowc, flowd in zip(flowsCost, flowsDict):
            if not self.checkFlow(supplies, flowd, nodesToix, ixToNodes):
                raw_input("Something's wrong!")
            else:
                vflowsCost.append(flowc)
                vflowsDict.append(flowd)
            
        return vflowsCost, vflowsDict
    
    
    
    def checkFlow(self, supplies, flowd, nodesToix, ixToNodes):
        balance = [0] * len(supplies)
        for nodes in flowd.keys():
            for nodet in flowd[nodes].keys():
                c = flowd[nodes][nodet]
                balance[nodesToix[nodes]] += c
                balance[nodesToix[nodet]] -= c
                
        supplies, balance = np.array(supplies), np.array(balance)
        ix = np.where(supplies != balance)[0]
        if len(ix) > 0:
            print("differences in %r %r %r" % (ix, np.array(ixToNodes)[ix], supplies[ix], balance[ix]))
        return (balance == supplies).all()
        
        
    def evaluateFlow(self, flowd):
        
        evallabels = list(self.costlabels) #Py2
        evallabels.extend(["length", "ttime"])
        ev = {clabel: 0 for clabel in evallabels}
        
        tmp = 0
        tmp2 = 0
        for nodeA in flowd.keys():
            for nodeB in flowd[nodeA].keys():
                link = self.nodes2Link[(nodeA, nodeB)]
                if self.linkData[link]["avgspeed"] == self.linkData[link]["maxspeed"]:
                    tmp += self.linkData[link]["length"]
                else:
                    tmp2 += self.linkData[link]["length"]
                nflowunits = flowd[nodeA][nodeB]
                if nflowunits > 0:
                    for elabel in evallabels:
                        ev[elabel] += nflowunits * self.linkData[link][elabel]
        
        return ev
    
    
    def getFlowDescription(self, flow, demand, sourcedest, mode=1):
        routes, routesT = {}, {}
        vehicles = []
        r = 0 #n routes
        t = 0 #n timeunits
        v = 0 #n vehicles
        
        if not isinstance(demand, int):
            dmnd = []
            vtps = []
            sdest = []
            
            for (dem, depTime, vtype), sd in zip(demand, sourcedest):
                dmnd.extend([depTime]*dem)
                vtps.extend([vtype])
                sdest.extend([sd]*dem)
            dmnd = np.asarray(dmnd)
            vtps = np.asarray(vtps)
            sdest = np.asarray(sdest)
            ix = np.argsort(dmnd)
            demand = dmnd[ix]
            vtypes = vtps[ix]
            sourcedest = sdest[ix]
            
            
        ivehToRoute = np.arange(len(sourcedest))
        vehicles = [(dep, -1, -1, vtype) for dep, vtype in zip(demand, vtypes)]
        
        startnodes = np.unique(sourcedest[:,0])
        
        for path in self.flowToPaths(flow, startnodes=startnodes):
            pathstr = "#".join(path)
            if pathstr in routesT:
                rid = routesT[pathstr]
            else:
                r += 1
                routes[r] = path
                routesT[pathstr] = r
                rid = r
                
            ix = np.where((sourcedest[ivehToRoute] == (path[0], path[-1])).all(axis=1))[0]
            v = ivehToRoute[ix[0]]
            ivehToRoute = np.delete(ivehToRoute, ix[0])
            vehicles[v] = (vehicles[v][0], v, rid, vehicles[v][3])
            t += 1
            
        #convert routes to sequence of arcs
        if mode == 2:
            routesA = {}
            for r, path in routes.items():
                routesA[r] = self.nodePathToArcPath(path)
            routes = routesA
        
        return routes, vehicles
            
            
    def flowToPaths(self, flowd, startnodes=None):
        
        flowd = {k: {k2: v for k2, v in flowd[k].items() if v > 0} for k in flowd.keys()}
        
        inf = {k: 0 for k in flowd.keys()}
        outf = {k: 0 for k in flowd.keys()}
        for k in flowd.keys():
            for k2, v in flowd[k].items():
                inf[k2] += v
                outf[k] += v
        
        if startnodes is None:
            startnodes = []
            for k in flowd.keys():
                if outf[k] > inf[k]:
                    startnodes.append(k)
        
        
        for nodes in startnodes:
            npaths = outf[nodes]-inf[nodes]
        
            stack = [(nodes, [nodes])]*npaths
            
            while len(stack) > 0:
            
                (node, path) = stack.pop()
                foundnxt = False
                for nxt in flowd[node].items():
                    if foundnxt:
                        break
                    nd, n = nxt #nd - next node, n - number of sent units
                    if n > 0:
                        flowd[node][nd] -= 1
                        
                        if len(flowd[nd]) == 0:
                            yield path + [nd] # add target node
                            foundnxt = True
                        else:
                            stack.append((nd, path + [nd]))
                            foundnxt = True
                
                if not foundnxt:
                    #print "current flow:", flowd
                    #print "path:", path
                    #print "stack:", stack
                    #print "node:", node
                    #print "flowd[node].items():", flowd[node].items()
                    raw_input("something is wrong!")
                    
                    
    #esta versao permite avaliacao parcial de fluxos
    def evaluateRoute(self, route):
        evallabels = list(self.costlabels) #Py2
        evallabels.extend(["length", "ttime"])
        ev = {clabel: 0 for clabel in evallabels}
        
        whichlinksevs = {clabel: [] for clabel in evallabels}
        for link in route:
            for elabel in evallabels:
                #print("elabel: %s" % elabel)
                ev[elabel] += self.linkData[link][elabel]
                if self.linkData[link][elabel] > 0:
                    whichlinksevs[elabel].append((link, self.linkData[link][elabel]))
        
        f = open("detailed-eval-mwgraph.txt", "w")
        for elabel in evallabels:
            f.write("\n%s\n" % elabel)
            f.write("%s\n" % "\n".join(map((lambda a: a[0]+"\t"+str(a[1])), whichlinksevs[elabel])))
        
        f.close()
        return ev
    

            
        
def writeMOPFile(linkData, nodes, links, start_nodes, end_nodes, supplies, capacities, fcostWeights, fcostLabels, fname="moProblem.mop", form="IP"):
    
    f = open(fname, "w")
    f.write("NAME MOBITEST\n")
    f.write("OBJSENSE\n MIN\n")
    f.write("ROWS\n")
    
    #set objective functions name
    for l in fcostLabels:
        f.write(" N %s\n" % l)
    
    #set equalities name
    for node in nodes:
        f.write(" E N%s\n" % node)
    
    f.write("COLUMNS\n")

    #set objective functions and equalities
    for i in range(len(links)):
        link = links[i]
        
        #obj functions
        for cost, label in zip(fcostWeights, fcostLabels):
            c = _iround(cost * linkData[link][label])
            f.write("\tL%s\t%s\t%d\n" % (link, label, c))
            
        #equality constraints
        snode = nodes[start_nodes[i]]
        enode = nodes[end_nodes[i]]
        f.write("\tL%s\tN%s\t%d\n" % (link, snode, -1))
        f.write("\tL%s\tN%s\t%d\n" % (link, enode, 1))
    
    #right hand side of equality constraints
    f.write("RHS\n")
    for i in range(len(nodes)):
        node = nodes[i]
        f.write("\tRHS\tN%s\t%d\n" %(node, -supplies[i]))
    
    f.write("BOUNDS\n")
    for i in range(len(links)):
        link = links[i]
        if form == "LP":
            #descomentar estas linhas se apenas quiser as solucoes extremas
            f.write("\tLO\tBOUNDS\tL%s\t%d\n" % (link, 0))
            f.write("\tUP\tBOUNDS\tL%s\t%d\n" % (link, capacities[i]))
        else: #form == "IP"
            #descomentar esta linha se quiser todas as solucoes nao dominadas
            f.write("\tUI\tBOUNDS\tL%s\t%d\n" % (link, capacities[i]))
        

    f.write("ENDATA\n")
    f.close()
    
    
# 'opts' e usado para passar outros parametros ao polyscip,
# por exemplo, a opcao "-x" pode ser passada para que procure
# apenas por solucoes extremas (ou serao as suportadas? - confirmar)
def runMOP(fname="moProblem.mop", tlimit=-1, opts="-x"):
    print("Running polyscip...")
    if tlimit > 0:
        print("Time limit: %f\n" % tlimit)
    #os.system("polyscip "+fname+" -x -w") #-x para encontrar apenas solucoes extremas
    
    cmd = "polyscip "+fname+" "+opts+" -w "
    if tlimit > 0:
        cmd += "-t "+str(tlimit)
    stime = time.time()
    os.system(cmd)
    etime = time.time()
    print("Time spent (polyscip): %.3f seconds" % (etime-stime))
    
    
    
def readMOPfile(link2Nodes, ixToNodes, fname="solutions.txt"):
    f = open(fname, "r")
    
    flowsCost = []
    flowsDict = []
    
    for line in f:
        i = line.index("]")
        objs = map(int, map(float, line[1:i].split()))
        varsv = line[i+1:].split()
        flowDict = {node: {} for node in ixToNodes}
        for el in varsv:
            link, val = el.split("=")
            val = int(float(val))
            (snode, enode) = link2Nodes[link[1:]]
            flowDict[snode][enode] = val
        flowsDict.append(flowDict)
        flowsCost.append(objs)
            
    f.close()
    return flowsCost, flowsDict
    
    
