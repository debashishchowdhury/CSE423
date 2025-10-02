# TASK1:

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import random

# Window dimensions
total_width, total_height = 800, 600

# Rain parameters
rain_lines = []
rain_angle = 0
sky_brightness = 0.0
speed_of_rain = 5
NUM_DROPS = 300

# Initialize rain drops
for _ in range(NUM_DROPS):
    x = random.randint(0, total_width)
    y = random.randint(0, 800)
    rain_lines.append([x, y])

# tree using a triangle
def draw_tree(x, y):
    glBegin(GL_TRIANGLES)
    glColor3f(0.0, 1.0, 0.0)
    glVertex2f(x, y)
    glVertex2f(x - 20, y - 80)
    glVertex2f(x + 20, y - 80)
    glEnd()

# multiple trees in a line
def draw_tree_line():
    for x in range(10, 900, 40):
        draw_tree(x, 420)

def house_draw():
    glBegin(GL_TRIANGLES)
    glColor3f(1.0, 1.0, 0.9)
    #1st triangle
    glVertex2f(275, 225)  
    glVertex2f(525, 225)   
    glVertex2f(525, 345)   
    #2nd triangle
    glVertex2f(275, 225)   
    glVertex2f(275, 345)   
    glVertex2f(525, 345)   
    glEnd()

    # Roof
    glBegin(GL_TRIANGLES)
    glColor3f(0.80, 0.33, 0.20)
    glVertex2f(260, 345)   
    glVertex2f(540, 345)   
    glVertex2f(400, 425)   
    glEnd()

    # Door
    glBegin(GL_TRIANGLES)
    glColor3f(0.2, 0.6, 1.0)
    glVertex2f(365, 225)
    glVertex2f(435, 225)
    glVertex2f(435, 295)

    glVertex2f(365, 225)
    glVertex2f(365, 295)
    glVertex2f(435, 295)
    glEnd()

    # Knob
    glPointSize(4)
    glBegin(GL_POINTS)
    glColor3f(0, 0, 0)
    glVertex2f(430, 255)
    glEnd()

    # Windows
    glColor3f(0.2, 0.6, 1.0)
    glBegin(GL_TRIANGLES)

    # Left window
    glVertex2f(295, 280)
    glVertex2f(325, 280)
    glVertex2f(325, 310)

    glVertex2f(295, 280)
    glVertex2f(295, 310)
    glVertex2f(325, 310)

    # Right window
    glVertex2f(475, 280)
    glVertex2f(505, 280)
    glVertex2f(505, 310)

    glVertex2f(475, 280)
    glVertex2f(475, 310)
    glVertex2f(505, 310)
    glEnd()

    # Window Grills
    glColor3f(0, 0, 0)
    glBegin(GL_LINES)
    # Left window
    glVertex2f(310, 280)
    glVertex2f(310, 310)
    glVertex2f(295, 295)
    glVertex2f(325, 295)
    # Right window
    glVertex2f(490, 280)
    glVertex2f(490, 310)
    glVertex2f(475, 295)
    glVertex2f(505, 295)
    glEnd()

def draw_background():
    # Sky
    glBegin(GL_TRIANGLES)
    glColor3f(sky_brightness, sky_brightness, sky_brightness)
    glVertex2f(0, 400)
    glVertex2f(800, 400)
    glVertex2f(800, 800)

    glVertex2f(0, 400)
    glVertex2f(0, 800)
    glVertex2f(800, 800)
    glEnd()

    # Ground
    glBegin(GL_TRIANGLES)
    glColor3f(0.6, 0.4, 0.2)
    glVertex2f(0, 0)
    glVertex2f(800, 0)
    glVertex2f(800, 400)

    glVertex2f(0, 0)
    glVertex2f(0, 400)
    glVertex2f(800, 400)
    glEnd()

# Draw all rain drops
def draw_rain():
    if sky_brightness > 0.5:
        glColor3f(0.0, 0.5, 1.0)  # Blue rain in day
    else:
        glColor3f(1.0, 1.0, 1.0)  # White rain in night

    glBegin(GL_LINES)
    for drop in rain_lines:
        x, y = drop
        glVertex2f(x, y)
        glVertex2f(x + rain_angle, y - 15)
    glEnd()

def update_rain():
    for drop in rain_lines:
        drop[0] += rain_angle
        drop[1] -= speed_of_rain

        # Loop left-right
        if drop[0] < 0:
            drop[0] += total_width
        elif drop[0] > total_width:
            drop[0] -= total_width

        # Loop top to bottom
        if drop[1] < 0:
            drop[0] = random.randint(0, total_width)
            drop[1] = random.randint(total_height, total_height + 200)

def iterate():
    glViewport(0, 0, 800, 800)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, 800, 0.0, 800, 0.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    iterate()
    draw_background()
    draw_tree_line()
    house_draw()
    draw_rain()
    glutSwapBuffers()

def animate():
    update_rain()
    glutPostRedisplay()

def keyboard(key, x, y):
    global sky_brightness, speed_of_rain
    if key == b'd':
        sky_brightness = min(1.0, sky_brightness + 0.02) # sky color will be white from black
    elif key == b'n':
        sky_brightness = max(0.0, sky_brightness - 0.02) # sky color will be black from white
    elif key == b'f':
        speed_of_rain = min(20, speed_of_rain + 1) # increasse rain speed 
    elif key == b's':
        speed_of_rain = max(1, speed_of_rain - 1) # decrease rain speed

def specialKeys(key, x, y):
    global rain_angle
    if key == GLUT_KEY_LEFT:
        rain_angle = max(-5, rain_angle - 0.5)
    elif key == GLUT_KEY_RIGHT:
        rain_angle = min(5, rain_angle + 0.5)

glutInit()
glutInitDisplayMode(GLUT_RGBA)
glutInitWindowSize(total_width, total_height)
glutInitWindowPosition(100, 100)
glutCreateWindow(b"Task 1: Building a House in Rainfall")
glutDisplayFunc(showScreen)
glutIdleFunc(animate)
glutKeyboardFunc(keyboard)
glutSpecialFunc(specialKeys)
glutMainLoop()
