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
