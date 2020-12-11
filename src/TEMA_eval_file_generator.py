import os

import utils

import ecorouting_connector as eco
from globals import Globals
from logger import logger


def find_TEMA_res_file_dirs():
    out_file_base = "baseTEMA.eval"
    out_file_sim = "simTEMA.eval"
    dirs = []
    for scenario, info in eco.get_test_cases().items():
        in_dir_base = [os.path.join(info["ofolder"], "inputdata")]
        if not os.path.exists(in_dir_base[0]):
            break
        for obj_pair in utils.get_objective_combinations():
            in_dirs_sim = []
            sols = []
            out_dir = os.path.join(info["ofolder"], obj_pair)
            if not os.path.exists(out_dir):
                break
            for file in os.listdir(out_dir):
                if os.path.isdir(os.path.join(out_dir, file)) and file.startswith("solution"):
                    sols.append(file)
            ordered_sols = sorted(sols, key=lambda x: int(x.replace("solution", "")))
            for sol in ordered_sols:
                in_dirs_sim.append(os.path.join(out_dir, sol))
            dirs.append({"input_dirs": in_dir_base, "output_file": os.path.join(out_dir, out_file_base)})
            dirs.append({"input_dirs": in_dirs_sim, "output_file": os.path.join(out_dir, out_file_sim)})
    return dirs


def generate_TEMA_eval_file(input_dirs: list, output_file: str):
    missing_res_file = None
    header = set()
    eval = []
    for input_dir in input_dirs:
        if Globals.TEMA_RESULTS_FILE_NAME in os.listdir(input_dir):
            res_sol = utils.read_res_file(os.path.join(input_dir, Globals.TEMA_RESULTS_FILE_NAME))
            ev_sol = utils.res_to_ev(res_sol)
            for h in ev_sol:
                header.add(h)
            eval.append(ev_sol)
        else:
            missing_res_file = input_dir
            break
    if missing_res_file:
        print_info = (output_file, missing_res_file, Globals.TEMA_RESULTS_FILE_NAME)
        print_msg = "Unable to generate %s as input directory %s does not have a %s file" % print_info
        logger.info("TEMA_EvalFileGenerator", print_msg)
    elif header and eval:
        utils.write_eval_file(output_file, list(header), eval)
        print_info = (output_file, Globals.TEMA_RESULTS_FILE_NAME, input_dirs)
        logger.info("TEMA_EvalFileGenerator", "Generated %s from %s files in %s" % print_info)


def run():
    for dir in find_TEMA_res_file_dirs():
        try:
            in_dirs = dir["input_dirs"]
            out_file = dir["output_file"]
            print_info = (out_file, Globals.TEMA_RESULTS_FILE_NAME, in_dirs)
            logger.info("TEMA_EvalFileGenerator", "Generating %s from %s files in %s" % print_info)
            generate_TEMA_eval_file(in_dirs, out_file)
        except BaseException as e:
            logger.error("TEMA_EvalFileGenerator", str(e))
        finally:
            if __name__ == '__main__':
                logger.flush()


if __name__ == '__main__':
    run()
