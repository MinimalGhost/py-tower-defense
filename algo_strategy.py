import gamelib
# import sys
# import math
# import util
# import time


"""
You are able to implement your own algo by subclassing the `AlgoCore` class and
overriding the methods `process_config(config_string)` and `step(game_map)`.
Most of the algo code you write will be in this file unless you create new
modules yourself.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()

    def process_config(self, config):
        """ Tweak strategy based on config and perform any initial algo setup """
        gamelib.debug_write('Configuring your custom algo strategy...')

        self.config = config

        # these attributes are specific to the funnel strategy, replace with your own
        self.funnel_point = None
        self.holeradius = 1
        self.holeradiusWide = 5
        self.supportStartPoint = None
        self.pathFound = False

    def step(self, game_map):
        """
        This step function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the board and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        gamelib.debug_write('Performing one turn of your custom algo strategy')

        self.funnel_strategy(game_map)  # replace with your own strategy

        game_map.send_messages()

    # NOTE: all the methods after this point are part of the sample funnel strategy
    def funnel_strategy(self, game_map):
        '''
        The main logic of this strategy, every turn it finds a hole location if
        it hasn't already, reinforces around the hole to create a funnel, and
        adds support towers leading up to the hole.
        '''
        path, success = game_map.find_path_to_edge([13, 0], 'top_right', 1)
        self.pathFound = success

        # specify tower placements
        if game_map.turnNumber == 0:
            self.towers_on_alternating_tiles(game_map)
        else:
            self.find_funnel_point(game_map)
            self.repair_wall(game_map)
            self.build_supports(game_map)

        # deploy units
        not_first_turn = game_map.turnNumber != 0

        easy_food = game_map.turnNumber > 10 or game_map.get_my_resource('food') == 10
        if not_first_turn and easy_food:
            if not self.pathFound:
                self.deploy_all_split_strategy("ST", game_map)
            self.deploy_all_split_strategy("SI", game_map)

    def find_funnel_point(self, game_map):
        '''
        Finds an open space that is not on the edges of the map, and uses that as a funnel point. Checks to see if that space
        has an available path that isn't blocked by that enemy. After the funnel is chosen it is set for the whole game
        which isn't optimal but this algo is simple.
        :param game_map: GameMap object
        :return: location of funnel point
        '''
        if self.funnel_point:
            return

        edgeGuard = 8  # So that left most and rightmost areas aren't chosen as funnel
        funnel_point = [game_map.boardSize - edgeGuard, 13]
        minPath = 99999999999
        for x in range(edgeGuard, game_map.boardSize - edgeGuard):
            if not game_map.is_blocked([x, 13]):
                start_point = [x, 13]
                path, success = game_map.find_path_to_edge(start_point, 'top_right', 1)
                if success and len(path) < minPath:
                    funnel_point = [x, 13]
                    minPath = len(path)
        self.funnel_point = funnel_point

    def towers_on_alternating_tiles(self, game_map):
        """ Puts a TB on every other square for 13th column """
        for x in range(0, game_map.boardSize):
            if x % 2 == 0:
                game_map.spawn_unit("TB", [x, 13])

    def blocks_funnel(self, x, radius=None):
        if radius is None:
            radius = self.holeradius
        funnel_x, _ = self.funnel_point
        return abs(x - funnel_x) <= radius

    def repair_wall(self, game_map):
        """ puts towers on the 13th row so that the hole is the only open location """
        locations = [[x, 13] for x in range(0, game_map.boardSize)]

        # Spawn TB away from the hole, and TE near the hole.
        funnel_compatible_locations_TB = [loc for loc in locations
                                          if not self.blocks_funnel(loc[0], self.holeradiusWide)]

        funnel_compatible_locations_TE = [loc for loc in locations
                                          if (self.blocks_funnel(loc[0], self.holeradiusWide)) and
                                          (not self.blocks_funnel(loc[0]))]

        game_map.attempt_spawn_multiple("TE", funnel_compatible_locations_TE)
        game_map.attempt_spawn_multiple("TB", funnel_compatible_locations_TB)

    def deploy_all_split_strategy(self, type, game_map):
        for i in range(game_map.number_affordable(type)):
            location = [5, 8] if i < 5 else [13, 0]
            game_map.spawn_unit(type, location)

    def build_supports(self, game_map):
        '''
        Builds support towers leading up to the hole. If the hole is completely blocked it also builds TB towers on a
        side of the hole so that it can funnel tanks to self destruct near the hole.
        Support towers are built in a diagonal line leading up the hole based on a few origin points in relation to
        the hole location.
        :param game_map:
        :return:
        '''
        if not self.supportStartPoint:
            for x in reversed(range(0, game_map.boardSize)):
                if not game_map.is_blocked([x, 13]) and self.blocks_funnel(x):
                    self.supportStartPoint = [x, 12]
                    break

        # If path is blocked completely, create TBs so that you can explode tanks in a good spot
        # Don't need anymore because new self destruct pathing!
        if not self.pathFound and False:
            self.funnel_to_self_destruct(self.supportStartPoint, game_map)

        bottom_left_edge = game_map.get_edge_locations('bottom_left')
        offset_points = [[loc[0], loc[1] + 1] for loc in bottom_left_edge]
        skip_build_points = bottom_left_edge + offset_points

        # get "origin points" for the TS tails, encoded here as horizontal offsets from self.supportStartPoint
        # build on origin points until out of metal or get to edge point and edge point +1y
        x0, y0 = self.supportStartPoint
        horizontal_offsets = [-3, 1, 2, -4]
        for origin_point in [(x0 + x_offset, y0) for x_offset in horizontal_offsets]:
            self.build_offset_supports(origin_point, skip_build_points, game_map)
