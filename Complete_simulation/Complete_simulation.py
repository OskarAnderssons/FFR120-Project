#Class for predator, constant speed for simplicity
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
import csv
from PIL import Image
import io   
import subprocess
import os
import datetime

#Seeding the randomness here for testing and reproducability, comment out to test with nonseeding randomness. This seed was quite nice for the 
#shark spawns but you can mess around with the seeds
#Tuneable Parameters
NUM_FISH = 100 #Amount of prey constant for now
NUM_SHARKS = 1 #Amount of predators
PREDATOR_COOLDOWN = 10 #Cooldown for predator after eating prey (30 for swarms, 10 for 1vs1)
PANIC_VISION = 10 #Vision of prey when predator is close (10 for swarms, 20 for 1vs1)
SWARM = True

TIMESTEP = 0.1
BASE_COHESION = 5
FIELD_SIZE = 75 #Size of area, also affects simulation windowsize!
PREDATOR_SPEED = 18 #Speed of predator m/s
FISH_SPEED = 16 #Speed of prey
FISH_VISION = 10 #Vision of prey

PREDATOR_VISION = FIELD_SIZE#Vision of predator
MAX_OFFSPRING = 5 #Max possible amount of prey offspring
TIME_STEP_DELAY = 20 #Changes speed of simulation (Higher = Slower)!
BASE_REPRODUCTION_PROB = 0.001 #Defaut reproduction probability, increases over time and resets to this when prey have offspring
  #Cooldown for predator chasing and eating
AGE_DEATH_RATE = 0.00005 #Exponent for the exponential death chance increase with prey age
RANDOM_DIRECTION_INTERVAL = 20 #How often predator changes direction when no prey in vision
SHARK_SPAWN_AREA = FIELD_SIZE/2 #Spawn area, used to distribute the predators. Increase denominator constant to decrease spawn radius
SENSORY_DELAY_SHARK = -2 #Placeholder value for now -2 or lower if USE_DELAY == TRUE
DELAY_TIME = -SENSORY_DELAY_SHARK #Inverse of the negative delay, used for preallocating array
USE_DELAY = True
T_FIT = np.arange(DELAY_TIME)

FUTURE_TIME = 1
FUTURE_MAX = FUTURE_TIME/TIMESTEP
WINDOWS_SIZE = 750
DRAW_FUTURE = False
SPAWNED = False

def BoundaryRepulsion(center_x, center_y, margin, repulsion_strength, x, y,vx,vy, field_size):
    # Calculate radial distance from the center
    distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
    boundary_radius = field_size / 2

    # Check if object is outside the effective boundary radius
    if distance > boundary_radius - margin:
        # Calculate direction vector pointing inward
        direction_x = center_x - x
        direction_y = center_y - y
        norm = math.sqrt(direction_x**2 + direction_y**2)
        if norm == 0:  # Avoid division by zero
            norm = 1e-6
        direction_x /= norm
        direction_y /= norm
       
        vx += direction_x * repulsion_strength * ((distance - (boundary_radius - margin))/boundary_radius-0.5)**2
        vy += direction_y * repulsion_strength * ((distance - (boundary_radius - margin))/boundary_radius-0.5)**2

        if distance > boundary_radius:

            vx += direction_x * repulsion_strength * math.exp(10*(distance - (boundary_radius - margin))/boundary_radius)
            vy += direction_y * repulsion_strength * math.exp(10*(distance - (boundary_radius - margin))/boundary_radius)

    return vx, vy

def clampPosition(x, y, field_size):
    boundary_radius = field_size / 2
    center_x, center_y = field_size / 2, field_size / 2

    distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
    if distance > boundary_radius:
        direction_x = (x - center_x) / distance
        direction_y = (y - center_y) / distance

        x = center_x + direction_x * boundary_radius
        y = center_y + direction_y * boundary_radius

    return x, y



class Fish:
    def __init__(self, cohesion, unique_id, simulation_instance):
        #Random spawns and speeds but seeded so OK
        
        if simulation_instance.spawned:
            reference_fish = random.choice(simulation_instance.fish_population)
            self.x = reference_fish.x 
            self.y = reference_fish.y
            simulation_instance.spawned = False
        else:    
            self.x = random.uniform(0, FIELD_SIZE)
            self.y = random.uniform(0, FIELD_SIZE)

        self.vx = random.uniform(FISH_SPEED/2, FISH_SPEED)
        self.vy = random.uniform(FISH_SPEED/2, FISH_SPEED)

        self.vx = self.vx * random.choice([-1, 1])
        self.vx = self.vx * random.choice([-1, 1])

        self.random_movex = 0
        self.random_movey = 0
        self.cohesion = cohesion  # Swarming parameter
        self.random_direction_timer = 0

        self.simulation = simulation_instance
        self.unique_id = unique_id

        self.lifetime = 0
        self.neighbors = 0
        self.total_neighbors = 0
        self.average_neighbors = 0

    def move(self, school, sharks):
        if NUM_FISH == 1:
            #Avoid predators
            for shark in sharks:
                shark_dist = math.sqrt((self.x - shark.x) ** 2 + (self.y - shark.y) ** 2)
                if shark_dist < PANIC_VISION:
                    self.vx += (self.x - shark.x) *(PANIC_VISION-shark_dist)/PANIC_VISION *self.cohesion
                    self.vy += (self.y - shark.y) *(PANIC_VISION-shark_dist)/PANIC_VISION*self.cohesion
                # else:
                #     if self.random_direction_timer == 0:

                #         self.random_movex = random.uniform(FISH_SPEED/2, FISH_SPEED)
                #         self.random_movey = random.uniform(FISH_SPEED/2, FISH_SPEED)
                #         self.random_movex = self.random_movex * random.choice([-1, 1])
                #         self.random_movey = self.random_movey * random.choice([-1, 1])
                #         self.random_direction_timer = RANDOM_DIRECTION_INTERVAL

                #     self.vx = self.random_movex
                #     self.vy = self.random_movey
                #     self.random_direction_timer -= 1
            self.vx, self.vy = BoundaryRepulsion(FIELD_SIZE/2,FIELD_SIZE/2 ,0.1*FIELD_SIZE, 5, self.x, self.y, self.vx, self.vy, FIELD_SIZE)
        

            #Limit fish speed
            speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
            if speed > FISH_SPEED:
                self.vx = (self.vx / speed) * FISH_SPEED
                self.vy = (self.vy / speed) * FISH_SPEED
                
            self.x += self.vx*TIMESTEP
            self.y += self.vy*TIMESTEP
        else:
            center_x, center_y, count = 0, 0, 0
            avg_vx, avg_vy = 0, 0
            sep_x, sep_y = 0, 0 

            self.lifetime += 1

            self.neighbors = 0
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
                    repulsion_strength = math.exp(-distance / 5) /10 #Exponential falloff
                    sep_x += (self.x - other.x) * repulsion_strength
                    sep_y += (self.y - other.y) * repulsion_strength

                    if distance < FISH_VISION/5:
                        self.total_neighbors += 1
                        self.neighbors += 1
                    

            if self.lifetime > 0:
                self.average_neighbors = self.total_neighbors / self.lifetime

            if count > 0:
                #Adjust movement based on cohesion
                center_x /= count
                center_y /= count
                self.vx += (center_x - self.x) * self.cohesion * 0.03
                self.vy += (center_y - self.y) * self.cohesion * 0.03
                avg_vx /= count
                avg_vy /= count

            #Fish movement controlled by noise, the schools average speed and a separation force to avoid clustering
            self.vx += random.uniform(-0.5, 0.5) * self.cohesion * 0.05
            self.vy += random.uniform(-0.5, 0.5) * self.cohesion * 0.05
            self.vx += avg_vx * 0.3
            self.vy += avg_vy * 0.3
            self.vx += sep_x * 0.1
            self.vy += sep_y * 0.1

            #Avoid predators
            for shark in sharks:
                shark_dist = math.sqrt((self.x - shark.x) ** 2 + (self.y - shark.y) ** 2)
                if shark_dist < PANIC_VISION:
                    self.vx += (self.x - shark.x) *(PANIC_VISION-shark_dist)/PANIC_VISION *self.cohesion*2
                    self.vy += (self.y - shark.y) *(PANIC_VISION-shark_dist)/PANIC_VISION*self.cohesion*2

            self.vx, self.vy = BoundaryRepulsion(FIELD_SIZE/2,FIELD_SIZE/2 ,0.1*FIELD_SIZE, 5, self.x, self.y, self.vx, self.vy, FIELD_SIZE)

            #Limit fish speed
            speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
            if speed > FISH_SPEED:
                self.vx = (self.vx / speed) * FISH_SPEED
                self.vy = (self.vy / speed) * FISH_SPEED

            #Update position
            self.x += self.vx*TIMESTEP
            self.y += self.vy*TIMESTEP
        # print("FISH SPEED")
        # print(self.vx)
        # print(self.vy)
    def getFishPosition(self):
        return self.x, self.y
    """
    def naturalDeath(self):
        #Exponentially increasing death probability with age
        death_probability = 1 - math.exp(-AGE_DEATH_RATE * self.age)
        return random.random() < death_probability
    """
    def getFishData(self):
        return {"lifetime": self.lifetime, "average_neighbors": self.average_neighbors}

#Class for predator, constant speed for simplicity
class Shark:
    def __init__(self, x, y,simulation_instance):
        self.x = x
        self.y = y
        self.vx = PREDATOR_SPEED*TIMESTEP
        self.vy = PREDATOR_SPEED*TIMESTEP
        self.cooldown = 0
        self.random_direction_timer = 0
        self.simulation = simulation_instance

        self.predicted_x = None  # Initialize predicted position
        self.predicted_y = None


    def move(self, fish_population, fish_position_x, fish_position_y):
        if self.cooldown > 0:

            # Calculate direction toward the center
            center_x, center_y = FIELD_SIZE / 2, FIELD_SIZE / 2
            dx = center_x - self.x
            dy = center_y - self.y
            distance = math.sqrt(dx**2 + dy**2)

            if distance > 0:
                self.vx = (dx / distance) * 0.4 * PREDATOR_SPEED  # Slower return during cooldown
                self.vy = (dy / distance) * 0.4 * PREDATOR_SPEED
            else:
                self.vx = 0
                self.vy = 0
            self.x += self.vx*TIMESTEP
            self.y += self.vy*TIMESTEP
            self.cooldown -= 1

        else:
            self.vx = PREDATOR_SPEED
            self.vy = PREDATOR_SPEED

            closest_fish = None
            closest_distance = float("inf")
            closest_index = 0
            for j, fish in enumerate(fish_population):
                distance = math.sqrt((fish.x - self.x) ** 2 + (fish.y - self.y) ** 2)
                if distance < closest_distance and distance < PREDATOR_VISION:
                    closest_fish = fish
                    closest_distance = distance
                    closest_index = j

            if closest_fish:

                dx1 = closest_fish.x - self.x
                dy1 = closest_fish.y - self.y
                dist1 = math.sqrt(dx1**2 + dy1**2)

                if USE_DELAY:
                    #future_time = min(FUTURE_MAX, max(FUTURE_MIN, closest_distance / PREDATOR_SPEED))
                    future_time = FUTURE_MAX
                    px = np.polyfit(T_FIT, fish_position_x[closest_index,:], 1)
                    py = np.polyfit(T_FIT, fish_position_y[closest_index,:], 1)

                    predicted_x = px[0] * (DELAY_TIME+future_time-1) + px[1]
                    predicted_y = py[0] * (DELAY_TIME+future_time-1) + py[1]
                    predicted_x, predicted_y = clampPosition(predicted_x, predicted_y, FIELD_SIZE)   
                    self.predicted_x = predicted_x  # Store predicted X
                    self.predicted_y = predicted_y  # Store predicted Y


                    dx = (self.predicted_x-self.x)
                    dy = (self.predicted_y-self.y)
                    dist = math.sqrt(dx**2 + dy**2)
                    
                    if dist > 0:
                        future_weight = min(0.8, closest_distance / (FISH_VISION))
                        immediate_weight = 1 - future_weight

                        dx_future = predicted_x - self.x
                        dy_future = predicted_y - self.y
                        dist_future = math.sqrt(dx_future**2 + dy_future**2)

                        self.x += future_weight * dx_future / dist_future * self.vx*TIMESTEP
                        self.y += future_weight * dy_future / dist_future * self.vy*TIMESTEP

                        self.x += immediate_weight * (dx1 / dist1) * self.vx*TIMESTEP
                        self.y += immediate_weight * (dy1 / dist1) * self.vy*TIMESTEP
                else:
                    self.x += dx1*self.vx/dist1*TIMESTEP
                    self.y += dy1*self.vy/dist1*TIMESTEP
            else:
            
                if self.random_direction_timer >= 0:
                
                    self.random_movex = random.uniform(-PREDATOR_SPEED, PREDATOR_SPEED)*TIMESTEP
                    self.random_movey = random.uniform(-PREDATOR_SPEED, PREDATOR_SPEED)*TIMESTEP
                    
                    self.random_direction_timer = RANDOM_DIRECTION_INTERVAL

                
                self.x += self.random_movex*TIMESTEP
                self.y += self.random_movey*TIMESTEP
                self.random_direction_timer -= 1
                
            #Soft boundary conditions, similiar to the fishes. #TODO Change this into a function and use it for both fish and shark (NOT NEEDED BUT
            #looks neater!)
        dx, dy = BoundaryRepulsion(FIELD_SIZE/2, FIELD_SIZE/2, 0.1*FIELD_SIZE, 20, self.x, self.y,self.vx,self.vy, FIELD_SIZE)
        self.vx = dx*TIMESTEP
        self.vy = dy*TIMESTEP
        # print("SHARK SPEED")
        # print(self.vx,self.vy)
        self.x, self.y = clampPosition(self.x, self.y, FIELD_SIZE)

    def eat(self, fish_population):
        if self.cooldown > 0:
            return 0

        fish_eaten = 0
        for fish in fish_population[:]:
            distance = math.sqrt((fish.x - self.x) ** 2 + (fish.y - self.y) ** 2)
            if distance < 2:  

                fish_data = {
                "lifetime": fish.lifetime,
                "average_neighbors": fish.average_neighbors,
                "neighbors": fish.neighbors
                 }      

                self.simulation.all_fish_data[fish.unique_id] = fish_data

                fish_population.remove(fish)
                self.cooldown = PREDATOR_COOLDOWN  #Set cooldown after eating
                fish_eaten += 1
                break
        return fish_eaten
            
#Main Simulation Class
class FishSimulation_1vs1:
    def __init__(self, root):
        self.root = root 
        self.avg_fish_eaten_per_step = 0
        #self.canvas = tk.Canvas(root, width=FIELD_SIZE, height=FIELD_SIZE, bg="lightblue")
        #self.canvas.pack()
        self.time_elapsed = 0  #Total time in simulation steps
        self.total_fish_eaten = 0
        self.fish_id_counter = 0
        self.all_fish_data = {}
        self.spawned = False
        root.geometry(f'{WINDOWS_SIZE + 20}x{WINDOWS_SIZE + 20}')
        #tk1.configure(background='#000000')
        root.attributes('-topmost', 1)
        self.canvas = tk.Canvas(root, background='#ECECEC')
        self.canvas.place(x=10, y=10, height=WINDOWS_SIZE, width=WINDOWS_SIZE)
        self.scaler = WINDOWS_SIZE / FIELD_SIZE

        root.geometry(f'{WINDOWS_SIZE + 20}x{WINDOWS_SIZE + 20}')
        #tk1.configure(background='#000000')
        root.attributes('-topmost', 1)
        self.canvas = tk.Canvas(root, background='#ECECEC')
        self.canvas.place(x=10, y=10, height=WINDOWS_SIZE, width=WINDOWS_SIZE)
        self.scaler = WINDOWS_SIZE / FIELD_SIZE

        self.fish_population = [
            Fish(BASE_COHESION, self.fish_id_counter + i, self) for i in range(NUM_FISH)
        ]
        self.fish_id_counter += NUM_FISH
                
        #Spawn sharks, seeded!
        self.sharks = [
            Shark(
                random.uniform(FIELD_SIZE / 2 - SHARK_SPAWN_AREA, FIELD_SIZE / 2 + SHARK_SPAWN_AREA),
                random.uniform(FIELD_SIZE / 2 - SHARK_SPAWN_AREA, FIELD_SIZE / 2 + SHARK_SPAWN_AREA),
                self
            )
            for _ in range(NUM_SHARKS)
            ]

        self.generation = 0
        self.running = True
        self.fish_positions = [[] for _ in range(NUM_FISH)]
        self.fish_position_x = np.zeros([NUM_FISH, DELAY_TIME])
        self.fish_position_y = np.zeros([NUM_FISH, DELAY_TIME])
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
                (shark.x - 1)*self.scaler,
                (shark.y - 1)*self.scaler,
                (shark.x + 1)*self.scaler,
                (shark.y + 1)*self.scaler,
                fill="red",
            )

        #Draw fish
        for fish in self.fish_population:
            self.canvas.create_oval(
                (fish.x - 0.25)*self.scaler, (fish.y - 0.25)*self.scaler, (fish.x + 0.25)*self.scaler, (fish.y + 0.25)*self.scaler, fill="blue"
            )

        #Calculate average cohesion and number of fish alive
        avg_cohesion = sum(fish.cohesion for fish in self.fish_population) / len(self.fish_population) if self.fish_population else 0 #Not used
        num_fish_alive = len(self.fish_population)
        
        #Calculate successrate of shark
        avg_fish_eaten_per_step = self.total_fish_eaten / (self.time_elapsed*TIMESTEP) if self.time_elapsed > 0 else 0
        self.avg_fish_eaten_per_step = avg_fish_eaten_per_step
        self.canvas.create_text(50, 20, text=f"Time: {int(self.time_elapsed*TIMESTEP)}", font=("Arial", 12), fill="black")
        self.canvas.create_text(65, 40, text=f"Amount of Fish: {NUM_FISH}", font=("Arial", 12), fill="black")
        self.canvas.create_text(80,80, text = f"Amount of Predator: {NUM_SHARKS}", font=("Arial", 12), fill='black')
        self.canvas.create_text(85,100, text= f'Sensory Delay Shark: {FUTURE_MAX}', font=("Arial", 12), fill='black')
        if avg_fish_eaten_per_step > 0:
            self.canvas.create_text(140, 60, text=f"Average Time To Kill (s): {1/avg_fish_eaten_per_step:.2f}", font=("Arial", 12), fill="black")

    
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
    def saveFishPositions(self):
        # Save positions to a CSV file
        with open("fish_positions.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Fish ID", "X Positions", "Y Positions"])
            for i, positions in enumerate(self.fish_positions):
                x_positions, y_positions = zip(*positions)
                writer.writerow([i, list(x_positions), list(y_positions)])
        print("Fish positions saved to 'fish_positions.csv'.")

    def saveFishData(self):
        # Save all fish data (alive and dead) to a CSV file
        with open("fish_data.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Fish ID", "Lifetime", "Average Neighbors", "Neighbors"])
            
            # Write data for currently alive fish
            for fish in self.fish_population:
                writer.writerow([fish.unique_id, fish.lifetime, fish.average_neighbors, fish.neighbors])
            
            # Write data for dead fish
            for fish_id, fish_data in self.all_fish_data.items():
                writer.writerow([fish_id, fish_data["lifetime"], fish_data["average_neighbors"], fish_data["neighbors"]])

        print("Fish data saved to 'fish_data.csv'.")

    def runSimulation(self):
        if NUM_FISH == 1:
            max_time = 10000
            max_steps = max_time/TIMESTEP
        else:
            max_time = 25000
        if not self.running:
            return
        
        if self.time_elapsed >= max_steps:
            self.running = False
            # self.saveFishData()
            root.after(1000, root.destroy)
            return
        
        #survivors = []

        for i,fish in enumerate(self.fish_population):
            fish.move(self.fish_population, self.sharks)
            self.fish_position_x[i,:] = np.roll(self.fish_position_x[i,:], -1, axis=0)
            self.fish_position_y[i,:] = np.roll(self.fish_position_y[i,:], -1, axis=0)
            xpos, ypos = fish.getFishPosition()
            self.fish_position_x[i,DELAY_TIME-1] = xpos
            self.fish_position_y[i,DELAY_TIME-1] = ypos

            if self.time_elapsed % 1000 == 0:
                self.fish_positions[i].append((xpos, ypos))
        
        self.moveSharks(self.fish_position_x,self.fish_position_y) #Moves sharks, eats fish
        
        #Check fish population size and add fish if needed
                
        if len(self.fish_population) != NUM_FISH:
            new_fish = Fish(BASE_COHESION, self.fish_id_counter,self)
            self.fish_id_counter += 1
            self.fish_population.append(new_fish)
            
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
        

        if self.time_elapsed % 1 == 0:
            self.updateCanvas()

        self.root.after(TIME_STEP_DELAY, self.runSimulation)
    def get_TTK(self):
        return self.avg_fish_eaten_per_step
    
class FishSimulation_swarm:
    def __init__(self, root):
        self.root = root 
        #self.canvas = tk.Canvas(root, width=FIELD_SIZE, height=FIELD_SIZE, bg="lightblue")
        #self.canvas.pack()
        self.time_elapsed = 0  #Total time in simulation steps
        self.total_fish_eaten = 0
        self.fish_id_counter = 0
        self.all_fish_data = {}
        self.spawned = False
        self.fish_eaten_log = []
        root.geometry(f'{WINDOWS_SIZE + 20}x{WINDOWS_SIZE + 20}')
        #tk1.configure(background='#000000')
        root.attributes('-topmost', 1)
        self.canvas = tk.Canvas(root, background='#ECECEC',bd=0, highlightthickness=0)
        self.canvas.place(x=10, y=10, height=WINDOWS_SIZE, width=WINDOWS_SIZE)
        self.scaler = WINDOWS_SIZE / FIELD_SIZE
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.predicted_colors = ["green", "orange", "purple", "cyan", "magenta"]  # Extend as needed
        self.fish_position_x = np.zeros([NUM_FISH, DELAY_TIME])
        self.fish_position_y = np.zeros([NUM_FISH, DELAY_TIME])
        self.fish_population = [
            Fish(BASE_COHESION, self.fish_id_counter + i, self) for i in range(NUM_FISH)
        ]
        self.fish_id_counter += NUM_FISH
        root.bind('<s>', lambda event: self.save_canvas_high_res())
        #Spawn sharks, seeded!
        self.sharks = [
            Shark(
                random.uniform(FIELD_SIZE / 2 - SHARK_SPAWN_AREA, FIELD_SIZE / 2 + SHARK_SPAWN_AREA),
                random.uniform(FIELD_SIZE / 2 - SHARK_SPAWN_AREA, FIELD_SIZE / 2 + SHARK_SPAWN_AREA),
                self
            )
            for _ in range(NUM_SHARKS)
            ]

        self.generation = 0
        self.running = True
        self.fish_positions = [[] for _ in range(NUM_FISH)]
        #self.reproduction_timer = 0  #Not used in current implementation
        #self.reproduction_prob = BASE_REPRODUCTION_PROB  #Not used in current implementation
        self.runSimulation()

    
    def moveSharks(self, fish_position_x, fish_position_y):
        for shark in self.sharks:
            shark.move(self.fish_population, fish_position_x, fish_position_y)
            fish_eaten = shark.eat(self.fish_population)
            
        self.total_fish_eaten += fish_eaten
        self.time_elapsed += 1
        self.fish_eaten_log.append((self.time_elapsed, self.total_fish_eaten))
    def saveFishEatenData(self):
        with open("fish_eaten_log.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Time Elapsed", "Fish Eaten"])
            writer.writerows(self.fish_eaten_log)
        print("Fish eaten data saved to 'fish_eaten_log.csv'.")

    def updateCanvas(self):
        self.canvas.delete("all")

        #Draw sharks
        for idx, shark in enumerate(self.sharks):
            self.canvas.create_oval(
                (shark.x - 1)*self.scaler,
                (shark.y - 1)*self.scaler,
                (shark.x + 1)*self.scaler,
                (shark.y + 1)*self.scaler,
                fill="red",
            )
            color = self.predicted_colors[idx % len(self.predicted_colors)]

            
            if shark.predicted_x is not None and shark.predicted_y is not None and DRAW_FUTURE:
                self.canvas.create_oval(
                    (shark.predicted_x - 0.5) * self.scaler,
                    (shark.predicted_y - 0.5) * self.scaler,
                    (shark.predicted_x + 0.5) * self.scaler,
                    (shark.predicted_y + 0.5) * self.scaler,
                    fill=color,
                )

        #Draw fish
        for fish in self.fish_population:
            self.canvas.create_oval(
                (fish.x - 0.25)*self.scaler, (fish.y - 0.25)*self.scaler, (fish.x + 0.25)*self.scaler, (fish.y + 0.25)*self.scaler, fill="blue"
            )

        #Calculate average cohesion and number of fish alive
        avg_cohesion = sum(fish.cohesion for fish in self.fish_population) / len(self.fish_population) if self.fish_population else 0 #Not used
        num_fish_alive = len(self.fish_population)
        
        #Calculate successrate of shark
        avg_fish_eaten_per_step = self.total_fish_eaten / self.time_elapsed if self.time_elapsed > 0 else 0
        
        #self.canvas.create_text(60, 20, text=f"Time: {self.time_elapsed}", font=("Arial", 12), fill="black")
        #self.canvas.create_text(60, 40, text=f"Fish Alive: {num_fish_alive}", font=("Arial", 12), fill="black")
        #self.canvas.create_text(80,80, text = f"Avg Cohesion: {avg_cohesion}", font=("Arial", 12), fill='black')
        #self.canvas.create_text(150, 60, text=f"Avg fish eaten per 1000 timestep: {1000*avg_fish_eaten_per_step:.2f}", font=("Arial", 12), fill="black")

    
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
    def saveFishPositions(self):
        # Save positions to a CSV file
        with open("fish_positions.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Fish ID", "X Positions", "Y Positions"])
            for i, positions in enumerate(self.fish_positions):
                x_positions, y_positions = zip(*positions)
                writer.writerow([i, list(x_positions), list(y_positions)])
        print("Fish positions saved to 'fish_positions.csv'.")

    def saveFishData(self):
        # Save all fish data (alive and dead) to a CSV file
        with open("fish_data.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Fish ID", "Lifetime", "Average Neighbors", "Neighbors"])
            
            # Write data for currently alive fish
            for fish in self.fish_population:
                writer.writerow([fish.unique_id, fish.lifetime, fish.average_neighbors, fish.neighbors])
            
            # Write data for dead fish
            for fish_id, fish_data in self.all_fish_data.items():
                writer.writerow([fish_id, fish_data["lifetime"], fish_data["average_neighbors"], fish_data["neighbors"]])

        print("Fish data saved to 'fish_data.csv'.")

    def save_canvas_high_res(self, dpi=200):

        prefix = "canvas_snapshot"
    
        x1, y1, x2, y2 = 0, 0, self.canvas.winfo_width(), self.canvas.winfo_height()
        ps = self.canvas.postscript(colormode='color', x=x1, y=y1, width=(x2 - x1), height=(y2 - y1))
        
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        snapshots_dir = os.path.join("snapshots_high_res", date_str)
        os.makedirs(snapshots_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{prefix}_{timestamp}.png"
        filepath = os.path.join(snapshots_dir, filename)

        temp_ps = os.path.join(snapshots_dir, f"temp_{prefix}_{timestamp}.ps")
        with open(temp_ps, "w") as file:
            file.write(ps)
        
        gs_executable = "gswin64c"  

        gs_command = [
            gs_executable,
            "-dNOPAUSE",
            "-dBATCH",
            "-sDEVICE=pngalpha",
            f"-r{dpi}",  
            f"-sOutputFile={filepath}",
            temp_ps
        ]

        subprocess.run(gs_command, check=True)

        os.remove(temp_ps)
        
        print(f"Canvas image saved as '{filepath}' with {dpi} DPI.")
           


    def runSimulation(self):
        if not self.running:
            return
        
        if self.time_elapsed >= 20000:
            self.running = False
            self.saveFishData()
            self.saveFishEatenData()
            return
    
        #survivors = []

        for i,fish in enumerate(self.fish_population):
            fish.move(self.fish_population, self.sharks)
            self.fish_position_x[i,:] = np.roll(self.fish_position_x[i,:], -1, axis=0)
            self.fish_position_y[i,:] = np.roll(self.fish_position_y[i,:], -1, axis=0)
            xpos, ypos = fish.getFishPosition()
            self.fish_position_x[i,DELAY_TIME-1] = xpos
            self.fish_position_y[i,DELAY_TIME-1] = ypos

            if self.time_elapsed % 1000 == 0:
                self.fish_positions[i].append((xpos, ypos))
        
        self.moveSharks(self.fish_position_x,self.fish_position_y) #Moves sharks, eats fish
        
        #Check fish population size and add fish if needed
                
        if len(self.fish_population) != NUM_FISH:
            self.spawned = True
            new_fish = Fish(BASE_COHESION, self.fish_id_counter,self)
            self.fish_id_counter += 1
            self.fish_population.append(new_fish)
            
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
        
        if self.time_elapsed % 1 == 0:
            self.updateCanvas()
            print(self.time_elapsed)
        

        self.root.after(TIME_STEP_DELAY, self.runSimulation)

if SWARM:
    # Run the simulation
    root = tk.Tk()
    root.title("Fish Simulation with Multiple Sharks")
    simulation = FishSimulation_swarm(root)
    root.mainloop()
# Run the simulation
else:
    delay_list = [0.5,0.55,0.6,0.65,0.7,0.75,0.8,0.85,0.9,1]
    TTK_list = []

    for delay in delay_list:
        # print(delay)
        random.seed(25)
        if delay == 0:
            USE_DELAY = False
            FUTURE_MAX = -delay
        else:
            USE_DELAY = True
            FUTURE_MAX = delay/TIMESTEP
            # print(FUTURE_MAX)
        root = tk.Tk()
        root.title("Fish Simulation with Multiple Sharks")
        simulation = FishSimulation_1vs1(root)
        root.mainloop()
        KPS = simulation.get_TTK()
        TTK = 1/KPS
        print(TTK)
        TTK_list.append(TTK)
        print(TTK_list)
        
        
    with open("delay_TTK.csv", "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Sensory Delay", "TTK"])
                for D,T in zip(delay_list, TTK_list):
                    writer.writerow([D,T])
            