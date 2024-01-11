import simpy
import numpy as np
import matplotlib.pyplot as plt
import scipy
from statistics import mean

UNLOADINGS_COUNT = 3
UNLOADING_GROUPS_COUNT = 3
CRANES_COUNT = 2

SHIP_CAPACITIES = [100, 80, 60]
SHIP_LOAD_STD = 10

NEXT_ARRIVAL = 150

# Типы контейнеров. Первое - параметр времени разгрузки. Второе - занимаемый объём 
CONTAINER_TYPES = [
    (20, 3), 
    (15, 2),
    (10, 1)
]


unloading_counts = [0]
unloading_times = [0]
unloading_crane_usetimes = 0
ships_dtimes = []
ships_max_queue = 0


class Container:
    def __init__(self):
        type = CONTAINER_TYPES[np.random.choice(len(CONTAINER_TYPES))]
        self.needs_crane = type[1] == 3
        self.unload_time = np.random.exponential(type[0])
        self.volume = type[1]


class Ship:
    def __init__(self):
        self.next_arrival = np.random.exponential(NEXT_ARRIVAL)
        self.move_time = np.random.normal(25, 10)
        self.containers: list[Container] = []
        self.unloaded_count = 0
        capacity_type = np.random.choice(SHIP_CAPACITIES)
        capacity = np.random.normal(capacity_type, SHIP_LOAD_STD)
        while capacity >= 3:
            container = Container()
            capacity -= container.volume
            self.containers.append(container)

    def select_unloading(self, unloadings: list[tuple[simpy.Resource, simpy.Resource]]) -> tuple[simpy.Resource, simpy.Resource]:
        global ships_max_queue
        queue_lens = [ len(unloading[0].queue) for unloading in unloadings ]
        if ships_max_queue < max(queue_lens):
            ships_max_queue = max(queue_lens)
        return unloadings[np.argmin(queue_lens)]


class Port:
    def __init__(self, env: simpy.Environment):
        self.env = env
        self.unloadings = [
            (simpy.Resource(env, 1), simpy.Resource(env, UNLOADING_GROUPS_COUNT)) 
            for _ in range(UNLOADINGS_COUNT)
        ]
        self.cranes = simpy.Resource(env, CRANES_COUNT)

    def unload_container(self, container: Container, unloading, unloading_area, start_unloading, ship: Ship):
        with unloading[1].request() as workgroup:
            global unloading_crane_usetimes, unloading_counts, unloading_times, ships_dtimes
            yield workgroup
            crane = None
            use_crane_start = 0
            if container.needs_crane:
                crane = self.cranes.request()
                yield crane
                use_crane_start = self.env.now
            yield self.env.timeout(container.unload_time)
            if container.needs_crane:
                self.cranes.release(crane)
                unloading_crane_usetimes += self.env.now - use_crane_start
            self.unloadings
            unloading_counts.append(unloading_counts[-1] + 1)
            unloading_times.append(self.env.now)
            ship.unloaded_count += 1
            if ship.unloaded_count == len(ship.containers):
                unloading[0].release(unloading_area)
                ships_dtimes.append(self.env.now - start_unloading)
            

    def unload_ship(self, ship: Ship):
        start_unloading = self.env.now
        unloading = ship.select_unloading(self.unloadings)
        unloading_area = unloading[0].request()
        yield unloading_area
        for container in ship.containers:
            env.process(self.unload_container(container, unloading, unloading_area, start_unloading, ship))

def arrival(env: simpy.Environment):
    port = Port(env)
    while True:
        ship = Ship()
        env.process(port.unload_ship(ship))
        yield env.timeout(ship.next_arrival)

env = simpy.Environment()
env.process(arrival(env))
env.run(until=43200)

print(f'Среднее время разгрузки корабля {round(mean(ships_dtimes), 2)}')
print(f'Максимальная длина очереди кораблей на разгрузку {ships_max_queue}')
cranes_activity = round(unloading_crane_usetimes / (43200 * CRANES_COUNT) * 100, 2)
print(f'Процент времени использования кранов для разгрузки {cranes_activity}%')

def_unloading_times = list(np.array(unloading_times) / 1440)
def_unloading_counts = list(unloading_counts)
def_ships_dtimes = ships_dtimes

unloading_counts = [0]
unloading_times = [0]
unloading_crane_usetimes = 0
ships_dtimes = []
ships_max_queue = 0


SHIP_CAPACITIES = list(np.array(SHIP_CAPACITIES) + 50)
CRANES_COUNT = 7
UNLOADINGS_COUNT = 4
NEXT_ARRIVAL = 200

env = simpy.Environment()
env.process(arrival(env))
env.run(until=43200)


ALPHA = 0.05
print(f'Среднее время разгрузки в эксперименте: {round(mean(ships_dtimes), 2)}')
print('Гипотеза H0: среднее время разгрузки коробля не изменилось')
print('Гипотиза H1: среднее время разгрузки коробля уменьшилось')
ttest, pval = scipy.stats.ttest_ind(def_ships_dtimes, ships_dtimes, alternative='greater')
print(f'ttest, pval: {ttest}, {pval}')
if pval < ALPHA:
    print('Верна гипотеза H1: среднее время разгрузки коробля уменьшилось')
else:
    print('Верна гипотеза H0: среднее время разгрузки коробля не изменилось')

unloading_times = np.array(unloading_times) / 1440
plt.plot(unloading_times, unloading_counts, label='experiment')
plt.plot(def_unloading_times, def_unloading_counts, label='default')
plt.xlabel('Дни моделирования')
plt.ylabel('Количество выгруженных контейнеров')
plt.legend()
plt.show()