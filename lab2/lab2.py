from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import time
import os

# ---------------- Window size ---------------- #
window_width, window_height = 500, 600  # Screen dimensions

# ---------------- Game states ---------------- #
paused = False        # Pause state
game_over = False     # Game over state
score = 0             # Player score

# ---------------- Catcher variables ---------------- #
catcher_x = 200       # Catcher initial x position
catcher_speed = 200   # Catcher speed (pixels per second)
move_left, move_right = False, False   # Movement flags
catcher_color = (1, 1, 1)  # White normally, turns red on Game Over

# ---------------- Diamond variables ---------------- #
diamond_x, diamond_y = 250, 550   # Initial diamond position
diamond_size = 13                 # Size of the diamond
diamond_speed = 100               # Falling speed (pixels per second)
diamond_color = (1, 1, 1)         # Diamond color (changes each spawn)

# ---------------- Time tracking ---------------- #
last_time = time.time()   # Used for delta-time movement updates

# ---------------- Low-level drawing ---------------- #
def draw_point(x, y):
    """Draws a single point (pixel) at (x, y)."""
    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()

# ---------------- Zone finding for midpoint algorithm ---------------- #
def find_zone(x1, y1, x2, y2):
    """Finds which of the 8 zones the line belongs to."""
    dx = x2 - x1
    dy = y2 - y1
   
    if dx >= 0 and dy >= 0:
        if abs(dx) >= abs(dy):
            return 0
        else:
            return 1
    elif dx < 0 and dy >= 0:
        if abs(dx) >= abs(dy):
            return 3
        else:
            return 2
    elif dx < 0 and dy < 0:
        if abs(dx) >= abs(dy):
            return 4
        else:
            return 5
    elif dx >= 0 and dy < 0:
        if abs(dx) >= abs(dy):
            return 7
        else:
            return 6

# ---------------- Coordinate conversion for zones ---------------- #
def convert_to_zone0(x, y, zone):
    """Converts any zone to Zone 0 for calculation."""
    if zone == 0: return x, y
    elif zone == 1: return y, x
    elif zone == 2: return y, -x
    elif zone == 3: return -x, y
    elif zone == 4: return -x, -y
    elif zone == 5: return -y, -x
    elif zone == 6: return -y, x
    elif zone == 7: return x, -y

def convert_back_from_zone0(x, y, zone):
    """Converts Zone 0 result back to original zone."""
    if zone == 0: return x, y
    elif zone == 1: return y, x
    elif zone == 2: return -y, x
    elif zone == 3: return -x, y
    elif zone == 4: return -x, -y
    elif zone == 5: return -y, -x
    elif zone == 6: return y, -x
    elif zone == 7: return x, -y

# ---------------- Midpoint line drawing ---------------- #
def midpoint_line(x1, y1, x2, y2):
    """Draws a line from (x1,y1) to (x2,y2) using Midpoint Line Algorithm."""
    zone = find_zone(x1, y1, x2, y2)

    # Convert to zone 0 if needed
    if zone != 0:
        x1, y1 = convert_to_zone0(x1, y1, zone)
        x2, y2 = convert_to_zone0(x2, y2, zone)

    dx = x2 - x1
    dy = y2 - y1
    d_initial = 2 * dy - dx
    incE = 2 * dy
    incNE = 2 * (dy - dx)

    x_new, y_new = x1, y1
    while x_new <= x2:
        xp, yp = convert_back_from_zone0(x_new, y_new, zone)
        draw_point(xp, yp)

        if d_initial > 0:
            d_initial += incNE
            y_new += 1
        else:
            d_initial += incE
        x_new += 1

# ---------------- Buttons ---------------- #
def restart_button():
    """Draws the Restart button (cyan arrow)."""
    glColor3f(0, 1, 1)  
    midpoint_line(30, 560, 70, 560)
    midpoint_line(30, 560, 50, 580)
    midpoint_line(30, 560, 50, 540)

def pause_button():
    """Draws the Pause/Play button (amber)."""
    glColor3f(1, 0.64, 0)  
    if paused:
        # ▶ Play icon (triangle)
        midpoint_line(240, 540, 240, 580)
        midpoint_line(240, 540, 260, 560)
        midpoint_line(240, 580, 260, 560)
    else:
        # || Pause icon (two bars)
        midpoint_line(240, 540, 240, 580)
        midpoint_line(260, 540, 260, 580)

def exit_button():
    """Draws the Exit button (red cross)."""
    glColor3f(1, 0, 0)  
    midpoint_line(420, 540, 460, 580)
    midpoint_line(420, 580, 460, 540)

# ---------------- Catcher ---------------- #
def catcher(x, y):
    """Draws the trapezoid catcher at (x,y)."""
    glColor3f(*catcher_color)
    
    width = 90
    height = 20
    slope = 20

    x1, y1 = x, y
    x2, y2 = x + width, y
    x3, y3 = x + width - slope, y - height
    x4, y4 = x + slope, y - height

    midpoint_line(x1, y1, x2, y2)
    midpoint_line(x2, y2, x3, y3)
    midpoint_line(x3, y3, x4, y4)
    midpoint_line(x4, y4, x1, y1)

# ---------------- Diamond ---------------- #
def draw_diamond(x, y, size, color):
    """Draws a diamond shape centered at (x,y)."""
    glColor3f(*color)
    top = (x, y + size + 5)
    right = (x + size, y)
    bottom = (x, y - size - 5)
    left = (x - size, y)

    midpoint_line(*top, *right)
    midpoint_line(*right, *bottom)
    midpoint_line(*bottom, *left)
    midpoint_line(*left, *top)

def new_diamond():
    """Spawns a new diamond at random x, fixed y."""
    global diamond_x, diamond_y, diamond_color
    diamond_x = random.randint(50, window_width - 50)
    diamond_y = 550
    r, g, b =  random.uniform(0.5, 1.0), random.uniform(0.5, 1.0), random.uniform(0.5, 1.0)
    diamond_color = (r, g, b)

# ---------------- Collision ---------------- #
def hasCollided():
    """Checks if catcher and diamond overlap using AABB collision."""
    catcher_y = 50
    catcher_height = 20
    catcher_width = 100

    # Catcher bounding box
    catcher_box = {
        "x": catcher_x,
        "y": catcher_y - catcher_height,
        "width": catcher_width,
        "height": catcher_height
    }
    # Diamond bounding box
    diamond_box = {
        "x": diamond_x - diamond_size,
        "y": diamond_y - diamond_size,
        "width": diamond_size * 2,
        "height": diamond_size * 2
    }
    # AABB overlap check
    return (
        catcher_box["x"] < diamond_box["x"] + diamond_box["width"] and
        catcher_box["x"] + catcher_box["width"] > diamond_box["x"] and
        catcher_box["y"] < diamond_box["y"] + diamond_box["height"] and
        catcher_box["y"] + catcher_box["height"] > diamond_box["y"]
    )

# ---------------- Display ---------------- #
def display():
    """Main render function (draws everything)."""
    glClear(GL_COLOR_BUFFER_BIT)

    restart_button()
    pause_button()
    exit_button()

    catcher(catcher_x, 30)
    if not game_over:
        draw_diamond(diamond_x, diamond_y, diamond_size, diamond_color)

    glFlush()

# ---------------- Update ---------------- #
def update():
    """Game loop: handles movement, collisions, and game logic."""
    global diamond_y, catcher_x, last_time, score, game_over, catcher_color, diamond_speed

    # Delta time calculation
    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time

    if paused or game_over:
        glutPostRedisplay()
        return

    # Move diamond downward
    diamond_y -= diamond_speed * delta_time

    # Collision check
    if hasCollided():
        score += 1
        diamond_speed += 10   # Increase falling speed each catch
        print("Score:", score)
        new_diamond()
    elif diamond_y < 0:  # Missed → Game Over
        print("Game Over! Final Score:", score)
        game_over = True
        catcher_color = (1, 0, 0)  # Turn catcher red

    # Catcher movement
    if move_left:
        if score > 5:   # Speed boost after score > 5
            catcher_x -= catcher_speed * delta_time * 1.5
        else:
            catcher_x -= catcher_speed * delta_time
    if move_right:
        if score > 5:
            catcher_x += catcher_speed * delta_time * 1.5
        else:
            catcher_x += catcher_speed * delta_time

    # Clamp catcher so it stays inside screen
    catcher_x = max(0, min(window_width - 100, catcher_x))
    glutPostRedisplay()

# ---------------- Keyboard ---------------- #
def handle_special_key(key, state):
    """Handles arrow key press/release."""
    global move_left, move_right
    if key == GLUT_KEY_LEFT:
        move_left = state
    elif key == GLUT_KEY_RIGHT:
        move_right = state

def special_key_down(key, x, y):
    handle_special_key(key, True)

def special_key_up(key, x, y):
    handle_special_key(key, False)

# ---------------- Mouse ---------------- #
def mouse(button, state, x, y):
    """Handles mouse clicks for buttons."""
    global paused, game_over, score, catcher_x, catcher_color, diamond_speed 
    if state == GLUT_DOWN:
        # Convert OpenGL coords (origin bottom-left)
        y = window_height - y

        # Restart button
        if 30 <= x <= 70 and 540 <= y <= 580:
            print("Starting Over")
            score = 0
            game_over = False
            catcher_x = 200
            catcher_color = (1, 1, 1)
            diamond_speed = 100
            new_diamond()

        # Pause button
        elif 230 <= x <= 270 and 540 <= y <= 580:
            paused = not paused

        # Exit button
        elif 420 <= x <= 460 and 540 <= y <= 580:
            print("Goodbye! Final Score =", score)
            os._exit(0)  # Hard exit since glutLeaveMainLoop not available

# ---------------- Init ---------------- #
def init():
    """Initial OpenGL setup."""
    glClearColor(0, 0, 0, 1)  # Black background
    gluOrtho2D(0, window_width, 0, window_height)  # 2D projection

# ---------------- Main ---------------- #
glutInit()
glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
glutInitWindowSize(window_width, window_height)
glutCreateWindow(b"Catch the Diamonds - Midpoint Algorithm")

init()
glutDisplayFunc(display)
glutIdleFunc(update)
glutSpecialFunc(special_key_down)
glutSpecialUpFunc(special_key_up)
glutMouseFunc(mouse)
glutMainLoop()
