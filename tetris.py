import numpy as np
import pygame
from random import randint
from time import time

COLS, ROWS = 8, 16  # rows and columns in screen
SQ_SIZE = 30  # size of a square
MIDDLE = SQ_SIZE * (COLS // 2)  # block will fall from the top-middle of the screen
SPD = SQ_SIZE // 2  # block falling speed

BG_COL = (30, 30, 30)
BG_LINE_COL = (70, 70, 70)
TEXT_COL = (200, 200, 200)

PIECE_TYPES = (
    ((0, 0), (0, 1), (1, 0), (1, 1)),  # square
    ((0, 0), (1, 0), (2, 0), (0, 1)),  # L
    ((0, 0), (0, 1), (-1, 0), (-2, 0)),  # J
    ((0, 0), (0, 1), (0, 2), (0, 3)),  # I
    ((0, 0), (-1, 0), (0, 1), (1, 1)),  # Z
    ((0, 0), (1, 0), (0, 1), (-1, 1)),  # S
    ((0, 0), (-1, 0), (1, 0), (0, 1))  # T
)

# colors for the pieces include: red, green, blue, yellow, magenta, cyan, grey
PIECE_COLOR = ((200, 0, 0), (0, 200, 0), (0, 0, 200), (200, 200, 0), (200, 0, 200), (0, 200, 200), (200, 200, 200))


class Block(pygame.Rect):
    # a single square block on screen
    def __init__(self, color, left, top):
        super().__init__(left, top, SQ_SIZE, SQ_SIZE)
        self.color = color

    def realign(self):
        # a block appears to fall square by square on screen buy actually falls by 'SPD'
        # returns a new block located to the nearest upper row and left column of the current block
        return Block(self.color, SQ_SIZE * (self.left // SQ_SIZE), SQ_SIZE * (self.top // SQ_SIZE))

    def copy(self):
        return Block(self.color, self.left, self.top)


def new_piece():
    # creates a new random piece
    n = randint(0, 6)  # determines the piece type and color
    shift_lr = randint(0, 2)  # block wouldn't always fall in the middle
    piece = list(
        map(lambda a: [a[0] * SQ_SIZE + MIDDLE - shift_lr * SQ_SIZE, a[1] * SQ_SIZE - SQ_SIZE * 2], PIECE_TYPES[n]))
    return [Block(PIECE_COLOR[n], p[0], p[1]) for p in piece]


def check_lr(current_piece: list[Block], fallen_blocks: list[Block], left: bool) -> bool:
    # checks if there is a wall / other (fallen) blocks to the left or right of the current block
    # the parameter <left> is to indicate the direction the block is going in (which key, l/r, was pressed)
    current_piece = [b.realign() for b in current_piece]
    l = [b.left for b in current_piece]
    if left:
        # get all blocks to the left of the 
        blocks = list(filter(lambda b: b.left < max(l), fallen_blocks))
        if min(l) <= 0:
            return False
    else:
        blocks = list(filter(lambda b: b.left > min(l), fallen_blocks))
        if max(l) >= (COLS - 1) * SQ_SIZE:
            return False
    for b in current_piece:
        if left:
            b.left -= SQ_SIZE
        else:
            b.left += SQ_SIZE
        if b.collidelist(blocks) != -1:
            return False
    return True


def in_screen(current_piece: list[Block]) -> bool:
    # checks if the block is in screen, (if it returns false, it's game over)
    for b in current_piece:
        if b.top < 0:
            return False
    return True


def check_fallen(current_piece: list[Block], fallen_blocks: list[Block]):
    # checks if the piece has fallen
    if max(b.top for b in current_piece) >= (ROWS - 1) * SQ_SIZE:
        return True
    current_piece = [b.realign() for b in current_piece]
    # filters for fallen blocks below the highest block in the current piece
    blocks = list(filter(lambda fb: fb.top > min([cb.top for cb in current_piece]), fallen_blocks))
    # if any blocks are overlapping fallen blocks after moving down one square, the current piece has fallen
    for b in current_piece:
        b.top += SQ_SIZE
        if b.collidelist(blocks) != -1:
            return True
    return False


def rotate(current_piece: list[Block], fallen_blocks: list[Block]):
    # a new piece is rotated, current_piece is copied to not be changed
    piece = [b.copy() for b in current_piece]
    coords = [[b.left, b.top] for b in piece]
    avg_x = sum([c[0] for c in coords]) / len(piece)
    avg_y = sum([c[1] for c in coords]) / len(piece)

    translated_blocks = [[b[0] - avg_x, b[1] - avg_y] for b in coords]
    new_coords = list(map(lambda c: np.array(c).dot([[0, 1], [-1, 0]]), translated_blocks))

    for b, c in zip(piece, new_coords):
        b.left, b.top = c[0] + avg_x, c[1] + avg_y
        if b.left < 0 or b.left > (COLS - 1) * SQ_SIZE or b.collidelist(fallen_blocks) != -1:
            return current_piece
    return piece


def clear_rows(f_blocks: list[Block], score):
    rows = [b.top for b in f_blocks]
    filled_rows = []
    for r in range(ROWS):
        if rows.count(r * SQ_SIZE) == COLS:
            filled_rows.append(r * SQ_SIZE)
            score += 1
    r_blocks = []  # remaining blocks
    for b in f_blocks:
        if b.top not in filled_rows:
            b.top += len(list(filter(lambda x: x > b.top, filled_rows))) * SQ_SIZE
            r_blocks.append(b)
    return r_blocks, score


def die(f_blocks: list[Block]):
    for b in f_blocks:
        if b.top <= 0:
            return True


def record_scores(score):
    with open('scores.txt', 'a') as scores:
        pass  # append score to socres, and updates highscore


def draw_win(surface, all_blocks: list[Block], score):
    surface.fill(BG_COL)
    # draw all blocks, fallen and falling
    for b in all_blocks:
        pygame.draw.rect(surface, b.color, b.realign())
    # draw the background lines
    for i in range(COLS + 1):
        pygame.draw.line(surface, BG_LINE_COL, (i * SQ_SIZE, 0), (i * SQ_SIZE, ROWS * SQ_SIZE))
    for i in range(ROWS + 1):
        pygame.draw.line(surface, BG_LINE_COL, (0, i * SQ_SIZE), (COLS * SQ_SIZE, i * SQ_SIZE))
    # draw the text
    txt = font.render(f'Score: {score}', True, TEXT_COL)
    surface.blit(txt, (5, 5))


def main():
    win = pygame.display.set_mode((COLS * SQ_SIZE, ROWS * SQ_SIZE))
    playing = True
    alive = True
    current_piece = new_piece()  # current block
    fallen_blocks = []  # fallen blocks
    score = 0
    clock = pygame.time.Clock()
    t_spin = time()  # for spinning block
    t_slide = 0  # for sliding block

    while playing:
        clock.tick(20)
        draw_win(win, fallen_blocks + current_piece, score)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                playing = False
        if alive:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and check_lr(current_piece, fallen_blocks, True):
                # move 
                for b in current_piece: b.left -= SPD
            elif keys[pygame.K_RIGHT] and check_lr(current_piece, fallen_blocks, False):
                for b in current_piece: b.left += SPD

            if keys[pygame.K_SPACE] and in_screen(current_piece):
                while not check_fallen(current_piece, fallen_blocks):
                    for b in current_piece:
                        b.top += SQ_SIZE

            # the block has fallen
            if check_fallen(current_piece, fallen_blocks):
                # player can still slide the block for 0.25s after it falls
                if t_slide == 0:
                    t_slide = time()
                elif 0.25 < time() - t_slide:
                    # after that time has passed, the blocks in the current_piece would be added to fallen_blocks
                    fallen_blocks += [b.realign() for b in current_piece]
                    t_slide = 0  # time for slide resets
                    if die(fallen_blocks):
                        alive = False  # game over
                    else:
                        # clears rows, updates score, creates a new piece
                        fallen_blocks, score = clear_rows(fallen_blocks, score)
                        current_piece = new_piece()
            else:  # not fallen, continues falling
                for b in current_piece:
                    # piece moves down (location on screen doesn't change until b.top s are at the next row)
                    b.top += 2
                    # after the current_piece is spinned, it can only be spinned again after 0.2s
                if keys[pygame.K_UP] and 0.2 < time() - t_spin:
                    current_piece = rotate(current_piece, fallen_blocks)
                    t_spin = time()
                # go down faster
                if keys[pygame.K_DOWN]:
                    for b in current_piece: b.top += SPD

        else:  # if not alive (game over)
            # a screen size transparent black rectangle is put on the screen, so it goes darker
            s = pygame.Surface((COLS * SQ_SIZE, ROWS * SQ_SIZE))
            s.set_alpha(150)
            s.fill((0, 0, 0))
            win.blit(s, (0, 0))
            # game over message is displayed
            text = font.render('You have died', True, TEXT_COL)
            text2 = font.render('Press z to restart', True, TEXT_COL)
            win.blit(text, (40, 2 * SQ_SIZE))
            win.blit(text2, (40, 2 * SQ_SIZE + 50))
            # if z is pressed, the game is reset
            keys = pygame.key.get_pressed()
            if keys[pygame.K_z]:
                alive = True
                current_piece = new_piece()
                fallen_blocks.clear()
                score = 0
                t_spin = time()
        pygame.display.update()
    pygame.quit()


if __name__ == '__main__':
    pygame.font.init()
    font = pygame.font.SysFont('calibri', 20)
    main()
