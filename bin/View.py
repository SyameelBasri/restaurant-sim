import pygame
from pygame.locals import *
from bin import *
from .ViewMisc import *
from .ViewMenus import *
import os
import math
from .Events import *
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.backends.backend_agg as agg


# MAIN VIEW MODULE ---------------------------------------------------------------------------------------------


class View:
    def __init__(self, evManager):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        pygame.init()

        self.screen = pygame.display.set_mode(DISPLAY_RESOLUTION, DOUBLEBUF | HWSURFACE)
        self.origin = pygame.Surface(DRAW_RESOLUTION)
        self.background = pygame.Surface(self.origin.get_size())
        self.background.fill(WHITE)
        self.screen.blit(self.background, (0, 0))
        pygame.display.set_caption("Restaurant Simulator")
        pygame.display.flip()

        #Sprite Layers and Groups
        self.overlay = pygame.sprite.RenderUpdates()
        self.mainUI = pygame.sprite.RenderUpdates()
        self.windows = pygame.sprite.RenderUpdates()
        self.popUp = pygame.sprite.RenderUpdates()
        self.misc = pygame.sprite.RenderUpdates()
        self.activeWindow = None
        self.activePopUp = None

        self.hoverTicks = 0
        self.currentHover = None
        self.prevHover = []


    def DestroyGameScreen(self):
        for sprite in self.mainUI:
            self.evManager.UnregisterListener(sprite)

        self.overlay.empty()
        self.mainUI.empty()
        self.windows.empty()
        self.popUp.empty()
        self.activeWindow = None
        self.activePopUp = None

    def CheckHover(self):
        pos = pygame.mouse.get_pos()

        if not self.currentHover:
            for sprite in self.windows:
                try: # To handle cases where sprite load too slow
                    if sprite.rect.collidepoint(pos):
                        if sprite in self.prevHover:
                            self.hoverTicks += 1
                            if self.hoverTicks > 100:
                                sprite.Hover()
                                self.currentHover = sprite
                                break
                        else:
                            self.prevHover.append(sprite)
                            self.hoverTicks = 0
                except AttributeError:
                    continue

            for sprite in self.mainUI:
                try:
                    if sprite.rect.collidepoint(pos):
                        if sprite in self.prevHover:
                            self.hoverTicks += 1
                            if self.hoverTicks > 100:
                                sprite.Hover()
                                self.currentHover = sprite
                                break
                        else:
                            self.prevHover.append(sprite)
                            self.hoverTicks = 0
                except AttributeError:
                    continue

            for sprite in self.popUp:
                try: # To handle cases where sprite load too slow
                    if sprite.rect.collidepoint(pos):
                        if sprite in self.prevHover:
                            self.hoverTicks += 1
                            if self.hoverTicks > 100:
                                sprite.Hover()
                                self.currentHover = sprite
                                break
                        else:
                            self.prevHover.append(sprite)
                            self.hoverTicks = 0
                except AttributeError:
                    continue

        else:
            reset = True
            for sprite in self.windows:
                try:
                    if sprite.rect.collidepoint(pos):
                        if sprite is self.currentHover:
                            reset = False
                            break
                except AttributeError:
                    continue
            for sprite in self.mainUI:
                try:
                    if sprite.rect.collidepoint(pos):
                        if sprite is self.currentHover:
                            reset = False
                            break
                except AttributeError:
                    continue
            for sprite in self.popUp:
                try:
                    if sprite.rect.collidepoint(pos):
                        if sprite is self.currentHover:
                            reset = False
                            break
                except AttributeError:
                    continue

            if reset:
                self.tooltip = None
                self.currentHover = None
                self.misc.empty()
            else:
                try:
                    (x,y) = pygame.mouse.get_pos()
                    self.tooltip.rect.topleft = (x + 8, y + 8)
                    self.tooltip.text.rect.topleft = (x + 10, y + 10)
                except AttributeError:
                    pass

    def Notify(self, event):
        try:
            if isinstance(event, GameStartedEvent):
                # All sprite start from here.
                # Sprite will carry it group from here.
                self.backgroundSprite = BackgroundSprite(self.evManager, self.mainUI)
                self.restaurantSprite = RestaurantSprite(self.evManager, self.mainUI)
                self.staffTab = StaffTab(self.evManager, self.mainUI, self.windows, self.popUp)
                self.menuTab = MenuTab(self.evManager, self.mainUI, self.popUp)
                self.inventoryTab = InventoryTab(self.evManager, self.mainUI, self.popUp)
                self.midTab = MidTab(self.evManager, self.mainUI)
                self.restaurantTab = RestaurantTab(self.evManager, self.mainUI, self.popUp)
                self.financeTab = FinanceTab(self.evManager, self.mainUI, self.windows)
                self.customersTab = CustomersTab(self.evManager, self.mainUI, self.windows)
                self.rivalTab = RivalTab(self.evManager, self.mainUI, self.windows)
                self.datetime = DateTime(self.evManager, self.mainUI)
                self.marketingButton = MarketingButton(self.evManager, self.mainUI, self.windows)
                self.marketButton = MarketButton(self.evManager, self.mainUI, self.windows)
                self.addDishButton = AddDishButton(self.evManager, self.mainUI, self.popUp, self.windows)
                self.trendNews = TrendNews(self.evManager, self.mainUI)
                self.mainMenuButton = MainMenuButton(self.evManager, self.mainUI)
                self.tooltip = None

                ev = GameScreenLoadedEvent()
                self.evManager.Post(ev)

            elif isinstance(event, GameOverEvent):
                self.DestroyGameScreen()
                GameOverMenu(self.evManager, self.mainUI)

            elif isinstance(event, GUIOpenStartMenuEvent):
                self.DestroyGameScreen()
                StartMenu(self.evManager, self.mainUI, event.new)

            elif isinstance(event, TickEvent):
                self.CheckHover()
                try:
                    self.trendNews.dynamic.Update()
                except AttributeError:
                    pass

                self.origin.fill(WHITE)

                self.mainUI.clear(self.origin, self.background)
                self.windows.clear(self.origin, self.background)
                self.popUp.clear(self.origin, self.background)
                self.misc.clear(self.origin, self.background)
                self.overlay.clear(self.origin, self.background)

                self.mainUI.update()
                self.windows.update()
                self.popUp.update()
                self.misc.update()
                self.overlay.update()

                dirtyRects = self.mainUI.draw(self.origin)
                dirtyRects += self.windows.draw(self.origin)
                dirtyRects += self.popUp.draw(self.origin)
                dirtyRects += self.misc.draw(self.origin)
                dirtyRects = self.overlay.draw(self.origin)

                pygame.transform.scale(self.origin, DISPLAY_RESOLUTION, self.screen)

                pygame.display.flip()

            elif isinstance(event, NotEnoughCashEvent):
                NotEnoughCashPrompt(self.evManager, self.overlay)

            elif isinstance(event, GUITooltipEvent):
                (x,y) = pygame.mouse.get_pos()
                self.tooltip = Tooltip(event.text, (x + 10, y + 10), self.evManager, self.misc)

            elif isinstance(event, GUIRequestWindowEvent):
                if self.activeWindow is not event.window:
                    event.draw()
                    self.activeWindow = event.window

            elif isinstance(event, GUIRequestWindowRedrawEvent):
                if self.activeWindow == event.window:
                    event.draw()

            elif isinstance(event, GUIRequestPopUpEvent):
                if self.activePopUp is not event.popUp:
                    event.draw()
                    self.activePopUp = event.popUp

            elif isinstance(event, GUIRequestPopUpRedrawEvent):
                if self.activePopUp == event.popUp:
                    event.draw()

            elif isinstance(event, GUICloseWindowEvent):
                event.group.empty()
                if event.group is self.windows:
                    self.activeWindow = None
                elif event.group is self.popUp:
                    self.activePopUp = None

            elif isinstance(event, LeftClickEvent):
                overlay = False
                for sprite in self.overlay:
                    overlay = True
                    if sprite.rect.collidepoint(event.pos):
                        try:
                            sprite.Clicked()
                            return
                        except AttributeError:
                            continue
                if overlay:
                    return

                for sprite in self.mainUI:
                    if sprite.rect.collidepoint(event.pos):
                        try:
                            sprite.Clicked()
                            return
                        except AttributeError:
                            continue
                for sprite in self.windows:
                    if sprite.rect.collidepoint(event.pos):
                        try:
                            sprite.Clicked()
                            return
                        except AttributeError:
                            continue
                for sprite in self.popUp:
                    if sprite.rect.collidepoint(event.pos):
                        try:
                            sprite.Clicked()
                            return
                        except AttributeError:
                            continue

            elif isinstance(event, ShiftLeftClickEvent):
                overlay = False
                for sprite in self.overlay:
                    overlay = True
                    if sprite.rect.collidepoint(event.pos):
                        try:
                            sprite.ShiftClicked()
                            return
                        except AttributeError:
                            try:
                                sprite.Clicked()
                                return
                            except AttributeError:
                                continue
                if overlay:
                    return

                for sprite in self.mainUI:
                    if sprite.rect.collidepoint(event.pos):
                        try:
                            sprite.ShiftClicked()
                            return
                        except AttributeError:
                            try:
                                sprite.Clicked()
                                return
                            except AttributeError:
                                continue
                for sprite in self.windows:
                    if sprite.rect.collidepoint(event.pos):
                        try:
                            sprite.ShiftClicked()
                            return
                        except AttributeError:
                            try:
                                sprite.Clicked()
                                return
                            except AttributeError:
                                continue
                for sprite in self.popUp:
                    if sprite.rect.collidepoint(event.pos):
                        try:
                            sprite.ShiftClicked()
                            return
                        except AttributeError:
                            try:
                                sprite.Clicked()
                                return
                            except AttributeError:
                                continue

            elif isinstance(event, CtrlLeftClickEvent):
                overlay = False
                for sprite in self.overlay:
                    overlay = True
                    if sprite.rect.collidepoint(event.pos):
                        try:
                            sprite.CtrlClicked()
                            return
                        except AttributeError:
                            try:
                                sprite.Clicked()
                                return
                            except AttributeError:
                                continue
                if overlay:
                    return

                for sprite in self.mainUI:
                    if sprite.rect.collidepoint(event.pos):
                        try:
                            sprite.CtrlClicked()
                            return
                        except AttributeError:
                            try:
                                sprite.Clicked()
                                return
                            except AttributeError:
                                continue
                for sprite in self.windows:
                    if sprite.rect.collidepoint(event.pos):
                        try:
                            sprite.CtrlClicked()
                            return
                        except AttributeError:
                            try:
                                sprite.Clicked()
                                return
                            except AttributeError:
                                continue
                for sprite in self.popUp:
                    if sprite.rect.collidepoint(event.pos):
                        try:
                            sprite.CtrlClicked()
                            return
                        except AttributeError:
                            try:
                                sprite.Clicked()
                                return
                            except AttributeError:
                                continue

        except AttributeError:
            pass

# --------------------------------------------------------------------------------------------------------------


class BackgroundSprite(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None):
        self.evManager = evManager

        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.image = SPRITES["Background"]
        self.rect = self.image.get_rect()

class RestaurantSprite(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        self.level = None

        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.rect = None

    def Notify(self, event):
        if isinstance(event, RestaurantUpdateEvent):
            self.level = event.level
            self.image = SPRITES["RestaurantLevel" + str(self.level)]
            self.rect = self.image.get_rect()
            self.rect.midbottom = (SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.6)


class MainMenuButton(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None):
        self.evManager = evManager

        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.image = SPRITES["Exit_to_Menu"]
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH * 97 / 100, SCREEN_HEIGHT * 4 / 100)

    def Clicked(self):
        ev = SaveGameRequestEvent()
        self.evManager.Post(ev)

        ev = GUIOpenStartMenuEvent()
        self.evManager.Post(ev)


class NextDayButton(pygame.sprite.Sprite):
    def __init__(self, x, y, evManager, group=None):
        self.evManager = evManager

        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.image = SPRITES["NextDay"]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def Clicked(self):
        ev = NewDayEvent()
        self.evManager.Post(ev)

    def Hover(self):
        text = "Next Day [Shortcut: E]"
        ev = GUITooltipEvent(text)
        self.evManager.Post(ev)


class DateTime(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.image = pygame.Surface((230, 50))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH * 86 / 100, SCREEN_HEIGHT * 4 / 100)

        self.date = str(Date.day) + " / " + str(Date.month) + " / " + str(Date.year)
        self.display = Numbers(self, "date", self.rect.right - 10, self.rect.centery, WHITE, 24, self.group)

        self.nextDayButton = NextDayButton(self.rect.left + 30, self.rect.centery, self.evManager, self.group)

    def Notify(self, event):
        if isinstance(event, NewDayEvent):
            self.date = str(Date.day) + " / " + str(Date.month) + " / " + str(Date.year)
            self.display.Update()


class NotEnoughCashPrompt(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None):
        self.evManager = evManager

        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.image = pygame.Surface((500, 200))
        self.image.fill(BLACK)
        surf = pygame.Surface((460, 160))
        surf.fill(RED)
        self.image.blit(surf, (20,20))
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH * 0.5, SCREEN_HEIGHT * 0.5)

        Text("Not Enough Cash", self.rect.centerx, self.rect.top + 50, WHITE, 40, self.group, TEXT_CENTER)
        OkButton(self.rect.centerx, self.rect.bottom - 70, evManager, self.group)

class OkButton(pygame.sprite.Sprite):
    def __init__(self, x, y, evManager, group=None):
        self.evManager = evManager

        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.image = pygame.Surface((200, 40))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        Text("OK", *self.rect.center, RED, 30, self.group, TEXT_CENTER)

    def Clicked(self):
        self.group.empty()

# FINANCE----------------------------------------------------------------------------------------------


class FinanceTab(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None, windowGroup=None):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        self.name = "Finance Window"

        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.image = pygame.Surface((230,50))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH * 10 / 100, SCREEN_HEIGHT * 4 / 100)

        FinanceTabIcon(self.rect.left + 20, self.rect.centery, self.evManager, self.group)

        self.cash = 0
        self.cashDisplay = Numbers(self, "cash", self.rect.right - 20, self.rect.centery, BLACK, 28, self.group, TEXT_RIGHT)

        self.windowGroup = windowGroup
        self.fiscalTerm = FIN_TERM_DAILY
        self.cashBook = []
        self.window = None


    def Draw(self):
        self.windowGroup.empty()
        self.window = FinanceWindow(self, self.evManager, self.windowGroup)

    def Clicked(self):
        ev = GUIRequestWindowEvent(self.name, self.Draw)
        self.evManager.Post(ev)

        ev = RequestFinanceWindowEvent(self.fiscalTerm)
        self.evManager.Post(ev)

    def Notify(self, event):
        if isinstance(event, UpdateFinanceWindowEvent):
            self.cashBook = event.cashBook

            ev = GUIRequestWindowRedrawEvent(self.name, self.Draw)
            self.evManager.Post(ev)

        elif isinstance(event, NewDayEvent):
            ev = RequestFinanceWindowEvent(self.fiscalTerm)
            self.evManager.Post(ev)

        elif isinstance(event, CashUpdateEvent):
            self.cash = event.cash
            self.cashDisplay.Update()

            ev = RequestFinanceWindowEvent(self.fiscalTerm)
            self.evManager.Post(ev)


class FinanceTabIcon(pygame.sprite.Sprite):
    def __init__(self, x, y, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.group = group
        self.image = SPRITES["FinanceIcon"]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def Hover(self):
        text = "Total Cash"
        ev = GUITooltipEvent(text)
        self.evManager.Post(ev)


class FinanceWindow:
    def __init__(self, parent, evManager, group=None):
        self.evManager = evManager
        self.group = group
        self.parent = parent
        self.window = MainWindow(GREEN, self.evManager, self.group)
        self.screens = []

        x = SCREEN_WIDTH / 2
        y = SCREEN_HEIGHT / 2
        #Button
        self.dayButton = FinanceButton(x - 300, y - 260, 140, 30, self.parent, "Day", YELLOW, self.evManager, self.group, FIN_TERM_DAILY)
        Text("Daily", x - 300, y - 260, BLACK, 25, self.group, TEXT_CENTER)
        self.monthButton = FinanceButton(x - 150, y - 260, 140, 30, self.parent, "Month", BLUE, self.evManager, self.group, FIN_TERM_MONTHLY)
        Text("Monthly", x - 150, y - 260, WHITE, 25, self.group, TEXT_CENTER)
        self.yearButton = FinanceButton(x, y - 260, 140, 30, self.parent,  "Year", RED, self.evManager, self.group, FIN_TERM_YEARLY)
        Text("Yearly", x, y - 260, WHITE, 25, self.group, TEXT_CENTER)
        #self.statementButton = FinanceButton(x + 250, y - 260, 30, 40, self.parent, "Statement", BLACK, self.evManager, self.group)
        #self.graphButton = FinanceButton(x + 285, y - 260, 30, 40, self.parent, "Graph", BLACK, self.evManager, self.group)

        #Text
        Text("Income:", x - 350, y - 200, BLACK, 25, self.group)
        Text("Sales", x - 330, y - 180, BLACK, 25, self.group)
        Text("Expense:", x - 350, y - 155, BLACK, 25, self.group)
        Text("Inventory", x - 330, y - 130, BLACK, 25, self.group)
        Text("Marketing", x - 330, y - 100, BLACK, 25, self.group)
        Text("Renovation", x - 330, y - 70, BLACK, 25, self.group)
        Text("Salary", x - 330, y - 40, BLACK, 25, self.group)
        Text("Misc.", x - 330, y - 10, BLACK, 25, self.group)
        Text("Profit/Loss", x - 350, y + 20, BLACK, 25, self.group)
        Text("Total Cash:", x - 350, y + 55, BLACK, 25, self.group)

        x = SCREEN_WIDTH * 40 / 100
        y = SCREEN_HEIGHT * 41 / 100
        for statement in self.parent.cashBook:
            self.screens.append(StatementScreen(x, y, statement, self.evManager, self.group))
            x += 180


class StatementScreen(pygame.sprite.Sprite):
    def __init__(self, x, y, statement, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.group = group
        self.statement = statement
        self.x = x
        self.y = y

        self.image = pygame.Surface((170, 290))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

        self.contents = []

        for key, value in statement.items():
            if key == FIN_SALES:
                sales = Text(str(value), self.rect.right - 10, y - 107, BLACK, 27, self.group, TEXT_RIGHT)
                self.contents.append(sales)

            elif key == FIN_INVENTORY:
                inventory = Text(str(value), self.rect.right - 10, y - 55, BLACK, 27, self.group, TEXT_RIGHT)
                self.contents.append(inventory)

            elif key == FIN_MARKETING:
                marketing = Text(str(value), self.rect.right - 10, y - 25, BLACK, 27, self.group, TEXT_RIGHT)
                self.contents.append(marketing)

            elif key == FIN_RENOVATION:
                renovation = Text(str(value), self.rect.right - 10, y + 5, BLACK, 27, self.group, TEXT_RIGHT)
                self.contents.append(renovation)

            elif key == FIN_SALARY:
                salary = Text(str(value), self.rect.right - 10, y + 35, BLACK, 27, self.group, TEXT_RIGHT)
                self.contents.append(salary)

            elif key == FIN_MISC:
                misc = Text(str(value), self.rect.right - 10, y + 65, BLACK, 27, self.group, TEXT_RIGHT)
                self.contents.append(misc)

            elif key == "Profit":
                profit = Text(str(value), self.rect.right - 10, y + 95, BLACK, 27, self.group, TEXT_RIGHT, bold=True)
                self.contents.append(profit)

            elif key == FIN_CASH:
                cash = Text(str(value), self.rect.right - 10, y + 130, BLACK, 27, self.group, TEXT_RIGHT)
                self.contents.append(cash)

            elif key == "Day":
                day = Text(str(value), self.x, self.rect.top, BLACK, 27, self.group, TEXT_RIGHT)
                self.contents.append(day)

            elif key == "Month":
                month = Text(str(value), self.x + 30, self.rect.top, BLACK, 27, self.group, TEXT_RIGHT)
                self.contents.append(month)

            elif key == "Year":
                year = Text(str(value), self.x + 80, self.rect.top, BLACK, 27, self.group, TEXT_RIGHT)
                self.contents.append(year)


class FinanceButton(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, parent, name, color, evManager, group=None, type=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.group = group
        self.parent = parent
        self.name = name
        self.color = color
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.type = type

        self.image = pygame.Surface((self.w, self.h))
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

    def Clicked(self):
        if self.type == None:
            pass
        else:
            self.parent.fiscalTerm = self.type
            ev = RequestFinanceWindowEvent(self.type)
            self.evManager.Post(ev)


# CUSTOMERS-------------------------------------------------------------------------------------------------


class CustomersTab(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None, windowGroup=None):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        self.name = "Customers Window"

        pygame.sprite.Sprite.__init__(self, group)
        self.image = pygame.Surface((230, 50))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH * 28 / 100, SCREEN_HEIGHT * 4 / 100)
        self.group = group
        self.windowGroup = windowGroup

        CustomerTabIcon(self.rect.left + 20, self.rect.centery, self.evManager, self.group, "Today Customer")

        self.customers = 0
        self.unfedCustomers = 0
        self.satisfaction = 0
        self.prevCustomers = 0
        self.prevUnfedCustomers = 0
        self.prevSatisfaction = 0
        self.dishesServed = []

        self.customersDisplay = Numbers(self, "customers", self.rect.right - 60, self.rect.centery, WHITE, 30,
                                        self.group, TEXT_RIGHT)
        self.satisfactionDisplay = None
        self.DrawSatisfaction()

    def DrawSatisfaction(self):
        if 0 <= self.satisfaction <= 20:
            self.satisfactionDisplay = SatisfactionSmiley(self.rect.right - 30, self.rect.centery, self.evManager,
                                                          self.group, "1")

        elif 21 <= self.satisfaction <= 40:
            self.satisfactionDisplay = SatisfactionSmiley(self.rect.right - 30, self.rect.centery, self.evManager,
                                                          self.group, "2")

        elif 41 <= self.satisfaction <= 60:
            self.satisfactionDisplay = SatisfactionSmiley(self.rect.right - 30, self.rect.centery, self.evManager,
                                                          self.group, "3")

        elif 61 <= self.satisfaction <= 80:
            self.satisfactionDisplay = SatisfactionSmiley(self.rect.right - 30, self.rect.centery, self.evManager,
                                                          self.group, "4")

        elif 81 <= self.satisfaction <= 100:
            self.satisfactionDisplay = SatisfactionSmiley(self.rect.right - 30, self.rect.centery, self.evManager,
                                                          self.group, "5")


    def Draw(self):
        self.windowGroup.empty()
        CustomersWindow(self, self.evManager, self.windowGroup)

    def Clicked(self):

        ev = GUIRequestWindowEvent(self.name, self.Draw)
        self.evManager.Post(ev)

    def Notify(self, event):
        if isinstance(event, SalesReportEvent):
            self.prevCustomers = self.customers
            self.prevUnfedCustomers = self.unfedCustomers
            self.prevSatisfaction = self.satisfaction

            self.dishesServed = event.dishesServed
            self.customers = event.customers
            self.unfedCustomers = event.unfedCustomers
            self.satisfaction = event.satisfaction

            self.customersDisplay.Update()

            self.satisfactionDisplay.kill()
            self.DrawSatisfaction()

            ev = GUIRequestWindowRedrawEvent(self.name, self.Draw)
            self.evManager.Post(ev)


class SatisfactionSmiley(pygame.sprite.Sprite):
    def __init__(self, x, y, evManager , group=None, type=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.x = x
        self.y = y
        self.group = group
        self.evManager = evManager
        self.type = type
        self.image = SPRITES[self.type + "Satisfaction"]

        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

    def Hover(self):
        text = "Customer Satisfaction"
        ev = GUITooltipEvent(text)
        self.evManager.Post(ev)


class CustomerTabIcon(pygame.sprite.Sprite):
    def __init__(self, x, y, evManager, group=None, type=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.group = group
        self.type = type
        self.image = SPRITES["CustomerIcon"]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def Hover(self):
        text = "Today Customer"
        ev = GUITooltipEvent(text)
        self.evManager.Post(ev)




class CustomersWindow:
    def __init__(self, parent, evManager, group=None):
        self.evManager = evManager
        self.group = group
        self.window = MainWindow(BLUE, self.evManager, self.group)
        self.previousTodayCustomer = PreviousTodayCustomer(self.window.rect.left + 10, self.window.rect.top + 60,
                                                           parent, self.evManager, self.group)

        self.dishBreakdown = DishBreakdown(self.window.rect.left + 380, self.window.rect.top + 60,
                                           parent, self.evManager, self.group)


class PreviousTodayCustomer(pygame.sprite.Sprite):
    def __init__(self, x, y, parent, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.group = group

        self.parent = parent
        self.x = x
        self.y = y
        self.image = pygame.Surface((360, 300))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        pygame.draw.line(self.image, BLACK, (180, 10), (180, 350), 1)
        pygame.draw.line(self.image, BLACK, (270, 10), (270, 350), 1)

        Text("Number of Customers", self.x + 10, self.y + 100, BLACK, 24, self.group)
        Text("Unserved Customer", self.x + 10, self.y + 150, BLACK, 24, self.group)
        Text("Satisfaction", self.x + 10, self.y + 200, BLACK, 24, self.group)
        Text("Today", self.x + 225, self.y + 30, BLACK, 24, self.group, TEXT_CENTER)
        Text("Yesterday", self.x + 315, self.y + 30, BLACK, 24, self.group, TEXT_CENTER)

        Text(str(self.parent.customers), self.x + 225, self.y + 110, BLACK, 28, self.group, TEXT_CENTER)
        Text(str(self.parent.unfedCustomers), self.x + 225, self.y + 160, BLACK, 28, self.group, TEXT_CENTER)
        Text(str(self.parent.satisfaction), self.x + 225, self.y + 210, BLACK, 28, self.group, TEXT_CENTER)

        Text(str(self.parent.prevCustomers), self.x + 315, self.y + 110, BLACK, 28, self.group, TEXT_CENTER)
        Text(str(self.parent.prevUnfedCustomers), self.x + 315, self.y + 160, BLACK, 28, self.group, TEXT_CENTER)
        Text(str(self.parent.prevSatisfaction), self.x + 315, self.y + 210, BLACK, 28, self.group, TEXT_CENTER)


class DishBreakdown(pygame.sprite.Sprite):
    def __init__(self, x, y, parent, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.group = group
        self.parent = parent
        self.x = x
        self.y = y

        sizes = []
        labels = []
        for dish in parent.dishesServed:
            if dish['sales'] > 0:
                sizes.append(dish['sales'])
                labels.append(dish['dish'].name)

        if len(sizes) == 0:
            sizes = [1]

        # Pie chart
        fig, ax = plt.subplots()
        ax.pie(sizes, startangle=90, radius=0.5)
        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        ax.legend(labels, loc="best")

        canvas = agg.FigureCanvasAgg(fig)
        canvas.draw()
        renderer = canvas.get_renderer()
        rawData = renderer.tostring_rgb()
        size = canvas.get_width_height()

        plt.close(fig)

        # self.image = pygame.image.tostring(pygame.Surface((360, 360)), "RGB")
        self.image = pygame.Surface((400, 300))
        self.piechart = pygame.image.fromstring(rawData, size, "RGB").convert()
        pygame.transform.scale(self.piechart, (400, 300), self.image)

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y


# RIVAL--------------------------------------------------------------------------------------------------


class RivalTab(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None, windowGroup=None):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        self.name = "Rival Window"
        self.group = group

        pygame.sprite.Sprite.__init__(self, group)
        self.image = pygame.Surface((50, 50))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH * 73 / 100, SCREEN_HEIGHT * 4 / 100)

        self.windowGroup = windowGroup

        RivalTabIcon(self.rect.centerx, self.rect.centery, self.evManager, self.group)

        self.rivals = None
        self.currentRival = 0

    def Draw(self):
        self.windowGroup.empty()
        RivalWindow(self, self.evManager, self.windowGroup)

    def Update(self):
        ev = GUIRequestWindowRedrawEvent(self.name, self.Draw)
        self.evManager.Post(ev)

    def Clicked(self):
        ev = GUIRequestWindowEvent(self.name, self.Draw)
        self.evManager.Post(ev)

    def Notify(self, event):
        if isinstance(event, NewDayEvent):
            self.Update()

        elif isinstance(event, RivalsUpdateEvent):
            self.rivals = event.rivals


class RivalTabIcon(pygame.sprite.Sprite):
    def __init__(self, x, y, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.group = group
        self.image = SPRITES["RivalIcon"]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def Hover(self):
        text = "Your Rivals"
        ev = GUITooltipEvent(text)
        self.evManager.Post(ev)



class RivalWindow:
    def __init__(self, parent, evManager, group=None):
        self.evManager = evManager
        self.group = group
        self.parent = parent
        self.window = MainWindow(YELLOW, self.evManager, self.group)

        x = SCREEN_WIDTH / 2
        y = SCREEN_HEIGHT / 2

        RivalScreen(x, y, self.parent.rivals[self.parent.currentRival], self.evManager, self.group)

        for rival in self.parent.rivals:
            RivalButton(x - 150, y - 265, rival, parent, self.evManager, self.group)
            x += 150


class RivalScreen(pygame.sprite.Sprite):
    def __init__(self, x, y, rivalInfo, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager

        (name, customers, dishes) = rivalInfo
        self.group = group
        self.x = x
        self.y = y

        self.image = pygame.Surface((780, 250))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y - 50)

        Text(name, x, y - 230, BLACK, 35, self.group, TEXT_CENTER)
        Text("Today Customers:", x - 30, y - 195, BLACK, 25, self.group, TEXT_CENTER)
        Text(str(customers), x + 80, y - 195, BLACK, 38, self.group, TEXT_CENTER)

        Text("MENU", x, y - 155, WHITE, 35, self.group, TEXT_CENTER)


        x = self.rect.left + 115
        y = self.rect.top + 100
        i = 0
        for dish in dishes:
            RivalDishContainer(x, y + 8, dish, self.evManager, self.group)
            x += 60

            i += 1
            if i >= 10:
                x = self.rect.left + 33
                y += 70
                i = 0


class RivalButton(pygame.sprite.Sprite):
    def __init__(self, x, y, rival, parent, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.parent = parent
        self.rival = rival
        self.group = group
        self.x = x
        self.y = y

        self.image = pygame.Surface((130, 30))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

        Text(self.rival[0], *self.rect.center, WHITE, 25, self.group, TEXT_CENTER)

    def Clicked(self):
        self.parent.currentRival = self.parent.rivals.index(self.rival)
        self.parent.Update()


class RivalDishContainer(pygame.sprite.Sprite):
    def __init__(self, x, y, dish, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager

        self.x = x
        self.y = y
        self.dish = dish['dish']
        self.group = group
        self.price = dish['price']

        self.image = pygame.Surface((45, 45))
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

        DishSprite(self.x, self.y, self.dish, self.group)

    def Hover(self):
        text = self.dish.name
        ev = GUITooltipEvent(text)
        self.evManager.Post(ev)


#STAFFs/WORKERs--------------------------------------------------------------------------------------------------

class StaffTab(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None, windowGroup=None, popUp=None):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        self.name = "Staff Window"
        self.group = group
        pygame.sprite.Sprite.__init__(self, group)
        self.image = pygame.Surface((100, 200))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH * 43.5 / 100, SCREEN_HEIGHT * 85 / 100)

        self.windowGroup = windowGroup
        self.popUp = popUp

        StaffTabIcon(self.rect.centerx, self.rect.centery - 50, self.evManager, self.group, "Chefs")
        StaffTabIcon(self.rect.centerx, self.rect.centery + 40, self.evManager, self.group, "Waiters")

        self.chefs = []
        self.waiters = []
        self.mode = "My Staff"
        self.chefsNumber = len(self.chefs)
        self.waitersNumber = len(self.waiters)
        self.staffType = "Chef"
        self.cuisine = CUISINE_WESTERN

        self.page = 1
        self.maxPage = 1

        self.chefsDisplay = Numbers(self, "chefsNumber", self.rect.centerx, self.rect.centery - 10, BLACK, 35,
                                    self.group, TEXT_CENTER)
        self.waitersDisplay = Numbers(self, "waitersNumber", self.rect.centerx, self.rect.centery + 80, BLACK, 35,
                                      self.group, TEXT_CENTER)

    def DrawMyStaff(self):
        self.windowGroup.empty()
        MyStaffScreen(self, self.evManager, self.windowGroup, self.popUp)
        self.mode = "My Staff"

    def DrawHireStaff(self):
        self.windowGroup.empty()
        HireStaffScreen(self, self.evManager, self.windowGroup)
        self.mode = "Hire Staff"

    def Update(self):
        if self.mode == "My Staff":
            ev = GUIRequestWindowRedrawEvent(self.name, self.DrawMyStaff)
            self.evManager.Post(ev)

    def Clicked(self):
        ev = GUIRequestWindowEvent(self.name, self.DrawMyStaff)
        self.evManager.Post(ev)

    def Notify(self, event):
        if isinstance(event, StaffUpdateEvent):
            self.chefs = event.chefs
            self.waiters = event.waiters

            self.chefsNumber = len(self.chefs)
            self.waitersNumber = len(self.waiters)
            self.chefsDisplay.Update()
            self.waitersDisplay.Update()

            self.maxPage = math.ceil((len(self.chefs) + len(self.waiters)) / 30)
            if self.maxPage <= 0:
                self.maxPage = 1
            if self.page > self.maxPage:
                self.page = self.maxPage

            if self.mode == "My Staff":
                ev = GUIRequestWindowRedrawEvent(self.name, self.DrawMyStaff)
                self.evManager.Post(ev)


        elif isinstance(event, GUIOpenMyStaffEvent):
            ev = GUIRequestWindowRedrawEvent(self.name, self.DrawMyStaff)
            self.evManager.Post(ev)

        elif isinstance(event, GUIOpenHireStaffEvent):
            ev = GUIRequestWindowRedrawEvent(self.name, self.DrawHireStaff)
            self.evManager.Post(ev)

        elif isinstance(event, GUISelectStaffEvent):
            self.staffType = event.staffType

            ev = GUIRequestWindowRedrawEvent(self.name, self.DrawHireStaff)
            self.evManager.Post(ev)

        elif isinstance(event, GUISelectCuisineEvent):
            self.cuisine = event.cuisine

            ev = GUIRequestWindowRedrawEvent(self.name, self.DrawHireStaff)
            self.evManager.Post(ev)


class StaffTabIcon(pygame.sprite.Sprite):
    def __init__(self, x, y, evManager, group=None, type=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.group = group
        self.type = type

        self.image = None
        if type == "Chefs":
            self.image = SPRITES["ChefIcon"]
        elif type == "Waiters":
            self.image = SPRITES["WaiterIcon"]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def Hover(self):
        if self.type == "Chefs":
            ev = GUITooltipEvent(self.type)
            self.evManager.Post(ev)

        elif self.type == "Waiters":
            ev = GUITooltipEvent(self.type)
            self.evManager.Post(ev)


class StaffWindow:
    def __init__(self, parent, evManager, group=None, popUp=None):
        self.evManager = evManager

        self.parent = parent
        self.group = group
        self.popUp = popUp

        MainWindow(YELLOW, self.evManager, group)

        MyStaffsTab(self.parent, self.evManager, self.group)
        HireStaffsTab(self.parent, self.evManager, self.group)


class StaffSprite(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, evManager, group=None, staff=None): #TODO: type, cuisine, and level: use to find sprite
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.group = group

        self.x = x
        self.y = y
        self.w = w
        self.h = h

        self.image = staff.sprite
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)


class MyStaffsTab(pygame.sprite.Sprite):
    def __init__(self, parent, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.group = group
        self.parent = parent

        self.image = pygame.Surface((110, 35))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH * 45 / 100, SCREEN_HEIGHT * 15 / 100)

        Text("My Staff", *self.rect.center, WHITE, 25, self.group, TEXT_CENTER)

    def Clicked(self):
        if self.parent.mode == "My Staff":
            pass
        else:
            ev = GUIOpenMyStaffEvent()
            self.evManager.Post(ev)


class HireStaffsTab(pygame.sprite.Sprite):
    def __init__(self, parent, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.group = group
        self.parent = parent

        self.image = pygame.Surface((110, 35))
        self.image.fill(PURPLE)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH * 55 / 100, SCREEN_HEIGHT * 15 / 100)

        Text("Hire Staff", *self.rect.center, WHITE, 25, self.group, TEXT_CENTER)

    def Clicked(self):
        if self.parent.mode == "Hire Staff":
            pass
        else:
            ev = GUIOpenHireStaffEvent()
            self.evManager.Post(ev)


class MyStaffScreen(StaffWindow):
    def __init__(self, parent, evManager, group=None, popUp=None):
        super().__init__(parent, evManager, group, popUp)
        self.x = SCREEN_WIDTH * 50 / 100
        self.y = SCREEN_HEIGHT * 40 / 100

        self.image = pygame.Surface((780, 300))
        self.image.fill(BLUE)
        self.image.set_colorkey(BLUE)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

        Text("Restaurant's Staff", self.x, self.y - 130, BLACK, 30, self.group, TEXT_CENTER)

        PrevPage(self.rect.right - 50, self.rect.centery - 50, 50, 50, self.parent, group)
        self.pageDisplay = Numbers(self.parent, "page", self.rect.right - 60, self.rect.centery, BLACK, 24,
                                   self.group)
        Text("/", self.rect.right - 50, self.rect.centery, BLACK, 32, self.group, TEXT_CENTER)
        self.maxPageDisplay = Numbers(self.parent, "maxPage", self.rect.right - 40, self.rect.centery, BLACK, 24,
                                      self.group, TEXT_LEFT)
        NextPage(self.rect.right - 50, self.rect.centery + 50, 50, 50, self.parent, group)

        x = self.x - 350
        y = self.y - 75

        from .Model import Chef, Waiter

        staffList = self.parent.chefs + self.parent.waiters
        baseIndex = (self.parent.page - 1) * 30
        for i in range(30):
            try:
                staff = staffList[i + baseIndex]

                if isinstance(staff, Chef):
                    MyChefContainer(x, y, staff, self.evManager, self.group, self.popUp)
                elif isinstance(staff, Waiter):
                    MyWaiterContainer(x, y, staff, self.evManager, self.group, self.popUp)
                x += 65
                if i in (9, 19):
                    x = self.x - 350
                    y += 75
            except IndexError:
                break




class HireStaffScreen(StaffWindow):
    def __init__(self, parent, evManager, group=None):
        super().__init__(parent, evManager, group)

        self.image = pygame.Surface((780, 300))
        self.image.fill(PURPLE)
        self.image.set_colorkey(PURPLE)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH * 50 / 100, SCREEN_HEIGHT * 40 / 100)

        ChefTab(self.evManager, self.group)
        WaiterTab(self.evManager, self.group)

        if self.parent.staffType == "Chef":
            self.LoadHireChefContents()
        elif self.parent.staffType == "Waiter":
            self.LoadHireWaiterContents()


    def LoadHireChefContents(self):
        tab_x = SCREEN_WIDTH * 31.5 / 100
        tab_y = SCREEN_HEIGHT * 23 / 100
        container_x = SCREEN_WIDTH * 38 / 100
        container_y = SCREEN_HEIGHT * 25.5 / 100
        level = 3

        for cuisine in CUISINES_LIST:
            ChefCuisine(tab_x, tab_y, cuisine, self.evManager, self.group)
            tab_y += 50

        while level >= 0:
            HireChefContainer(container_x, container_y, 500, 60, self.parent.cuisine, level,
                                                   self.evManager, self.group)
            level -= 1
            container_y += 70


    def LoadHireWaiterContents(self):
        x = SCREEN_WIDTH * 26.5 / 100
        y = SCREEN_HEIGHT * 30 / 100
        level = 3

        while level >= 0:
            HireWaiterContainer(x, y, 330, 130, level, self.evManager, self.group)
            x += 340
            level -= 1
            if level == 1:
                x = SCREEN_WIDTH * 26.5 / 100
                y += 145


class ChefTab(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.group = group

        self.image = SPRITES["ChefIcon"]
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH * 22 / 100, SCREEN_HEIGHT * 25 / 100)

    def Clicked(self):
        staffType = "Chef"
        ev = GUISelectStaffEvent(staffType)
        self.evManager.Post(ev)


class WaiterTab(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.group = group

        self.image = SPRITES["WaiterIcon"]
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH * 22 / 100, SCREEN_HEIGHT * 34 / 100)

    def Clicked(self):
        staffType = "Waiter"
        ev = GUISelectStaffEvent(staffType)
        self.evManager.Post(ev)


class ChefCuisine(pygame.sprite.Sprite):
    def __init__(self, x, y, cuisine, evManager, group=None):
        self.evManager = evManager

        pygame.sprite.Sprite.__init__(self, group)
        self.cuisine = cuisine
        self.group = group
        self.x = x
        self.y = y
        self.image = SPRITES[cuisine + "Cuisine"]
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

        Text(self.cuisine, *self.rect.center, WHITE, 25, self.group, TEXT_CENTER)

    def Clicked(self):
        ev = GUISelectCuisineEvent(self.cuisine)
        self.evManager.Post(ev)


class ChefDetail(pygame.sprite.Sprite):
    def __init__(self, chef, evManager, group=None):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        pygame.sprite.Sprite.__init__(self, group)
        self.group = group

        self.name = ""

        self.x = SCREEN_WIDTH * 9 / 100
        self.y = SCREEN_HEIGHT * 40 / 100
        self.w = 230
        self.h = 300
        self.chef = chef
        self.level = self.chef.level
        self.cuisine = self.chef.cuisine
        self.name = None
        self.wage = None

        if self.level == 3:
            self.name = "Chef de Cuisine"
            self.wage = 5000
        elif self.level == 2:
            self.name = "Sous Chef"
            self.wage = 3500
        elif self.level == 1:
            self.name = "Chef de Partie"
            self.wage = 2000
        elif self.level == 0:
            self.name = "Commis Chef"
            self.wage = 1000

        self.image = pygame.Surface((self.w, self.h))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        self.contents = []

        x = self.rect.right - 20
        y = self.rect.top + 20
        self.closeButton = CloseButton(x, y, self.evManager, self.group)

        self.contents.append(Text("CHEF", self.x, self.y - 130, BLACK, 35, self.group, TEXT_CENTER))
        self.contents.append(StaffSprite(self.x, self.y - 80, 50, 50, self.evManager, self.group, self.chef))
        self.contents.append(Text(self.name, self.x, self.y - 35, BLACK, 20, self.group, TEXT_CENTER))
        self.contents.append(Text(self.cuisine, self.x, self.y - 20, BLACK, 20, self.group, TEXT_CENTER))
        self.contents.append(Text("Wage/Day:", self.x - 100, self.y, BLACK, 20, self.group))
        self.contents.append(Text(str(self.chef.salary), self.x - 20, self.y, BLACK, 20, self.group))
        self.contents.append(FireStaffButton(self.x, self.y + 100, self.chef, self.evManager, self.group))

    def Notify(self, event):
        if isinstance(event, StaffUpdateEvent):
            if self.chef not in event.chefs:
                self.group.empty()


class WaiterDetail(pygame.sprite.Sprite):
    def __init__(self, waiter, evManager, group=None):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        pygame.sprite.Sprite.__init__(self, group)
        self.group = group

        self.x = SCREEN_WIDTH * 9 / 100
        self.y = SCREEN_HEIGHT * 40 / 100
        self.w = 230
        self.h = 300
        self.waiter = waiter
        self.level = self.waiter.level
        self.name = None
        self.wage = None

        if self.level == 3:
            self.name = "Highly-Trained"
            self.wage = 2500
        elif self.level == 2:
            self.name = "Well-Trained"
            self.wage = 2000
        elif self.level == 1:
            self.name = "Basic-Trained"
            self.wage = 1500
        elif self.level == 0:
            self.name = "Untrained"
            self.wage = 1000

        self.image = pygame.Surface((self.w, self.h))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        self.contents = []

        x = self.rect.right - 20
        y = self.rect.top + 20
        self.closeButton = CloseButton(x, y, self.evManager, self.group)

        self.contents.append(Text("WAITER", self.x, self.y - 130, BLACK, 35, self.group, TEXT_CENTER))
        self.contents.append(StaffSprite(self.x, self.y - 80, 50, 50, self.evManager, self.group, self.waiter))
        self.contents.append(Text(self.name, self.x, self.y - 35, BLACK, 20, self.group, TEXT_CENTER))
        self.contents.append(Text("Wage/Day:", self.x - 100, self.y, BLACK, 20, self.group))
        self.contents.append(Text(str(self.waiter.salary), self.x - 20, self.y, BLACK, 20, self.group))
        self.contents.append(FireStaffButton(self.x, self.y + 100, self.waiter, self.evManager, self.group))

    def Notify(self, event):
        if isinstance(event, StaffUpdateEvent):
            if self.waiter not in event.waiters:
                self.group.empty()


class FireStaffButton(pygame.sprite.Sprite):
    def __init__(self, x, y, staff, evManager, group=None):
        self.evManager = evManager
        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.staff = staff
        self.x = x
        self.y = y

        self.image = pygame.Surface((150, 80))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        Text("FIRE!!!", self.rect.centerx, self.rect.centery - 20, BLACK, 30, self.group, TEXT_CENTER)
        Text("($" + str(self.staff.salary * 3) + ")", self.rect.centerx, self.rect.centery + 20, BLACK, 30, self.group, TEXT_CENTER)

    def Clicked(self):
        ev = FireStaffEvent(self.staff)
        self.evManager.Post(ev)


class MyChefContainer(pygame.sprite.Sprite):
    def __init__(self, x, y, chef, evManager, group=None, popUp=None):
        self.evManager = evManager
        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.chef = chef
        self.level = chef.level
        self.cuisine = chef.cuisine
        self.popUp = popUp
        self.type = "Chef"

        self.name = str(self.chef)

        self.image = pygame.Surface((55, 70))
        self.image.fill(RED)

        self.x = x
        self.y = y
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

        self.contents = []

        self.contents.append(StaffSprite(self.x, self.y - 8, 50, 50, self.evManager, self.group, self.chef))
        self.contents.append(Text(str(self.chef.level), self.x, self.y + 30, BLACK, 20, self.group, TEXT_CENTER))

    def Draw(self):
        self.popUp.empty()
        ChefDetail(self.chef, self.evManager, self.popUp)

    def Clicked(self):
        ev = GUIRequestPopUpEvent(self.name, self.Draw)
        self.evManager.Post(ev)


class HireChefContainer(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, cuisine, level, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.group = group
        self.staffType = "Chef"

        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.cuisine = cuisine
        self.level = level
        self.name = None
        self.wage = None
        self.cost = None

        if self.level == 3:
            self.name = "Chef de Cuisine"
        elif self.level == 2:
            self.name = "Sous Chef"
        elif self.level == 1:
            self.name = "Chef de Partie"
        elif self.level == 0:
            self.name = "Commis Chef"

        self.image = pygame.Surface((self.w, self.h))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.midleft = (self.x, self.y)
        self.contents = []

        #self.contents.append(StaffSprite(self.x + 30, self.y, 40, 40, self.evManager, self.group))

        self.contents.append(Text(self.name, self.x + 60, self.y - 25, WHITE, 23, self.group))
        self.contents.append(Text(self.cuisine, self.x + 60, self.y, WHITE, 22, self.group))
        self.contents.append(Text("Wage/Week:", self.x + 220, self.y - 25, WHITE, 22, self.group))
        self.contents.append(Text("$" + str(CHEF_SALARY[self.level]), self.x + 370, self.y - 14, WHITE, 22, self.group, TEXT_RIGHT))
        self.contents.append(Text("Hire Cost:", self.x + 220, self.y, WHITE, 22, self.group))
        self.contents.append(Text("$" + str(CHEF_SALARY[self.level] * 2), self.x + 370, self.y + 10, WHITE, 22, self.group, TEXT_RIGHT))

        self.contents.append(HireButton(self.x + 450, self.y, 50, 20, self, self.evManager, self.group))


class MyWaiterContainer(pygame.sprite.Sprite):
    def __init__(self, x, y, waiter, evManager, group=None, popUp=None):
        self.evManager = evManager
        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.waiter = waiter
        self.level = waiter.level
        self.popUp = popUp
        self.type = "Waiter"

        self.name = str(self.waiter)

        self.image = pygame.Surface((55, 70))
        self.image.fill(LIGHT_BLUE)

        self.x = x
        self.y = y
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

        self.contents = []

        self.sprite = StaffSprite(self.x, self.y - 8, 50, 50, self.evManager, self.group, self.waiter)
        self.contents.append(self.sprite)
        self.contents.append(Text(str(self.waiter.level), self.x, self.y + 30, BLACK, 20, self.group, TEXT_CENTER))

    def Draw(self):
        self.popUp.empty()
        WaiterDetail(self.waiter, self.evManager, self.popUp)

    def Clicked(self):
        ev = GUIRequestPopUpEvent(self.name, self.Draw)
        self.evManager.Post(ev)


class HireWaiterContainer(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, level, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.group = group
        self.staffType = "Waiter"

        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.level = level
        self.name = None

        if self.level == 3:
            self.name = "Highly-Trained"
        elif self.level == 2:
            self.name = "Well-Trained"
        elif self.level == 1:
            self.name = "Basic-Trained"
        elif self.level == 0:
            self.name = "Untrained"

        self.image = pygame.Surface((self.w, self.h))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.midleft = (self.x, self.y)
        self.contents = []

        #self.contents.append(StaffSprite(self.x + 30, self.y - 30, 40, 40, self.evManager, self.group))

        self.contents.append(Text(self.name, self.x + 60, self.y - 45, WHITE, 26, self.group))
        self.contents.append(Text("Wage/Week:", self.x + 60, self.y, WHITE, 24, self.group))
        self.contents.append(Text("$" + str(WAITER_SALARY[self.level]), self.x + 180, self.y, WHITE, 24, self.group))
        self.contents.append(Text("Hire Cost:", self.x + 60, self.y + 25, WHITE, 24, self.group))
        self.contents.append(Text("$" + str(WAITER_SALARY[self.level] * 2), self.x + 180, self.y + 25, WHITE, 24, self.group))

        self.contents.append(HireButton(self.x + 290, self.y + 25, 50, 50, self, self.evManager, self.group))


class HireButton(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, container, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.group = group
        self.container = container

        self.x = x
        self.y = y
        self.w = w
        self.h = h

        self.image = pygame.Surface((self.w, self.h))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

    def Clicked(self):
        if self.container.staffType == "Chef":
            ev = HireChefEvent(self.container.level, self.container.cuisine)
            self.evManager.Post(ev)

        elif self.container.staffType == "Waiter":
            ev = HireWaiterEvent(self.container.level)
            self.evManager.Post(ev)

        ev = StaffUpdateRequestEvent()
        self.evManager.Post(ev)


# RESTAURANT LEVEL & UPGRADE -----------------------------------------------------------------------------------------


class RestaurantTab(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None, popUp=None):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        self.name = "Restaurant Window"

        pygame.sprite.Sprite.__init__(self, group)
        self.image = SPRITES["UpgradeIcon"]
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH * 56.7 / 100, SCREEN_HEIGHT * 78 / 100)

        self.popUp = popUp

        self.level = None
        self.nextLevel = None
        self.operatingCost = None
        self.upgradeLevelCost = None
        self.operatingCostDiff = None

    def Draw(self):
        self.popUp.empty()
        RestaurantDetail(self, self.evManager, self.popUp)

    def Hover(self):
        text = "Upgrade Restaurant"
        ev = GUITooltipEvent(text)
        self.evManager.Post(ev)

    def Clicked(self):
        ev = GUIRequestPopUpEvent(self.name, self.Draw)
        self.evManager.Post(ev)

    def Notify(self, event):
        if isinstance(event, RestaurantUpdateEvent):
            self.level = event.level
            self.operatingCost = event.operatingCost

            upgrades = event.upgrades
            self.nextLevel = upgrades.NextLevel(event.player)
            self.upgradeLevelCost = upgrades.UpgradeLevelCost(event.player)
            self.operatingCostDiff = upgrades.OperatingCost(self.nextLevel) - self.operatingCost

            ev = GUIRequestPopUpRedrawEvent(self.name, self.Draw)
            self.evManager.Post(ev)


class RestaurantDetail(pygame.sprite.Sprite):
    def __init__(self, parent, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.group = group
        self.parent = parent

        self.image = pygame.Surface((230, 380))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH * 9 / 100, SCREEN_HEIGHT * 36.5 / 100)

        Text("Restaurant Level:", self.rect.centerx, self.rect.top + 60, BLACK, 25, self.group, TEXT_CENTER)
        Text(str(self.parent.level), self.rect.centerx, self.rect.top + 90, BLACK, 25,
             self.group, TEXT_CENTER)

        Text("Operating Cost:", self.rect.centerx, self.rect.top + 120, BLACK, 25, self.group, TEXT_CENTER)
        Text(str(self.parent.operatingCost), SCREEN_WIDTH * 8.5 / 100, self.rect.top + 140, BLACK, 25,
             self.group, TEXT_CENTER)

        Text("UPGRADE", self.rect.centerx, self.rect.top + 165, BLACK, 27, self.group, TEXT_CENTER)

        self.upgradeDetail = UpgradeDetail(self.parent, self.evManager, self.group)

        x = self.rect.right - 20
        y = self.rect.top + 20

        self.closeButton = CloseButton(x, y, self.evManager, self.group)



class UpgradeDetail(pygame.sprite.Sprite):
    def __init__(self, parent, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.group = group
        self.parent = parent

        self.image = pygame.Surface((200, 190))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH * 9 / 100, SCREEN_HEIGHT * 48 / 100)
        self.contents = []

        #UPGRADE LEVEL

        Text("Level:", self.rect.left + 40, self.rect.top + 10, BLACK, 23, self.group)
        Text(str(self.parent.level), self.rect.left + 95, self.rect.top + 17.5, BLACK, 25, self.group, TEXT_CENTER)

        if not self.parent.level == self.parent.nextLevel:
            # TODO: Replace with Arrow Sprite
            Text("-->", self.rect.left + 120, self.rect.top + 17, BLACK, 25, self.group, TEXT_CENTER)
            Text(str(self.parent.nextLevel), self.rect.left + 145, self.rect.top + 17, BLACK, 25, self.group, TEXT_CENTER)

            Text("Upgrade Cost", self.rect.centerx, self.rect.top + 45, BLACK, 25, self.group, TEXT_CENTER)
            Text("$" + str(self.parent.upgradeLevelCost), self.rect.centerx, self.rect.top + 70, BLACK, 25,
                 self.group, TEXT_CENTER)

            Text("Add. Operating Cost", self.rect.centerx, self.rect.top + 100, BLACK, 25, self.group, TEXT_CENTER)
            Text("+$" + str(self.parent.operatingCostDiff), self.rect.centerx, self.rect.top + 125, BLACK, 25,
                 self.group, TEXT_CENTER)

            UpgradeButton(SCREEN_WIDTH * 9 / 100, self.rect.top + 160, self, "level", self.evManager, self.group)
            Text("Upgrade", self.rect.centerx, self.rect.top + 160, WHITE, 25, self.group, TEXT_CENTER)
        else:
            Text("Max Level", self.rect.centerx, self.rect.top + 45, BLACK, 25, self.group, TEXT_CENTER)


class UpgradeButton(pygame.sprite.Sprite):
    def __init__(self, x, y, parent, type, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.evManager = evManager
        self.type = type
        self.x = x
        self.y = y
        self.parent = parent

        self.image = pygame.Surface((90, 25))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

    def Clicked(self):
        if self.type == "level":
            ev = UpgradeLevelEvent()
            self.evManager.Post(ev)

        elif self.type == "capacity":
            ev = UpgradeCapacityEvent()
            self.evManager.Post(ev)



# MAIN UI: Menu, Inventory ---------------------------------------------------------------------------------------------


class MenuTab(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None, popUp=None):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        self.group = group
        self.popUp = popUp

        pygame.sprite.Sprite.__init__(self, group)
        self.image = pygame.Surface((500, 200))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH * 20 / 100, SCREEN_HEIGHT * 85 / 100)

        self.contents = []

    def UpdateDishes(self, dishes):
        x = self.rect.left + 33
        y = self.rect.top + 30
        i = 0
        for dish in dishes:
            self.contents.append(MenuDishContainer(x, y + 8, dish, self.evManager, self.group, self.popUp))
            x += 48

            i += 1
            if i >= 10:
                x = self.rect.left + 33
                y += 70
                i = 0


    def Notify(self, event):
        if isinstance(event, MenuUpdateEvent):
            for sprite in self.contents:
                try:
                    for s in sprite.contents:
                        s.kill()
                except AttributeError:
                    pass
                sprite.kill()
            self.contents = []
            self.UpdateDishes(event.dishes)


class MenuDishContainer(pygame.sprite.Sprite):
    def __init__(self, x, y, dish, evManager, group=None, popUp=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager

        self.x = x
        self.y = y
        self.dish = dish['dish']
        self.name = self.dish.name
        self.group = group
        self.popUp = popUp
        self.price = dish['price']

        self.image = pygame.Surface((45, 60))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        self.contents = []

        self.contents.append(DishSprite(self.x, self.y - 7, self.dish, self.group))
        self.contents.append(Text("$" + " " + str(self.price), self.x, self.y + 23, BLACK, 20, self.group, TEXT_CENTER))

    def Draw(self):
        self.popUp.empty()
        DishDetail(self.dish, self.evManager, self.popUp)

    def Clicked(self):
        ev = GUIRequestPopUpEvent(self.name, self.Draw)
        self.evManager.Post(ev)


class InventoryTab(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None, popUp=None):
        self.evManager = evManager
        self.evManager.RegisterListener(self)
        self.group = group
        self.popUp = popUp

        pygame.sprite.Sprite.__init__(self, group)
        self.image = pygame.Surface((500, 200))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH * 80 / 100, SCREEN_HEIGHT * 85 / 100)

        self.inventory = []
        self.contents = []
        self.page = 1
        self.maxPage = 1

        PrevPage(self.rect.right - 50, self.rect.centery - 50, 50, 50, self, group)
        self.pageDisplay = Numbers(self, "page", self.rect.right - 60, self.rect.centery, WHITE, 24,
                                   self.group)
        Text("/", self.rect.right - 50, self.rect.centery, WHITE, 32, self.group, TEXT_CENTER)
        self.maxPageDisplay = Numbers(self, "maxPage", self.rect.right - 40, self.rect.centery, WHITE, 24,
                                      self.group, TEXT_LEFT)
        NextPage(self.rect.right - 50, self.rect.centery + 50, 50, 50, self, group)

    def Update(self):
        self.pageDisplay.Update()
        self.maxPageDisplay.Update()

        for sprite in self.contents:
            self.evManager.UnregisterListener(sprite)
            try:
                for s in sprite.contents:
                    s.kill()
            except AttributeError:
                pass
            sprite.kill()
        self.contents = []

        x = self.rect.left + 33
        y = self.rect.top + 30

        baseIndex = (self.page - 1) * 16
        for i in range(16):
            try:
                ingredient = self.inventory[i + baseIndex]
                self.contents.append(InventoryItemContainer(x, y + 8, ingredient, self.evManager, self.group, self.popUp))
                x += 48

                if i == 7:
                    x = self.rect.left + 33
                    y += 70
            except IndexError:
                break

    def Notify(self, event):
        if isinstance(event, InventoryUpdateEvent):
            for sprite in self.contents:
                self.evManager.UnregisterListener(sprite)
                try:
                    for s in sprite.contents:
                        s.kill()
                except AttributeError:
                    pass
                sprite.kill()
            self.contents = []

            self.inventory = event.inventory

            self.maxPage = math.ceil(len(self.inventory) / 16)
            if self.maxPage <= 0:
                self.maxPage = 1
            if self.page > self.maxPage:
                self.page = self.maxPage

            self.Update()



class InventoryItemContainer(pygame.sprite.Sprite):
    def __init__(self, x, y, item, evManager, group=None, popUp=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        self.x = x
        self.y = y

        self.group = group
        self.popUp = popUp
        self.item = item

        self.name = item.name

        self.image = pygame.Surface((45, 60))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        self.contents = []
        self.amount = self.item.amount

        self.contents.append(IngredientSprite(self.x, self.y - 7, self.item,self.evManager, self.group))
        self.contents.append(Numbers(self, "amount", self.x, self.y + 20, WHITE, 18, self.group, TEXT_CENTER))

        self.amounts = []

    def Draw(self):
        self.popUp.empty()
        InventoryItemDetail(self, self.item, self.evManager, self.popUp)

    def Clicked(self):
        ev = RequestIngredientAmountEvent(self.item)
        self.evManager.Post(ev)

        ev = GUIRequestPopUpEvent(self.name, self.Draw)
        self.evManager.Post(ev)

    def Notify(self, event):
        if isinstance(event, ReturnIngredientAmountEvent):
            if self.item.name == event.ingredient.name:
                self.amounts = [sum(x) for x in zip(event.amount, event.expire)]

                ev = GUIRequestWindowRedrawEvent(self.name, self.Draw)
                self.evManager.Post(ev)

        elif isinstance(event, BuyIngredientsEvent):
            ev = RequestIngredientAmountEvent(self.item)
            self.evManager.Post(ev)

        elif isinstance(event, SalesReportEvent):
            ev = RequestIngredientAmountEvent(self.item)
            self.evManager.Post(ev)


class InventoryItemDetail(pygame.sprite.Sprite):
    def __init__(self, parent, item, evManager, group=None):
        self.evManager = evManager

        self.parent = parent
        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.item = item
        self.x = SCREEN_WIDTH * 9 / 100
        self.y = SCREEN_HEIGHT * 37 / 100
        self.w = 230
        self.h = 350

        self.image = pygame.Surface((self.w, self.h))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

        self.contents = []

        x = self.rect.right - 20
        y = self.rect.top + 20
        self.closeButton = CloseButton(x, y, self.evManager, self.group)

        IngredientSprite(self.x, self.y - 110, self.item, self.evManager, self.group)
        Text(self.item.name, self.x, self.y - 80, BLACK, 25, self.group, TEXT_CENTER)
        Text("Stock:", self.x - 110, self.y - 70, BLACK, 25, self.group)

        Text("Quality", self.x - 100, self.y - 53, BLACK, 22, self.group)
        Text("Amount", self.x - 30, self.y - 53, BLACK, 22, self.group)

        y = self.y - 32
        for q in reversed(range(1, 6)):
            Text(str(q), self.x - 75, y, BLACK, 22, self.group)
            y += 20

        for sprite in self.contents:
            sprite.kill()
        self.contents = []

        y = self.y - 32
        for amount in self.parent.amounts:
            self.contents.append(Text(str(amount), self.x - 30, y, BLACK, 22, self.group))
            y += 20


# MAIN UI: Add Dish, Market, Marketing -------------------------------------------------------------------------------


class MidTab(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None):
        self.evManager = evManager

        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.image = pygame.Surface((170, 200))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH * 54 / 100, SCREEN_HEIGHT * 85 / 100)



      
# MARKETING ------------------------------------------------------------------------------------------------

class MarketingButton(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None, windowGroup=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.evManager.RegisterListener(self)
        self.name = "Marketing Window"

        self.x = SCREEN_WIDTH * 56.7 / 100
        self.y = SCREEN_HEIGHT * 90 / 100
        self.image = SPRITES["Marketing"]
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        self.windowGroup = windowGroup

        self.activeBonuses = []


    def Draw(self):
        self.windowGroup.empty()
        MarketingWindow(self, self.evManager, self.windowGroup)

    def Clicked(self):
        ev = GUIRequestWindowEvent(self.name, self.Draw)
        self.evManager.Post(ev)


    def Hover(self):
        text = "Promote Your Restaurant"
        ev = GUITooltipEvent(text)
        self.evManager.Post(ev)

    def Notify(self, event):
        if isinstance(event, MarketingUpdateEvent):
            self.activeBonuses = event.bonuses

            ev = GUIRequestWindowRedrawEvent(self.name, self.Draw)
            self.evManager.Post(ev)


class MarketingWindow:
    def __init__(self, parent, evManager, group=None):
        self.evManager = evManager
        self.parent = parent

        self.group = group
        self.window = MainWindow(PURPLE, self.evManager, self.group)

        x = SCREEN_WIDTH * 29.75 / 100
        y = SCREEN_HEIGHT * 26.5 / 100
        s = 0
        for strategy in MARKETING_LIST:
            MarketingContainer(x, y, strategy, self.parent, self.evManager, self.group)
            x += 260
            s += 1
            if s == 3:
                x = SCREEN_WIDTH * 29.75 / 100
                y += 170


class MarketingContainer(pygame.sprite.Sprite):
    def __init__(self, x, y, strategy, parent, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.x = x
        self.y = y
        self.evManager = evManager
        self.group = group
        self.parent = parent
        self.strategy = strategy

        self.image = pygame.Surface((250, 150))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

        Text("Cost: " + str(self.strategy.cost), self.rect.left + 10, self.y + 50, BLACK, 23, self.group)
        MarketingSprite(self.rect.centerx, self.rect.centery - 20, self.strategy, self.evManager, self.group)

        if self.strategy.name not in (bonus.name for bonus in self.parent.activeBonuses):
            StrategyButton(self.rect.right - 55, self.rect.bottom - 18, self.strategy, self.evManager, self.group)
        else:
            Text("ACTIVATED", *self.rect.center, RED, 50, self.group, TEXT_CENTER, bold=True)


class MarketingSprite(pygame.sprite.Sprite):
    def __init__(self, x, y, strategy, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.x = x
        self.y = y
        self.evManager = evManager
        self.group = group
        self.strategy = strategy

        self.image = MARKETING_SPRITES[self.strategy.name]
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)


class StrategyButton(pygame.sprite.Sprite):
    def __init__(self, x, y, strategy, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.x = x
        self.y = y
        self.evManager = evManager
        self.group = group
        self.strategy = strategy

        self.image = pygame.Surface((90, 35))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

        Text("Activate", *self.rect.center, BLACK, 25, self.group, TEXT_CENTER)

    def Clicked(self):
        ev = AddMarketingEvent(self.strategy)
        self.evManager.Post(ev)


# MENU CATALOGUE & ADD DISH TO PLAYER's MENUS ----------------------------------------------------------------

class AddDishButton(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None, popUp=None, windowGroup=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager

        self.name = "Add Dish Window"
        self.group = group
        self.popUp = popUp

        self.x = SCREEN_WIDTH * 50 / 100
        self.y = SCREEN_HEIGHT * 78 / 100
        self.image = SPRITES["Add_Dish"]
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        self.windowGroup = windowGroup

        self.cuisine = "Western"
        self.page = 1
        self.maxPage = math.ceil(len(WESTERN_DISHES) / 12)

    def Draw(self):
        self.windowGroup.empty()
        AddDishWindow(self, self.evManager, self.popUp, self.windowGroup)

    def Update(self):
        dishList = []
        if self.cuisine == "Western":
            dishList = WESTERN_DISHES
        elif self.cuisine == "Chinese":
            dishList = CHINESE_DISHES
        elif self.cuisine == "Korean":
            dishList = KOREAN_DISHES

        self.maxPage = math.ceil(len(dishList) / 12)

        ev = GUIRequestWindowRedrawEvent(self.name, self.Draw)
        self.evManager.Post(ev)

    def Clicked(self):
        ev = GUIRequestWindowEvent(self.name, self.Draw)
        self.evManager.Post(ev)

    def Hover(self):
        text = "Add Dish to Your Menu"
        ev = GUITooltipEvent(text)
        self.evManager.Post(ev)


class AddDishWindow:
    def __init__(self, parent, evManager, popUp=None, group=None):
        self.evManager = evManager
        self.parent = parent

        self.group = group
        self.window = MainWindow(BLUE, self.evManager, self.group)
        self.popUp = popUp
        self.tab = range(5)

        PrevPage(SCREEN_WIDTH * 78 / 100, SCREEN_HEIGHT * 30 / 100, 50, 50, self.parent, group)
        self.pageDisplay = Numbers(self.parent, "page", SCREEN_WIDTH * 77 / 100, SCREEN_HEIGHT * 38 / 100, WHITE, 24, self.group)
        Text("/", SCREEN_WIDTH * 78 / 100, SCREEN_HEIGHT * 38 / 100, WHITE, 32, self.group, TEXT_CENTER)
        self.maxPageDisplay = Numbers(self.parent, "maxPage", SCREEN_WIDTH * 79 / 100, SCREEN_HEIGHT * 38 / 100, WHITE, 24, self.group, TEXT_LEFT)
        NextPage(SCREEN_WIDTH * 78 / 100, SCREEN_HEIGHT * 46 / 100, 50, 50, self.parent, group)

        self.dishScreen = DishScreen(self.parent.page, self.parent.cuisine, self, self.evManager, self.popUp, group)

        x = SCREEN_WIDTH * 25 / 100
        y = SCREEN_HEIGHT * 17 / 100

        for cuisine in CUISINES_LIST:
            CuisineTab(x, y, cuisine, self.parent, self.evManager, group)
            y += 50


class CuisineTab(pygame.sprite.Sprite):
    def __init__(self, x, y, cuisine, window, evManager, group=None):
        self.evManager = evManager

        pygame.sprite.Sprite.__init__(self, group)
        self.cuisine = cuisine
        self.window = window
        self.group = group
        self.x = x
        self.y = y
        self.image = SPRITES[cuisine + "Cuisine"]
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

        Text(self.cuisine, *self.rect.center, WHITE, 25, self.group, TEXT_CENTER)

    def Clicked(self):
        self.window.page = 1
        self.window.cuisine = self.cuisine
        self.window.Update()


class DishScreen(pygame.sprite.Sprite):
    def __init__(self, page, cuisine, window, evManager, popUp=None, group=None):
        self.evManager = evManager

        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.popUp = popUp
        self.image = pygame.Surface((570, 350))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH * 53 / 100, SCREEN_HEIGHT * 36 / 100)

        self.cuisine = cuisine
        if self.cuisine == "Western":
            self.dishList = WESTERN_DISHES
        elif self.cuisine == "Chinese":
            self.dishList = CHINESE_DISHES
        elif self.cuisine == "Korean":
            self.dishList = KOREAN_DISHES

        self.dishContainers = []

        self.window = window
        self.page = page
        self.window.maxPage = math.ceil(len(self.dishList) / 12)
        self.window.maxPageDisplay.Update()

        x = SCREEN_WIDTH * 42 / 100
        y = SCREEN_HEIGHT * 17 / 100
        baseIndex = (self.page - 1) * 12
        for i in range(12):
            try:
                dish = self.dishList[i + baseIndex]
                if self.cuisine == dish.cuisine:
                    self.dishContainers.append(DishContainer(x, y, dish, self.cuisine, self.window, self.evManager,
                                                             self.popUp, group))
                    y += 55
                    if i == 5:
                        x += 280
                        y = SCREEN_HEIGHT * 17 / 100

            except IndexError:
                break


class DishSprite(pygame.sprite.Sprite):
    def __init__(self, x, y, dish, group=None, large=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.dish = dish
        self.x = x
        self.y = y
        if large:
            self.image = DISH_SPRITES[self.dish.name + " Large"]
        else:
            self.image = DISH_SPRITES[self.dish.name]
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)



class DishContainer(pygame.sprite.Sprite):
    def __init__(self, x, y, dish, cuisine, window, evManager, popUp=None, group=None):
        self.evManager = evManager

        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.popUp = popUp
        self.x = x
        self.y = y
        self.image = pygame.Surface((265, 50))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

        self.cuisine = cuisine
        self.dish = dish
        self.window = window
        self.contents = []
        self.name = dish.name

        self.contents.append(Text(self.dish.name, self.x - 75, self.y - 20, WHITE, 22, self.group))
        self.contents.append(DishSprite(self.x - 100, self.y, dish, self.group))

    def Draw(self):
        self.popUp.empty()
        DishDetail(self.dish, self.evManager, self.popUp)

    def Clicked(self):
        ev = GUIRequestPopUpEvent(self.name, self.Draw)
        self.evManager.Post(ev)


class DishDetail(pygame.sprite.Sprite):
    def __init__(self, dish, evManager, group=None):
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.dish = dish
        self.x = SCREEN_WIDTH * 9 / 100
        self.y = SCREEN_HEIGHT * 36.5 / 100
        self.w = 230
        self.h = 380

        self.image = pygame.Surface((self.w, self.h))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

        x = self.rect.right - 20
        y = self.rect.top + 20
        self.closeButton = CloseButton(x, y, self.evManager, self.group)

        self.price = 0 # For price
        self.contents = []

        DishSprite(self.x, self.y - 140, self.dish, self.group, large=True)
        Text(self.dish.name, self.x, self.y - 90, BLACK, 22, self.group, TEXT_CENTER, bold=True)

        Text("TYPE:", self.rect.left + 10, self.y - 60, BLACK, 22, self.group)
        Text(self.dish.type, self.rect.left + 17, self.y - 40, BLACK, 21, self.group)

        Text("CUISINE:", self.rect.left + 10, self.y - 10, BLACK, 22, self.group)
        Text(self.dish.cuisine, self.rect.left + 17, self.y + 10, BLACK, 21, self.group)

        Text("INGREDIENTS:", self.x - 20, self.y - 60, BLACK, 22, self.group)
        i = 40
        for ingredients in self.dish.ingredients:
            Text(ingredients.name, self.x - 13, self.y - i, BLACK, 21, self.group)
            i -= 17

        Text("Price:", self.x - 40, self.y + 120, BLACK, 22, self.group, TEXT_CENTER)
        ArrowLeft(self.x, self.y + 120, self, "price", self.group)
        ArrowRight(self.x + 60, self.y + 120, self, "price", self.group)
        self.priceDisplay = Numbers(self, "price", self.x + 30, self.y + 120, BLACK, 16, self.group, TEXT_CENTER)

        FindIngredients(self.x + 100, self.y - 60, dish, evManager, self.group)

        ev = GUICheckDishMenuEvent(self.dish, self)
        self.evManager.Post(ev)

    def Update(self):
        if self.price > 99999:
            self.price = 99999
        self.priceDisplay.Update()

    def Notify(self, event):
        if isinstance(event, GUICheckDishMenuResponseEvent):
            for sprite in self.contents:
                sprite.kill()

            self.contents = []

            if event.container is self:
                if event.dish:
                    self.price = event.dish['price']

                    self.contents.append(UpdateDishPrice(self.x - 50, self.y + 150, self.dish,
                                                         self, self.evManager, self.group))
                    self.contents.append(Text("Update Price", self.x - 50, self.y + 150, BLACK, 22, self.group, TEXT_CENTER))

                    self.contents.append(RemoveDish(self.x + 50, self.y + 150, self.dish,
                                                    self, self.evManager, self.group))
                    self.contents.append(Text("Remove Dish", self.x + 50, self.y + 150, WHITE, 22, self.group, TEXT_CENTER))

                else:
                    self.contents.append(AddToMenu(self.x, self.y + 150, self.dish, self, self.evManager, self.group))
                    self.contents.append(Text("Add To Menu ($" + str(ADD_DISH_COST) + ")", self.x, self.y + 150, WHITE, 22,
                                              self.group, TEXT_CENTER))
            self.Update()



class AddToMenu(pygame.sprite.Sprite):
    def __init__(self, x, y, dish, window, evManager, group=None):
        self.evManager = evManager
        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.dish = dish
        self.window = window

        self.x = x
        self.y = y
        self.image = pygame.Surface((200, 30))
        self.image.fill(PURPLE)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

    def Clicked(self):
        ev = AddDishEvent(self.dish, self.window.price)
        self.evManager.Post(ev)

        ev = GUICheckDishMenuEvent(self.dish, self.window)
        self.evManager.Post(ev)


class UpdateDishPrice(pygame.sprite.Sprite):
    def __init__(self, x, y, dish, window, evManager, group=None):
        self.evManager = evManager
        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.dish = dish
        self.window = window

        self.x = x
        self.y = y
        self.image = pygame.Surface((95, 30))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

    def Clicked(self):
        ev = UpdateDishPriceEvent(self.dish, self.window.price)
        self.evManager.Post(ev)

        ev = GUICheckDishMenuEvent(self.dish, self.window)
        self.evManager.Post(ev)


class RemoveDish(pygame.sprite.Sprite):
    def __init__(self, x, y, dish, window, evManager, group=None):
        self.evManager = evManager
        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.dish = dish
        self.window = window

        self.x = x
        self.y = y
        self.image = pygame.Surface((95, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

    def Clicked(self):
        self.window.price = 0

        ev = RemoveDishEvent(self.dish)
        self.evManager.Post(ev)

        ev = GUICheckDishMenuEvent(self.dish, self.window)
        self.evManager.Post(ev)


class FindIngredients(pygame.sprite.Sprite):
    def __init__(self, x, y, dish, evManager, group=None):
        self.evManager = evManager
        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.dish = dish

        self.x = x
        self.y = y
        self.image = SPRITES["FindIngredients"]
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

    def Clicked(self):
        ev = GUIDishSpecificMarketEvent(self.dish)
        self.evManager.Post(ev)

    def Hover(self):
        text = "Find Ingredients"
        ev = GUITooltipEvent(text)
        self.evManager.Post(ev)


# MARKET: BUY INGREDIENT into INVENTORY -------------------------------------------------------------------------------


class MarketButton(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None, windowGroup=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.evManager.RegisterListener(self)
        self.name = "Market Window"
        self.group = group

        self.x = SCREEN_WIDTH * 50 / 100
        self.y = SCREEN_HEIGHT * 90 / 100
        self.image = SPRITES["Market"]
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        self.windowGroup = windowGroup

        self.dish = None
        self.quality = 1

        self.ingredients = INGREDIENTS_LIST[:]

        self.cart = []
        self.totalPrice = 0

        self.page = 1
        self.maxPage = math.ceil(len(INGREDIENTS_LIST) / 10)
        self.cartPage = 1
        self.cartMaxPage = 1

    def Draw(self):
        self.windowGroup.empty()
        MarketWindow(self, self.evManager, self.windowGroup)
        CartScreen(self, self.evManager, self.windowGroup)
        self.ingredients = INGREDIENTS_LIST[:]

    def Redraw(self):
        self.windowGroup.empty()
        MarketWindow(self, self.evManager, self.windowGroup)
        CartScreen(self, self.evManager, self.windowGroup)

    def Update(self):
        ev = GUIRequestWindowRedrawEvent(self.name, self.Redraw)
        self.evManager.Post(ev)

    def Clicked(self):
        ev = GUIRequestWindowEvent(self.name, self.Draw)
        self.evManager.Post(ev)

    def Notify(self, event):
        if isinstance(event, CartUpdateEvent):
            self.cart = event.cart
            self.totalPrice = event.price

            self.cartMaxPage = math.ceil(len(self.cart) / 16)
            if self.cartMaxPage <= 0:
                self.cartMaxPage = 1
            if self.cartPage > self.cartMaxPage:
                self.cartPage = self.cartMaxPage

            ev = GUIRequestWindowRedrawEvent(self.name, self.Redraw)
            self.evManager.Post(ev)

        elif isinstance(event, GUIDishSpecificMarketEvent):
            self.dish = event.dish

            ev = GUIRequestWindowEvent(self.name, self.Draw)
            self.evManager.Post(ev)

            ev = GUIRequestWindowRedrawEvent(self.name, self.Redraw)
            self.evManager.Post(ev)

    def Hover(self):
        text = "Open Market"
        ev = GUITooltipEvent(text)
        self.evManager.Post(ev)


class MarketWindow:
    def __init__(self, parent, evManager, group=None):
        self.evManager = evManager

        self.parent = parent
        self.group = group

        self.window = MainWindow(GREEN, self.evManager, self.group)
        self.tab = range(5)

        x = SCREEN_WIDTH * 25 / 100
        y = SCREEN_HEIGHT * 15 / 100
        qualityNumber = 1

        # Instantiate Sprite in the window.
        self.ingredientScreen = IngredientScreen(self.parent, self.evManager, self.group)
        PrevPage(SCREEN_WIDTH * 75 / 100, SCREEN_HEIGHT * 30 / 100, 50, 50, self.parent, self.group)
        self.pageDisplay = Numbers(self.parent, "page", SCREEN_WIDTH * 74 / 100, SCREEN_HEIGHT * 38 / 100, WHITE, 24, self.group)
        Text("/", SCREEN_WIDTH * 75 / 100, SCREEN_HEIGHT * 38 / 100, WHITE, 32, self.group, TEXT_CENTER)
        self.maxPageDisplay = Numbers(self.parent, "maxPage", SCREEN_WIDTH * 76 / 100, SCREEN_HEIGHT * 38 / 100, WHITE, 24, self.group, TEXT_LEFT)
        NextPage(SCREEN_WIDTH * 75 / 100, SCREEN_HEIGHT * 46 / 100, 50, 50, self.parent, self.group)

        for tab in self.tab:
            imageName = str(qualityNumber) + "quality"
            image = SPRITES[imageName]
            QualityTab(x, y, image, qualityNumber, self, self.evManager, group)
            x += 110
            qualityNumber += 1

    def UpdateQuality(self):
        for container in self.ingredientScreen.ingredientContainers:
            container.Update()

    def Update(self):
        self.ingredientScreen.kill()
        for container in self.ingredientScreen.ingredientContainers:
            self.group.remove(contents for contents in container.contents)
            container.kill()

        self.ingredientScreen.ingredientContainers = []
        self.ingredientScreen = None
        self.ingredientScreen = IngredientScreen(self.parent, self.evManager, self.group)

        self.pageDisplay.Update()
        self.maxPageDisplay.Update()


class QualityTab(pygame.sprite.Sprite):
    def __init__(self, x, y, image, quality, window, evManager, group=None):
        self.evManager = evManager

        pygame.sprite.Sprite. __init__(self, group)
        self.window = window
        self.group = group
        self.x = x
        self.y = y
        self.image = image
        self.quality = quality
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

        stars = SPRITES[str(self.quality) + "QualityStar"]
        self.image.blit(stars, (15, 8))

    def Clicked(self):
        self.window.parent.quality = self.quality
        self.window.UpdateQuality()


class IngredientScreen(pygame.sprite.Sprite):
    def __init__(self, parent, evManager, group=None):
        self.evManager = evManager

        pygame.sprite.Sprite.__init__(self, group)
        self.imageName = "Container"
        self.image = SPRITES[self.imageName]
        self.group = group
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH * 46.5 / 100, SCREEN_HEIGHT * 38 / 100)
        self.ingredientContainers = []

        self.parent = parent

        x = SCREEN_WIDTH * 34 / 100
        y = SCREEN_HEIGHT * 22.5 / 100

        if self.parent.dish:
            for i in range(8):
                try:
                    ingredient = self.parent.dish.ingredients[i]
                    self.ingredientContainers.append(IngredientContainer(x, y, ingredient, self.parent, self.evManager,
                                                                         group))
                    y += 55
                    if i == 3:
                        x += 315
                        y = SCREEN_HEIGHT * 22.5 / 100
                except IndexError:
                    break

            y = SCREEN_HEIGHT * 22.5 / 100
            DishFocus(self.rect.centerx, y + 220, self.parent.dish, self.ingredientContainers,
                          self.parent, self.evManager, group)

        else:
            baseIndex = (self.parent.page - 1) * 10
            for i in range(10):
                try:
                    ingredient = self.parent.ingredients[i + baseIndex]
                    self.ingredientContainers.append(IngredientContainer(x, y, ingredient, self.parent, self.evManager,
                                                                         group))
                    y += 55
                    if i == 4:
                        x += 315
                        y = SCREEN_HEIGHT * 22.5 / 100
                except IndexError:
                    break


class DishFocus(pygame.sprite.Sprite):
    def __init__(self, x, y, dish, containers, window, evManager, group=None):
        self.evManager = evManager

        pygame.sprite.Sprite.__init__(self, group)
        self.dish = dish
        self.x = x
        self.y = y
        self.group = group
        self.image = pygame.Surface((620, 50))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        self.window = window
        self.contents = []

        self.ingredients = []
        for container in containers:
            if container is not self:
                self.ingredients.append(container)
        self.quantity = 0

        self.contents.append(Text("Focus:", self.rect.left + 10, self.rect.top + 15, WHITE, 28, self.group))
        self.contents.append(DishSprite(self.rect.left + 100, self.rect.centery, self.dish, self.group))
        self.contents.append(Text(self.dish.name, self.rect.left + 130, self.rect.top + 15, WHITE, 22, self.group))

        self.contents.append(ResetMarketButton(self.rect.right - 30, self.y, self.window, evManager, self.group))
        self.contents.append(ArrowLeft(self.x + 50, self.y, self, "quantity", self.group, multiply=10, override=True))
        self.contents.append(Text("All Amounts", self.x + 105, self.rect.centery, WHITE, 22, self.group, TEXT_CENTER))
        self.contents.append(ArrowRight(self.x + 160, self.y, self, "quantity", self.group, multiply=10))
        self.contents.append(DishFocusAddCart(self.x + 220, self.y, self, self.evManager, self.group))

    def Update(self):
        for container in self.ingredients:
            container.ingredient.amount += self.quantity
            container.Update()

        self.quantity = 0


class DishFocusAddCart(pygame.sprite.Sprite):
    def __init__(self, x, y, window, evManager, group=None):
        self.evManager = evManager
        pygame.sprite.Sprite.__init__(self, group)
        self.x = x
        self.y = y
        self.group = group
        self.image = SPRITES["Add_to_Cart"]
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        self.window = window

    def Clicked(self):
        for container in self.window.ingredients:
            if container.ingredient.amount > 0:
                ev = AddToCartEvent(container.ingredient, container.quality, container.ingredient.amount)

                container.ingredient.amount = 0
                container.Update()

                self.evManager.Post(ev)


class ResetMarketButton(pygame.sprite.Sprite):
    def __init__(self, x, y, parent, evManager, group=None):
        self.evManager = evManager
        pygame.sprite.Sprite.__init__(self, group)
        self.x = x
        self.y = y
        self.group = group
        self.image = SPRITES["Close_Button"]
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        self.parent = parent

    def Clicked(self):
        self.parent.dish = None
        self.parent.Update()


class IngredientContainer(pygame.sprite.Sprite):
    def __init__(self, x, y, ingredient, parent, evManager, group=None):
        self.evManager = evManager

        pygame.sprite.Sprite.__init__(self, group)
        self.ingredient = ingredient
        self.x = x
        self.y = y
        self.group = group
        self.image = pygame.Surface((300, 50))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        self.parent = parent
        self.contents = []
        self.quantity = 0
        self.quality = self.parent.quality
        self.price = "$" + str(self.ingredient.Price(self.quality))

        self.ingredientQuantity = Numbers(self.ingredient, "amount", self.x + 105, self.y - 13, WHITE, 16, self.group, TEXT_CENTER)
        self.ingredientPrice = Numbers(self, "price", self.x + 30, self.y + 5, WHITE, 19, self.group)
        self.contents.append(Text(" / unit", self.x + 30, self.y + 5, WHITE, 19, self.group))

        self.contents.append(Text(self.ingredient.name, self.x - 95, self.y - 20, WHITE, 21, self.group))
        self.contents.append(IngredientSprite(self.x - 120, self.y, ingredient, self.evManager, self.group))

        self.contents.append(self.ingredientQuantity)
        self.contents.append(self.ingredientPrice)

        self.contents.append(ArrowLeft(self.x + 75, self.y - 10,  self, "quantity", self.group, multiply=10, override=True))
        self.contents.append(ArrowRight(self.x + 135, self.y - 10,  self, "quantity", self.group, multiply=10))
        self.contents.append(AddToCart(self.x + 105, self.y + 10, self, self.evManager, self.group))

        self.displayQuality = QualityStar(self.x - 55, self.y + 5, self.group, str(self.quality))

    def Update(self):
        self.quality = self.parent.quality

        self.ingredient.amount += self.quantity
        if self.ingredient.amount < 0:
            self.ingredient.amount = 0
        elif self.ingredient.amount > 99990:
            self.ingredient.amount = 99990
        self.quantity = 0

        self.ingredientQuantity.Update()

        self.displayQuality.kill()
        self.displayQuality = QualityStar(self.x - 55, self.y + 5, self.group, str(self.quality))

        self.price = "$" + str(self.ingredient.Price(self.quality))
        self.ingredientPrice.Update()


class QualityStar(pygame.sprite.Sprite):
    def __init__(self, x, y, group=None, type=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.x = x
        self.y = y
        self.group = group
        self.type = type
        self.image = SPRITES[self.type + "QualityStar"]

        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)


class IngredientSprite(pygame.sprite.Sprite):
    def __init__(self, x, y, ingredient, evManager, group=None):
        self.evManager = evManager

        pygame.sprite.Sprite.__init__(self, group)
        self.ingredient = ingredient
        self.x = x
        self.y = y
        #self.image = pygame.Surface((40, 40))
        #self.image.fill(BLACK)
        self.image = INGREDIENT_SPRITES[self.ingredient.name]
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)


class AddToCart(pygame.sprite.Sprite):
    def __init__(self, x, y, container, evManager, group=None):
        self.evManager = evManager

        pygame.sprite.Sprite.__init__(self, group)
        self.x = x
        self.y = y
        self.container = container
        self.group = group
        self.image = SPRITES["Add_to_Cart"]
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

    def Clicked(self):
        if self.container.ingredient.amount > 0:
            ev = AddToCartEvent(self.container.ingredient, self.container.quality, self.container.ingredient.amount)

            self.container.ingredient.amount = 0
            self.container.Update()

            self.evManager.Post(ev)



    def Hover(self):
        text = "Add to Cart"
        ev = GUITooltipEvent(text)
        self.evManager.Post(ev)


class CartScreen(pygame.sprite.Sprite):
    def __init__(self, parent, evManager, group=None):
        self.evManager = evManager

        pygame.sprite.Sprite.__init__(self, group)
        self.x = SCREEN_WIDTH * 88.5 / 100
        self.y = SCREEN_HEIGHT * 38 / 100
        self.parent = parent
        self.group = group
        self.image = pygame.Surface((260, 320))
        self.image.fill(PURPLE)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

        self.contents = []

        Text("Total:  $ " + str(self.parent.totalPrice), self.rect.left + 10, self.rect.bottom - 65, WHITE, 25, self.group)
        BuyButton(self.rect.centerx + 25, self.rect.bottom - 25, self.parent, self.evManager, self.group)
        ClearButton(self.rect.centerx - 75, self.rect.bottom - 25, self.evManager, self.group)

        PrevPage(self.rect.right - 30, self.rect.centery - 50, 50, 50, self.parent, group, "cartPage")
        self.pageDisplay = Numbers(self.parent, "cartPage", self.rect.right - 40, self.rect.centery, WHITE, 24,
                                   self.group)
        Text("/", self.rect.right - 30, self.rect.centery, WHITE, 32, self.group, TEXT_CENTER)
        self.maxPageDisplay = Numbers(self.parent, "cartMaxPage", self.rect.right - 20, self.rect.centery, WHITE, 24,
                                      self.group, TEXT_LEFT)
        NextPage(self.rect.right - 30, self.rect.centery + 50, 50, 50, self.parent, group, "cartPage", "cartMaxPage")

        x = self.rect.left + 25
        y = self.rect.top + 30

        baseIndex = (self.parent.cartPage - 1) * 16
        for i in range(16):
            try:
                item = self.parent.cart[i + baseIndex]
                self.contents.append(ItemContainer(x, y, item, self, self.evManager, self.group))
                x += 45
                if i in (3, 7, 11):
                    x = self.rect.left + 25
                    y += 60
            except IndexError:
                break


class ItemContainer(pygame.sprite.Sprite):
    def __init__(self, x, y, item, window, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager

        self.x = x
        self.y = y
        self.item = item
        self.window = window
        self.group = group

        self.image = pygame.Surface((50, 20))
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        self.contents = []

        self.contents.append(ItemSprite(self.x, self.y, self.item, self.evManager, self.group))
        self.contents.append(CartQuality(self.x, self.y - 18, self.item.quality, self.group))
        self.contents.append(Text(str(self.item.amount), self.x, self.y + 25, WHITE, 18, self.group, TEXT_CENTER))

    def Clicked(self):
        ev = RemoveFromCartEvent(self.item)
        self.evManager.Post(ev)


class ItemSprite(IngredientSprite):
    def __init__(self, x, y, item, evManager, group=None):
        super().__init__(x, y, item, evManager, group)
        self.evManager = evManager

    def Hover(self):
        text = self.item.name
        ev = GUITooltipEvent(text)
        self.evManager.Post(ev)

class CartQuality(pygame.sprite.Sprite):
    def __init__(self, x, y, quality, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager

        self.quality = quality

        self.image = SPRITES["CartQuality" + str(self.quality)]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)


class BuyButton(pygame.sprite.Sprite):
    def __init__(self, x, y, parent, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.group = group
        self.x = x
        self.y = y
        self.parent = parent

        self.image = pygame.Surface((90, 25))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

        Text("Buy", self.rect.centerx, self.rect.centery, BLACK, 25, self.group, TEXT_CENTER)

    def Clicked(self):
        ev = BuyIngredientsEvent(self.parent.cart, self.parent.totalPrice)
        self.evManager.Post(ev)


class ClearButton(pygame.sprite.Sprite):
    def __init__(self, x, y, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.group = group
        self.x = x
        self.y = y

        self.image = pygame.Surface((90, 25))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

        Text("Clear", self.rect.centerx, self.rect.centery, WHITE, 25, self.group, TEXT_CENTER)

    def Clicked(self):
        ev = ClearCartEvent()
        self.evManager.Post(ev)


 # TREND PopUp --------------------------------------------------------------------------------------------------


class TrendNews(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager
        self.evManager.RegisterListener(self)

        self.evManager = evManager
        self.trend = None
        self.group = group

        x = SCREEN_WIDTH * 50 / 100
        y = SCREEN_HEIGHT * 68 / 100
        self.image = pygame.Surface((1270, 40))
        self.image.fill(PINK)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.text = None
        self.dynamic = None

    def Notify(self, event):
        if isinstance(event, SetTrendEvent):
            try:
                self.dynamic.kill()
                self.dynamic = None
            except AttributeError:
                pass

            self.trend = event.trend
            if self.trend in DISHES_LIST:
                self.text = self.trend.name
            else:
                self.text = self.trend

            self.dynamic = DynamicText(self.text, self.rect.centerx, self.rect.centery, self, BLACK, 25, self.group)








