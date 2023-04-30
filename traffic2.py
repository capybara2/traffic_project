# -*- coding: utf-8 -*-
"""
Created on Sat Mar 25 19:16:09 2023

@author: johnk
"""

## STAT-4345 PROJECT: TRAFFIC INTERSECTION

# Objective: Simulate traffic at an intersection and find optimum
# settings for traffic lights based on different levels of traffic.

# Cars appear as a poisson process with parameter lambda at some predetermined point.
# If car is generated too close to car in front when generated it is automatically 
# forced back to a safe distance. Perceived safe distance varies by driver.
# Each car has a location, acceleration, current speed and preferred top speed.
# Acceleration is restricted by car in front.
# Reaction time when light changes is an exponential rv.

#Imports
import numpy as np
import matplotlib.pyplot as plt

#Global settings
default_start = 100 #Number of meters from traffic lights where cars appear
L = 10 #Default lambda parameter of poisson process (number of cars per minute at each
#of 4 starting points)
acc_mean = 1.3 #m/s^2
acc_sd = 0.1
ts_mean = 20 #m/s. Equivalent to 45 mph
ts_sd = 1.33 #Equivalent to 3 mph
safe_d_mean = 1.5 #number of seconds it would take to reach back of car in front
safe_d_sd = 0.2
chunk = 0.1 #Number of seconds that elapse in each cycle
car_length = 6.5 #equivalent to 4.5 meters for the car plus 2 meter gap
green_t = 30 #Default number of seconds light is on green
green_arrow_t = 10 #Default number of seconds light is on green arrow
change_lag = 2 #Number of seconds all lights are on red between changes
react = 0.5 #Mean number of seconds to start moving when light goes green/car in front start moving.
react1 = 1 #First car at light
turn_props = [0.1,0.8,0.1] #Proportion turning left, straight, right.
safe_turning_gap = 3 #Need 3 second gap to turn left

class Car():
    
    def __init__(self, front_loc, front_speed, intention, lane):
        self.intention=intention #left turn, straight, right_turn
        self.location=default_start
        self.acceleration=np.random.normal(acc_mean, acc_sd)
        self.top_speed=np.random.normal(ts_mean, ts_sd)
        self.safe_d=np.random.normal(safe_d_mean, safe_d_sd)
        self.speed=self.top_speed
        self.react=np.random.exponential(scale=react)
        self.lane=lane
        self.arrival_time=self.lane.intersection.elapsed_secs
        self.through_time=None
        self.duration=None
        #Check car in front and move back to safe distance if necessary
        safe_dist = front_loc + car_length + self.safe_d*self.speed
        if safe_dist > self.location:
            self.location = safe_dist
            self.speed = front_speed
            
            
    def move(self, chunk, front_loc, front_speed, light, time_to_change):
        
        start_speed = self.speed
        if start_speed==0:
            if front_loc>=(self.location-car_length) and front_speed==0:
                return
            self.react -= chunk
            if self.react > 0:
                return
            else:
                self.react = np.random.exponential(scale=react)
        
        ### There are three intentions: straight, left, right.
        # 1. if car is going straight:
        if self.intention=="straight":
            #Can car beat red light at current speed? If no, decelerate.
            if light=="green" or (light=="green" and start_speed*time_to_change > self.location):
                self.speed = min(self.top_speed, self.speed + chunk*self.acceleration)
                self.location -= ((start_speed + self.speed)/2) * chunk
            else: #Decelerate
                #Need to get from current speed to zero at location 1 (red light plus 1m gap).
                #3rd equation of motion: v^2 = u^2 + 2as
                #So a = (v^2 - u^2) / 2s
                #Where a = acceleration, v=final velocity, u=initial velocity, s=distance
                decel = (0 - self.speed**2) / (2*(self.location-1))
                self.speed += (decel*chunk) #Negative
                self.speed = max(self.speed, 0) #cannot go backwards!
                self.location -= ((start_speed + self.speed)/2) * chunk
                
        # 2. if car is turning left:
        elif self.intention=="left turn":
            #Green arrow light
            if light=="green arrow" or (light=="green arrow" and start_speed*time_to_change > self.location):
                self.speed = min(self.top_speed, self.speed + chunk*self.acceleration)
                self.location -= ((start_speed + self.speed)/2) * chunk

            #Green light
            elif light=="green" or (light=="green" and start_speed*time_to_change > self.location):
                #Check oncoming gap
                gap = self.lane.oncoming_lane.gap
                if gap > safe_turning_gap: #effectively green
                    self.speed = min(self.top_speed, self.speed + chunk*self.acceleration)
                    self.location -= ((start_speed + self.speed)/2) * chunk
                else: #effectively red
                    decel = (0 - self.speed**2) / (2*(self.location-1))
                    self.speed += (decel*chunk) #Negative
                    self.speed = max(self.speed, 0) #cannot go backwards!
                    self.location -= ((start_speed + self.speed)/2) * chunk
            else: #red light
                decel = (0 - self.speed**2) / (2*(self.location-1))
                self.speed += (decel*chunk) #Negative
                self.speed = max(self.speed, 0) #cannot go backwards!
                self.location -= ((start_speed + self.speed)/2) * chunk
                
        # 3. if car is turning right:
        elif self.intention=="right turn":
            #Green light
            if light=="green" or (light=="green" and start_speed*time_to_change > self.location):
                self.speed = min(self.top_speed, self.speed + chunk*self.acceleration)
                self.location -= ((start_speed + self.speed)/2) * chunk

            #Red light
            elif light=="red":
                 #Check L to R gap
                 gap = self.lane.l_to_r_lane.gap
                 if gap > safe_turning_gap: #effectively green
                     self.speed = min(self.top_speed, self.speed + chunk*self.acceleration)
                     self.location -= ((start_speed + self.speed)/2) * chunk
                 else: #effectively red
                     decel = (0 - self.speed**2) / (2*(self.location-1))
                     self.speed += (decel*chunk) #Negative
                     self.speed = max(self.speed, 0) #cannot go backwards!
                     self.location -= ((start_speed + self.speed)/2) * chunk
            #Green arrow
            elif light=="green arrow":
                #Check oncoming left turn gap
                gap = self.lane.oncoming_lt_lane.gap
                if gap > safe_turning_gap: #effectively green
                    self.speed = min(self.top_speed, self.speed + chunk*self.acceleration)
                    self.location -= ((start_speed + self.speed)/2) * chunk
                else: #effectively red
                    decel = (0 - self.speed**2) / (2*(self.location-1))
                    self.speed += (decel*chunk) #Negative
                    self.speed = max(self.speed, 0) #cannot go backwards!
                    self.location -= ((start_speed + self.speed)/2) * chunk
            
        #Check car in front and move back to safe distance if necessary
        safe_dist = front_loc + car_length + self.safe_d*self.speed
        if safe_dist > self.location:
            self.speed = front_speed
            self.location = front_loc + car_length + self.safe_d*self.speed
        
class Lane():
    
    def __init__(self, intersection, lane_type, orientation):
        self.cars=[]
        self.lane_type=lane_type
        self.intersection=intersection
        self.orientation=orientation
        if self.orientation=="north":
            self.oncoming = "south" #oncoming lane affects left turn
            self.l_to_r = "east" #L to R lane affects right turn
        elif self.orientation=="south":
            self.oncoming = "north"
            self.l_to_r = "west"
        elif self.orientation=="west":
            self.oncoming = "east"
            self.l_to_r = "north"
        elif self.orientation=="east":
            self.oncoming = "west"
            self.l_to_r = "south"
        self.cars_through=[]
        self.gap=1000
        if self.orientation=="ns" or self.orientation=="sn":
            self.light="green"
            self.time_to_change=green_t
        else:
            self.light="red"
            self.time_to_change=green_t + change_lag
            
    def get_oncoming_lane(self):
        for lane in self.intersection.lanes:
            if lane.orientation==self.oncoming and lane.lane_type=="straight":
                self.oncoming_lane = lane
                
    def get_oncoming_lt_lane(self):
        for lane in self.intersection.lanes:
            if lane.orientation==self.oncoming and lane.lane_type=="left turn":
                self.oncoming_lane = lane
                
    def get_l_to_r_lane(self):
        for lane in self.intersection.lanes:
            if lane.orientation==self.l_to_r and lane.lane_type=="straight":
                self.l_to_r_lane = lane
        
    def generate_cars(self):
        
        if self.lane_type == "left turn":
            n = np.random.poisson(chunk*(self.intersection.L*turn_props[0])/60) #Poisson process
        else:
            n = np.random.poisson(chunk*(self.intersection.L*(1-turn_props[0]))/60)
        for i in range(n):
            #First check speed and location of car in front
            if self.cars == []: #Lane is empty
                front_loc = -1000
                front_speed = -1000
            else:
                front_car = self.cars[-1]
                front_loc = front_car.location
                front_speed = front_car.speed
            if self.lane_type == "straight":
                r = np.random.rand()
                p = turn_props[1] / (turn_props[1] + turn_props[2])
                if r < p:
                    intention = "straight"
                else:
                    intention = "right turn"
            else:
                intention = "left turn"
            new_car = Car(front_loc, front_speed, intention, lane=self)
            self.cars.append(new_car)
            
    def move_cars(self):
        for i, car in enumerate(self.cars):
            #First check speed and location of car in front
            if i == 0: #Road is empty ahead
                front_loc = -1000
                front_speed = -1000
            else:
                front_car = self.cars[i-1]
                front_loc = front_car.location
                front_speed = front_car.speed
            car.move(chunk, front_loc, front_speed, self.light, self.time_to_change)

                
    def remove_cars(self):
        for car in self.cars:
            if car.location < 0:
                car.through_time = self.intersection.elapsed_secs
                car.duration = car.through_time - car.arrival_time
                self.cars_through.append(car)
                self.cars.remove(car)
                
    def print_status(self):
        print("Current status: "+self.light)
        print("Time to change: "+str(self.time_to_change))
        print("Cars passed through: "+str(self.through))
        print("Current car locations:")
        for car in self.cars:
            print(str(car.location))
            
    def run_chunk(self):
        self.generate_cars()
        self.move_cars()
        self.remove_cars()
        self.time_to_change -= chunk
        if self.cars==[] or self.cars[0].speed==0:
            self.gap = 1000
        else:
            self.gap = self.cars[0].location / self.cars[0].speed

        if self.lane_type=="left turn":
            if self.time_to_change <= 0:
                if self.light=="red":
                    #Generate reaction time of first car (if any).
                    stationary_cars = [car for car in self.cars if car.speed==0]
                    if stationary_cars != []:
                        stationary_cars[0].react = np.random.exponential(scale=react1)
                    self.light = "green arrow"
                    self.time_to_change = green_arrow_t
                elif self.light=="green arrow":
                    self.light = "red2" #red2 denotes red between green arrow and green
                    self.time_to_change = change_lag
                elif self.light=="red2":
                    #Generate reaction time of first car (if any).
                    stationary_cars = [car for car in self.cars if car.speed==0]
                    if stationary_cars != []:
                        stationary_cars[0].react = np.random.exponential(scale=react1)
                    self.light = "green"
                    self.time_to_change = green_arrow_t
                elif self.light=="green":
                    self.light = "red"
                    self.time_to_change = green_t + change_lag
        else: #Straight lane
            if self.light=="red":
                #Generate reaction time of first car (if any).
                stationary_cars = [car for car in self.cars if car.speed==0]
                if stationary_cars != []:
                    stationary_cars[0].react = np.random.exponential(scale=react1)
                self.light = "green"
                self.time_to_change = green_t
            elif self.light=="green":
                self.light = "red"
                self.time_to_change = green_t + change_lag + green_arrow_t + change_lag
                
        

class Intersection():
    
    def __init__(self):
        lane_orientations = ["north", "west", "south", "east"]
        lane_types = ["left turn", "straight"]
        self.lanes = []
        self.L=L
        for o in lane_orientations:
            for t in lane_types:
                new_lane = Lane(self, t, o)
                self.lanes.append(new_lane)
        for lane in self.lanes:
            lane.get_oncoming_lane()
            lane.get_oncoming_lt_lane()
            lane.get_l_to_r_lane()
        self.elapsed_secs = 0
        self.cars_through=[]
        
    def run_chunk(self):
        for lane in self.lanes:
            lane.run_chunk()
        self.elapsed_secs += chunk
            
    def simulate(self, L, minutes, burn):
        
        self.L=L
        for lane in self.lanes:
            self.cars_through.extend(lane.cars_through)
            
        n = int((minutes*60) / chunk)
        for i in range(n):
            self.run_chunk()
        
        for lane in self.lanes:
            self.cars_through.extend(lane.cars_through)
            
        #Ignore burn-in cars
        durations = [car.duration for car in self.cars_through if car.arrival_time >= 5 and car.through_time]
        cplpm = round(len(durations) / (minutes * 4), 2)
        
        my_results = {"Lambda":L, "Total Cars Through":len(durations), 
                      "Cars per Light per Minute":cplpm, 
                      "Mean Time": round(np.mean(durations),2),
                      "Mean Time Squared": round(np.mean([x**2 for x in durations]),2)}
        
        return(my_results)
    

#test for one hour
my_results = []
for i in range(1, 21):
    my_intersection = Intersection()
    my_results.append(my_intersection.simulate(L=i, minutes=65, burn=5))

# Plot Mean Time
x = [result["Lambda"] for result in my_results]
y = [result["Mean Time"] for result in my_results]
plt.plot(x, y, marker="o", linestyle="-")
plt.xlabel("Lambda")
plt.ylabel("Mean Time")
plt.xticks(np.arange(2, 21, 2), labels=np.arange(2, 21, 2))
plt.show()

#Plot Cars per Light per Minute
x = [result["Lambda"] for result in my_results]
y = [result["Cars per Light per Minute"] for result in my_results]
plt.plot(x, y, marker="o", linestyle="-")
plt.xlabel("Lambda")
plt.ylabel("Cars per Light per Minute")
plt.xticks(np.arange(2, 21, 2), labels=np.arange(2, 21, 2))
plt.show()

#Loop through for values of lambda 5, 10, 15. For each one loop through green_t = 15,
#30, 45, 60 and green_arrow_t = 5, 10, 15. Get Mean Time and Mean Time ^2 for each.

for l in [5, 10, 15]:
    for g in [15, 30, 45, 60]:
        for a in [5, 10, 15]:
            my_intersection = Intersection()
            green_t = g
            green_arrow_t = a
            results = my_intersection.simulate(L=l, minutes=65, burn=5)
            print("Lambda:", l)
            print("Green Light Time:", g)
            print("Green Arrow Time:", a)
            print("Mean Time:", results["Mean Time"])
            print("Mean Time Squared:", results["Mean Time Squared"])