from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import time
import os

window_width, window_height = 500, 600

paused = False
game_over = False
score = 0

catcher_x = 200       
catcher_speed = 200
catcher_height = 20
catcher_width = 90
left_movement, right_movement = False, False
catcher_color = (1, 1, 1)  

diamond_x, diamond_y = 250, 550
diamond_size = 13
diamond_speed = 100   
diamond_color = (1, 1, 1)  

last_time = time.time()

def draw_point(x, y):
    glBegin(GL_POINTS)
    glVertex2f(x, y)
    glEnd()

def find_zone(x1, y1, x2, y2):
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

def convert_to_zone0(x, y, zone):
    if zone == 0: return x, y
    elif zone == 1: return y, x
    elif zone == 2: return y, -x
    elif zone == 3: return -x, y
    elif zone == 4: return -x, -y
    elif zone == 5: return -y, -x
    elif zone == 6: return -y, x
    elif zone == 7: return x, -y

def convert_back_from_zone0(x, y, zone):
    if zone == 0: return x, y
    elif zone == 1: return y, x
    elif zone == 2: return -y, x
    elif zone == 3: return -x, y
    elif zone == 4: return -x, -y
    elif zone == 5: return -y, -x
    elif zone == 6: return y, -x
    elif zone == 7: return x, -y

def midpoint_line(x1, y1, x2, y2):

    zone = find_zone(x1, y1, x2, y2)

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

def restart_button():
    glColor3f(0, 1, 1)  
    midpoint_line(30, 560, 70, 560)
    midpoint_line(30, 560, 50, 580)
    midpoint_line(30, 560, 50, 540)

def pause_play_button():
    glColor3f(1, 0.64, 0)  
    if paused:
        midpoint_line(240, 540, 240, 580)
        midpoint_line(240, 540, 260, 560)
        midpoint_line(240, 580, 260, 560)
    else:
        midpoint_line(240, 540, 240, 580)
        midpoint_line(260, 540, 260, 580)

def exit_button():
    glColor3f(1, 0, 0)  
    midpoint_line(420, 540, 460, 580)
    midpoint_line(420, 580, 460, 540)

def catcher(x, y):
    global catcher_height, catcher_width 

    glColor3f(*catcher_color)
    
    slope = 20

    x1, y1 = x, y
    x2, y2 = x + catcher_width, y
    x3, y3 = x + catcher_width - slope, y - catcher_height
    x4, y4 = x + slope, y - catcher_height

    midpoint_line(x1, y1, x2, y2)
    midpoint_line(x2, y2, x3, y3)
    midpoint_line(x3, y3, x4, y4)
    midpoint_line(x4, y4, x1, y1)

def diamond(x, y, size, color):
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
    global diamond_x, diamond_y, diamond_color
    diamond_x = random.randint(10, window_width - 10)
    diamond_y = 550
    r, g, b =  random.uniform(0.5, 1.0), random.uniform(0.5, 1.0), random.uniform(0.5, 1.0)
    diamond_color = (r, g, b)

def hasCollided():
    global catcher_height, catcher_width 

    catcher_y = 50

    catcher_box = {
        "x": catcher_x,
        "y": catcher_y - catcher_height,
        "width": catcher_width,
        "height": catcher_height
    }
    diamond_box = {
        "x": diamond_x - diamond_size,
        "y": diamond_y - diamond_size,
        "width": diamond_size * 2,
        "height": diamond_size * 2
    }
    return (
        catcher_box["x"] < diamond_box["x"] + diamond_box["width"] and
        catcher_box["x"] + catcher_box["width"] > diamond_box["x"] and
        catcher_box["y"] < diamond_box["y"] + diamond_box["height"] and
        catcher_box["y"] + catcher_box["height"] > diamond_box["y"]
    )

def display():
    glClear(GL_COLOR_BUFFER_BIT)

    restart_button()
    pause_play_button()
    exit_button()

    catcher(catcher_x, 30)
    if not game_over:
        diamond(diamond_x, diamond_y, diamond_size, diamond_color)

    glFlush()

def update():
    global diamond_y, catcher_x, last_time, score, game_over, catcher_color, diamond_speed, catcher_width

    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time

    if paused or game_over:
        glutPostRedisplay()
        return

    diamond_y -= diamond_speed * delta_time

    if hasCollided():
        score += 1
        diamond_speed+= 10
        print("Score:", score)
        new_diamond()
    elif diamond_y < 0:
        print("Game Over! Final Score:", score)
        game_over = True
        catcher_color = (1, 0, 0)

    if left_movement:
        if score > 5:
            catcher_x -= catcher_speed * delta_time * 1.5
        else:
            catcher_x -= catcher_speed * delta_time
    if right_movement:
        if score > 5:
            catcher_x += catcher_speed * delta_time * 1.5
        else:
            catcher_x += catcher_speed * delta_time

    catcher_x = max(0, min(window_width - catcher_width, catcher_x))
    glutPostRedisplay()

def specialKeyListener(key, state):
    global left_movement, right_movement
    if key == GLUT_KEY_LEFT:
        left_movement = state
    elif key == GLUT_KEY_RIGHT:
        right_movement = state

def special_key_down(key, x, y):
    specialKeyListener(key, True)

def special_key_up(key, x, y):
    specialKeyListener(key, False)

def mouseListener(button, state, x, y):
    global paused, game_over, score, catcher_x, catcher_color, diamond_speed 
    if state == GLUT_DOWN:
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
            os._exit(0)
            # glutLeaveMainLoop()

def init():
    glClearColor(0, 0, 0, 1)
    gluOrtho2D(0, window_width, 0, window_height)

glutInit()
glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
glutInitWindowSize(window_width, window_height)
glutCreateWindow(b"Catch the Diamonds - Midpoint Algorithm")

init()
glutDisplayFunc(display)
glutIdleFunc(update)
glutSpecialFunc(special_key_down)
glutSpecialUpFunc(special_key_up)
glutMouseFunc(mouseListener)
glutMainLoop()
