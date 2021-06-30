import pygame
import os
from .Constants import *
from .Events import *

# define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 230, 0)
BLUE = (0, 0, 255)
LIGHT_BLUE = (0, 150, 255)
YELLOW = (250, 250, 0)
PURPLE = (128, 0, 128)
PINK = (255, 182, 193)

fontName = 'Century Gothic'

imgFolder = os.path.join("asset")

class DynamicText(pygame.sprite.Sprite):
    def __init__(self, text, x, y, parent, color, fontSize, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.text = text
        self.color = color
        self.fontSize = fontSize
        self.parent = parent
        self.x = x
        self.y = y
        font = pygame.font.SysFont(fontName, 36)
        self.image = font.render(self.text, True, self.color)
        self.rect = self.image.get_rect()
        self.rect.midleft = (SCREEN_WIDTH, self.y)

    def Update(self):
        if self.rect.right > self.parent.rect.left:
            self.rect.move_ip(-1, 0)
        else:
            self.kill()
            self.parent.dynamic = None


class Text(pygame.sprite.Sprite):
    def __init__(self, text, x, y, color, fontSize, group=None, align=None, bold=False):
        pygame.sprite.Sprite.__init__(self, group)
        self.text = text
        self.color = color
        self.fontSize = fontSize - 8
        self.textFont = pygame.font.SysFont(fontName, self.fontSize, bold)
        self.image = self.textFont.render(self.text, True, self.color)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y

        if align is TEXT_CENTER:
            self.rect.center = (self.x, self.y)

        elif align is TEXT_RIGHT:
            self.rect.midright = (self.x, self.y)

        else:
            self.rect.x = self.x
            self.rect.y = self.y


class Numbers(pygame.sprite.Sprite):
    def __init__(self, parent, attribute, x, y, color, fontSize, group=None, align=None, bold=False):
        pygame.sprite.Sprite.__init__(self, group)
        self.color = color
        self.parent = parent
        self.attribute = attribute
        self.text = str(getattr(self.parent, self.attribute))
        self.fontSize = fontSize - 4
        self.align = align
        self.textFont = pygame.font.SysFont(fontName, self.fontSize, bold)
        self.image = self.textFont.render(self.text, True, self.color)
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y

        # Default alignment = right
        if self.align is TEXT_CENTER:
            self.rect.center = (self.x, self.y)
        elif self.align is TEXT_LEFT:
            self.rect.midleft = (self.x, self.y)
        else:
            self.rect.midright = (self.x, self.y)

    def Update(self):
        self.text = str(getattr(self.parent, self.attribute))
        self.image = self.textFont.render(self.text, True, self.color)
        self.rect = self.image.get_rect()

        if self.align is TEXT_CENTER:
            self.rect.center = (self.x, self.y)
        elif self.align is TEXT_LEFT:
            self.rect.midleft = (self.x, self.y)
        else:
            self.rect.midright = (self.x, self.y)


class Tooltip(pygame.sprite.Sprite):
    def __init__(self, text, pos, evManager, group=None):
        self.evManager = evManager
        self.group = group
        pygame.sprite.Sprite.__init__(self, self.group)

        (x,y) = pos

        self.text = Text(text, x + 2, y + 2, WHITE, 23, self.group)

        self.image = pygame.Surface((self.text.rect.w + 4, self.text.rect.h + 4))
        self.image.fill(BLACK)
        self.rect = self.image.get_rect()
        self.rect.topleft = pos


class MainWindow(pygame.sprite.Sprite):
    def __init__(self, color, evManager, group=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.evManager = evManager

        self.group = group
        self.color = color
        self.image = pygame.Surface((800, 380))
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2.75)

        x = SCREEN_WIDTH / 1.25
        y = SCREEN_HEIGHT / 8

        self.closeButton = CloseButton(x, y, self.evManager, self.group)


class CloseButton(pygame.sprite.Sprite):
    def __init__(self, x, y, evManager, group=None, window=None):
        self.evManager = evManager

        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.window = window
        self.x = x
        self.y = y

        self.image = SPRITES["Close_Button"]
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)

    def Clicked(self):
        ev = GUICloseWindowEvent(self.group)
        self.evManager.Post(ev)



class ArrowLeft(pygame.sprite.Sprite):
    def __init__(self, x, y, parent, attribute, group=None, multiply=None, override=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.x = x
        self.y = y
        self.image = SPRITES["Left_Arrow"]
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        self.parent = parent
        self.attribute = attribute
        self.multiply = multiply
        self.override = override

    def Clicked(self):
        value = getattr(self.parent, self.attribute)
        if self.multiply:
            value -= 1 * self.multiply
        else:
            value -= 1

        if value < 0 and not self.override:
            value = 0
        setattr(self.parent, self.attribute, value)
        self.parent.Update()

    def ShiftClicked(self):
        value = getattr(self.parent, self.attribute)
        if self.multiply:
            value -= 10 * self.multiply
        else:
            value -= 10

        if value < 0 and not self.override:
            value = 0
        setattr(self.parent, self.attribute, value)
        self.parent.Update()


    def CtrlClicked(self):
        value = getattr(self.parent, self.attribute)
        if self.multiply:
            value -= 100 * self.multiply
        else:
            value -= 100

        if value < 0 and not self.override:
            value = 0
        setattr(self.parent, self.attribute, value)
        self.parent.Update()



class ArrowRight(pygame.sprite.Sprite):
    def __init__(self, x, y, parent, attribute, group=None, multiply=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.x = x
        self.y = y
        self.image = SPRITES["Right_Arrow"]
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        self.parent = parent
        self.attribute = attribute
        self.multiply = multiply

    def Clicked(self):
        value = getattr(self.parent, self.attribute)
        if self.multiply:
            value += 1 * self.multiply
        else:
            value += 1
        setattr(self.parent, self.attribute, value)
        self.parent.Update()

    def ShiftClicked(self):
        value = getattr(self.parent, self.attribute)
        if self.multiply:
            value += 10 * self.multiply
        else:
            value += 10
        setattr(self.parent, self.attribute, value)
        self.parent.Update()

    def CtrlClicked(self):
        value = getattr(self.parent, self.attribute)
        if self.multiply:
            value += 100 * self.multiply
        else:
            value += 100
        setattr(self.parent, self.attribute, value)
        self.parent.Update()


class PrevPage(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, window, group=None, page=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.image = SPRITES["Previous_Page"]
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        self.window = window

        self.page = page

    def Clicked(self):
        if self.page:
            page = getattr(self.window, self.page)

            if page > 1:
                page -= 1
                setattr(self.window, self.page, page)
                self.window.Update()

        else:
            if self.window.page > 1:
                self.window.page -= 1
                self.window.Update()


class NextPage(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, window, group=None, page=None, maxPage=None):
        pygame.sprite.Sprite.__init__(self, group)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.image = SPRITES["Next_Page"]
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        self.window = window

        self.page = page
        self.maxPage = maxPage

    def Clicked(self):
        if self.page and self.maxPage:
            page = getattr(self.window, self.page)
            maxPage = getattr(self.window, self.maxPage)

            if page < maxPage:
                page += 1
                setattr(self.window, self.page, page)
                self.window.Update()

        else:
            if self.window.page < self.window.maxPage:
                self.window.page += 1
                self.window.Update()