angest = {

    "ifolder":      "../dataSets/Angeja_Estarreja",
    "netfile":      "angeja_estarreja.net.xml",
    "roufile":      "angeja_estarreja.rou.xml",
    
    "ofolder":      "../results/angeja_estarreja",
    "bname":        "angeja_estarreja",
    "dynamicTypes": ["EcoRoutingSN", "Car"],
    "onlyExtremalSols": False
    }


portoSB_8AM9AM_fewerv = {

    "ifolder":      "../dataSets/Porto/8AM9AM_Routing_SaoBento",
    "netfile":      "Porto.net.xml",
    "roufile":      "Porto-less_vdynamic.rou.xml",
    
    "ofolder":      "../results/Porto/8AM9AM_Routing_SaoBento_fewerv",
    "bname":        "Porto",
    "dynamicTypes": ["Routing", "Car", "Routing_SaoBento"],
    "onlyExtremalSols": True
    }


portoSB_8AM9AM = {

    "ifolder":      "../dataSets/Porto/8AM9AM_Routing_SaoBento",
    "netfile":      "Porto.net.xml",
    "roufile":      "Porto.rou.xml",
    
    "ofolder":      "../results/Porto/8AM9AM_Routing_SaoBento",
    "bname":        "Porto",
    "dynamicTypes": ["Routing", "Car", "Routing_SaoBento"],
    "onlyExtremalSols": True
    }


testcases = {
        "ang-est":                  angest,
        "portoSB_8AM9AM_fewerv":    portoSB_8AM9AM_fewerv,
        "portoSB_8AM9AM":           portoSB_8AM9AM,
    }
