import os
import datetime
import traci  # traci is a dependency shipped with the SUMO distribution at https://sumo.dlr.de


g_sim_running = False
g_sim_step = 0
g_sim_delta_secs = 0.0
g_img_name = "view%05d.jpg"


def run(sumo_gui: str, sumo_port: int, sumo_data: str, sumo_net: str, sumo_route: str, sumo_settings: str):
    sumo_cmd = [sumo_gui, "--net-file", os.path.join(sumo_data, sumo_net),
                "--route-files", os.path.join(sumo_data, sumo_route),
                "--gui-settings-file", os.path.join(sumo_data, sumo_settings),
                "--start", "true", "--quit-on-end"]
    traci.start(cmd=sumo_cmd, port=sumo_port, verbose=True)

    for f in os.listdir("output"):
        os.remove(os.path.join("output", f))

    deltas = 0.0
    global g_sim_running
    global g_sim_step
    global g_sim_delta_secs
    try:
        # run while more than 1 vehicle is in the simulation
        while traci.simulation.getMinExpectedNumber() > 0:
            g_sim_running = True
            start_time = datetime.datetime.now()
            traci.simulationStep()
            g_sim_step = int(traci.simulation.getTime())
            traci.gui.screenshot(traci.gui.DEFAULT_VIEW, os.path.join("output", g_img_name % g_sim_step))
            last_delta = (datetime.datetime.now() - start_time).total_seconds()
            deltas += last_delta
            g_sim_delta_secs = deltas / g_sim_step
    except Exception as e:
        print("An error occurred: %s" % str(e))

    print("SUMO finished the simulation after %d steps" % g_sim_step)
    g_sim_running = False
    g_sim_step = 0
    g_sim_delta_secs = 0.0

    traci.close()


def run_default():
    run(os.path.join("D:", os.sep, "Programs", "SUMO", "1.6.0", "bin", "sumo-gui.exe"), 1234,
        os.path.join("D:", os.sep, "Documents", "CISUC", "MobiWise - Demo", "Porto data", "SUMO", "Input"),
        "Porto.net.xml", "Porto-base.rou.xml", "gui-settings.xml")


if __name__ == '__main__':
    run_default()
