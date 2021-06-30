from bin import *
import glob
import ntpath
import pickle
import os


class MainModule:
    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        if not os.path.exists("users"):
            os.makedirs("users")

        self.folder = ""
        self.game = None

    def LoadAssets(self):
        # Load list of ingredients
        config = configparser.ConfigParser()
        config.read("data/ingredients.rs")
        for section in config.sections():
            name = str(config.get(section, "name"))
            type = str(config.get(section, "type"))
            baseCost = config.getfloat(section, "cost")
            INGREDIENTS_LIST.append(Ingredient(name, type, baseCost))

        # Load list of dishes
        config = configparser.ConfigParser()  # Reinitiate for new file
        config.read("data/dishes.rs")
        for section in config.sections():
            name = str(config.get(section, "name"))
            type = str(config.get(section, "type"))
            cuisine = str(config.get(section, "cuisine"))
            rawIngre = str(config.get(section, "ingredients")).strip()

            ingredients = []
            split = rawIngre.split(', ')
            for ingredient in split:
                for i in INGREDIENTS_LIST:
                    if ingredient == i.name:
                        ingredients.append(i)
                        break

            dish = Dish(name, type, cuisine, ingredients)
            DISHES_LIST.append(dish)
            if cuisine == "Western":
                WESTERN_DISHES.append(dish)
            elif cuisine == "Chinese":
                CHINESE_DISHES.append(dish)
            elif cuisine == "Korean":
                KOREAN_DISHES.append(dish)

        # Load list of marketing strats
        config = configparser.ConfigParser()
        config.read("data/marketing.rs")
        for section in config.sections():
            name = str(config.get(section, "name"))
            modifier = config.getfloat(section, "modifier")
            cost = config.getint(section, "cost")
            duration = config.getint(section, "duration")
            desc = config.get(section, "desc")

            MARKETING_LIST.append(MarketingBonus(name, modifier, cost, duration, desc))

    def LoadSprites(self):
        smallDishSprites = glob.glob("asset/dish/Small/*.png")
        for sprite in smallDishSprites:
            key = ntpath.basename(sprite)[:-4] # Takes filename and removes '.png'
            DISH_SPRITES[key] = pygame.image.load(sprite).convert_alpha()

        largeDishSprites = glob.glob("asset/dish/Large/*.png")
        for sprite in largeDishSprites:
            key = ntpath.basename(sprite)[:-4]
            DISH_SPRITES[key] = pygame.image.load(sprite).convert_alpha()

        ingredientSprites = glob.glob("asset/ingredient/*.png")
        for sprite in ingredientSprites:
            key = ntpath.basename(sprite)[:-4]
            INGREDIENT_SPRITES[key] = pygame.image.load(sprite).convert_alpha()

        marketingSprites = glob.glob("asset/marketing/*.png")
        for sprite in marketingSprites:
            key = ntpath.basename(sprite)[:-4]
            MARKETING_SPRITES[key] = pygame.image.load(sprite).convert_alpha()

        chefSprites = glob.glob("asset/staff/Chef/*.png")
        for sprite in chefSprites:
            key = ntpath.basename(sprite)[:-4]
            CHEF_SPRITES[key] = pygame.image.load(sprite).convert_alpha()

        waiterSprites = glob.glob("asset/staff/Waiter/*.png")
        for sprite in waiterSprites:
            key = ntpath.basename(sprite)[:-4]
            WAITER_SPRITES[key] = pygame.image.load(sprite).convert_alpha()

        generalSprites = glob.glob("asset/general/*.png")
        for sprite in generalSprites:
            key = ntpath.basename(sprite)[:-4]
            SPRITES[key] = pygame.image.load(sprite).convert_alpha()


    def StartGame(self, new=None):
        if new:
            self.game = Game(self.folder, self.evManager)

        else:
            with open(self.folder+"/game.save", "rb") as file:
                self.game = pickle.load(file)
                ev = GameStartedEvent()
                self.evManager.Post(ev)

    def SaveGame(self):
        if self.game:
            with open(self.folder + "/game.save", "wb") as file:
                pickle.dump(self.game, file)

    def Start(self):
        # Start pygame GUI and Controller
        view = View(self.evManager)
        self.LoadSprites() # Can only be done after pygame init
        control = Controller(Main.evManager)

        new = False
        if not os.path.isfile(self.folder + "/game.save"):
            new = True

        ev = GUIOpenStartMenuEvent(new)
        self.evManager.Post(ev)

        control.Run()



    def Notify(self, event):
        if isinstance(event, AuthenticatedEvent):
            self.folder = "users/" + event.user
            if not os.path.exists(self.folder):
                os.makedirs(self.folder)

            self.LoadAssets()
            self.Start()

        elif isinstance(event, GUIOpenStartMenuEvent):
            self.game = None

        elif isinstance(event, NewGameRequestEvent):
            self.StartGame(new=True)

        elif isinstance(event, ContinueGameRequestEvent):
            self.StartGame()

        elif isinstance(event, SaveGameRequestEvent):
            self.SaveGame()

        elif isinstance(event, GameOverEvent):
            self.game = None
            try:
                os.remove(self.folder+"/game.save")
            except FileNotFoundError:
                pass
            try:
                os.remove(self.folder+"/info.json")
            except FileNotFoundError:
                pass



def main():
    Main.evManager = EventManager()
    auth = Authentication(Main.evManager)
    mainModule = MainModule(Main.evManager)

    auth.mainloop()

