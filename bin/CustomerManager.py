from bin import *
import math
import random


class CustomerManager:
    def __init__(self, evManager):
        self.evManager = evManager

        self.totalCustomers = None
        self.prevCustomers = STARTING_CUSTOMERS

    def __getstate__(self):
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.evManager = Main.evManager

    def TotalCustomers(self):
        # TODO: Implement BETTER system to generate number of customers incorporating random events
        customers = None
        r = random.randint(0, 4) # 20% chance
        if not r:
            customers = self.prevCustomers * 1.001 # Simple growth equation
            self.prevCustomers = customers
        else:
            customers = self.prevCustomers

        self.totalCustomers = math.floor(customers)

    def CalculateCustomerSplit(self, players):
        self.TotalCustomers()

        totalImpression = 0
        for player in players:
            player.impression = player.CalculateImpression()
            if player.impression > 0:
                totalImpression += player.impression
            else:
                player.impression = 0

        for player in players:
            customers = math.floor(self.totalCustomers * (player.impression / totalImpression))
            rivals = players[:]
            rivals.remove(player)

            player.ProcessSales(customers, rivals)