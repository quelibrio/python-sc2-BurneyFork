import sc2
from sc2 import maps
from sc2.main import run_game
from sc2.data import Difficulty, Race
from sc2.player import Bot, Computer
from sc2.bot_ai import BotAI
from sc2 import position
from sc2.ids.unit_typeid import UnitTypeId
import random
import cv2
import numpy as np
import os
import time
import math
#import keras
import traceback
from minimap_revision import MinimapRevision

#os.environ["SC2PATH"] = '/starcraftstuff/StarCraftII/'
HEADLESS = False


class SentdeBot(BotAI):
    def __init__(self, use_model=False, title=1):
        self.MAX_WORKERS = 50
        self.do_something_after = 0
        self.use_model = use_model
        self.title = title
        self.unit_command_uses_self_do = True
        self.scouts_and_spots = {}

        # ADDED THE CHOICES #
        self.choices = {0: self.build_scout,
                        1: self.build_zealot,
                        2: self.build_gateway,
                        3: self.build_voidray,
                        4: self.build_stalker,
                        5: self.build_worker,
                        6: self.build_assimilator,
                        7: self.build_stargate,
                        8: self.build_pylon,
                        9: self.defend_nexus,
                        10: self.attack_known_enemy_unit,
                        11: self.attack_known_enemy_structure,
                        12: self.expand,
                        13: self.do_nothing,
                        }

        self.train_data = []
        if self.use_model:
            print("USING MODEL!")
            self.model = keras.models.load_model("BasicCNN-30-epochs-0.0001-LR-4.2")

    def on_end(self, game_result):
        print('--- on_end called ---')
        print(game_result, self.use_model)

        with open("gameout-random-vs-medium.txt","a") as f:
            if self.use_model:
                f.write("Model {} - {}\n".format(game_result, int(self.time_m)))
            else:
                f.write("Random {} - {}\n".format(game_result, int(self.time_m)))

    async def on_step(self, iteration):

        #self.time = (self.state.game_loop/22.4) / 60
        self.time_m = self.time / 60

        #print('Time:',self.time)
        await self.distribute_workers()
        await self.scout()
        await self.intel()
        await self.do_something()

    def random_location_variance(self, location):
        x = location[0]
        y = location[1]

        #  FIXED THIS
        x += random.randrange(-5,5)
        y += random.randrange(-5,5)

        if x < 0:
            print("x below")
            x = 0
        if y < 0:
            print("y below")
            y = 0
        if x > self.game_info.map_size[0]:
            print("x above")
            x = self.game_info.map_size[0]
        if y > self.game_info.map_size[1]:
            print("y above")
            y = self.game_info.map_size[1]

        go_to = position.Point2(position.Pointlike((x,y)))

        return go_to

    async def scout(self):
        '''
        ['__call__', '__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_game_data', '_proto', '_type_data', 'add_on_tag', 'alliance', 'assigned_harvesters', 'attack', 'build', 'build_progress', 'cloak', 'detect_range', 'distance_to', 'energy', 'facing', 'gather', 'has_add_on', 'has_buff', 'health', 'health_max', 'hold_position', 'ideal_harvesters', 'is_blip', 'is_burrowed', 'is_enemy', 'is_flying', 'is_idle', 'is_mine', 'is_mineral_field', 'is_powered', 'is_ready', 'is_selected', 'is_snapshot', 'is_structure', 'is_vespene_geyser', 'is_visible', 'mineral_contents', 'move', 'name', 'noqueue', 'orders', 'owner_id', 'position', 'radar_range', 'radius', 'return_resource', 'shield', 'shield_max', 'stop', 'tag', 'train', 'type_id', 'vespene_contents', 'warp_in']
        '''
        self.expand_dis_dir = {}

        for el in self.expansion_locations_list:
            distance_to_enemy_start = el.distance_to(self.enemy_start_locations[0])
            #print(distance_to_enemy_start)
            self.expand_dis_dir[distance_to_enemy_start] = el

        self.ordered_exp_distances = sorted(k for k in self.expand_dis_dir)

        existing_ids = [unit.tag for unit in self.all_units]
        # removing of scouts that are actually dead now.
        to_be_removed = []
        for noted_scout in self.scouts_and_spots:
            if noted_scout not in existing_ids:
                to_be_removed.append(noted_scout)

        for scout in to_be_removed:
            del self.scouts_and_spots[scout]

        if len(self.structures(UnitTypeId.ROBOTICSFACILITY).ready) == 0:
            unit_type = UnitTypeId.PROBE
            unit_limit = 1
        else:
            unit_type = UnitTypeId.OBSERVER
            unit_limit = 15

        assign_scout = True

        if unit_type == UnitTypeId.PROBE:
            for unit in self.all_units(UnitTypeId.PROBE):
                if unit.tag in self.scouts_and_spots:
                    assign_scout = False

        if assign_scout:
            if len(self.all_units(unit_type).idle) > 0:
                for obs in self.all_units(unit_type).idle[:unit_limit]:
                    if obs.tag not in self.scouts_and_spots:
                        for dist in self.ordered_exp_distances:
                            try:
                                location = next(value for key, value in self.expand_dis_dir.items() if key == dist)
                                # DICT {UNIT_ID:LOCATION}
                                active_locations = [self.scouts_and_spots[k] for k in self.scouts_and_spots]

                                if location not in active_locations:
                                    if unit_type == UnitTypeId.PROBE:
                                        for unit in self.all_units(UnitTypeId.PROBE):
                                            if unit.tag in self.scouts_and_spots:
                                                continue

                                    await self.do(obs.move(location))
                                    self.scouts_and_spots[obs.tag] = location
                                    break
                            except Exception as e:
                                pass

        for obs in self.all_units(unit_type):
            if obs.tag in self.scouts_and_spots:
                if obs in [probe for probe in self.all_units(UnitTypeId.PROBE)]:
                    await self.do(obs.move(self.random_location_variance(self.scouts_and_spots[obs.tag])))

    async def intel(self):
        pass
        minimap=MinimapRevision(self)
        game_data = minimap.map_data
        # #map_data = np.copy(self._game_info.terrain_height)
        # draw_dict = {
        #              UnitTypeId.NEXUS: [15, (0, 255, 0)],
        #              UnitTypeId.PYLON: [3, (20, 235, 0)],
        #              UnitTypeId.PROBE: [1, (55, 200, 0)],
        #              UnitTypeId.ASSIMILATOR: [2, (55, 200, 0)],
        #              UnitTypeId.GATEWAY: [3, (200, 100, 0)],
        #              UnitTypeId.CYBERNETICSCORE: [3, (150, 150, 0)],
        #              UnitTypeId.STARGATE: [5, (255, 0, 0)],
        #              UnitTypeId.ROBOTICSFACILITY: [5, (215, 155, 0)],
        #              UnitTypeId.VOIDRAY: [3, (255, 100, 0)],
        #             }

        # for unit_type in draw_dict:
        #     for unit in self.all_units(unit_type).ready:
        #         pos = unit.position
        #         cv2.circle(game_data, (int(pos[0]), int(pos[1])), draw_dict[unit_type][0], draw_dict[unit_type][1], -1)
        #     for unit in self.structures(unit_type).ready:
        #         pos = unit.position
        #         cv2.circle(game_data, (int(pos[0]), int(pos[1])), draw_dict[unit_type][0], draw_dict[unit_type][1], -1)

        # # from Александр Тимофеев via YT
        # main_base_names = ['nexus', 'commandcenter', 'orbitalcommand', 'planetaryfortress', 'hatchery']
        # for enemy_building in self.enemy_structures:
        #     pos = enemy_building.position
        #     if enemy_building.name.lower() not in main_base_names:
        #         cv2.circle(game_data, (int(pos[0]), int(pos[1])), 5, (200, 50, 212), -1)
        # for enemy_building in self.enemy_structures:
        #     pos = enemy_building.position
        #     if enemy_building.name.lower() in main_base_names:
        #         cv2.circle(game_data, (int(pos[0]), int(pos[1])), 15, (0, 0, 255), -1)

        # for enemy_unit in self.all_enemy_units:

        #     if not enemy_unit.is_structure:
        #         worker_names = ["probe",
        #                         "scv",
        #                         "drone"]
        #         # if that unit is a PROBE, SCV, or DRONE... it's a worker
        #         pos = enemy_unit.position
        #         if enemy_unit.name.lower() in worker_names:
        #             cv2.circle(game_data, (int(pos[0]), int(pos[1])), 1, (55, 0, 155), -1)
        #         else:
        #             cv2.circle(game_data, (int(pos[0]), int(pos[1])), 3, (50, 0, 215), -1)

        # for obs in self.all_units(UnitTypeId.OBSERVER).ready:
        #     pos = obs.position
        #     cv2.circle(game_data, (int(pos[0]), int(pos[1])), 1, (255, 255, 255), -1)

        # for vr in self.all_units(UnitTypeId.VOIDRAY).ready:
        #     pos = vr.position
        #     cv2.circle(game_data, (int(pos[0]), int(pos[1])), 3, (255, 100, 0), -1)

        # line_max = 50
        # mineral_ratio = self.minerals / 1500
        # if mineral_ratio > 1.0:
        #     mineral_ratio = 1.0

        # vespene_ratio = self.vespene / 1500
        # if vespene_ratio > 1.0:
        #     vespene_ratio = 1.0

        # population_ratio = self.supply_left / self.supply_cap
        # if population_ratio > 1.0:
        #     population_ratio = 1.0

        # plausible_supply =  self.supply_cap / 200.0

        # worker_weight = len(self.all_units(UnitTypeId.PROBE)) / (self.supply_cap-self.supply_left)

        # if worker_weight > 1.0:
        #     worker_weight = 1.0

        # cv2.line(game_data, (0, 19), (int(line_max*worker_weight), 19), (250, 250, 200), 3)  # worker/supply ratio
        # cv2.line(game_data, (0, 15), (int(line_max*plausible_supply), 15), (220, 200, 200), 3)  # plausible supply (supply/200.0)
        # cv2.line(game_data, (0, 11), (int(line_max*population_ratio), 11), (150, 150, 150), 3)  # population ratio (supply_left/supply)
        # cv2.line(game_data, (0, 7), (int(line_max*vespene_ratio), 7), (210, 200, 0), 3)  # gas / 1500
        # cv2.line(game_data, (0, 3), (int(line_max*mineral_ratio), 3), (0, 255, 25), 3)  # minerals minerals/1500

        # flip horizontally to make our final fix in visual representation:
        self.flipped = cv2.flip(game_data, 0)
        resized = cv2.resize(self.flipped, dsize=None, fx=2, fy=2)

        if not HEADLESS:
            cv2.imshow(str(self.title), resized)
            cv2.waitKey(1)

    def find_target(self, state):
        if len(self.all_enemy_units) > 0:
            return random.choice(self.all_enemy_units)
        elif len(self.enemy_structures) > 0:
            return random.choice(self.enemy_structures)
        else:
            return self.enemy_start_locations[0]

    async def build_scout(self):
        for rf in self.structures(UnitTypeId.ROBOTICSFACILITY).ready:
            print(len(self.structures(UnitTypeId.OBSERVER)), self.time_m/3)
            if self.can_afford(UnitTypeId.OBSERVER) and self.supply_left > 0:
                await self.do(rf.train(UnitTypeId.OBSERVER))
                break

    async def build_worker(self):
        nexuses = self.structures(UnitTypeId.NEXUS).ready
        if nexuses.exists:
            if self.can_afford(UnitTypeId.PROBE):
                self.do(random.choice(nexuses).train(UnitTypeId.PROBE))

    async def build_zealot(self):
        gateways = self.structures(UnitTypeId.GATEWAY).ready
        if gateways.exists:
            if self.can_afford(UnitTypeId.ZEALOT):
                await self.do(random.choice(gateways).train(UnitTypeId.ZEALOT))

    async def build_gateway(self):
        pylon = self.structures(UnitTypeId.PYLON).ready
        if len(pylon) > 0 and self.can_afford(UnitTypeId.GATEWAY) and not self.already_pending(UnitTypeId.GATEWAY):
            await self.build(UnitTypeId.GATEWAY, near=pylon[0])

    async def build_voidray(self):
        stargates = self.structures(UnitTypeId.STARGATE).ready
        if stargates.exists:
            if self.can_afford(UnitTypeId.VOIDRAY):
                await self.do(random.choice(stargates).train(UnitTypeId.VOIDRAY))

    async def build_stalker(self):
        pylon = self.structures(UnitTypeId.PYLON).ready
        gateways = self.structures(UnitTypeId.GATEWAY).ready
        cybernetics_cores = self.structures(UnitTypeId.CYBERNETICSCORE).ready

        if gateways.exists and cybernetics_cores.exists:
            if self.can_afford(STALKER):
                await self.do(random.choice(gateways).train(UnitTypeId.STALKER))

        if not cybernetics_cores.exists:
            if self.structures(UnitTypeId.GATEWAY).ready.exists:
                if self.can_afford(UnitTypeId.CYBERNETICSCORE) and not self.already_pending(UnitTypeId.CYBERNETICSCORE):
                    await self.build(UnitTypeId.CYBERNETICSCORE, near=pylon[0])

    async def build_assimilator(self):
        for nexus in self.structures(UnitTypeId.NEXUS).ready:
            vaspenes = self.vespene_geyser.closer_than(15.0, nexus)
            for vaspene in vaspenes:
                if not self.can_afford(UnitTypeId.ASSIMILATOR):
                    break
                worker = self.select_build_worker(vaspene.position)
                if worker is None:
                    break
                if not self.structures(UnitTypeId.ASSIMILATOR).closer_than(1.0, vaspene).exists:
                    self.do(worker.build(UnitTypeId.ASSIMILATOR, vaspene))

    async def build_stargate(self):
        if self.structures(UnitTypeId.PYLON).ready.exists:
            pylon = self.structures(UnitTypeId.PYLON).ready[0]
            if self.structures(UnitTypeId.CYBERNETICSCORE).ready.exists:
                if self.can_afford(UnitTypeId.STARGATE) and not self.already_pending(UnitTypeId.STARGATE):
                    await self.build(UnitTypeId.STARGATE, near=pylon)

    async def build_pylon(self):
            nexuses = self.structures(UnitTypeId.NEXUS).ready
            if nexuses.exists:
                if self.can_afford(UnitTypeId.PYLON):
                    await self.build(UnitTypeId.PYLON, near=self.structures(UnitTypeId.NEXUS).first.position.towards(self.game_info.map_center, 5))

    async def expand(self):
        try:
            if self.can_afford(UnitTypeId.NEXUS):
                await self.expand_now()
        except Exception as e:
            print(str(e))

    async def do_nothing(self):
        wait = random.randrange(7, 100)/100
        self.do_something_after = self.time_m + wait

    async def defend_nexus(self):
        if len(self.all_enemy_units) > 0:
            target = self.all_enemy_units.closest_to(random.choice(self.structures(NEXUS)))
            for u in self.all_units(VOIDRAY).idle:
                await self.do(u.attack(target))
            for u in self.all_units(STALKER).idle:
                await self.do(u.attack(target))
            for u in self.all_units(ZEALOT).idle:
                await self.do(u.attack(target))

    async def attack_known_enemy_structure(self):
        if len(self.enemy_structures) > 0:
            target = random.choice(self.enemy_structures)
            for u in self.all_units(VOIDRAY).idle:
                await self.do(u.attack(target))
            for u in self.all_units(STALKER).idle:
                await self.do(u.attack(target))
            for u in self.all_units(ZEALOT).idle:
                await self.do(u.attack(target))

    async def attack_known_enemy_unit(self):
        if len(self.all_enemy_units) > 0:
            target = self.all_enemy_units.closest_to(random.choice(self.units(NEXUS)))
            for u in self.all_units(VOIDRAY).idle:
                await self.do(u.attack(target))
            for u in self.all_units(STALKER).idle:
                await self.do(u.attack(target))
            for u in self.all_units(ZEALOT).idle:
                await self.do(u.attack(target))

    async def do_something(self):

        if self.time_m > self.do_something_after:
            if self.use_model:
                prediction = self.model.predict([self.flipped.reshape([-1, 176, 200, 3])])
                choice = np.argmax(prediction[0])
            else:
                choice = random.randrange(0, 14)
            try:
                await self.choices[choice]()
            except Exception as e:
                traceback.print_exc()
                print(str(e))
            ###### NEW CHOICE HANDLING HERE #########
            ###### NEW CHOICE HANDLING HERE #########
            y = np.zeros(14)
            y[choice] = 1
            self.train_data.append([y, self.flipped])

    

if True:
    run_game(maps.get("EternalEmpireLE"), [
        Bot(Race.Protoss, SentdeBot(use_model=False, title=1)),
        #Bot(Race.Protoss, SentdeBot(use_model=False, title=2)),
        Computer(Race.Protoss, Difficulty.Medium),
        ], realtime=False)