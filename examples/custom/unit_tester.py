import sc2
from sc2 import run_game, maps, Race, Difficulty, Result
from sc2.player import Bot, Computer
from sc2 import position
from sc2.constants import NEXUS, PROBE, PYLON, ASSIMILATOR, GATEWAY, \
 CYBERNETICSCORE, STARGATE, VOIDRAY, SCV, DRONE, ROBOTICSFACILITY, OBSERVER, \
 ZEALOT, STALKER
import random
import cv2
import numpy as np
import os
import time
import math
#import keras
import traceback
from sc2.minimap_revision import MinimapRevision

#os.environ["SC2PATH"] = '/starcraftstuff/StarCraftII/'
HEADLESS = False


class SentdeBot(sc2.BotAI):
    def __init__(self, use_model=False, title=1):
        self.do_something_after = 0


    def on_end(self, game_result):
        print('--- on_end called ---')

    async def on_step(self, iteration):
        await self.scout()

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

        for unit in self.all_units(PROBE):
            pass
            #nexuses = self.structures(NEXUS).ready
            #if self.can_afford(PYLON):
            #await self.build(PYLON, near=unit.position.towards(self.game_info.map_center, 5))


    async def intel(self):
        minimap=MinimapRevision(self)
        game_data = minimap.map_data
        self.flipped = cv2.flip(game_data, 0)
        resized = cv2.resize(self.flipped, dsize=None, fx=2, fy=2)

        if not HEADLESS:
            cv2.imshow(str(self.title), resized)
            cv2.waitKey(1)


    async def build_worker(self):
        nexuses = self.structures(NEXUS).ready
        if nexuses.exists:
            if self.can_afford(PROBE):
                self.do(random.choice(nexuses).train(PROBE))

    async def build_zealot(self):
        gateways = self.structures(GATEWAY).ready
        if gateways.exists:
            if self.can_afford(ZEALOT):
                await self.do(random.choice(gateways).train(ZEALOT))

        # if gateways.exists and cybernetics_cores.exists:
        #     if self.can_afford(STALKER):
        #         await self.do(random.choice(gateways).train(STALKER))


    async def expand(self):
        try:
            if self.can_afford(NEXUS):
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
    run_game(maps.get("UnitTesterEdited"), [
        Bot(Race.Protoss, SentdeBot(use_model=False, title=1)),
        #Bot(Race.Protoss, SentdeBot(use_model=False, title=2)),
        Bot(Race.Protoss, SentdeBot(use_model=False, title=2)),
        #Computer(Race.Protoss, Difficulty.Medium),
        ], realtime=False)