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

dump_conf_list = [
    {
        "tag": "default",
    },
    {
        "tag": "high_mutation",
        "mating": {
            "mutation_chance": 0.15,
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
        print(f">>> START: {dump_conf['tag']} {i+1}/{REPEAT_CONF}")
        subprocess.run(["python", "-u", "src/run.py"])


def save_averaged_results(tag):
    all_values = []
    for i in range(REPEAT_CONF):
        file_path = os.path.join("dump", tag, f"{tag}_{i}.txt")
        
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                line = f.read().strip()
                if line:
                    values = [float(x) for x in line.split()]
                    all_values.append(values)
        else:
            print(f"Error: File not found {file_path}")

    if not all_values:
        return

    averages = [sum(col) / len(col) for col in zip(*all_values)]
    avg_file_path = os.path.join("dump", tag, f"{tag}_avg.txt")
    with open(avg_file_path, "w") as f:
        line_to_save = " ".join(f"{val:.2f}" for val in averages)
        f.write(line_to_save)
        f.write('\n')


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

    with open("config.yaml", "w") as f:
        yaml.dump(base_template, f, sort_keys=False)
