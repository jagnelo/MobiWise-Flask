import os

import utils

import ecorouting_connector as eco
from logger import logger


def find_objetive_pair_dirs():
    dirs = []
    for scenario, info in eco.get_test_cases().items():
        for obj_pair in utils.get_objective_combinations():
            dirs.append(os.path.join(info["ofolder"], obj_pair))
    return dirs


def fix_eval_file(dir):
    header = []
    solution_evs = {}
    for file in os.listdir(dir):
        sol_dir = os.path.join(dir, file)
        if os.path.isdir(sol_dir) and file.startswith("solution"):
            for sol_file in os.listdir(sol_dir):
                if sol_file.endswith("sim.ev"):
                    sol_sim_ev = utils.read_ev_file(os.path.join(sol_dir, sol_file))
                    solution_evs[file] = sol_sim_ev
                    header = list(sol_sim_ev)
                    break
            if file not in solution_evs:
                solution_evs[file] = None
    if header:
        data = []
        sols = list(solution_evs)
        ordered_sols = sorted(sols, key=lambda x: int(x.replace("solution", "")))
        for sol in ordered_sols:
            sol_values = {h: solution_evs[sol][h] if solution_evs[sol] else float(0) for h in header}
            data.append(sol_values)
        utils.write_eval_file(os.path.join(dir, "sim_fixed.eval"), header, data)
        logger.info("EvalFileFixer", "Fixed sim.eval file at %s" % dir)
    else:
        logger.info("EvalFileFixer", "Unable to fix sim.eval file for %s as no solutions have been simulated yet" % dir)


def run():
    for dir in find_objetive_pair_dirs():
        try:
            logger.info("EvalFileFixer", "Fixing sim.eval file at %s" % dir)
            fix_eval_file(dir)
        except BaseException as e:
            logger.error("EvalFileFixer", str(e))
        finally:
            if __name__ == '__main__':
                logger.flush()


if __name__ == '__main__':
    run()
