import shutil
import yaml
import subprocess
import copy
import os

# {
#     "tag": "name",
#     "mating": {
#         "min_age_percent": 0.10,
#         "min_energy_level": 0.20,
#         "max_range": 50,
#         "mutation_chance": 0.05,
#         "mutation_multiply_border": 0.1,
#         "mutation_addding_border": 0.1,
#     },
#     "environment": {
#         "initial_agent_count": 500,
#         "initial_food_count": 12,
#     },
# },

REPEAT_CONF = 5

COLUMNS = {
    "Agent count": 2,
    "Average agent health": 3,
    "Average agent energy": 4,
    "Food sources with stock": 5,
    "Total food in environment": 6
}

dump_conf_list = [
    {
        "tag": "default",
    },
    {
        "tag": "high_mutation",
        "mating": {
            "mutation_chance": 0.10,
        },
    },
    {
        "tag": "low_agent_count",
        "environment": {
            "initial_agent_count": 100,
        },
    },
    {
        "tag": "high_food_count",
        "environment": {
            "initial_food_count": 30,
        },
    },
    {
        "tag": "low_mating_req",
        "mating": {
            "min_age_percent": 0.10,
            "min_energy_level": 0.20,
            "max_range": 50,
        },
    },
]

def dump(config_template, dump_conf):
    current_conf = copy.deepcopy(config_template)
    
    for section, params in dump_conf.items():
        if section == "tag": 
            continue
        
        if section in current_conf:
            for key, value in params.items():
                current_conf[section][key] = value
        else:
            print(f"Error parsing {dump_conf['tag']}: Invalid section {section}!")


    current_conf['dump']['dump'] = True 
    dir_path = os.path.join("dump", dump_conf['tag'])
    os.makedirs(dir_path, exist_ok=True)
    for i in range(REPEAT_CONF):
        file_path = os.path.join(dir_path, f"{dump_conf['tag']}_{i}.txt")
        current_conf['dump']['file_name'] = file_path
        with open("config.yaml", "w") as f:
            yaml.dump(current_conf, f)
        print(f"\n>>> START: {dump_conf['tag']} {i+1}/{REPEAT_CONF}")
        subprocess.run(["python", "-u", "src/run.py"])


def save_averaged_results(tag):
    sums = []

    for run in range(REPEAT_CONF):
        file_path = os.path.join("dump", tag, f"{tag}_{run}.txt")
        with open(file_path, "r") as f:
            for i, line in enumerate(f):
                if not line.strip(): continue
                values = [float(x) for x in line.split()]
                if run == 0:
                    sums.append(values)
                else:
                    for j in range(len(values)):
                        sums[i][j] += values[j]


    avg_file_path = os.path.join("dump", tag, f"{tag}_avg.txt")
    with open(avg_file_path, "w") as f:
        for row in sums:
            avg = [val / REPEAT_CONF for val in row]
            line_to_save = " ".join(f"{val:.2f}" for val in avg)
            f.write(f"{line_to_save}\n")

def cleanup(tag):
    filename = f"{tag}_avg.txt"
    dump_dir = os.path.join("dump", tag)
    file_path = os.path.join(dump_dir, filename)
    os.rename(file_path, os.path.join("dump", filename))
    shutil.rmtree(dump_dir)
    
def generate_comparison_plots():
    # Dla każdego rodzaju danych tworzymy osobny wykres
    if os.path.exists("plots"):
        shutil.rmtree("plots")
    os.makedirs("plots")
    for data_name, col_idx in COLUMNS.items():
        plt_file_path = os.path.join("plots", f"{data_name.replace(' ', '_')}.plt")
        
        with open(plt_file_path, "w") as f:
            # f.write("set terminal pdf\n")
            f.write(f"set title 'Comprasion: {data_name}'\n")
            f.write("set xlabel 'Simulation Tick'\n")
            f.write(f"set ylabel '{data_name}'\n")
            f.write("set grid\n")
            f.write("set key outside right center\n")
            
            plot_commands = []
            for i, dump_conf in enumerate(dump_conf_list):
                tag = dump_conf['tag']
                file_path = os.path.join("dump", f"{tag}_avg.txt")
                if os.path.exists(file_path):
                    plot_commands.append(f"'{file_path}' using 1:{col_idx} with lines title '{tag.replace('_', ' ')}' lw 2 lt {i+1}")
            
            f.write("plot " + ",\\\n     ".join(plot_commands) + "\n")

if __name__ == "__main__":
    if not os.path.exists("config.yaml"):
        print("Error: Config.yaml does not exist!")
        exit()

    with open("config.yaml", "r") as f:
        base_template = yaml.safe_load(f)

    if os.path.exists("dump"):
        shutil.rmtree("dump")

    os.makedirs("dump")
    for i, dump_conf in enumerate(dump_conf_list):
        print(f"\n--- Processing: {i+1}/{len(dump_conf_list)} ---")
        dump(base_template, dump_conf)
        save_averaged_results(dump_conf['tag'])
        cleanup(dump_conf['tag'])
    generate_comparison_plots()

    with open("config.yaml", "w") as f:
        yaml.dump(base_template, f, sort_keys=False)
