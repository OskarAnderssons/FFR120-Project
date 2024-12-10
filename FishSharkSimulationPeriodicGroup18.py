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

#Seeding the randomness here for testing and reproducability, comment out to test with nonseeding randomness. This seed was quite nice for the 
#shark spawns but you can mess around with the seeds
random.seed(62)

#Tuneable Parameters
NUM_FISH = 200 #Amount of prey constant for now
BASE_COHESION = 0.5
NUM_SHARKS = 2 #Amount of predators
FIELD_SIZE = 1000 #Size of area, also affects simulation windowsize!
PREDATOR_SPEED = 8 #Speed of predator
FISH_SPEED = 6 #Speed of prey
FISH_VISION = 150 #Vision of prey
PANIC_VISION = 100 #Vision of prey when predator is close
PREDATOR_VISION = FIELD_SIZE*2 #Vision of predator
MAX_OFFSPRING = 5 #Max possible amount of prey offspring
TIME_STEP_DELAY = 10 #Changes speed of simulation (Higher = Slower)!
BASE_REPRODUCTION_PROB = 0.001 #Defaut reproduction probability, increases over time and resets to this when prey have offspring
PREDATOR_COOLDOWN = 50  #Cooldown for predator chasing and eating
AGE_DEATH_RATE = 0.00005 #Exponent for the exponential death chance increase with prey age
RANDOM_DIRECTION_INTERVAL = 20 #How often predator changes direction when no prey in vision
SHARK_SPAWN_AREA = FIELD_SIZE/2 #Spawn area, used to distribute the predators. Increase denominator constant to decrease spawn radius
SENSORY_DELAY_SHARK = -5 #Placeholder value for now -2 or lower if USE_DELAY == TRUE
DELAY_TIME = -SENSORY_DELAY_SHARK #Inverse of the negative delay, used for preallocating array
USE_DELAY = True
T_FIT = np.arange(DELAY_TIME)
FUTURE_MAX = 2
FUTURE_MIN = 2
WINDOWS_SIZE = 750

class Fish:
    def __init__(self, cohesion):
        #Random spawns and speeds but seeded so OK
        self.x = random.uniform(0, FIELD_SIZE)
        self.y = random.uniform(0, FIELD_SIZE)
        self.vx = random.uniform(-FISH_SPEED, FISH_SPEED)
        self.vy = random.uniform(-FISH_SPEED, FISH_SPEED)
        self.cohesion = cohesion  #Swarming parameter

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
                repulsion_strength = math.exp(-distance / 5)  #Exponential falloff
                sep_x += (self.x - other.x) * repulsion_strength
                sep_y += (self.y - other.y) * repulsion_strength

        if count > 0:
            #Adjust movement based on cohesion
            center_x /= count
            center_y /= count
            self.vx += (center_x - self.x) * self.cohesion * 0.01
            self.vy += (center_y - self.y) * self.cohesion * 0.01
            avg_vx /= count
            avg_vy /= count

        #Fish movement controlled by noise, the schools average speed and a separation force to avoid clustering
        self.vx += random.uniform(-0.5, 0.5) * self.cohesion * 0.1
        self.vy += random.uniform(-0.5, 0.5) * self.cohesion * 0.1
        self.vx += avg_vx * 0.2
        self.vy += avg_vy * 0.2
        self.vx += sep_x * 0.05
        self.vy += sep_y * 0.05

        #Avoid predators
        for shark in sharks:
            shark_dist = math.sqrt((self.x - shark.x) ** 2 + (self.y - shark.y) ** 2)
            if shark_dist < PANIC_VISION:
                self.vx += (self.x - shark.x) *(PANIC_VISION-shark_dist)/PANIC_VISION * self.cohesion 
                self.vy += (self.y - shark.y) *(PANIC_VISION-shark_dist)/PANIC_VISION* self.cohesion


        #Limit fish speed
        speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        if speed > FISH_SPEED:
            self.vx = (self.vx / speed) * FISH_SPEED
            self.vy = (self.vy / speed) * FISH_SPEED

        # Periodic boundary conditions
        if self.x < 0:
            self.x += FIELD_SIZE
        elif self.x > FIELD_SIZE:
            self.x -= FIELD_SIZE

        if self.y < 0:
            self.y += FIELD_SIZE
        elif self.y > FIELD_SIZE:
            self.y -= FIELD_SIZE

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
        self.vx = random.uniform(-PREDATOR_SPEED, PREDATOR_SPEED)
        self.vy = random.uniform(-PREDATOR_SPEED, PREDATOR_SPEED)
        self.cooldown = 0
        self.random_direction_timer = 0

    def move(self, fish_population, fish_position_x, fish_position_y):
        if self.cooldown > 0:
            self.vx = 0.4*PREDATOR_SPEED
            self.vy = 0.4*PREDATOR_SPEED
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

                predicted_x = px[0] * future_time + px[1]
                predicted_y = py[0] * future_time + py[1]

                dx = (px[0]-self.x)
                dy = (py[0]-self.y)
                dist = math.sqrt(dx**2 + dy**2)
                
                if dist > 0:
                    future_weight = min(1, closest_distance / PREDATOR_VISION)
                    immediate_weight = 1 - future_weight

                    dx_future = predicted_x - self.x
                    dy_future = predicted_y - self.y
                    dist_future = math.sqrt(dx_future**2 + dy_future**2)

                    self.x += future_weight * dx_future / dist_future * self.vx
                    self.y += future_weight * dy_future / dist_future * self.vy

                    self.x += immediate_weight * (dx1 / dist1) * self.vx
                    self.y += immediate_weight * (dy1 / dist1) * self.vy
            else:
                self.x += dx1*self.vx/dist1
                self.y += dy1*self.vy/dist1
        else:
        
            if self.random_direction_timer >= 0:
            
                self.random_movex = random.uniform(-PREDATOR_SPEED, PREDATOR_SPEED)
                self.random_movey = random.uniform(-PREDATOR_SPEED, PREDATOR_SPEED)
                
                self.random_direction_timer = RANDOM_DIRECTION_INTERVAL

            
            self.x += self.random_movex
            self.y += self.random_movey
            self.random_direction_timer -= 1
            
        #Soft boundary conditions, similiar to the fishes. #TODO Change this into a function and use it for both fish and shark (NOT NEEDED BUT
        #looks neater!)
        if self.x < 0:
            self.x += FIELD_SIZE
        elif self.x > FIELD_SIZE:
            self.x -= FIELD_SIZE

        if self.y < 0:
            self.y += FIELD_SIZE
        elif self.y > FIELD_SIZE:
            self.y -= FIELD_SIZE

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
        #self.canvas = tk.Canvas(root, width=FIELD_SIZE, height=FIELD_SIZE, bg="lightblue")
        #self.canvas.pack()
        self.time_elapsed = 0  #Total time in simulation steps
        self.total_fish_eaten = 0

        root.geometry(f'{WINDOWS_SIZE + 20}x{WINDOWS_SIZE + 20}')
        #tk1.configure(background='#000000')
        root.attributes('-topmost', 1)
        self.canvas = tk.Canvas(root, background='#ECECEC')
        self.canvas.place(x=10, y=10, height=WINDOWS_SIZE, width=WINDOWS_SIZE)
        self.scaler = WINDOWS_SIZE / FIELD_SIZE

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

    def updateCanvas(self):
        self.canvas.delete("all")

        #Draw sharks
        for shark in self.sharks:
            self.canvas.create_oval(
                (shark.x - 10)*self.scaler,
                (shark.y - 10)*self.scaler,
                (shark.x + 10)*self.scaler,
                (shark.y + 10)*self.scaler,
                fill="red",
            )

        #Draw fish
        for fish in self.fish_population:
            self.canvas.create_oval(
                (fish.x - 5)*self.scaler, (fish.y - 5)*self.scaler, (fish.x + 5)*self.scaler, (fish.y + 5)*self.scaler, fill="blue"
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
        
        if self.time_elapsed >= 10000:
            self.running = False
            self.saveFishPositions()
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

            self.fish_positions[i].append((xpos, ypos))


        self.moveSharks(fish_position_x,fish_position_y) #Moves sharks, eats fish
        #Check fish population size and add fish if needed
        if len(self.fish_population) != NUM_FISH:
            self.fish_population.append(Fish(BASE_COHESION))
        
        if self.time_elapsed % 100 == 0:
            self.updateCanvas()
        print(self.time_elapsed)
        self.root.after(TIME_STEP_DELAY, self.runSimulation)
            
# Run the simulation
root = tk.Tk()
root.title("Fish Simulation with Multiple Sharks")
simulation = FishSimulation(root)
root.mainloop()