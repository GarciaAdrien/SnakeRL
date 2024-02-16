import pygame
import random
from enum import Enum
from collections import namedtuple
import numpy as np

# Initialize
pygame.init()
font = pygame.font.Font('arial.ttf', 25)

# For directions
class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4

Point = namedtuple('Point', 'x, y')

# Some colors
WHITE = (255, 255, 255)
RED = (231, 76, 60)  # Alizarin
GREEN = (46, 204, 113)  # Emerald
BLUE = (52, 152, 219)  # Peter River
BLACK = (0, 0, 0)
DARK_GRAY = (44, 62, 80)  # Concrete
LIGHT_GRAY = (149, 165, 166)  # Silver
BLOCK_SZ = 20
INIT_VEL = 10
VEL_INCREMENT = 5
VEL_MANUEL = INIT_VEL

# Particle class for special effects
class Particle:
    def __init__(self, pos):
        self.x, self.y = pos
        self.colour = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        self.size = random.randint(5, 10)
        self.thickness = random.randint(1, 3)
        self.speed = random.randint(1, 3)
        self.angle = random.uniform(0, 2 * np.pi)

    def move(self):
        self.x += np.cos(self.angle) * self.speed
        self.y += np.sin(self.angle) * self.speed
        self.size -= 0.05
        self.thickness = int(self.size / 2)

    def draw(self, screen):
        pygame.draw.circle(screen, self.colour, (int(self.x), int(self.y)), max(0, int(self.size)), self.thickness)


class SnakeGameAI:

    def __init__(self, w=640, h=480):
        self.w = w
        self.h = h
        # Init display
        self.display = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption('Snake')
        self.clock = pygame.time.Clock()
        self.reset()

    def reset(self):
        # Init game state
        self.direction = Direction.RIGHT

        self.head = Point(self.w/2, self.h/2)
        # 3 blocks initially as the body
        self.snake = [self.head,
                      Point(self.head.x - BLOCK_SZ, self.head.y),
                      Point(self.head.x - (2 * BLOCK_SZ), self.head.y)]

        self.score = 0
        self.food = None
        self._place_food()
        self.frame_iteration = 0
        self.vel = INIT_VEL
        self.particles = []

    def _place_food(self):
        x = random.randint(0, (self.w - BLOCK_SZ) // BLOCK_SZ) * BLOCK_SZ
        y = random.randint(0, (self.h - BLOCK_SZ) // BLOCK_SZ) * BLOCK_SZ
        self.food = Point(x, y)
        if self.food in self.snake:
            # Case if food spawns on the snake body, try again
            self._place_food()

    def play_step(self, action):
        global VEL_MANUEL
        self.frame_iteration += 1
        # Getting the key which player pressed
        for event in pygame.event.get():
            # Quit case
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:  # Touches du pavé numérique pour incrémenter la vitesse
                    self.vel += VEL_INCREMENT
                    VEL_MANUEL = self.vel
                elif event.key == pygame.K_DOWN:  # Touches du pavé numérique pour décrémenter la vitesse
                    self.vel -= VEL_INCREMENT
                    VEL_MANUEL = self.vel
                    if self.vel < 0:
                        self.vel = 0
                    VEL_MANUEL = self.vel

        # Move
        self._move(action)  # Update head
        self.snake.insert(0, self.head)

        # Game over case
        reward = 0
        game_over = False
        if self.is_collision() or self.frame_iteration > 100 * len(self.snake):
            # If for a long time, doesn't eat or doesn't die, we need to terminate,
            # len factor is to give more time for larger snakes
            game_over = True
            reward = -10
            return reward, game_over, self.score

        # New food/moving
        if self.head == self.food:
            self.score += 1
            reward = 10
            self._place_food()
            self.particles = [Particle(self.food) for _ in range(20)]  # Create particles
        else:
            self.snake.pop()  # Move (remove the last part)

        # Update display and clock
        self._update_ui()
        self.clock.tick(VEL_MANUEL)


        # Return game over and score
        return reward, game_over, self.score

    def is_collision(self, pt=None):
        if pt is None:
            pt = self.head
        # Hits the boundary
        if pt.x > self.w - BLOCK_SZ or pt.x < 0 or pt.y > self.h - BLOCK_SZ or pt.y < 0:
            return True
        # Hits its own body
        if pt in self.snake[1:]:
            return True

        return False

    def _update_ui(self):
        self.display.fill(BLACK)

        # Particles
        for p in self.particles:
            p.move()
            p.draw(self.display)

        for pt in self.snake:
            pygame.draw.rect(self.display, BLUE, pygame.Rect(pt.x, pt.y, BLOCK_SZ, BLOCK_SZ))
            pygame.draw.rect(self.display, DARK_GRAY, pygame.Rect(pt.x + 4, pt.y + 4, 12, 12))

        pygame.draw.rect(self.display, RED, pygame.Rect(self.food.x, self.food.y, BLOCK_SZ, BLOCK_SZ))

        text = font.render("Score: " + str(self.score), True, BLUE)
        self.display.blit(text, [10, 10])

        # Affichage de la vitesse dans le coin en haut à droite
        vel_text = font.render("Vitesse: " + str(VEL_MANUEL), True, BLUE)
        vel_rect = vel_text.get_rect()
        vel_rect.topright = (self.w - 10, 10)
        self.display.blit(vel_text, vel_rect)
        pygame.display.flip()

    def _move(self, action):
        # Has 3 actions straight, left, right

        clock_wise = [Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP]
        idx = clock_wise.index(self.direction)

        if np.array_equal(action, [1, 0, 0]):  # Straight
            new_dir = clock_wise[idx]  # No change
        elif np.array_equal(action, [0, 1, 0]):  # Right
            next_idx = (idx + 1) % 4
            new_dir = clock_wise[next_idx]  # Turned right so right->down->left->up
        else:  # Left
            next_idx = (idx - 1) % 4
            new_dir = clock_wise[next_idx]  # Counter clockwise : right->up->left->down

        self.direction = new_dir

        x = self.head.x
        y = self.head.y
        if self.direction == Direction.RIGHT:
            x += BLOCK_SZ
        elif self.direction == Direction.LEFT:
            x -= BLOCK_SZ
        elif self.direction == Direction.DOWN:
            y += BLOCK_SZ
        elif self.direction == Direction.UP:
            y -= BLOCK_SZ

        self.head = Point(x, y)

# Main loop
if __name__ == "__main__":
    game = SnakeGameAI()

    while True:
        game_over, score = game.play_step(np.random.choice([[1, 0, 0], [0, 1, 0], [0, 0, 1]]))
        if game_over:
            break

    print('Final Score:', score)
    pygame.quit()
