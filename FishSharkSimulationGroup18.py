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

#Seeding the randomness here for testing and reproducability, comment out to test with nonseeding randomness. This seed was quite nice for the 
#shark spawns but you can mess around with the seeds
#random.seed(62)

#Tuneable Parameters
NUM_FISH = 200 #Amount of prey
NUM_SHARKS = 2 #Amount of predators
FIELD_SIZE = 750 #Size of area, also affects simulation windowsize!
PREDATOR_SPEED = 5 #Speed of predator
FISH_SPEED = 2 #Speed of prey
FISH_VISION = 50 #Vision of prey
PREDATOR_VISION = 150 #Vision of predator
MAX_OFFSPRING = 5 #Max possible amount of prey offspring
TIME_STEP_DELAY = 1 #Changes speed of simulation (Higher = Slower)!
BASE_REPRODUCTION_PROB = 0.001 #Defaut reproduction probability, increases over time and resets to this when prey have offspring
PREDATOR_COOLDOWN = 20  #Cooldown for predator chasing and eating
AGE_DEATH_RATE = 0.00005 #Exponent for the exponential death chance increase with prey age
RANDOM_DIRECTION_INTERVAL = 20 #How often predator changes direction when no prey in vision
SHARK_SPAWN_AREA = FIELD_SIZE/2 #Spawn area, used to distribute the predators. Increase denominator constant to decrease spawn radius


#Class for the prey, changes speed depending on outer factos
class Fish:
    def __init__(self, cohesion, alignment, separation):
        self.x = random.uniform(0, FIELD_SIZE)
        self.y = random.uniform(0, FIELD_SIZE)
        self.vx = random.uniform(-FISH_SPEED, FISH_SPEED)
        self.vy = random.uniform(-FISH_SPEED, FISH_SPEED)
        #These parameters randomized outside of loop (done this way so we can manually set them for testing)
        self.cohesion = cohesion 
        self.alignment = alignment
        self.separation = separation
        
        self.age = 0

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
                avg_vx += other.vx
                avg_vy += other.vy
                count += 1
                sep_x += (self.x - other.x) / distance
                sep_y += (self.y - other.y) / distance

        if count > 0:
            center_x /= count
            center_y /= count
            self.vx += (center_x - self.x) * self.cohesion * 0.01
            self.vy += (center_y - self.y) * self.cohesion * 0.01
            avg_vx /= count
            avg_vy /= count
            self.vx += avg_vx * self.alignment * 0.01
            self.vy += avg_vy * self.alignment * 0.01
            self.vx += sep_x * self.separation * 0.05
            self.vy += sep_y * self.separation * 0.05

        #Avoid sharks
        for shark in sharks:
            shark_dist = math.sqrt((self.x - shark.x) ** 2 + (self.y - shark.y) ** 2)
            if shark_dist < PREDATOR_VISION:
                self.vx += (self.x - shark.x) / shark_dist
                self.vy += (self.y - shark.y) / shark_dist

        if self.x <= 0 or self.x >= FIELD_SIZE:
            self.vx *= -1
        if self.y <= 0 or self.y >= FIELD_SIZE:
            self.vy *= -1

        speed = math.sqrt(self.vx ** 2 + self.vy ** 2)
        if speed > FISH_SPEED:
            self.vx = (self.vx / speed) * FISH_SPEED
            self.vy = (self.vy / speed) * FISH_SPEED

        self.x += self.vx
        self.y += self.vy
        self.age += 1

    #Function to make the fish die of old age
    def naturalDeath(self):
        #Exponentially increasing death probability with age
        death_probability = 1 - math.exp(-AGE_DEATH_RATE * self.age)
        return random.random() < death_probability


#Class for predator, constant speed for simplicity
class Shark:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.cooldown = 0
        self.random_direction_timer = 0
    def move(self, fish_population):
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
            for fish in fish_population:
                distance = math.sqrt((fish.x - self.x) ** 2 + (fish.y - self.y) ** 2)
                if distance < closest_distance and distance < PREDATOR_VISION:
                    closest_fish = fish
                    closest_distance = distance

            if closest_fish:
                dx = closest_fish.x - self.x
                dy = closest_fish.y - self.y
                dist = math.sqrt(dx ** 2 + dy ** 2)
                if dist > 0:
                    self.x += (dx / dist) * PREDATOR_SPEED
                    self.y += (dy / dist) * PREDATOR_SPEED
            else:
           
                if self.random_direction_timer <= 0:
                
                    self.random_movex = random.uniform(-PREDATOR_SPEED, PREDATOR_SPEED)
                    self.random_movey = random.uniform(-PREDATOR_SPEED, PREDATOR_SPEED)
                  
                    self.random_direction_timer = RANDOM_DIRECTION_INTERVAL

                
                self.x += self.random_movex
                self.y += self.random_movey

                
                self.random_direction_timer -= 1
                
    def eat(self, fish_population):
        for fish in fish_population[:]:
            distance = math.sqrt((fish.x - self.x) ** 2 + (fish.y - self.y) ** 2)
            if distance < 10:  
                fish_population.remove(fish)
                self.cooldown = PREDATOR_COOLDOWN  #Set cooldown after eating
                break


#Main Simulation Class
class FishSimulation:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=FIELD_SIZE, height=FIELD_SIZE, bg="lightblue")
        self.canvas.pack()

        self.fish_population = [
            Fish(random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1)) for _ in range(NUM_FISH)
        ]
        #Spawn sharks, random now (seed for reproducability?)
        self.sharks = [
            Shark(
                random.uniform(FIELD_SIZE / 2 - SHARK_SPAWN_AREA, FIELD_SIZE / 2 + SHARK_SPAWN_AREA),
                random.uniform(FIELD_SIZE / 2 - SHARK_SPAWN_AREA, FIELD_SIZE / 2 + SHARK_SPAWN_AREA)
            )
            for _ in range(NUM_SHARKS)
            ]

        self.generation = 0
        self.running = True
        self.reproduction_timer = 0
        self.reproduction_prob = BASE_REPRODUCTION_PROB
        self.runSimulation()

    def moveSharks(self):
        for shark in self.sharks:
            shark.move(self.fish_population)
            shark.eat(self.fish_population)

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
        avg_cohesion = sum(fish.cohesion for fish in self.fish_population) / len(self.fish_population) if self.fish_population else 0
        num_fish_alive = len(self.fish_population)

        
        self.canvas.create_text(60, 20, text=f"Generation: {self.generation}", font=("Arial", 12), fill="black")
        self.canvas.create_text(60, 40, text=f"Fish Alive: {num_fish_alive}", font=("Arial", 12), fill="black")
        self.canvas.create_text(80, 60, text=f"Avg Cohesion: {avg_cohesion:.2f}", font=("Arial", 12), fill="black")

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

    def runSimulation(self):
        if not self.running:
            return

        self.moveSharks()

        survivors = []
        for fish in self.fish_population:
            fish.move(self.fish_population, self.sharks)

            #Check if the fish dies of old age
            if not fish.naturalDeath():
                survivors.append(fish)

        self.fish_population = survivors

        if len(self.fish_population) == 0:
            print(f"All fish eaten by generation {self.generation}!")
        else:
            self.generation += 1
            print(f"Generation {self.generation}: {len(self.fish_population)} fish survive.")
            self.fish_population += self.reproduce()

        self.updateCanvas()
        self.root.after(TIME_STEP_DELAY, self.runSimulation)


# Run the simulation
root = tk.Tk()
root.title("Fish Simulation with Multiple Sharks")
simulation = FishSimulation(root)
root.mainloop()
