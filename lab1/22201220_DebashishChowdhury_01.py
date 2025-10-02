# #TASK1
# from OpenGL.GL import *
# from OpenGL.GLUT import *
# from OpenGL.GLU import *

# import random

# total_width, total_height = 800, 600
# rain_lines = []
# rain_angle = 0
# sky_brightness = 0.0
# speed_of_rain = 5

# NUM_DROPS = 300
# for _ in range(NUM_DROPS):
#     x = random.randint(0, total_width)
#     y = random.randint(0, 800)
#     rain_lines.append([x, y])

# def draw_tree(x, y):
#     glBegin(GL_TRIANGLES)
#     glColor3f(0.0, 1.0, 0.0)
#     glVertex2f(x, y)
#     glVertex2f(x - 20, y - 80)
#     glVertex2f(x + 20, y - 80)
#     glEnd()

# def draw_tree_line():
#     for x in range(10, 900, 40):
#         draw_tree(x, 420)

# def house_draw():
#     #body
#     glBegin(GL_TRIANGLES)
#     glColor3f(1.0, 1.0, 0.9)
#     glVertex2f(275, 225)
#     glVertex2f(525, 225)
#     glVertex2f(525, 345)

#     glVertex2f(275, 225)
#     glVertex2f(275, 345)
#     glVertex2f(525, 345)
#     glEnd()
#     #roof
#     glBegin(GL_TRIANGLES)
#     glColor3f(0.80, 0.33, 0.20)
#     glVertex2f(260, 345)
#     glVertex2f(540, 345)
#     glVertex2f(400, 425)
#     glEnd()
#     #door
#     glBegin(GL_TRIANGLES)
#     glColor3f(0.2, 0.6, 1.0)
#     glVertex2f(365, 225)
#     glVertex2f(435, 225)
#     glVertex2f(435, 295)

#     glVertex2f(365, 225)
#     glVertex2f(365, 295)
#     glVertex2f(435, 295)
#     glEnd()
#     #knob
#     glPointSize(4)
#     glBegin(GL_POINTS)
#     glColor3f(0, 0, 0)
#     glVertex2f(430, 255)
#     glEnd()
#     #window
#     glColor3f(0.2, 0.6, 1.0)
#     glBegin(GL_TRIANGLES)
#     glVertex2f(295, 280)
#     glVertex2f(325, 280)
#     glVertex2f(325, 310)

#     glVertex2f(295, 280)
#     glVertex2f(295, 310)
#     glVertex2f(325, 310)

#     glVertex2f(475, 280)
#     glVertex2f(505, 280)
#     glVertex2f(505, 310)

#     glVertex2f(475, 280)
#     glVertex2f(475, 310)
#     glVertex2f(505, 310)
#     glEnd()

#     #grills
#     glColor3f(0, 0, 0)
#     glBegin(GL_LINES)
#     glVertex2f(310, 280)
#     glVertex2f(310, 310)
#     glVertex2f(295, 295)
#     glVertex2f(325, 295)

#     glVertex2f(490, 280)
#     glVertex2f(490, 310)
#     glVertex2f(475, 295)
#     glVertex2f(505, 295)
#     glEnd()

# def draw_background():
#     glBegin(GL_TRIANGLES)
#     glColor3f(sky_brightness, sky_brightness, sky_brightness)
#     glVertex2f(0, 400)
#     glVertex2f(800, 400)
#     glVertex2f(800, 800)

#     glVertex2f(0, 400)
#     glVertex2f(0, 800)
#     glVertex2f(800, 800)
#     glEnd()

#     glBegin(GL_TRIANGLES)
#     glColor3f(0.6, 0.4, 0.2)    
#     glVertex2f(0, 0)
#     glVertex2f(800, 0)
#     glVertex2f(800, 400)

#     glVertex2f(0, 0)
#     glVertex2f(0, 400)
#     glVertex2f(800, 400)
#     glEnd()

# def draw_rain():
#     if sky_brightness > 0.5:
#         glColor3f(0.0, 0.5, 1.0)  
#     else:
#         glColor3f(1.0, 1.0, 1.0)  

#     glBegin(GL_LINES)
#     for drop in rain_lines:
#         x, y = drop
#         glVertex2f(x, y)
#         glVertex2f(x + rain_angle, y - 15)
#     glEnd()

# def update_rain():
#     for drop in rain_lines:
#         drop[0] += rain_angle
#         drop[1] -= speed_of_rain
#         if drop[0] < 0:
#             drop[0] = total_width + drop[0]
#         elif drop[0] > total_width:
#             drop[0] = drop[0] - total_width
#         if drop[1] < 0:
#             drop[0] = random.randint(0, total_width)
#             drop[1] = random.randint(total_height, total_height + 200)

# def iterate():
#     glViewport(0, 0, 800, 800)
#     glMatrixMode(GL_PROJECTION)
#     glLoadIdentity()
#     glOrtho(0.0, 800, 0.0, 800, 0.0, 1.0)
#     glMatrixMode(GL_MODELVIEW)
#     glLoadIdentity()

# def showScreen():
#     glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
#     glLoadIdentity()
#     iterate()
#     draw_background()
#     draw_tree_line()
#     house_draw()
#     draw_rain()
#     glutSwapBuffers()

# def animate():
#     update_rain()
#     glutPostRedisplay()

# def keyboardListener(key, x, y):
#     global sky_brightness
#     global speed_of_rain
#     if key == b'd':
#         sky_brightness = min(1.0, sky_brightness + 0.02)
#     elif key == b'n':
#         sky_brightness = max(0.0, sky_brightness - 0.02)

#     elif key == b'f':
#         speed_of_rain = min(20, speed_of_rain + 1)
#     elif key == b's':
#         speed_of_rain = max(1, speed_of_rain - 1)

# def specialKeyListener(key, x, y):
#     global rain_angle
#     if key == GLUT_KEY_LEFT:
#         rain_angle -= 0.5
#         if rain_angle < -5:
#             rain_angle = -5
#     elif key == GLUT_KEY_RIGHT:
#         rain_angle += 0.5
#         if rain_angle > 5:
#             rain_angle = 5


# glutInit()
# glutInitDisplayMode(GLUT_RGBA)
# glutInitWindowSize(total_width, total_height)
# glutInitWindowPosition(100, 100)
# glutCreateWindow(b"Task 1: Building a House in Rainfall")
# glutDisplayFunc(showScreen)
# glutIdleFunc(animate)
# glutKeyboardFunc(keyboardListener)
# glutSpecialFunc(specialKeyListener)

# glutMainLoop()

# #================================================================================================

#TASK2
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random

total_width, total_height = 800, 600
points = []
x_coordinate = []
y_coordinate = []
colors = []

blink_state = True
freeze = False
blink = False
speed = 1

directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

def init():
    glClearColor(0.0, 0.0, 0.0, 1.0) 
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, total_width, 0, total_height)

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glPointSize(5)

    global blink_state
    if blink and not freeze:
        blink_state = not blink_state

    for i in range(len(points)):
        if blink and not blink_state:
            continue  
        r, g, b = colors[i]
        glColor3f(r, g, b)
        glBegin(GL_POINTS)
        x, y = points[i]
        glVertex2f(x, y)
        glEnd()

    glutSwapBuffers()

def update():
    if freeze:
        glutPostRedisplay()
        return

    for i in range(len(points)):
        x, y = points[i]
        new_x = x + x_coordinate[i] * speed
        new_y = y + y_coordinate[i] * speed

        if new_x <= 0 or new_x >= total_width:
            x_coordinate[i] *= -1
        if new_y <= 0 or new_y >= total_height:
            y_coordinate[i] *= -1

        points[i] = (x + x_coordinate[i] * speed, y + y_coordinate[i] * speed)

    glutPostRedisplay()

def MouseListener(button, state, x, y):
    global blink
    y = total_height - y  

    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        if 0 < x < total_width and 0 < y < total_height:
            new_direction = random.choice(directions)
            r, g, b = random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1)
            points.append((x, y))
            x_coordinate.append(new_direction[0]), y_coordinate.append(new_direction[1])
            colors.append((r, g, b))

    elif button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        blink = not blink

def keyboardListener(key, x, y):
    global freeze
    if key == b' ':
        freeze = not freeze

def specialKeyListener(key, x, y):
    global speed
    if key == GLUT_KEY_UP:
        speed += 1
    elif key == GLUT_KEY_DOWN:
        speed = max(1, speed - 1)

def reshape(width, height):
    global total_width, total_height
    total_width, total_height = width, height
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)

glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
glutInitWindowSize(total_width, total_height)
glutInitWindowPosition(100, 100)
glutCreateWindow(b"Task2: Amazing Box")

init()
glutDisplayFunc(display)
glutIdleFunc(update)
glutMouseFunc(MouseListener)
glutKeyboardFunc(keyboardListener)
glutSpecialFunc(specialKeyListener)
glutReshapeFunc(reshape)
glutMainLoop()
