# **Evolution Simulation**

A Python-based evolutionary simulation where autonomous agents navigate a grid-based environment, consume food sources, reproduce, and evolve over time. The project uses neural network decision making for agent behavior and tracks population statistics through real time charts.

## Features

- **Agent-Based Simulation**: Autonomous agents with neural network brains making movement decisions
- **Evolutionary Dynamics**: Agents reproduce with genetic crossover and mutations, leading to different behaviors
- **Dynamic Environment**: Multiple food sources (grass patches, berry bushes, fruit trees, cactus pads) with regeneration
- **Real Time Visualization**: Pygame-based UI showing the grid state and population charts
- **Statistics & Monitoring**: Live charts tracking population age, energy levels, and other metrics
- **Configurable Parameters**: YAML-based configuration for world size, mating rules, mutation rates, and more

## How It Works

1. **Agents** spawn in the environment and consume food to gain energy
2. **Decision Making** is governed by neural networks with inputs from food and agent sensing
3. **Mating** occurs when nearby agents of the same group have sufficient energy and age
4. **Evolution** happens through genetic crossover and mutations in offspring
5. **Visualization** displays the grid with agents and food, plus real time population statistics

## Setup

```bash
# Create virtual environment (first time only)
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip3 install -r requirements.txt

# Run the simulation
python3 src/run.py
```

## Dependencies

- **pygame** - Graphics and event handling
- **pygame_gui** - UI components
- **PyYAML** - Configuration file parsing

## Configuration

Edit [`config.yaml`](config.yaml) to adjust:
- Window and panel dimensions
- Grid cell size
- Mating parameters (age threshold, energy level, mutation rates)
- Chart display settings

## Project Structure

- `src/agent.py` - Agent class with neural network decision making and genetics
- `src/environment.py` - Main simulation state and update logic
- `src/area.py` - Grid-based spatial representation
- `src/food.py` - Food source types and behavior
- `src/mating.py` - Reproduction and genetic inheritance logic
- `src/terrain.py` - World generation and topology
- `src/ui.py` - User interface management
- `src/charts.py` - Statistics and visualization
- `src/sense.py` - Agent sensory input processing

## Notes

- GitHub Actions runs pylint checks on all pull requests
- The simulation uses torus topology (wraps at edges)
