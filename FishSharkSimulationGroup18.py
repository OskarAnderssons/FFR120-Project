#Notes 29/11 supervisor meeting:
#Parameters need to have a physical meaning to be useful.
#Bounded parameters have a min/max and the meaning of these values.
#Save variables, arrays, plots and other useful things so that additional data does not have to be generated again leading to a timewaste.
#Work paralell
#Rank phenomena we like to study and start at the top and work down.
#Can send 1/2 emails, 10 is too much to supervisor
#Overleaf can be used to make poster or powerpoint, check the forskarbyggnad to get inspiration for the poster.
#


"""
This is a WIP for a predator/prey system. The simulation has prey(fish) and predators(sharks). This simulation aims to check if 
swarming is a beneficial behaviour for the prey to ward againts the predator. This will be done using a simple evolutionary model where fish produce
offspring with similiar swarming preference as their parents. The expected behaviour is that the fish parameter self.cohesion which models
swarming preference will increase over time as more fish with this benificial trait survives and reproduces


Notes:

Please use camelCase for function "word1_word2_word3" for constants/variables and the same but with CAPITAL LETTERS for the tuneable parameters
defined in the beginning of the code. Also try to follow the coding "standard" I've begun as well as possible. Add many comments so that your 
groupmates can understand what you have implemented. If you have any ideas please comment somewhere fitting in the code a #TODO so that it can 
be implemented.
"""

#Imports
import tkinter as tk
import random
import math
import numpy as np

#Seeding the randomness here for testing and reproducability, comment out to test with nonseeding randomness. This seed was quite nice for the 
#shark spawns but you can mess around with the seeds
random.seed(62)

#Tuneable Parameters
NUM_FISH = 50 #Amount of prey constant for now
BASE_COHESION = 0.5
NUM_SHARKS = 2 #Amount of predators
FIELD_SIZE = 750 #Size of area, also affects simulation windowsize!
PREDATOR_SPEED = 7 #Speed of predator
FISH_SPEED = 4 #Speed of prey
FISH_VISION = 150 #Vision of prey
PREDATOR_VISION = 150 #Vision of predator
MAX_OFFSPRING = 5 #Max possible amount of prey offspring
TIME_STEP_DELAY = 30 #Changes speed of simulation (Higher = Slower)!
BASE_REPRODUCTION_PROB = 0.001 #Defaut reproduction probability, increases over time and resets to this when prey have offspring
PREDATOR_COOLDOWN = 10 #Cooldown for predator chasing and eating
AGE_DEATH_RATE = 0.00005 #Exponent for the exponential death chance increase with prey age
RANDOM_DIRECTION_INTERVAL = 20 #How often predator changes direction when no prey in vision
SHARK_SPAWN_AREA = FIELD_SIZE/2 #Spawn area, used to distribute the predators. Increase denominator constant to decrease spawn radius
SENSORY_DELAY_SHARK = -2 #Placeholder value for now
DELAY_TIME = -SENSORY_DELAY_SHARK #Inverse of the negative delay, used for preallocating array
T_FIT = np.arange(DELAY_TIME)
USE_DELAY = True

class Fish:
    def __init__(self, cohesion):
        #Random spawns and speeds but seeded so OK
        self.x = random.uniform(0, FIELD_SIZE)
        self.y = random.uniform(0, FIELD_SIZE)
        self.vx = random.uniform(-FISH_SPEED, FISH_SPEED)
        self.vy = random.uniform(-FISH_SPEED, FISH_SPEED)
        self.cohesion = cohesion  # Swarming parameter
        self.avoidence = 0.5

    def move(self, school, sharks):
        center_x, center_y, count = 0, 0, 0
        avg_vx, avg_vy = 0, 0
        sep_x, sep_y = 0, 0 

        for other in school:
            if other == self:
                continue
            distance = math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
            if distance < FISH_VISION:
                center_x += other.x
                center_y += other.y
                count += 1
                avg_vx += other.vx
                avg_vy += other.vy
                
                if distance == 0:
                    distance = 1e-6
                
                #Calculate sepration, to avoid overlap while keeping swarming behaviour   
                repulsion_strength = math.exp(-distance / 10)  #Exponential falloff
                sep_x += (self.x - other.x) * repulsion_strength
                sep_y += (self.y - other.y) * repulsion_strength

        #Fish movement controlled by noise, the schools average speed and a separation force to avoid clustering
        self.vx += random.uniform(-0.5, 0.5) * self.cohesion * 0.1
        self.vy += random.uniform(-0.5, 0.5) * self.cohesion * 0.1
        self.vx += avg_vx * 0.02
        self.vy += avg_vy * 0.02 #Remove 0.2 add variable named something
        self.vx += sep_x * 0.05
        self.vy += sep_y * 0.05
        self.cohesion = 0.5
        #Avoid predators
        for shark in sharks:
            shark_dist = math.sqrt((self.x - shark.x) ** 2 + (self.y - shark.y) ** 2)
            if shark_dist < PREDATOR_VISION:
                self.vx += (self.x - shark.x) / shark_dist * self.avoidence
                self.vy += (self.y - shark.y) / shark_dist * self.avoidence
                if shark_dist < 50:
                    self.vx += (self.x - shark.x) / shark_dist * self.avoidence
                    self.vy += (self.y - shark.y) / shark_dist * self.avoidence
                
        if count > 0:
            #Adjust movement based on cohesion
            if shark_dist < 50:
                center_x /= count
                center_y /= count
                self.vx += (center_x - self.x) * self.cohesion*0.00000000000001
                self.vy += (center_y - self.y) * self.cohesion*0.00000000000001
                avg_vx /= count
                avg_vy /= count
            else:
                center_x /= count
                center_y /= count
                self.vx += (center_x - self.x) * self.cohesion*0.1
                self.vy += (center_y - self.y) * self.cohesion*0.1
                avg_vx /= count
                avg_vy /= count
            
        #Soft boundary conditions, fish are weakly repelled when approching border 
        repel_distance = 0.2*FIELD_SIZE  #Distance at which repelling force is applied
        repel_strength = 2  #Force strength
        self.cohesion = 0.5
        if self.x < repel_distance:
            self.vx += (repel_distance - self.x) * repel_strength / repel_distance
        elif self.x > FIELD_SIZE - repel_distance:
            self.vx -= (self.x - (FIELD_SIZE - repel_distance)) * repel_strength / repel_distance

        if self.y < repel_distance:
            self.vy += (repel_distance - self.y) * repel_strength / repel_distance
        elif self.y > FIELD_SIZE - repel_distance:
            self.vy -= (self.y - (FIELD_SIZE - repel_distance)) * repel_strength / repel_distance

        #Limit fish speed
        speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        if speed > FISH_SPEED:
            self.vx = (self.vx / speed) * FISH_SPEED
            self.vy = (self.vy / speed) * FISH_SPEED

        #Update position
        self.x += self.vx
        self.y += self.vy
    def getFishPosition(self):
        return self.x, self.y
        
        
    
    """
    def naturalDeath(self):
        #Exponentially increasing death probability with age
        death_probability = 1 - math.exp(-AGE_DEATH_RATE * self.age)
        return random.random() < death_probability
    """

#Class for predator, constant speed for simplicity
class Shark:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.cooldown = 0
        self.random_direction_timer = 0
    def move(self, fish_population, fish_position_x, fish_position_y):
        #If shark on cooldown choose a random direction and follow it until cooldown is over
        if self.cooldown > 0:
            
            if self.cooldown == PREDATOR_COOLDOWN:
                self.random_movex = random.uniform(-PREDATOR_SPEED, PREDATOR_SPEED)
                self.random_movey = random.uniform(-PREDATOR_SPEED, PREDATOR_SPEED)
                
            self.x += self.random_movex
            self.y += self.random_movey
            self.cooldown -= 1
        else:
            
            closest_fish = None
            closest_distance = float("inf")
            closest_index = 0
            for j, fish in enumerate(fish_population):
                distance = math.sqrt((fish.x - self.x) ** 2 + (fish.y - self.y) ** 2)
                if distance < closest_distance and distance < PREDATOR_VISION:
                    closest_fish = fish
                    closest_distance = distance
                    closest_index = j
            
            #TODO: Add sensory delay here in the "chase phase" of the shark, we somehow need to have the index for the closest fish aswell
            #The way it is coded should make it fish 1 index 1 et.c. but I have not confirmed this yet!
            if closest_fish:
                dx1 = closest_fish.x - self.x
                dy1 = closest_fish.y - self.y
                dist1 = math.sqrt(dx1**2 + dy1**2)
                if USE_DELAY:
                    px = np.polyfit(T_FIT, fish_position_x[closest_index,:], 1)[0]
                    py = np.polyfit(T_FIT, fish_position_y[closest_index,:], 1)[0]
                    dx = (px-self.x)
                    dy = (py-self.y)
                    dist = math.sqrt(dx**2 + dy**2)
                    
                    if dist > 0:
                        #self.x += (dx / dist) * PREDATOR_SPEED
                        #self.y += (dy / dist) * PREDATOR_SPEED
                        self.x += 0.5*dx*PREDATOR_SPEED/dist + 0.5*(dx1 / dist1) * PREDATOR_SPEED
                        self.y += 0.5*dy*PREDATOR_SPEED/dist + 0.5*(dy1 / dist1) * PREDATOR_SPEED
                else:
                    self.x += dx1*PREDATOR_SPEED/dist1
                    self.y += dy1*PREDATOR_SPEED/dist1
            else:
                
                if self.random_direction_timer <= 0:
                
                    self.random_movex = random.uniform(-PREDATOR_SPEED, PREDATOR_SPEED)
                    self.random_movey = random.uniform(-PREDATOR_SPEED, PREDATOR_SPEED)
                  
                    self.random_direction_timer = RANDOM_DIRECTION_INTERVAL

                
                self.x += self.random_movex
                self.y += self.random_movey

                
                self.random_direction_timer -= 1
                
        #Soft boundary conditions, similiar to the fishes. #TODO Change this into a function and use it for both fish and shark (NOT NEEDED BUT
        #looks neater!)
        repulsion_strength = 2 #Adjustable parameter to control boundary force
        margin = 0.2*FIELD_SIZE #Distance where soft boundary applies

        if self.x < margin:
            self.x += (margin - self.x) * repulsion_strength * 0.01
        elif self.x > FIELD_SIZE - margin:
            self.x += (FIELD_SIZE - margin - self.x) * repulsion_strength * 0.01

        if self.y < margin:
            self.y += (margin - self.y) * repulsion_strength * 0.01
        elif self.y > FIELD_SIZE - margin:
            self.y += (FIELD_SIZE - margin - self.y) * repulsion_strength * 0.01
                    
    def eat(self, fish_population):
        fish_eaten = 0
        for fish in fish_population[:]:
            distance = math.sqrt((fish.x - self.x) ** 2 + (fish.y - self.y) ** 2)
            if distance < 10:  
                fish_population.remove(fish)
                self.cooldown = PREDATOR_COOLDOWN  #Set cooldown after eating
                fish_eaten += 1
                break
        return fish_eaten
                
        
        

#Main Simulation Class
class FishSimulation:
    def __init__(self, root):
        self.root = root 
        self.canvas = tk.Canvas(root, width=FIELD_SIZE, height=FIELD_SIZE, bg="lightblue")
        self.canvas.pack()
        self.time_elapsed = 0  #Total time in simulation steps
        self.total_fish_eaten = 0

        self.fish_population = [
            Fish(BASE_COHESION) for _ in range(NUM_FISH)#, random.uniform(0, 1), random.uniform(0, 1)) for _ in range(NUM_FISH)
        ]
        
        #Spawn sharks, seeded!
        self.sharks = [
            Shark(
                random.uniform(FIELD_SIZE / 2 - SHARK_SPAWN_AREA, FIELD_SIZE / 2 + SHARK_SPAWN_AREA),
                random.uniform(FIELD_SIZE / 2 - SHARK_SPAWN_AREA, FIELD_SIZE / 2 + SHARK_SPAWN_AREA)
            )
            for _ in range(NUM_SHARKS)
            ]

        self.generation = 0
        self.running = True
        #self.reproduction_timer = 0  #Not used in current implementation
        #self.reproduction_prob = BASE_REPRODUCTION_PROB  #Not used in current implementation
        self.runSimulation()

    
    def moveSharks(self, fish_position_x, fish_position_y):
        for shark in self.sharks:
            shark.move(self.fish_population, fish_position_x, fish_position_y)
            fish_eaten = shark.eat(self.fish_population)
            
        self.total_fish_eaten += fish_eaten
        self.time_elapsed += 1

    def updateCanvas(self):
        self.canvas.delete("all")

        #Draw sharks
        for shark in self.sharks:
            self.canvas.create_oval(
                shark.x - 10,
                shark.y - 10,
                shark.x + 10,
                shark.y + 10,
                fill="red",
            )

        #Draw fish
        for fish in self.fish_population:
            self.canvas.create_oval(
                fish.x - 5, fish.y - 5, fish.x + 5, fish.y + 5, fill="blue"
            )

        #Calculate average cohesion and number of fish alive
        avg_cohesion = sum(fish.cohesion for fish in self.fish_population) / len(self.fish_population) if self.fish_population else 0 #Not used
        num_fish_alive = len(self.fish_population)
        
        #Calculate successrate of shark
        avg_fish_eaten_per_step = self.total_fish_eaten / self.time_elapsed if self.time_elapsed > 0 else 0
        
        self.canvas.create_text(60, 20, text=f"Generation: {self.generation}", font=("Arial", 12), fill="black")
        self.canvas.create_text(60, 40, text=f"Fish Alive: {num_fish_alive}", font=("Arial", 12), fill="black")
        self.canvas.create_text(80,80, text = f"Avg Cohesion: {avg_cohesion}", font=("Arial", 12), fill='black')
        self.canvas.create_text(150, 60, text=f"Avg fish eaten per 1000 timestep: {1000*avg_fish_eaten_per_step:.2f}", font=("Arial", 12), fill="black")

    
    #No reproduction for now, added a simple spawning mechanism instead to keep #fish constant
    """
    def reproduce(self):
        new_population = []
        self.reproduction_timer += 1
        self.reproduction_prob = BASE_REPRODUCTION_PROB * (1 + self.reproduction_timer / 50)

        for fish in self.fish_population:
            if random.random() < self.reproduction_prob:
                for _ in range(MAX_OFFSPRING):
                    cohesion = max(0, min(1, fish.cohesion + random.uniform(-0.05, 0.05)))
                    alignment = max(0, min(1, fish.alignment + random.uniform(-0.05, 0.05)))
                    separation = max(0, min(1, fish.separation + random.uniform(-0.05, 0.05)))
                    new_population.append(Fish(cohesion, alignment, separation))
        self.reproduction_timer = 0
        self.reproduction_prob = BASE_REPRODUCTION_PROB
        return new_population
    """
    
    def runSimulation(self):
        if not self.running:
            return

        fish_position_x = np.zeros([NUM_FISH, DELAY_TIME])
        fish_position_y = np.zeros([NUM_FISH, DELAY_TIME])
        #survivors = []
        for i,fish in enumerate(self.fish_population):
            fish.move(self.fish_population, self.sharks)
            fish_position_x[i,:] = np.roll(fish_position_x[i,:], -1, axis=0)
            fish_position_y[i,:] = np.roll(fish_position_y[i,:], -1, axis=0)
            xpos, ypos = fish.getFishPosition()
            fish_position_x[i,DELAY_TIME-1] = xpos
            fish_position_y[i,DELAY_TIME-1] = ypos
        
        self.moveSharks(fish_position_x,fish_position_y) #Moves sharks, eats fish
        
        #Check fish population size and add fish if needed
        
        if len(self.fish_population) != NUM_FISH:
            self.fish_population.append(Fish(BASE_COHESION))
            
        """
            #Check if the fish dies of old age, unused in current implementation

            if not fish.naturalDeath():
                survivors.append(fish)

 
        self.fish_population = survivors

        if len(self.fish_population) == 0:
            print(f"All fish eaten by generation {self.generation}!")
        else:
            self.generation += 1
            print(f"Generation {self.generation}: {len(self.fish_population)} fish survive.")
            self.fish_population += self.reproduce()
        """
        
        self.updateCanvas()
        self.root.after(TIME_STEP_DELAY, self.runSimulation)


#Run the simulation
root = tk.Tk()
root.title("Fish Simulation with Multiple Sharks")
simulation = FishSimulation(root)
root.mainloop()
