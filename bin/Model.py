from bin import *
from .Events import *
import json
import configparser
import copy
import weakref


class Game:
    def __init__(self, folder, evManager):
        self.state = STATE_PAUSED

        self.evManager = evManager
        self.folder = folder

        self.date = DateManager(self.evManager)

        # Human player exclusive modules
        self.cart = Cart(self.evManager)

        self.trendManager = TrendManager(self.evManager)
        self.customerManager = CustomerManager(self.evManager)
        self.dishManager = DishManager(self.evManager)

        self.players = [Player(self, self.evManager),
                        AI("Deen's Cafe", 2, CUISINE_WESTERN, self, self.evManager),
                        AI("Emperor's Spice", 3, CUISINE_CHINESE, self, self.evManager),
                        AI("Bap Bap", 4, CUISINE_KOREAN, self, self.evManager)]

        for player in self.players:
            if not hasattr(player, "ai"):
                player.finance = Finance(self.evManager)
                player.finance.FirstDay(player.cash)
                player.marketing = Marketing(self.evManager)

        self.evManager.RegisterListener(self)

        ev = GameStartedEvent()
        self.evManager.Post(ev)

    def __getstate__(self):
        self.state = STATE_PAUSED
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.evManager = Main.evManager
        self.evManager.RegisterListener(self)

    def UpdateAI(self):
        rivals = []
        for player in self.players:
            if hasattr(player, "ai"):
                rivals.append(player.GetInfo())

        ev = RivalsUpdateEvent(rivals)
        self.evManager.Post(ev)

    def Notify(self, event):
        if isinstance(event, NewDayEvent):
            self.customerManager.CalculateCustomerSplit(self.players)
            self.UpdateAI()

            ev = FinishDayEvent()
            self.evManager.Post(ev)

        elif isinstance(event, GameScreenLoadedEvent):
            self.UpdateAI()


class Player:
    def __init__(self, game, evManager):
        self.evManager = evManager
        self.evManager.RegisterListener(self)
        self.folder = game.folder

        self.finance = None
        self.marketing = None
        self.upgrades = UpgradesManager(self.evManager)
        self.customerManager = game.customerManager
        self.dishManager = game.dishManager

        self.inventory = Inventory(True, self.evManager)
        self.menu = Menu(self.evManager)
        self.chefs = [Chef(0, CUISINE_WESTERN, self.evManager)]
        self.waiters = [Waiter(0, self.evManager), Waiter(0, self.evManager)]

        self.impression = 0 # Value assigned at start of day
        self.baseImpression = 60 # Affected by satisfaction
        self.impressionRetention = 60

        self.cash = 50000
        #self.cash = 99999999999
        self.restaurantLvl = 1
        self.restaurantCapacity = 100
        self.menu.dishLimit = 4 * self.restaurantLvl

        self.salesReport = ([], 0, 0, 0) # For load game purpose

        self.gameOver = False

    def __getstate__(self):
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.evManager = Main.evManager
        self.evManager.RegisterListener(self)

    def SpendMoney(self, value, category, force=None):
        if value > self.cash and not force:
            ev = NotEnoughCashEvent()
            self.evManager.Post(ev)
            return False
        else:
            self.cash -= value
            self.finance.CashFlow(value, category, self.cash)

            ev = CashUpdateEvent(self.cash)
            self.evManager.Post(ev)

            return True

    def EarnMoney(self, value, category):
        self.cash += value
        self.finance.CashFlow(value, category, self.cash)

        ev = CashUpdateEvent(self.cash)
        self.evManager.Post(ev)

    def GetChefs(self):
        # Returns highest level of each cuisine chef in dictionary
        chefs = []
        for chef in self.chefs:
            if chef.cuisine not in (c['cuisine'] for c in chefs):
                chefDict = dict(cuisine=chef.cuisine, level=chef.level)
                chefs.append(chefDict)
            else:
                for c in chefs:
                    if chef.cuisine == c['cuisine'] and chef.level > c['level']:
                        c['level'] = chef.level
        return chefs

    def WaitersLevel(self):
        total = 0
        for waiter in self.waiters:
            total += waiter.level

        try:
            avgLevel = total / len(self.waiters)
        except ZeroDivisionError:
            avgLevel = 0

        return avgLevel

    def CalculateImpression(self):
        cuisineDiversityModifer = -0.1 + (self.menu.NumberOfCuisines() / 10)
        restaurantModifier = 0.05 * (self.restaurantLvl - 1)
        marketingModifier = 0
        try:
            marketingModifier = self.marketing.MarketingModifier()
        except AttributeError:
            pass

        if self.baseImpression > 0:
            grossImpression = self.baseImpression + self.menu.ImpressionPoints()
        else:
            grossImpression = self.menu.ImpressionPoints()

        impression = math.floor(grossImpression * (1 + restaurantModifier + marketingModifier + cuisineDiversityModifer))

        # Impression retention bonus
        if impression > self.impressionRetention:
            self.impressionRetention = impression
        else:
            difference = self.impressionRetention - impression
            retention = math.floor(difference * 0.75)
            impression += retention
            self.impressionRetention -= retention * 0.5
        return impression

    def CalculateSatisfaction(self, dishesServed, customers, unfedCustomers, rivals):
        # Calculate satisfaction based on base cost to sale price value
        costModifier = math.floor(self.restaurantLvl ** 1.7)
        totalSatisfaction = 0

        # Calculate gross satisfaction
        for dish in dishesServed:
            qualityModifier = (dish['quality']/2) * (1 + ((dish['quality'] - 2) / 20))  # Scale from 10 to 2, 2 to 1
            cost = dish['dish'].baseCost * qualityModifier
            adjustedCost = cost * costModifier

            if dish['price'] == 0:
                qualitySatisfaction = 100
            else:
                qualitySatisfaction = math.floor( ((adjustedCost / dish['price']) * 100) * (1 + (dish['quality'] - 2) / 10))
                if qualitySatisfaction > 100:
                    qualitySatisfaction = 100

            dish['satisfaction'] = qualitySatisfaction # To calculate dish competition for next day

            totalSatisfaction += dish['satisfaction'] * dish['sales']

            # Missing demand fulfilled penalty
            if dish['demand'] > dish['sales']:
                missingDemand = dish['demand'] - dish['sales']
                totalSatisfaction -= missingDemand * 40

        totalSatisfaction -= unfedCustomers * 200

        # Customer service modifiers
        insufficientStaff = customers - (len(self.waiters) * CUSTOMERS_PER_WAITER)
        insufficientStaff += customers - (len(self.chefs) * CUSTOMERS_PER_CHEF)
        if insufficientStaff > 0:
            totalSatisfaction -= insufficientStaff ** 2

        waitersLvl = self.WaitersLevel()
        totalSatisfaction *= 1 - 0.05 * (3 - waitersLvl)

        return math.floor(totalSatisfaction)

    def ProcessSales(self, customers, rivals):
        dishesServed = self.dishManager.ProcessDishes(self, customers)

        unfedCustomers = self.dishManager.UnfedCustomers(customers, dishesServed)
        salesRevenue = self.dishManager.SalesRevenue(dishesServed)

        satisfaction = self.CalculateSatisfaction(dishesServed, customers, unfedCustomers, rivals)
        if satisfaction < 0:
            satisfaction = 0

        if customers > 0:
            avgSatisfaction = math.floor(satisfaction / customers)
        else:
            satisfaction = 0
            avgSatisfaction = 0

        self.baseImpression = (avgSatisfaction * 10) * (1 + customers/100)

        self.EarnMoney(salesRevenue, FIN_SALES)

        if not hasattr(self, "ai"):
            self.salesReport = (dishesServed, customers, unfedCustomers, avgSatisfaction)
            ev = SalesReportEvent(*self.salesReport)
            self.evManager.Post(ev)

        self.ProcessDay(customers) # For AI usage

    def ProcessDay(self, customers):
        pass

    def HireChef(self, level, cuisine):
        if self.SpendMoney(CHEF_SALARY[level] * 2, FIN_SALARY):
            self.chefs.append(Chef(level, cuisine, self.evManager))

    def HireWaiter(self, level):
        if self.SpendMoney(WAITER_SALARY[level] * 2, FIN_SALARY):
            self.waiters.append(Waiter(level, self.evManager))

    def FireStaff(self, staff):
        if self.SpendMoney(staff.salary * 3, FIN_SALARY):
            try:
                self.chefs.remove(staff)
            except ValueError:
                pass
            try:
                self.waiters.remove(staff)
            except ValueError:
                pass

    def Notify(self, event):
        if isinstance(event, GameScreenLoadedEvent):
            ev = RestaurantUpdateEvent(self, self.restaurantLvl, self.upgrades.OperatingCost(self.restaurantLvl),
                                       self.upgrades)
            self.evManager.Post(ev)

            ev = MarketingUpdateEvent(self.marketing.activeBonuses)
            self.evManager.Post(ev)

            ev = InventoryUpdateEvent(self.inventory.Stock())
            self.evManager.Post(ev)

            ev = MenuUpdateEvent(self.menu.dishes)
            self.evManager.Post(ev)

            ev = CashUpdateEvent(self.cash)
            self.evManager.Post(ev)

            ev = StaffUpdateEvent(self.chefs, self.waiters)
            self.evManager.Post(ev)

            ev = SalesReportEvent(*self.salesReport)
            self.evManager.Post(ev)


        elif isinstance(event, NewDayEvent):
            self.finance.NewDay(self.cash)
            for staff in self.chefs + self.waiters:
                staff.CountDay(self.SpendMoney)

            ev = InventoryUpdateEvent(self.inventory.Stock())
            self.evManager.Post(ev)

            if self.gameOver:
                ev = GameOverEvent()
                self.evManager.Post(ev)
            elif self.cash < -10000:
                self.gameOver = True

        elif isinstance(event, NewMonthEvent):
            self.finance.NewDay(self.cash)
            self.finance.NewMonth(self.cash)

            self.SpendMoney(self.upgrades.OperatingCost(self.restaurantLvl), FIN_MISC, True)

        elif isinstance(event, NewYearEvent):
            self.finance.NewYear(self.cash)

        elif isinstance(event, AddDishEvent):
            if len(self.menu.dishes) < self.menu.dishLimit:
                if self.SpendMoney(ADD_DISH_COST, FIN_MISC):
                    self.menu.AddDish(event.dish, event.price)

                    ev = MenuUpdateEvent(self.menu.dishes)
                    self.evManager.Post(ev)

        elif isinstance(event, UpdateDishPriceEvent):
            self.menu.UpdateDishPrice(event.dish, event.price)

            ev = MenuUpdateEvent(self.menu.dishes)
            self.evManager.Post(ev)

        elif isinstance(event, RemoveDishEvent):
            self.menu.RemoveDish(event.dish)

            ev = MenuUpdateEvent(self.menu.dishes)
            self.evManager.Post(ev)

        elif isinstance(event, BuyIngredientsEvent):
            if self.SpendMoney(event.price, FIN_INVENTORY):
                new = True
                for batch in self.inventory.batches:
                    # Loop and check for same-day batch
                    if batch.age == 0:
                        batch.AddIngredients(event.cart)
                        new = False

                if new:
                    newBatch = Batch(self.evManager)
                    newBatch.AddIngredients(event.cart)
                    self.inventory.batches.append(newBatch)

                ev = InventoryUpdateEvent(self.inventory.Stock())
                self.evManager.Post(ev)

                ev = ClearCartEvent()
                self.evManager.Post(ev)

        elif isinstance(event, RequestIngredientAmountEvent):
            amount = self.inventory.IngredientStock(event.ingredient)
            expired = self.inventory.IngredientExpiredAmount(event.ingredient)

            ev = ReturnIngredientAmountEvent(event.ingredient, amount, expired)
            self.evManager.Post(ev)

        elif isinstance(event, HireChefEvent):
            self.HireChef(event.level, event.cuisine)

            ev = StaffUpdateEvent(self.chefs, self.waiters)
            self.evManager.Post(ev)

        elif isinstance(event, HireWaiterEvent):
            self.HireWaiter(event.level)

            ev = StaffUpdateEvent(self.chefs, self.waiters)
            self.evManager.Post(ev)

        elif isinstance(event, FireStaffEvent):
            self.FireStaff(event.staff)

            ev = StaffUpdateEvent(self.chefs, self.waiters)
            self.evManager.Post(ev)

        elif isinstance(event, GUICheckDishMenuEvent):
            d = None
            for dish in self.menu.dishes:
                if event.dish == dish['dish']:
                    d = dish

            ev = GUICheckDishMenuResponseEvent(d, event.container)
            self.evManager.Post(ev)

        elif isinstance(event, StaffUpdateRequestEvent):
            ev = StaffUpdateEvent(self.chefs, self.waiters)
            self.evManager.Post(ev)

        elif isinstance(event, UpgradeLevelEvent):
            if self.SpendMoney(self.upgrades.UpgradeLevelCost(self), FIN_RENOVATION):
                self.upgrades.UpgradeLevel(self)
                self.menu.dishLimit = 4 * self.restaurantLvl

                ev = RestaurantUpdateEvent(self, self.restaurantLvl, self.upgrades.OperatingCost(self.restaurantLvl),
                                           self.upgrades)
                self.evManager.Post(ev)

        elif isinstance(event, AddMarketingEvent):
            if self.SpendMoney(event.bonus.cost, FIN_MARKETING):
                self.marketing.AddBonus(event.bonus)


class AI(Player):
    def __init__(self, name, level, cuisine, game, evManager):
        super().__init__(game, evManager)
        self.ai = ""
        self.name = name
        self.level = level
        self.cuisine = cuisine

        self.inventory = Inventory(False, self.evManager)

        self.chefs = [Chef(self.level - 1, self.cuisine, self.evManager), Chef(self.level - 1, self.cuisine, self.evManager)]
        self.waiters = []
        for i in range(4):
            self.waiters.append(Waiter(self.level - 1, self.evManager))

        self.baseImpression = 80
        self.impressionRetention = 80

        self.cash = 100000000
        self.restaurantLvl = 2
        self.restaurantCapacity = 200
        self.menu.dishLimit = 4 * self.restaurantLvl

        self.customers = 0 # For RivalsTab

        self.ProcessDay(1000) # Buy ingredients for 100 customers

    def SpendMoney(self, value, category=None, force=None):
        self.cash -= value

    def EarnMoney(self, value, category=None, force=None):
        self.cash += value

    def GetInfo(self):
        return self.name, self.customers, self.menu.dishes

    def GetLeastPopularDish(self):
        dish = None
        for d in self.menu.dishes:
            if dish:
                if d['dish'].ImpressionPoints() < dish.ImpressionPoints():
                    dish = d['dish']
            else:
                dish = d['dish']

        return dish

    def EvaluateMenu(self):
        dish = self.GetLeastPopularDish()
        if dish:
            dishImpression = dish.ImpressionPoints()
            averageImpression = self.menu.ImpressionPoints() / len(self.menu.dishes)

            if dishImpression < averageImpression * 0.75:
                self.menu.RemoveDish(dish)

    def UpdateMenu(self):
        while len(self.menu.dishes) < self.menu.dishLimit:
            dish = None
            for d in DISHES_LIST:
                if d.cuisine == self.cuisine:
                    if d not in (x['dish'] for x in self.menu.dishes):
                        if dish:
                            if d.ImpressionPoints() > dish.ImpressionPoints():
                                dish = d
                        else:
                            dish = d
            quality = 5
            price = math.floor(dish.baseCost * quality * (1 + ((quality - 1) / 10))) * 2
            self.menu.AddDish(dish, price)

    def EvaluateInventory(self, customers):
        dishList = self.dishManager.DishesByDemand(self, customers, estimate=True)
        ingredientsList = []

        # Estimate amount of ingredients required
        for dish in dishList:
            amount = dish['demand']
            for ingredient in dish['dish'].ingredients:
                new = True

                for i in ingredientsList:
                    if i.name == ingredient.name:
                        i.amount += amount
                        new = False

                if new:
                    ing = copy.deepcopy(ingredient)
                    ing.quality = self.level
                    ing.amount = amount
                    ingredientsList.append(ing)

        # Calculate ingredients needed to purchase
        for ingredient in ingredientsList:
            stock = sum(self.inventory.IngredientStock(ingredient))
            expiredStock = sum(self.inventory.IngredientExpiredAmount(ingredient))
            ingredient.amount -= stock
            ingredient.amount += expiredStock
            if ingredient.amount < 0:
                ingredient.amount = 0

        return ingredientsList

    def PurchaseIngredients(self, ingredientsList):
        newBatch = Batch(self.evManager)
        newBatch.AddIngredients(ingredientsList)
        self.inventory.batches.append(newBatch)

        price = 0
        for ingredient in ingredientsList:
            price += ingredient.Price(ingredient.quality) * ingredient.amount

        self.SpendMoney(price)

    def ProcessDay(self, customers):
        if not Date.dayNumber == 0:
            self.customers = customers
        
        self.EvaluateMenu()
        self.UpdateMenu()

        ingredientsList = self.EvaluateInventory(customers)
        self.PurchaseIngredients(ingredientsList)

        if customers > len(self.chefs) * CUSTOMERS_PER_CHEF:
            self.HireChef(self.level - 1, self.cuisine)

        if customers > len(self.waiters) * CUSTOMERS_PER_WAITER:
            self.HireWaiter(self.level - 1)

    def Notify(self, event):
        pass


class Staff:
    def __init__(self, evManager):
        self.evManager = evManager

        self.salary = 0
        self.deltaDay = 0

    def __getstate__(self):
        self.sprite = None
        state = self.__dict__.copy()
        return state

    def CountDay(self, spendMoney):
            self.deltaDay += 1
            if self.deltaDay == 7:
                self.deltaDay = 0
                spendMoney(self.salary, FIN_SALARY, True)

class Chef(Staff):
    def __init__(self, level, cuisine, evManager):
        super().__init__(evManager)
        self.level = level
        self.cuisine = cuisine
        self.salary = CHEF_SALARY[self.level]

        self.sprite = CHEF_SPRITES[self.cuisine]

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.evManager = Main.evManager
        self.sprite = CHEF_SPRITES[self.cuisine]


class Waiter(Staff):
    def __init__(self, level, evManager):
        super().__init__(evManager)
        self.level = level
        self.salary = WAITER_SALARY[self.level]

        self.spriteName, self.sprite = random.choice(list(WAITER_SPRITES.items()))

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.evManager = Main.evManager
        self.sprite = WAITER_SPRITES[self.spriteName]


class Menu:
    def __init__(self, evManager):
        self.evManager = evManager

        # Dishes stored as dictionary of 'dish' and 'price'
        self.dishes = []
        self.dishLimit = 0

    def __getstate__(self):
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.evManager = Main.evManager

    def AddDish(self, dish, price):
        if len(self.dishes) < self.dishLimit:
            dishDict = dict(dish=dish, price=price, satisfaction=0)
            if dish not in (d['dish'] for d in self.dishes):
                self.dishes.append(dishDict)

    def UpdateDishPrice(self, dish, price):
        for d in self.dishes:
            if d['dish'].name == dish.name:
                d['price'] = price

    def RemoveDish(self, dish):
        for d in self.dishes:
            if d['dish'].name == dish.name:
                self.dishes.remove(d)

    def NumberOfCuisines(self):
        cuisines = []
        for dish in self.dishes:
            if dish['dish'].cuisine not in cuisines:
                cuisines.append(dish['dish'].cuisine)

        return len(cuisines)

    def ImpressionPoints(self):
        points = 0
        cuisines = []
        for dish in self.dishes:
            points += dish['dish'].ImpressionPoints()

        return points


class Dish:
    def __init__(self, name, type, cuisine, ingredients):
        self.name = name
        self.type = type
        self.cuisine = cuisine
        self.ingredients = ingredients

        self.numberIngredients = len(ingredients)

        self.baseCost = 0
        for ingredient in self.ingredients:
            self.baseCost += ingredient.baseCost

        self.trendModifier = 1.0

    def ImpressionPoints(self):
        points = DISH_BASE_IMPRESSION * self.trendModifier
        return points


class Ingredient:
    def __init__(self, name, ingreType, baseCost):
        self.name = name
        self.type = ingreType
        self.baseCost = baseCost * 10

        self.quality = None
        self.amount = 0

    def Price(self, quality):
        price = self.baseCost * quality * (1 + ((quality - 1) / 10))
        price = round(price * 100)
        return round(price / 100)



class Inventory:
    def __init__ (self, doPost, evManager):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        self.doPost = doPost

        self.batches = []
        self.expiredList = []

    def __getstate__(self):
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.evManager = Main.evManager
        self.evManager.RegisterListener(self)

    def Stock(self):
        stock = []
        for batch in self.batches:
            for ingredient in batch.ingredients:
                new = True
                for i in stock:
                    if ingredient.name == i.name:
                        i.amount += ingredient.amount
                        new = False

                if new:
                    ing = copy.deepcopy(ingredient)
                    ing.quality = 0 # No need quality
                    ing.amount = ingredient.amount
                    stock.append(ing)

        return stock

    def IngredientStock(self, ingredient):
        stock = [0, 0, 0, 0, 0] # Initialise based on quality 5 to 1
        for batch in self.batches:
            addStock = batch.IngredientStock(ingredient)
            stock = [sum(x) for x in zip(stock, addStock)] # Sums value of corresponding elements

        return stock

    def UseIngredients(self, dish, amount):
        # amount must be non-zero
        # Deduct ingredient stock based on precalculated amount of dishes (amount reflects how much able to make)
        for ingredient in dish.ingredients:
            useAmount = amount
            quality = 5
            countIngredient = True
            while countIngredient:
                for batch in self.batches:
                    for i in batch.ingredients:
                        if i.name == ingredient.name and i.quality == quality:
                            i.amount -= useAmount
                            if i.amount < 0:
                                useAmount = - i.amount
                                i.amount = 0
                                break
                            else:
                                useAmount = 0
                                countIngredient = False
                quality -= 1

        for batch in self.batches:
            ingredientsToRemove = []
            for ingredient in batch.ingredients:
                if ingredient.amount == 0:
                    ingredientsToRemove.append(ingredient)

            for ingredient in ingredientsToRemove:
                batch.ingredients.remove(ingredient)

                if self.doPost:
                    ev = ReturnIngredientAmountEvent(ingredient, self.IngredientStock(ingredient), self.IngredientExpiredAmount(ingredient))
                    self.evManager.Post(ev)

        if self.doPost:
            ev = InventoryUpdateEvent(self.Stock())
            self.evManager.Post(ev)

    def IngredientExpiredAmount(self, ingredient):
        stock = [0, 0, 0, 0, 0] # Initialise based on quality 5 to 1
        for i in self.expiredList:
            if i.name == ingredient.name:
                stock[5 - i.quality] = i.amount

        return stock

    def AddToExpiredList(self, batch):
        self.expiredList = []
        for ingredient in batch.ingredients:
            new = True
            for i in self.expiredList:
                if ingredient.name == i.name and ingredient.quality == i.quality:
                    i.amount += ingredient.amount
                    new = False

            if new:
                if ingredient.amount > 0:
                    self.expiredList.append(ingredient)

    def RemoveBatch(self, batch):
        for b in self.batches:
            if b is batch:
                self.batches.remove(b)

    def Notify(self, event):
        if isinstance(event, FinishDayEvent):
            batchesToRemove = []
            for batch in self.batches:
                batch.age += 1
                if batch.age > 7:
                    batchesToRemove.append(batch)

            for batch in batchesToRemove:
                self.batches.remove(batch)

            if self.doPost:
                ev = InventoryUpdateEvent(self.Stock())
                self.evManager.Post(ev)


class Batch:
    def __init__(self, evManager):
        self.evManager = evManager

        self.ingredients = []
        self.age = 0

    def __getstate__(self):
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.evManager = Main.evManager

    def IngredientStock(self, ingredient):
        stock = [0, 0, 0, 0, 0] # Initialise based on quality 1 to 5
        for i in self.ingredients:
            if i.name == ingredient.name:
                quality = i.quality
                amount = i.amount
                stock[quality - 1] = amount

        stock.reverse()
        return stock

    def AddIngredients(self, list):
        for ingredient in list:
            new = True
            for i in self.ingredients:
                if i.name == ingredient.name and i.quality == ingredient.quality:
                    i.amount += ingredient.amount
                    new = False

            if new:
                self.ingredients.append(ingredient)

    def RemoveIngredients(self, ingredient, quality, amount):
        for ing in self.ingredients:
            if ing.name == ingredient.name \
                    and ing.quality == quality:
                ing.amount -= amount

                if ing.amount == 0:
                    for i in self.ingredients:
                        if i is ing:
                            self.ingredients.remove(ing)


class Cart:
    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        self.cart = []
        self.totalPrice = 0

    def __getstate__(self):
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.evManager = Main.evManager
        self.evManager.RegisterListener(self)


    def AddToCart(self, ingredient, quality, amount):
        new = True
        for i in self.cart:
            if i.name == ingredient.name and i.quality == quality:
                i.amount += amount
                new = False

        if new:
            newIng = copy.deepcopy(ingredient)
            newIng.quality = quality
            newIng.amount = amount
            self.cart.append(newIng)

        self.totalPrice += ingredient.Price(quality) * amount

        # Tell View to update cart list
        ev = CartUpdateEvent(self.cart, self.totalPrice)
        self.evManager.Post(ev)

    def RemoveFromCart(self, ingredient):
        for i in self.cart:
            if i.name == ingredient.name and i.quality == ingredient.quality:
                self.cart.remove(i)

        self.totalPrice -= ingredient.Price(ingredient.quality) * ingredient.amount

        ev = CartUpdateEvent(self.cart, self.totalPrice)
        self.evManager.Post(ev)

    def Notify(self, event):
        if isinstance(event, AddToCartEvent):
            self.AddToCart(event.ingredient, event.quality, event.amount)

        elif isinstance(event, RemoveFromCartEvent):
            self.RemoveFromCart(event.ingredient)

        elif isinstance(event, ClearCartEvent):
            self.cart = []
            self.totalPrice = 0

            ev = CartUpdateEvent(self.cart, self.totalPrice)
            self.evManager.Post(ev)

