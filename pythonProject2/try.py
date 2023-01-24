import pygame
import numpy
import os
import sys
import random
points = 0

WIDTH = 1400
HEIGHT = 700
BACKGROUND = (0, 0, 0)
snow_list = []
screen_rect = (0, 0, 1400, 700)


def load_image(name, color_key=None):
    fullname = os.path.join(name)
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


class Particle(pygame.sprite.Sprite):
    # сгенерируем частицы разного размера
    fire = [load_image("shine.png")]
    for scale in (5, 10, 20):
        fire.append(pygame.transform.scale(fire[0], (scale, scale)))

    def __init__(self, pos, dx, dy):
        super().__init__(all_sprites)
        self.image = random.choice(self.fire)
        self.rect = self.image.get_rect()

        # у каждой частицы своя скорость — это вектор
        self.velocity = [dx, dy]
        # и свои координаты
        self.rect.x, self.rect.y = pos

        # гравитация будет одинаковой (значение константы)
        self.gravity = 0.25

    def update(self):
        # применяем гравитационный эффект:
        # движение с ускорением под действием гравитации
        self.velocity[1] += self.gravity
        # перемещаем частицу
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        # убиваем, если частица ушла за экран
        if not self.rect.colliderect(screen_rect):
            self.kill()
def create_particles(position):
    # количество создаваемых частиц
    particle_count = 20
    # возможные скорости
    numbers = range(-5, 6)
    for _ in range(particle_count):
        Particle(position, random.choice(numbers), random.choice(numbers))


class Player(Sprite):
    def __init__(self, startx, starty):
        super().__init__("skeleton-animation_0.png", startx, starty)
        self.stand_image = self.image
        self.jump_image = pygame.image.load("skeleton-animation_0.png")

        self.x = startx
        self.y = starty

        self.walk_cycle = [pygame.image.load(f"p1_front.png") for i in range(1, 12)]
        self.animation_index = 0
        self.facing_left= False

        self.speed = 4
        self.jumpspeed = 20
        self.vsp = 0
        self.gravity = 1
        self.min_jumpspeed = 4
        self.prev_key = pygame.key.get_pressed()

    def walk_animation(self):
        self.image = self.walk_cycle[self.animation_index]
        if self.facing_left:
            self.image = pygame.transform.flip(self.image, True, False)

        if self.animation_index < len(self.walk_cycle)-1:
            self.animation_index += 1
        else:
            self.animation_index = 0

    def jump_animation(self):
        self.image = self.jump_image
        if self.facing_left:
            self.image = pygame.transform.flip(self.image, True, False)

    def update(self, boxes):
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


class Box(Sprite):
    def __init__(self, startx, starty):
        super().__init__("planet1.png", startx, starty)


def terminate():
    pygame.quit()
    sys.exit


def draw_circle_alpha(surface, color, center, radius):
    target_rect = pygame.Rect(center, (0, 0)).inflate((radius * 2, radius * 2))
    shape_surf = pygame.Surface(target_rect.size, pygame.SRCALPHA)
    pygame.draw.circle(shape_surf, color, (radius, radius), radius)
    surface.blit(shape_surf, target_rect)


def start_screen():
    point = 0
    pygame.font.init()
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

    font = pygame.font.Font(None, 80)
    font_2 = pygame.font.Font(None, 40)
    text = font.render("Alian Game", True, [83, 55, 122])
    text_2 = font_2.render("To start press 'enter'", True, [83, 55, 122])
    while True:
        fon = pygame.transform.scale(load_image('fon.jpg'), screen_size)
        screen.blit(fon, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN:
                return
            #stars
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

        pygame.draw.rect(screen, 'white', (100, 100, 400, 200))
        pygame.draw.rect(screen, [83, 55, 122], (100, 100, 400, 200), 8)
        screen.blit(text, (130, 150))
        screen.blit(text_2, (150, 210))
        pygame.display.flip()
        clock.tick(60)


def final_screen():
    pygame.font.init()
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
    text_2 = font_2.render(f"Your points:{points}", True, [83, 55, 122])
    while True:
        fon = pygame.transform.scale(load_image('fon.jpg'), screen_size)
        screen.blit(fon, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN:
                return
            #stars
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

        pygame.draw.rect(screen, 'white', (100, 100, 400, 200))
        pygame.draw.rect(screen, [83, 55, 122], (100, 100, 400, 200), 8)
        screen.blit(text, (130, 150))
        screen.blit(text_2, (150, 210))
        pygame.display.flip()
        clock.tick(60)


def main():
    pygame.init()
    screen_size = (600, 400)
    screen = pygame.display.set_mode(screen_size)
    start_screen()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    player = Player(100, 200)

    boxes = pygame.sprite.Group()
    boxes.add(Box(100, 150))
    for bx in range(0, 800, 150):
        boxes.add(Box(bx, 300))

    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            pygame.event.pump()
        player.update(boxes)

        if player.y > 700:
            print('lose')
            final_screen()

        print(player.y)
        screen.blit(text, (130, 150))
        screen.fill(BACKGROUND)
        player.draw(screen)
        boxes.draw(screen)
        pygame.display.flip()

        clock.tick(60)


if __name__ == "__main__":
    main()