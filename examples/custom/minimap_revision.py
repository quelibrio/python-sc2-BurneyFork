import numpy as np
import cv2
from sc2.constants import PYLON

class MinimapRevision():
    def __init__(self, game):
        self.game=game
        self.map_data=self.empty_map()
        self.heightmap(self.map_data)
        self.add_minerals(self.map_data)
        self.add_geysers(self.map_data)
        self.add_psi(self.map_data)
        self.add_destructables(self.map_data)
        self.add_allies(self.map_data)
        self.add_enemies(self.map_data)
        #self.add_visibility(self.map_data)
        

    def empty_map(self):
            self.map_scale=3
            map_scale = self.map_scale
            map_data = np.zeros(
                (
                    self.game.game_info.map_size[1] * map_scale,
                    self.game.game_info.map_size[0] * map_scale,
                    3,
                ),
                np.uint8,
            )
            print("Creating map {}x{}".format(self.game.game_info.map_size[1], self.game.game_info.map_size[0]))
            return map_data

    def add_minerals(self, map_data):
            for mineral in self.game.mineral_field:
                mine_pos = mineral.position
                cv2.rectangle(
                    map_data,
                    (
                        int((mine_pos[0] - 0.75) * self.map_scale),
                        int((mine_pos[1] - 0.25) * self.map_scale),
                    ),
                    (
                        int((mine_pos[0] + 0.75) * self.map_scale),
                        int((mine_pos[1] + 0.25) * self.map_scale),
                    ),
                    (220, 180, 140),
                    -1,
                )

    def add_geysers(self, map_data):
        for g in self.game.vespene_geyser:
            g_pos = g.position
            cv2.rectangle(
                map_data,
                (
                    int((g_pos[0] - g.radius / 2) * self.map_scale),
                    int((g_pos[1] - g.radius / 2) * self.map_scale),
                ),
                (
                    int((g_pos[0] + g.radius / 2) * self.map_scale),
                    int((g_pos[1] + g.radius / 2) * self.map_scale),
                ),
                (130, 220, 170),
                -1,
            )
    
    def add_psi(self, map_data):
        for unit in self.game.watchtowers:
            cv2.circle(map_data, 
                (
                    int(unit.position[0]*self.map_scale),
                    int(unit.position[1]*self.map_scale)
                ),
                int(unit.radius*self.map_scale), 
                (0, 250, 250), 
                -1
            )

    def add_destructables(self, map_data):
        # TODO: make a dictionary that contains all footprints of all destructables to draw them the right way
        for unit in self.game.destructables:
            cv2.circle(
                map_data,
                (
                    int(unit.position[0] * self.map_scale),
                    int(unit.position[1] * self.map_scale),
                ),
                int(unit.radius * self.map_scale),
                (80, 100, 120),
                -1,
            )


    def add_allies(self, map_data):
        for unit in self.game.structures:
            if unit.is_structure:
                cv2.rectangle(
                    map_data,
                    (
                        int((unit.position[0] - unit.radius / 2) * self.map_scale),
                        int((unit.position[1] - unit.radius / 2) * self.map_scale),
                    ),
                    (
                        int((unit.position[0] + unit.radius / 2) * self.map_scale),
                        int((unit.position[1] + unit.radius / 2) * self.map_scale),
                    ),
                    (0, 255, 0),
                    -1,
                )
        for unit in self.game.units:
            cv2.circle(
                map_data,
                (
                    int(unit.position[0] * self.map_scale),
                    int(unit.position[1] * self.map_scale),
                ),
                int(unit.radius * self.map_scale),
                (0, 255, 0),
                -1,
            )

    def add_enemies(self, map_data):
        for unit in self.game.enemy_structures:
            if unit.is_structure:
                cv2.rectangle(
                    map_data,
                    (
                        int((unit.position[0] - unit.radius / 2) * self.map_scale),
                        int((unit.position[1] - unit.radius / 2) * self.map_scale),
                    ),
                    (
                        int((unit.position[0] + unit.radius / 2) * self.map_scale),
                        int((unit.position[1] + unit.radius / 2) * self.map_scale),
                    ),
                    (0, 0, 255),
                    -1,
                )
        for unit in self.game.enemy_units:
            cv2.circle(
                map_data,
                (
                    int(unit.position[0] * self.map_scale),
                    int(unit.position[1] * self.map_scale),
                ),
                int(unit.radius * self.map_scale),
                (0, 0, 255),
                -1,
            )
                
    def heightmap(self, map_data):
        # gets the min and max heigh of the map for a better contrast
        #Original was terrain_eight
        h_min = np.amin(self.game._game_info.pathing_grid.data_numpy)
        h_max = np.amax(self.game._game_info.pathing_grid.data_numpy)
        multiplier = 150 / (h_max - h_min)


        for (y, x), h in np.ndenumerate(self.game._game_info.pathing_grid.data_numpy):
            color = (h - h_min) * multiplier
            cv2.rectangle(
                map_data,
                (x * self.map_scale, y * self.map_scale),
                (
                    x * self.map_scale + self.map_scale,
                    y * self.map_scale + self.map_scale,
                ),
                (color, color, color),
                -1,
            )
        for r in self.game.game_info.map_ramps:
            for p in r.points:
                cv2.circle(
                    map_data,
                    (int(p[0] * self.map_scale), int(p[1] * self.map_scale)),
                    2,
                    (120, 100, 100),
                    -1,
                )
            for p in r.upper:
                cv2.circle(
                    map_data,
                    (int(p[0] * self.map_scale), int(p[1] * self.map_scale)),
                    1,
                    (160, 140, 140),
                    -1,
                )
            for p in r.lower:
                cv2.circle(
                    map_data,
                    (int(p[0] * self.map_scale), int(p[1] * self.map_scale)),
                    1,
                    (100, 80, 80),
                    -1,
                )
        return map_data
    
    def add_visibility(self, map_data):
        visibility = map_data.copy()
        # gets the min and max heigh of the map for a better contrast
        v_min = np.amin(self.game.state.visibility.data_numpy)
        v_max = np.amax(self.game.state.visibility.data_numpy)
        multiplier = (255 / (v_max - v_min))/3

        for (y, x), v in np.ndenumerate(self.game.state.visibility.data_numpy):
            color = (v - v_min) * multiplier
            #print(color)
            if v != v_min and v != v_max:
                #print(v_max)
                pass
            cv2.rectangle(
                visibility,
                (x * self.map_scale, y * self.map_scale),
                (
                    x * self.map_scale + self.map_scale,
                    y * self.map_scale + self.map_scale,
                ),
                (color, color, color),
                -1,
            )
        alpha = 0.5  # Transparency factor.
        self.map_data = cv2.addWeighted(map_data, alpha, visibility, 1 - alpha, 0)