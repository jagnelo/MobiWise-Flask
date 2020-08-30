import numpy as np
import matplotlib.pyplot as plt
import sys

def parallelCoordinates(datas, labels, figname, colors=('b','r','g'), maxv=None, minv=None):

    datas = np.array(datas)
    maxv = np.amax(datas, axis=(0,1)) if maxv is None else maxv
    minv = np.amin(datas, axis=(0,1)) if minv is None else minv
    
    d = len(datas[0][0])
    x = range(1,d+1)
    for data, color in zip(datas, colors):
        for pt in data:
            plt.plot(x, (pt-minv)/(maxv-minv), '-', color=color)
    plt.ylim(-0.05, 1.05)
    
    plt.xticks(x, labels)
    plt.savefig(figname)
    plt.show()
    plt.clf()


#2D apenas
def plot(datas, labels, figname, legend=None, colors=('b', 'r', 'g'), maxv=None, minv=None):
    
    if len(datas[0][0]) == 2:
        
        for data, marker, color in zip(datas, ('o', 'x', "v"), colors):
            plt.plot(data[:,0], data[:,1], marker=marker, color=color, linestyle="None")
            
        plt.xlabel(labels[0])
        plt.ylabel(labels[1])
        
        delta = [0,0] if maxv is None or minv is None else (maxv-minv)*0.05
        if maxv is not None:
            plt.xlim(right=maxv[0]+delta[0])
            plt.ylim(top=maxv[1]+delta[1])
        if minv is not None:
            plt.xlim(left=minv[0]-delta[0])
            plt.ylim(bottom=minv[1]-delta[1])
        
        if legend is not None:
            plt.legend(legend)
        plt.savefig(figname)
        plt.show()
        plt.clf()
    else:
        parallelCoordinates(datas, labels, figname, colors, maxv, minv)
    
    

    
        
"""
    Gera e guarda imagens que resumem os resultados
        resFolder:      pasta onde estao os ficheiros "pred.eval" e "sim.eval"
        plotsFolder:    pasta onde guardar as imagens geradas
        labels:         As labels dos dados que se pretende que sejam mostrados nos graficos
                        (ex.: length, cost_co, ...)
        labelsAxis:     Os nomes com que cada uma das labels deve aparecer nos graficos
"""
def plotResults(resFolder, plotFolder, labels, labelsAxis=None, fname="figure"):
    labelsAxis = labels if labelsAxis is None else labelsAxis
    
    
    f = open(plotFolder+"/pred.eval", "r")
    filelabels = f.readline()[1:].split()
    f.close()
    
    f = open(plotFolder+"/sim.eval", "r")
    sfilelabels = f.readline()[1:].split()
    f.close()
    
    
    f = open(plotFolder+"/base.eval", "r")
    bfilelabels = f.readline()[1:].split()
    f.close()

    pred_eval = np.loadtxt(plotFolder+"/pred.eval")
    pred_eval = pred_eval[np.newaxis, :] if len(pred_eval.shape) == 1 else pred_eval
    sim_eval = np.loadtxt(plotFolder+"/sim.eval")
    sim_eval = sim_eval[np.newaxis, :] if len(sim_eval.shape) == 1 else sim_eval
    base_eval = np.array([np.loadtxt(plotFolder+"/base.eval")])
    
    
    print("pred_eval\n%r" % pred_eval)
    
    #indexes of labels
    ix = [filelabels.index(l) for l in labels]
    ixs = [sfilelabels.index(l) for l in labels]
    ixb = [bfilelabels.index(l) for l in labels]
    
    basefname = plotFolder+"/"+fname+"_"
    
    datas = np.concatenate([pred_eval[:,ix], sim_eval[:,ixs], base_eval[:,ixb]], axis=0)
    
    maxv = np.amax(datas, axis=0)
    minv = np.amin(datas, axis=0)
    
    
    plot([pred_eval[:,ix]], labelsAxis, basefname+"pred_eval.png", colors=("b"), maxv=maxv, minv=minv)
    plot([sim_eval[:,ixs]], labelsAxis, basefname+"sim_eval.png", colors=("r"), maxv=maxv, minv=minv)
    plot([base_eval[:,ixb]], labelsAxis, basefname+"base_eval.png", colors=("g"), maxv=maxv, minv=minv)
    
    plot([pred_eval[:,ix], sim_eval[:,ixs], base_eval[:,ixb]], labelsAxis, basefname+"compare_eval.png", colors=("b", "r", "g"), maxv=maxv, minv=minv, legend=["predicted", "simulated", "initial"])
    
    
def plotExample(resFolder, optCostLabels):
    
    plotsFolder = resFolder
    
    labelsNames = {"ttime":      "time",
                  "length":     "dist",
                  "cost_co":    "CO",
                  "cost_co2":   "CO2",
                  "cost_PMx":   "PMx",
                  "cost_hc":    "HC",
                  "cost_nox":   "NOx",
                  "cost_fuel":  "fuel",
        }
    
    toPlot = [(labelsNames.keys(), "all"),
              (["length", "ttime"], "opt"),
              (["length", "ttime"], "dist-time"),
              (["cost_PMx", "length"], "pmx-dist"),
              (["cost_co2", "ttime"], "co2-time")]
    
    for labels, fname in toPlot:
        labelsAxis = [labelsNames[l] for l in labels]
        plotResults(resFolder, resFolder, labels, labelsAxis=labelsAxis, fname=fname)
    
    
    
    
if __name__ == "__main__":
   
    plotExample(sys.argv[1], sys.argv[2:])


#python plotSummarizedData.py results/angeja_estarreja/length-ttime length ttime
