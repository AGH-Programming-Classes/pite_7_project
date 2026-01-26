from __future__ import annotations
from agent import Agent, dist2
import typing
import config
from random import choice, randint, random, uniform

class Mating:
    """Handles reproduction logic for agents including mate selection and genome crossover."""
    
    def __init__(self, parent: Agent):
        self.parent : Agent = parent

    def mate(self):
        """Attempt mating if constraints are met. Creates offspring with blended genetics."""
        if not self._checking_constrains():
            return
        close_agents = self._get_nearby_agents()
        if not close_agents:
            return
        
        matrix, vector = self.get_new_genome(choice(close_agents))
        new_agent = Agent((self.parent.x, self.parent.y), self.parent.environment, decision_matrix= matrix, genome= vector, species = self.parent.group_id)
        energy_level = self.parent.energy / self.parent.max_energy
        new_agent.energy = new_agent.max_energy * energy_level / 2
        self.parent.energy /= 2
        self.parent.environment.create_agent(new_agent)

    def _get_nearby_agents(self) -> typing.List[Agent]:
        """Find nearby agents of the same group within mating range."""
        close_agents: typing.List[Agent] = []
        for agent in self.parent.environment.get_agents():
            if dist2(self.parent.x, self.parent.y, agent.x, agent.y) < config.MAX_RANGE and agent.group_id == self.parent.group_id:
                close_agents.append(agent)
        return close_agents

    def _checking_constrains(self) -> bool:
        """Check if parent meets mating requirements (age and energy thresholds)."""
        return not( self.parent.age < config.MIN_AGE_PERCENT * self.parent.max_age or self.parent.energy < config.MIN_ENERGY_LEVEL * self.parent.max_energy)
        
    def get_new_genome(self, second : Agent) -> typing.Tuple[typing.List[typing.List[float]], typing.Dict[str, int]]:
        """Generate offspring genome by crossing over parent genomes and applying mutations."""
        matrix =  self.create_new_decision_matrix(second)
        vector = self.create_new_genome_vector(second)

        numbers_to_change_in_matrix = int(len(matrix) * len(matrix[0]) / (1 / config.MUTATION_CHANCE))

        #Applying mutation - there could be multiply of value or adding

        for _ in range(numbers_to_change_in_matrix):
            row =choice(matrix)
            i = randint(0, len(row)-1)
            if random() < 0.2:
                row[i] *= uniform(1 - config.MUTATION_MULTIPLY_BORDER, 1 + config.MUTATION_MULTIPLY_BORDER)
            else:
                row[i] += uniform(-config.MUTATION_ADDING_BORDER, config.MUTATION_ADDING_BORDER)

        for _ in range(int(len(vector) / (1 / config.MUTATION_CHANCE))):
            item = choice(vector.keys())
            if random() < 0.2:
                vector[item] *= uniform(1 - config.MUTATION_ADDING_BORDER, 1 + config.MUTATION_ADDING_BORDER)
            else:
                vector[item] += uniform(-config.MUTATION_MULTIPLY_BORDER, config.MUTATION_MULTIPLY_BORDER)

        #Normalisation of vector

        normalisation = 100 / sum(vector.values())
        for key,value in vector.items():
            vector[key] = value * normalisation

        return matrix, vector
    
    def create_new_decision_matrix(self, second : Agent) -> typing.List[typing.List[float]]:
        """Perform two-point crossover on neural network weights."""
        output = []
        crossover_points = [randint(1, len(self.parent.weights[0])-1) for _ in range(2)]
        crossover_points.sort()
        
        for i in range(len(self.parent.weights)):
            row = []
            last_point = 0
            parent = self.parent
            
            for cp in crossover_points:
                row.extend(parent.weights[i][last_point:cp])
                parent = second if parent == self.parent else self.parent
                last_point = cp
            
            row.extend(parent.weights[i][last_point:])
            output.append(row)
        
        return output

    def create_new_genome_vector(self, second : Agent):
        genome = self.parent.body_points.copy()
        for item in genome.keys():
            genome[item] = self.parent.body_points[item] if randint(0,1) == 1 else second.body_points[item]
        return genome