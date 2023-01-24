import pygame
import numpy
import sys
import random
from PIL import Image, ImageSequence
import csv
import os
import time

pygame.init()

WIDTH = 1400
HEIGHT = 700
BACKGROUND = (0, 0, 0)
snow_list = []
points = 0
lvl = 1
time = 0
screen_rect = (0, 0, 1400, 700)

all_sprites = pygame.sprite.Group()
part_sprites = pygame.sprite.Group()


def pilImageToSurface(pilImage):
    mode, size, data = pilImage.mode, pilImage.size, pilImage.tobytes()
    return pygame.image.fromstring(data, size, mode).convert_alpha()


def loadGIF(filename):
    pilImage = Image.open(filename)
    frames = []
    if pilImage.format == 'GIF' and pilImage.is_animated:
        for frame in ImageSequence.Iterator(pilImage):
            pygameImage = pilImageToSurface(frame.convert('RGBA'))
            frames.append(pygameImage)
    else:
        frames.append(pilImageToSurface(pilImage))
    return frames


def load_image(name, color_key=None):
    fullname = name
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        print('Не удаётся загрузить:', name)
        raise SystemExit(message)
    image = image.convert_alpha()
    if color_key is not None:
        if color_key is -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    return image


class Sprite(pygame.sprite.Sprite):
    def __init__(self, image, startx, starty):
        super().__init__()

        self.image = pygame.image.load(image)
        self.rect = self.image.get_rect()

        self.rect.center = [startx, starty]

    def update(self):
        pass

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Player(Sprite):
    def __init__(self, startx, starty):
        super().__init__("skeleton-animation_0.png", startx, starty)
        self.stand_image = self.image
        self.jump_image = pygame.image.load("skeleton-animation_0.png")

        self.x = startx
        self.y = starty
        self.point = 0

        self.walk_cycle = [pygame.image.load(f"skeleton-animation_{i}.png") for i in range(0, 20)]
        self.animation_index = 0
        self.facing_left= False

        self.speed = 6
        self.jumpspeed = 20
        self.vsp = 0
        self.gravity = 1
        self.min_jumpspeed = 4
        self.prev_key = pygame.key.get_pressed()

    def walk_animation(self):
        self.image = self.walk_cycle[self.animation_index]
        if not self.facing_left:
            self.image = pygame.transform.flip(self.image, True, False)

        if self.animation_index < len(self.walk_cycle)-1:
            self.animation_index += 1
        else:
            self.animation_index = 0

    def jump_animation(self):
        self.image = self.jump_image
        if self.facing_left:
            self.image = pygame.transform.flip(self.image, True, False)

    def update(self, boxes, coins):
        global points
        hsp = 0
        onground = self.check_collision(0, 1, boxes)
        # check keys
        key = pygame.key.get_pressed()
        if key[pygame.K_LEFT]:
            self.facing_left = True
            self.walk_animation()
            hsp = -self.speed
        elif key[pygame.K_RIGHT]:
            self.facing_left = False
            self.walk_animation()
            hsp = self.speed
        else:
            self.image = self.stand_image

        if key[pygame.K_UP] and onground:
            self.vsp = -self.jumpspeed

        # variable height jumping
        if self.prev_key[pygame.K_UP] and not key[pygame.K_UP]:
            if self.vsp < -self.min_jumpspeed:
                self.vsp = -self.min_jumpspeed

        self.prev_key = key

        # gravity
        if self.vsp < 10 and not onground:
            self.jump_animation()
            self.vsp += self.gravity

        if onground and self.vsp > 0:
            self.vsp = 0

        # movement
        self.move(hsp, self.vsp, boxes)

        # coins
        for coin in coins:
            if pygame.sprite.collide_rect(player, coin):
                pygame.mixer.Sound.play(pygame.mixer.Sound('eating.mp3'))
                create_particles([coin.rect.x, coin.rect.y])
                coin.kill()
                points += 1

    def move(self, x, y, boxes):
        self.x += x
        self.y += y
        dx = x
        dy = y

        while self.check_collision(0, dy, boxes):
            dy -= numpy.sign(dy)

        while self.check_collision(dx, dy, boxes):
            dx -= numpy.sign(dx)

        self.rect.move_ip([dx, dy])

    def check_collision(self, x, y, grounds):
        self.rect.move_ip([x, y])
        collide = pygame.sprite.spritecollideany(self, grounds)
        self.rect.move_ip([-x, -y])
        return collide

player = Player(100, 200)


class Box(Sprite):
    def __init__(self, startx, starty):
        super().__init__(f"stone_{random.randint(0, 4)}.png", startx, starty)


class Coin(Sprite):
    def __init__(self, startx, starty):
        super().__init__("ham.png", startx, starty)
        self.x = startx
        self.y = starty

    def ded(self):
        self.kill()


def terminate():
    pygame.quit()
    sys.exit


class Particle(pygame.sprite.Sprite):
    # сгенерируем частицы разного размера
    fire = [pygame.image.load("shine_1.png")]
    for scale in (5, 10, 20):
        fire.append(pygame.transform.scale(fire[0], (scale, scale)))

    def __init__(self, pos, dx, dy):
        super().__init__(part_sprites)
        self.image = random.choice(self.fire)
        self.rect = self.image.get_rect()

        # у каждой частицы своя скорость — это вектор
        self.velocity = [dx, dy]
        # и свои координаты
        self.rect.x, self.rect.y = pos

        # гравитация будет одинаковой (значение константы)
        self.gravity = 0.5

    def update(self):
        # применяем гравитационный эффект:
        # движение с ускорением под действием гравитации
        self.velocity[1] += self.gravity
        # перемещаем частицу
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        # убиваем, если частица ушла за экран
        if not self.rect.colliderect(pygame.Rect(screen_rect)):
            self.kill()


def create_particles(position):
    # количество создаваемых частиц
    particle_count = 20
    # возможные скорости
    numbers = range(-5, 6)
    for _ in range(particle_count):
        Particle(position, random.choice(numbers), random.choice(numbers))


def relax():
    all_sprites = pygame.sprite.Group()
    clock = pygame.time.Clock()
    running = True
    screen = pygame.display.set_mode((400, 400))
    screen_rect = (0, 0, 400, 400)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                # создаём частицы по щелчку мыши
                create_particles(pygame.mouse.get_pos())

        all_sprites.update()
        screen.fill((0, 0, 0))
        all_sprites.draw(screen)
        pygame.display.flip()
        clock.tick(50)

    pygame.quit()


def inf_screen():
    pygame.font.init()
    pygame.display.set_caption('Info')
    clock = pygame.time.Clock()
    screen_size = (600, 400)
    screen = pygame.display.set_mode(screen_size)
    st_1 = 3
    snow_list_1 = []
    for i in range(50):
        x = random.randrange(0, 700)
        y = random.randrange(0, 600)
        snow_list_1.append([x, y])
    pygame.font.init()

    intro_text = ["This game's plot",
                  'is abstract and',
                  'really absurd...',
                  '',
                  'Control buttons:',
                  'up      down',
                  'left    right']
    fon = pygame.transform.scale(load_image('fon.jpg'), screen_size)
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 35)
    run = True
    while run:
        fon = pygame.transform.scale(load_image('fon.jpg'), screen_size)
        screen.blit(fon, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_i:
                    run = False

            # stars
        for i in range(len(snow_list_1)):
            pygame.draw.circle(screen, 'white', snow_list_1[i], st_1)
        if st_1 <= 0:
            st_1 = 3
            snow_list_1 = []
            for i in range(50):
                x = random.randrange(0, 600)
                y = random.randrange(0, 400)
                snow_list_1.append([x, y])
        st_1 -= 1

        pygame.draw.rect(screen, 'white', (100, 50, 400, 300))
        pygame.draw.rect(screen, [83, 55, 122], (100, 50, 400, 300), 7)

        for line in intro_text:
            text = font.render(line, True, [83, 55, 122])
            screen.blit(text, (120, 90 + 30 * intro_text.index(line)))

        pygame.display.flip()
        clock.tick(60)


def start_screen():
    global points
    global lvl
    pygame.font.init()
    pygame.display.set_caption('Start screen')
    clock = pygame.time.Clock()
    screen_size = (600, 400)
    screen = pygame.display.set_mode(screen_size)
    st_1 = 3
    snow_list_1 = []
    for i in range(50):
        x = random.randrange(0, 1400)
        y = random.randrange(0, 600)
        snow_list_1.append([x, y])
    pygame.font.init()

    font = pygame.font.Font(None, 80)
    font_2 = pygame.font.Font(None, 20)
    text = font.render("Burger's fly", True, [83, 55, 122])
    text_2 = font_2.render("To start press 'space'", True, [83, 55, 122])
    text_3 = font_2.render("To read a story press 'i'", True, [83, 55, 122])
    text_4 = font_2.render("To chose level press 1, 2 or 3", True, [83, 55, 122])
    while True:
        fon = pygame.transform.scale(load_image('fon.jpg'), screen_size)
        screen.blit(fon, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game()
                if event.key == pygame.K_i:
                    inf_screen()
                if event.key == pygame.K_1:
                    lvl = 1
                if event.key == pygame.K_2:
                    lvl = 2
                if event.key == pygame.K_3:
                    lvl = 3

            # stars
        for i in range(len(snow_list_1)):
            pygame.draw.circle(screen, 'white', snow_list_1[i], st_1)
        if st_1 <= 0:
            st_1 = 3
            snow_list_1 = []
            for i in range(50):
                x = random.randrange(0, 700)
                y = random.randrange(0, 600)
                snow_list_1.append([x, y])
        st_1 -= 1
        text_5 = font_2.render(f'LEVEL: {lvl}', True, [83, 55, 122])
        pygame.draw.rect(screen, 'white', (100, 100, 400, 200))
        pygame.draw.rect(screen, [83, 55, 122], (100, 100, 400, 200), 8)
        screen.blit(text, (150, 130))
        screen.blit(text_2, (230, 190))
        screen.blit(text_3, (220, 215))
        screen.blit(text_4, (200, 240))
        screen.blit(text_5, (270, 265))
        pygame.display.flip()
        clock.tick(60)


def final_screen():
    global player
    global points
    global time
    pygame.font.init()
    pygame.display.set_caption('Result')
    clock = pygame.time.Clock()
    screen_size = (600, 400)
    screen = pygame.display.set_mode(screen_size)
    st_1 = 3
    snow_list_1 = []
    for i in range(50):
        x = random.randrange(0, 700)
        y = random.randrange(0, 600)
        snow_list_1.append([x, y])

    pygame.font.init()
    font = pygame.font.Font(None, 70)
    font_2 = pygame.font.Font(None, 40)
    text = font.render("Game finished", True, [83, 55, 122])
    text_2 = font_2.render(f"Your points: {points}", True, [83, 55, 122])
    text_3 = font_2.render(f"Your time: {time} s", True, [83, 55, 122])

    with open('records.txt') as f:
        k = f.readlines()
        print(k)
    s = k[0].split('/n')[-2].split('---')
    print(s)
    text_4 = font_2.render(f"Previouse result: {s[0]} p; {s[1]} s", True, [83, 55, 122])
    with open('records.txt', 'w') as f:
        f.write(f'{"/n".join(k)}{points}---{time}/n')

    run = True
    while run:
        fon = pygame.transform.scale(load_image('fon.jpg'), screen_size)
        screen.blit(fon, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN:
                player = Player(100, 200)
                points = 0
                start_screen()
                return

            # stars
        for i in range(len(snow_list_1)):
            pygame.draw.circle(screen, 'white', snow_list_1[i], st_1)
        if st_1 <= 0:
            st_1 = 3
            snow_list_1 = []
            for i in range(50):
                x = random.randrange(0, 700)
                y = random.randrange(0, 600)
                snow_list_1.append([x, y])
        st_1 -= 1

        pygame.draw.rect(screen, 'white', (100, 100, 450, 200))
        pygame.draw.rect(screen, [83, 55, 122], (100, 100, 450, 200), 4)
        screen.blit(text, (130, 120))
        screen.blit(text_2, (150, 180))
        screen.blit(text_3, (150, 220))
        screen.blit(text_4, (150, 260))
        pygame.display.flip()
        clock.tick(60)


def game():
    global points
    global lvl
    global time
    pygame.display.set_caption('Fly burger')
    print(lvl)
    screen = pygame.display.set_mode((WIDTH, HEIGHT), 0, 100)
    counter = 0
    timer_event = pygame.USEREVENT + 1
    pygame.time.set_timer(timer_event, 1000)
    clock = pygame.time.Clock()
    boxes = pygame.sprite.Group()
    coins = pygame.sprite.Group()

    if lvl == 2:
        coins.add(Coin(500, 100))
        coins.add(Coin(300, 500))
        coins.add(Coin(1200, 600))

        for bx in range(100, 750, 250):
            boxes.add(Box(bx, 300))

        for bx in range(200, 400, 200):
            boxes.add(Box(bx, 400))

        for bx in range(100, 600, 250):
            boxes.add(Box(bx, 600))

        for bx in range(700, 1100, 170):
            boxes.add(Box(bx, 600))

        boxes.add(Box(1000, 180))
        boxes.add(Box(1200, 400))
        boxes.add(Box(1200, 700))
        boxes.add(Box(300, 230))
        boxes.add(Box(1250, 350))

    elif lvl == 1:
        coins.add(Coin(900, 100))
        coins.add(Coin(400, 100))
        for bx in range(100, 1300, 400):
            boxes.add(Box(bx, 300))

        for bx in range(300, 1300, 400):
            boxes.add(Box(bx, 500))

        for bx in range(370, 1400, 400):
            boxes.add(Box(bx, 400))

        for bx in range(100, 1300, 400):
            boxes.add(Box(bx, 800))

    elif lvl == 3:
        coins.add(Coin(900, 200))
        coins.add(Coin(500, 100))
        coins.add(Coin(750, 500))
        coins.add(Coin(1300, 150))

        for bx in range(100, 1300, 400):
            boxes.add(Box(bx, 300))
        boxes.add(Box(330, 230))
        boxes.add(Box(550, 500))
        boxes.add(Box(700, 600))
        boxes.add(Box(750, 400))
        boxes.add(Box(1110, 350))

    run = True
    while run:
        fon = pygame.transform.scale(load_image('big_sky.jpg'), (1400, 700))
        screen.blit(fon, (0, 0))
        font = pygame.font.Font(None, 50)
        text_1 = font.render(f"POINTS: {points}", True, [83, 55, 122])
        text_2 = font.render(f'TIME: {counter} s', True, [83, 55, 122])
        pygame.draw.rect(screen, 'white', (0, 0, 220, 150))
        pygame.draw.rect(screen, [83, 55, 122], (0, 0, 220, 150), 3)
        screen.blit(text_1, (20, 20))
        screen.blit(text_2, (20, 80))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                points = Player.poin
                run = False
            elif event.type == timer_event:
                counter += 1
                print
            pygame.event.pump()
        player.update(boxes, coins)

        if player.y > 700 or points == lvl + 1:
            print('fin')
            pygame.time.delay(500)
            time = counter
            final_screen()

        # screen.fill(BACKGROUND)
        part_sprites.update()
        part_sprites.draw(screen)
        player.draw(screen)
        boxes.draw(screen)
        coins.draw(screen)
        pygame.display.flip()

        # screen.blit(text, (30, 30))

        clock.tick(60)


def main():
    pygame.init()
    pygame.font.init()
    pygame.display.init()
    pygame.mixer.music.load("music")
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(0.1)
    start_screen()


if __name__ == "__main__":
    main()