from bin import *

class UpgradesManager:
    def __init__(self, evManager):
        self.evManager = evManager

    def __getstate__(self):
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.evManager = Main.evManager

    def UpgradeLevel(self, player):  # initial LEVEL is 1
        player.restaurantLvl = self.NextLevel(player)

    def UpgradeLevelCost(self, player):
        cost = 1000000 * player.restaurantLvl**2
        return int(cost)

    def NextLevel(self, player):
        if player.restaurantLvl < 5:
            level = player.restaurantLvl + 1
        else:
            level = 5

        return level

    def OperatingCost(self, level):
        cost = 70000 * (level**2)
        return int(cost)
