import pygame
import os
from .ViewMisc import *
from .Events import *
from .Constants import *


class StartMenu(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None, new=None):
        self.evManager = evManager
        pygame.sprite.Sprite.__init__(self, group)
        self.image = SPRITES["startmenu"]
        self.rect = self.image.get_rect()

        if not new:
            ContinueButton(evManager, group)
        StartButton(evManager, group)
        QuitButton(evManager, group)


class ContinueButton(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None):
        self.evManager = evManager
        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.image = pygame.Surface((300, 50))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH * 0.5
        self.rect.centery = SCREEN_HEIGHT * 0.6

        Text("Continue Game", *self.rect.center, BLACK, 36, group, TEXT_CENTER)

    def Clicked(self):
        self.group.empty()
        ev = ContinueGameRequestEvent()
        self.evManager.Post(ev)


class StartButton(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None):
        self.evManager = evManager
        pygame.sprite.Sprite.__init__(self, group)
        self.group = group
        self.image = pygame.Surface((300, 50))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH * 0.5
        self.rect.centery = SCREEN_HEIGHT * 0.7

        Text("Start New Game", *self.rect.center, BLACK, 36, group, TEXT_CENTER)


    def Clicked(self):
        self.group.empty()
        ev = NewGameRequestEvent()
        self.evManager.Post(ev)


class QuitButton(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None):
        self.evManager = evManager
        pygame.sprite.Sprite.__init__(self, group)
        self.image = pygame.Surface((300, 50))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH * 0.5
        self.rect.centery = SCREEN_HEIGHT * 0.8

        Text("Quit", *self.rect.center, BLACK, 36, group, TEXT_CENTER)

    def Clicked(self):
        ev = QuitEvent()
        self.evManager.Post(ev)


class GameOverMenu(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None):
        self.evManager = evManager
        pygame.sprite.Sprite.__init__(self, group)
        self.image = SPRITES["closed"]
        self.rect = self.image.get_rect()


        Text("It's over...you've gone bankrupt!", self.rect.centerx, self.rect.centery + 100, BLACK, 60, group, TEXT_CENTER)
        FinishButton(evManager, group)


class FinishButton(pygame.sprite.Sprite):
    def __init__(self, evManager, group=None):
        self.evManager = evManager
        pygame.sprite.Sprite.__init__(self, group)
        self.image = pygame.Surface((300, 50))
        self.image.fill(PURPLE)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH * 0.5
        self.rect.centery = SCREEN_HEIGHT * 0.8

        Text("Finish", *self.rect.center, BLACK, 36, group, TEXT_CENTER)

    def Clicked(self):
        ev = GUIOpenStartMenuEvent(new=True)
        self.evManager.Post(ev)