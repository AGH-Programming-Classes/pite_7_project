import yaml
import subprocess
import copy
import os

dump_conf_list = [
    {
        "tag": "exp_1_standard",
        "mating": {"mutation_chance": 0.05, "max_range": 10},
        "environment": {"initial_agent_count": 500},
        "dump": {"max_tick": 20}
    }
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

    os.makedirs("dump", exist_ok=True)
    current_conf['dump']['file_name'] = f"dump/{dump_conf['tag']}.txt"
    current_conf['dump']['dump'] = True 

    with open("config.yaml", "w") as f:
        yaml.dump(current_conf, f)

    print(f">>> START: {dump_conf['tag']}")
    
    subprocess.run(["python", "-u", "src/run.py"])

if __name__ == "__main__":
    if not os.path.exists("config.yaml"):
        print("Error: Config.yaml does not exist!")
        exit()

    with open("config.yaml", "r") as f:
        base_template = yaml.safe_load(f)

    for i, dump_conf in enumerate(dump_conf_list):
        print(f"\n--- Processing: {i+1}/{len(dump_conf_list)} ---")
        dump(base_template, dump_conf)

    with open("config.yaml", "w") as f:
        yaml.dump(base_template, f, sort_keys=False)
