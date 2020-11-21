import os
import subprocess

import utils
from ecorouting.testcases import testcases
from globals import Globals


def get_test_cases():
    return testcases


def check_content():
    tcs = get_test_cases()
    total_objective_combinations = utils.get_objective_combinations()
    count_combs_total = len(total_objective_combinations)
    simulations_total = 0
    simulations_done = 0
    heatmaps_total = 0
    heatmaps_done = 0
    videos_total = 0
    videos_done = 0

    def verbose(value: bool) -> str:
        return "FOUND" if value else "MISSING"

    def exists(path: str) -> bool:
        return os.path.exists(path)

    def join(*paths: str) -> str:
        return os.path.join(*paths)

    print("Checking content...")
    for scenario in tcs:
        tc = tcs[scenario]
        print("Test case: %s (%s)" % (tc["prettyName"], scenario))

        data_dir = tc["ifolder"]
        data_dir_exists = exists(data_dir)
        data_netfile_exists = exists(join(data_dir, tc["netfile"]))
        data_roufile_exists = exists(join(data_dir, tc["roufile"]))
        print_info = (verbose(data_dir_exists), verbose(data_netfile_exists), verbose(data_roufile_exists))
        print("\tDataset directory: %s | Net file: %s | Route file: %s" % print_info)

        res_dir = tc["ofolder"]
        res_dir_exists = exists(res_dir)
        done_objective_combinations = []
        if res_dir_exists:
            for name in os.listdir(res_dir):
                if utils.is_objective_pair(name):
                    done_objective_combinations.append(name)
        res_base_roufile_exists = exists(join(res_dir, "inputdata", tc["bname"]) + "-base.rou.xml")
        simulations_total += 1
        if res_base_roufile_exists:
            simulations_done += 1
        count_combs_done = len(done_objective_combinations)
        count_combs_left = count_combs_total - count_combs_done
        simulations_total += count_combs_left
        heatmaps_total += count_combs_left
        videos_total += count_combs_left
        heatmap_base_exists = exists(join(Globals.HEATMAPS_DIR, utils.format_file_name_base(scenario), "jpg"))
        heatmaps_total += 1
        if heatmap_base_exists:
            heatmaps_done += 1
        video_base_exists = exists(join(Globals.VIDEOS_DIR, utils.format_file_name_base(scenario), "mp4"))
        videos_total += 1
        if video_base_exists:
            videos_done += 1
        print_info = (verbose(res_dir_exists), verbose(res_base_roufile_exists), verbose(heatmap_base_exists),
                      verbose(video_base_exists), count_combs_done, count_combs_total)
        print("\tResults directory: %s | Base route file: %s | Heatmap file: %s | Video file: %s | "
              "Objective combinations: %d/%d" % print_info)

        for combination in done_objective_combinations:
            comb_dir = join(res_dir, combination)
            comb_base_eval_exists = exists(join(comb_dir, "base.eval"))
            comb_pred_eval_exists = exists(join(comb_dir, "pred.eval"))
            comb_sim_eval_exists = exists(join(comb_dir, "sim.eval"))
            solutions_total = []
            solutions_done = []
            for name in os.listdir(comb_dir):
                if os.path.isdir(join(comb_dir, name)) and name.startswith("solution"):
                    solutions_total.append(name)
                    if any([file.endswith(".rou.xml") for file in os.listdir(join(comb_dir, name))]):
                        solutions_done.append(name)
            objective1, objective2 = utils.reverse_format_objective_names(combination)
            objective1_pretty = Globals.METRICS[objective1]["pretty"]
            objective2_pretty = Globals.METRICS[objective2]["pretty"]
            combination_pretty = utils.format_objective_names(objective1_pretty, objective2_pretty)
            count_sols_total = len(solutions_total)
            count_sols_done = len(solutions_done)
            print_info = (combination_pretty, combination, verbose(comb_base_eval_exists),
                          verbose(comb_pred_eval_exists), verbose(comb_sim_eval_exists),
                          count_sols_done, count_sols_total)
            print("\t\t%s (%s): Base results file: %s | Pred results file: %s | Sim results file: %s | "
                  "Solutions: %d/%d" % print_info)

            for solution in solutions_total:
                sol_dir = join(comb_dir, solution)
                sol_sim_roufile_exists = exists(join(sol_dir, tc["bname"]) + ".rou.xml")
                simulations_total += 1
                if sol_sim_roufile_exists:
                    simulations_done += 1
                solution_number = int(solution.replace("solution", ""))
                solution_pretty = "Solution %d" % solution_number
                image_name = utils.format_file_name_sim(scenario, objective1, objective2, solution_number)
                sol_heatmap_sim_exists = exists(join(Globals.HEATMAPS_DIR, image_name, "jpg"))
                heatmaps_total += 1
                if sol_heatmap_sim_exists:
                    heatmaps_done += 1
                video_name = utils.format_file_name_sim(scenario, objective1, objective2, solution_number)
                sol_video_sim_exists = exists(join(Globals.VIDEOS_DIR, video_name, "mp4"))
                videos_total += 1
                if sol_video_sim_exists:
                    videos_done += 1
                print_info = (solution_pretty, verbose(sol_sim_roufile_exists),
                              verbose(sol_heatmap_sim_exists), verbose(sol_video_sim_exists))
                print("\t\t\t%s: Sim route file: %s | Heatmap file: %s | Video file: %s" % print_info)
        print()
    print_info = (simulations_done, simulations_total, heatmaps_done, heatmaps_total, videos_done, videos_total)
    print("Finished checking content: Simulations done: %d/%d | Heatmaps done: %d/%d | Videos done: %d/%d" % print_info)


def call_ecorouting():
    cmd = "python main-interactive.py -t ang-est --mode 1"
    ecorouting_proc = subprocess.Popen(cmd.split(" "), cwd="../ecorouting")
