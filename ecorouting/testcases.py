angest = {

    "prettyName": "Angeja - Estarreja",

    "ifolder":      "../dataSets/Angeja_Estarreja",
    "netfile":      "angeja_estarreja.net.xml",
    "roufile":      "angeja_estarreja.rou.xml",
    
    "ofolder":      "../results/angeja_estarreja",
    "bname":        "angeja_estarreja",
    "dynamicTypes": ["EcoRoutingSN", "Car"],
    "onlyExtremalSols": False
    }


# portoSB_8AM9AM_fewerv = {
#
#     "ifolder":      "../dataSets/Portos/8AM9AM_Routing_SaoBento",
#     "netfile":      "Porto.net.xml",
#     "roufile":      "Porto-less_vdynamic.rou.xml",
#
#     "ofolder":      "../results/Porto/8AM9AM_Routing_SaoBento_fewerv",
#     "bname":        "Porto",
#     "dynamicTypes": ["Routing", "Car", "Routing_SaoBento"],
#     "onlyExtremalSols": True
#     }
#
#
# portoSB_8AM9AM = {
#
#     "ifolder":      "../dataSets/Porto/8AM9AM_Routing_SaoBento",
#     "netfile":      "Porto.net.xml",
#     "roufile":      "Porto.rou.xml",
#
#     "ofolder":      "../results/Porto/8AM9AM_Routing_SaoBento",
#     "bname":        "Porto",
#     "dynamicTypes": ["Routing", "Car", "Routing_SaoBento"],
#     "onlyExtremalSols": True
#     }


portoSB_6AM7AM = {

    "prettyName": "Porto 6AM-7AM São Bento",

    "ifolder": "../dataSets/Porto/6AM7AM_Routing_SaoBento",
    "netfile": "Porto.net.xml",
    "roufile": "Trips6AM7AM.rou.xml",

    "ofolder": "../results/Porto/6AM7AM_Routing_SaoBento",
    "bname": "Porto",
    "dynamicTypes": ["Routing", "Car", "Routing_SaoBento"],
    "onlyExtremalSols": True
}


portoSB_8AM9AM = {

    "prettyName": "Porto 8AM-9AM São Bento",

    "ifolder": "../dataSets/Porto/8AM9AM_Routing_SaoBento",
    "netfile": "Porto.net.xml",
    "roufile": "Trips8AM9AM.rou.xml",

    "ofolder": "../results/Porto/8AM9AM_Routing_SaoBento",
    "bname": "Porto",
    "dynamicTypes": ["Routing", "Car", "Routing_SaoBento"],
    "onlyExtremalSols": True
}


portoBV_6AM7AM = {

    "prettyName": "Porto 6AM-7AM Boavista",

    "ifolder": "../dataSets/Porto/6AM7AM_Routing_Boavista",
    "netfile": "Porto.net.xml",
    "roufile": "Trips6AM7AM.rou.xml",

    "ofolder": "../results/Porto/6AM7AM_Routing_Boavista",
    "bname": "Porto",
    "dynamicTypes": ["Routing", "Car", "Routing_Boavista"],
    "onlyExtremalSols": True
}


portoBV_8AM9AM = {

    "prettyName": "Porto 8AM-9AM Boavista",

    "ifolder": "../dataSets/Porto/8AM9AM_Routing_Boavista",
    "netfile": "Porto.net.xml",
    "roufile": "Trips8AM9AM.rou.xml",

    "ofolder": "../results/Porto/8AM9AM_Routing_Boavista",
    "bname": "Porto",
    "dynamicTypes": ["Routing", "Car", "Routing_Boavista"],
    "onlyExtremalSols": True
}


portoA3_6PM7PM = {

    "prettyName": "Porto 6PM-7PM A3",

    "ifolder": "../dataSets/Porto/6PM7PM_Routing_A3",
    "netfile": "Porto.net.xml",
    "roufile": "Trips6PM7PM.rou.xml",

    "ofolder": "../results/Porto/6PM7PM_Routing_A3",
    "bname": "Porto",
    "dynamicTypes": ["Routing", "Car", "Routing_A3"],
    "onlyExtremalSols": True
}


testcases = {
        "ang-est":                  angest,
        # "portoSB_8AM9AM_fewerv":    portoSB_8AM9AM_fewerv,
        "portoSB_6AM7AM":           portoSB_6AM7AM,
        "portoSB_8AM9AM":           portoSB_8AM9AM,
        "portoBV_6AM7AM":           portoBV_6AM7AM,
        "portoBV_8AM9AM":           portoBV_8AM9AM,
        "portoA3_6PM7PM":           portoA3_6PM7PM
    }
