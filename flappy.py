import pygame, random, time
from pygame.locals import *
import uuid
import os
from PIL import Image, ImageFilter
import numpy as np
from tensorflow import keras
from tensorflow.keras import layers
from numpy import asarray

ia_mode = True
if ia_mode:
    model = keras.models.load_model("../model")

# VARIABLES
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
SPEED = 20
GRAVITY = 2.5
GAME_SPEED = 15

GROUND_WIDTH = 2 * SCREEN_WIDTH
GROUND_HEIGHT = 100

PIPE_WIDTH = 80
PIPE_HEIGHT = 500

PIPE_GAP = 150

wing = 'assets/audio/wing.wav'
hit = 'assets/audio/hit.wav'

pygame.mixer.init()


class Bird(pygame.sprite.Sprite):

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        self.images = [pygame.image.load('assets/sprites/bluebird-upflap.png').convert_alpha(),
                       pygame.image.load('assets/sprites/bluebird-midflap.png').convert_alpha(),
                       pygame.image.load('assets/sprites/bluebird-downflap.png').convert_alpha()]

        self.speed = SPEED

        self.current_image = 0
        self.image = pygame.image.load('assets/sprites/bluebird-upflap.png').convert_alpha()
        self.mask = pygame.mask.from_surface(self.image)

        self.rect = self.image.get_rect()
        self.rect[0] = SCREEN_WIDTH / 6
        self.rect[1] = SCREEN_HEIGHT / 2

    def update(self):
        self.current_image = (self.current_image + 1) % 3
        self.image = self.images[self.current_image]
        self.speed += GRAVITY

        # UPDATE HEIGHT
        self.rect[1] += self.speed

    def bump(self):
        self.speed = -SPEED

    def begin(self):
        self.current_image = (self.current_image + 1) % 3
        self.image = self.images[self.current_image]


class Pipe(pygame.sprite.Sprite):

    def __init__(self, inverted, xpos, ysize):
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.image.load('assets/sprites/pipe-green.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (PIPE_WIDTH, PIPE_HEIGHT))

        self.rect = self.image.get_rect()
        self.rect[0] = xpos

        if inverted:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect[1] = - (self.rect[3] - ysize)
        else:
            self.rect[1] = SCREEN_HEIGHT - ysize

        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        self.rect[0] -= GAME_SPEED


class Ground(pygame.sprite.Sprite):

    def __init__(self, xpos):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('assets/sprites/base.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (GROUND_WIDTH, GROUND_HEIGHT))

        self.mask = pygame.mask.from_surface(self.image)

        self.rect = self.image.get_rect()
        self.rect[0] = xpos
        self.rect[1] = SCREEN_HEIGHT - GROUND_HEIGHT

    def update(self):
        self.rect[0] -= GAME_SPEED


def is_off_screen(sprite):
    return sprite.rect[0] < -(sprite.rect[2])


def get_random_pipes(xpos):
    size = random.randint(150, 350)
    pipe = Pipe(False, xpos, size)
    pipe_inverted = Pipe(True, xpos, SCREEN_HEIGHT - size - PIPE_GAP)
    return pipe, pipe_inverted


def should_jump(flappy, pipe_grp):
    # If the bird is too low, or if it is under the 3/8 of pipe gap, it should jump
    # returns {0 : fall ; 1 : jump ; 2 : JUMP}
    flappy_bottom = flappy.rect[1] + flappy.rect[3]
    if (flappy_bottom >= 460) or (flappy_bottom >= 450 and flappy.speed < 0):
        return 2
    if flappy.rect[1] + flappy.rect[3] // 2 > (pipe_grp.sprites()[0].rect[1] - int(1 / 3 * PIPE_GAP)):
        return 1
    return 0


"""
def draw_stuff(img, color):
    # Draw the action hint on the image with the given color
    for x in range(bird.rect[0]):
        for y in range(SCREEN_HEIGHT):
            img.putpixel((x, y), (color, color, color))


def draw_action_hint(img, action):
    # Depending on the action, draw the hint on the image
    if action == 0:
        draw_stuff(img, 255)  # White
    elif action == 1:
        draw_stuff(img, 100)  # Grey
    else:  # should_jump == 2
        draw_stuff(img, 0)  # Black
"""

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Flappy Bird')

BACKGROUND = pygame.image.load('assets/sprites/background-day.png')
BACKGROUND = pygame.transform.scale(BACKGROUND, (SCREEN_WIDTH, SCREEN_HEIGHT))
BEGIN_IMAGE = pygame.image.load('assets/sprites/message.png').convert_alpha()

# restart game when bird dies :/
while True:

    bird_group = pygame.sprite.Group()
    bird = Bird()
    bird_group.add(bird)

    ground_group = pygame.sprite.Group()

    for i in range(2):
        ground = Ground(GROUND_WIDTH * i)
        ground_group.add(ground)

    pipe_group = pygame.sprite.Group()
    for i in range(2):
        pipes = get_random_pipes(SCREEN_WIDTH * i + 800)
        pipe_group.add(pipes[0])
        pipe_group.add(pipes[1])

    # make sure dataset/jump | dataset/no_jump are valid folders
    DATASET_FOLDER = "dataset"
    JUMP_FOLDER = "jump"
    NO_JUMP_FOLDER = "no_jump"
    if not os.path.isdir(f"{DATASET_FOLDER}/"):
        os.mkdir(DATASET_FOLDER)
    if not os.path.isdir(f"{DATASET_FOLDER}/{JUMP_FOLDER}"):
        os.mkdir(f"{DATASET_FOLDER}/{JUMP_FOLDER}")
    if not os.path.isdir(f"{DATASET_FOLDER}/{NO_JUMP_FOLDER}"):
        os.mkdir(f"{DATASET_FOLDER}/{NO_JUMP_FOLDER}")

    clock = pygame.time.Clock()

    begin = True

    while begin and not ia_mode:

        clock.tick(20)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
            if event.type == KEYDOWN:
                if event.key == K_SPACE or event.key == K_UP:
                    bird.bump()
                    pygame.mixer.music.load(wing)
                    pygame.mixer.music.play()
                    begin = False

        screen.blit(BACKGROUND, (0, 0))
        screen.blit(BEGIN_IMAGE, (120, 150))

        if is_off_screen(ground_group.sprites()[0]):
            ground_group.remove(ground_group.sprites()[0])

            new_ground = Ground(GROUND_WIDTH - 20)
            ground_group.add(new_ground)

        bird.begin()
        ground_group.update()

        bird_group.draw(screen)
        ground_group.draw(screen)

        pygame.display.update()

    screens = []

    while True:

        clock.tick(15)

        jumped = False

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
            if event.type == KEYDOWN:
                if event.key == K_SPACE or event.key == K_UP:
                    bird.bump()
                    pygame.mixer.music.load(wing)
                    pygame.mixer.music.play()
                    jumped = True

        # screen.blit(BACKGROUND, (0, 0))
        screen.fill((0, 0, 0))

        if is_off_screen(ground_group.sprites()[0]):
            ground_group.remove(ground_group.sprites()[0])

            new_ground = Ground(GROUND_WIDTH - 20)
            ground_group.add(new_ground)

        if is_off_screen(pipe_group.sprites()[0]):
            pipe_group.remove(pipe_group.sprites()[0])
            pipe_group.remove(pipe_group.sprites()[0])

            pipes = get_random_pipes(SCREEN_WIDTH * 2)

            pipe_group.add(pipes[0])
            pipe_group.add(pipes[1])

        bird_group.update()
        ground_group.update()
        pipe_group.update()

        bird_group.draw(screen)
        pipe_group.draw(screen)
        ground_group.draw(screen)

        pygame.display.update()

        strFormat = 'RGBA'
        raw_str = pygame.image.tostring(screen, strFormat, False)
        image = Image.frombytes(strFormat, screen.get_size(), raw_str)
        # draw_action_hint(image, should_jump(bird, pipe_group))
        # speed_data = int(bird.speed * 2 + 100)  # bird speed is typically between -50 and 50
        # for x in range(bird.rect[0]):
        #     for y in range(SCREEN_HEIGHT):
        #         image.putpixel((x, y), (speed_data, speed_data, speed_data))

        if ia_mode:
            # image = image.convert("L").filter(ImageFilter.FIND_EDGES).resize((50, 50))
            image = image.convert("L").resize((50, 50))
            pred = model(asarray(image)[None, :, :, None]).numpy()[0]
            # print(pred)
            if pred[1] > 0.5:
                pygame.event.post(pygame.event.Event(pygame.KEYDOWN,
                                                     {'mod': 0, 'scancode': 30, 'key': pygame.K_SPACE, 'unicode': ' '}))
                print("JUMPING !")
        else:
            image.save(
                f"dataset/{'jump' if (should_jump(bird, pipe_group) == 1 or should_jump(bird, pipe_group) == 2) else 'no_jump'}/{uuid.uuid4()}.png")
            # screens.append(image)
            # if len(screens) >= 10:
            #    screens.pop(0).save(f"dataset/{'jump' if jumped else 'no_jump'}/{uuid.uuid4()}.png")
            # print("Bird: ", bird.rect[1] + bird.rect[3] / 2, " | Speed: ", bird.speed, " | Jumped: ", jumped)
            # print("Pipe: ", pipe_group.sprites()[0].rect[1] - PIPE_GAP // 2)

            # print(len(screens))
            # pygame.image.save(screen, f"dataset/{'jump' if jumped else 'no_jump'}/{uuid.uuid4()}.jpg")

        if (pygame.sprite.groupcollide(bird_group, ground_group, False, False, pygame.sprite.collide_mask) or
                pygame.sprite.groupcollide(bird_group, pipe_group, False, False, pygame.sprite.collide_mask)):
            pygame.mixer.music.load(hit)
            pygame.mixer.music.play()
            time.sleep(1)
            break
