import simpy

class Ship:
    def __init__(self):
        self.next_arrival = 0

class Port:
    def __init__(self, env):
        self.env = env

    def unload(self, ship):
        pass

def arrival(env: simpy.Environment):
    port = Port()
    while True:
        ship = Ship()
        env.process(port.unload(ship))
        env.timeout(ship.next_arrival)
        

env = simpy.Environment()
env.process(arrival(env))
env.run(until=43200)