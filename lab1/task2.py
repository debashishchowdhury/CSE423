from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random

total_width, total_height = 800, 600

points = []
x_coordinate = []
y_coordinate = []
colors = []

blink_state = True       # currently visibility of points
freeze = False           # moving or not
blink = False            # blinking or not
speed = 1               

directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)  # Set background color to black
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, total_width, 0, total_height)  # 2D coordinate system

def display():
    glClear(GL_COLOR_BUFFER_BIT)  # Clear the screen
    glPointSize(8)  # point size

    global blink_state
    # Toggle blink state only if blink is active and not frozen
    if blink and not freeze:
        blink_state = not blink_state

    # Loop through all points
    for i in range(len(points)):
        # If blinking is on and current state is "off", skip drawing
        if blink and not blink_state:
            continue

        # Set color of the current point
        r, g, b = colors[i]
        glColor3f(r, g, b)

        # Draw the point
        glBegin(GL_POINTS)
        x, y = points[i]
        glVertex2f(x, y)
        glEnd()

    glutSwapBuffers()  #to show the drawn frame

def update():
    # if not freeze == true, redraw without movement
    if freeze:
        glutPostRedisplay()
        return

    # Move each point in its current direction
    for i in range(len(points)):
        x, y = points[i]
        new_x = x + x_coordinate[i] * speed
        new_y = y + y_coordinate[i] * speed

        # Bounce off the left-right borders
        if new_x <= 0 or new_x >= total_width:
            x_coordinate[i] *= -1

        # Bounce off the top/bottom borders
        if new_y <= 0 or new_y >= total_height:
            y_coordinate[i] *= -1

        # Update the new position
        points[i] = (x + x_coordinate[i] * speed, y + y_coordinate[i] * speed)

    glutPostRedisplay()  # Redraw the screen

def MouseListener(button, state, x, y):
    global blink

    # Convert mouse y-coordinate (bottom-left as origin)
    y = total_height - y

    # Right-click to add a new moving point
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        if 0 < x < total_width and 0 < y < total_height:
            new_direction = random.choice(directions)  # Pick random diagonal direction
            r, g, b = random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1)  # Random color
            points.append((x, y))
            x_coordinate.append(new_direction[0])
            y_coordinate.append(new_direction[1])
            colors.append((r, g, b))

    # Left-click to toggle blinking on/off
    elif button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        blink = not blink

# --- Keyboard interaction handler (normal keys) ---
def keyboardListener(key, x, y):
    global freeze
    # Press spacebar to freeze/unfreeze the animation
    if key == b' ':
        freeze = not freeze

# --- Special keys handler (arrow keys) ---
def specialKeyListener(key, x, y):
    global speed
    # UP arrow to increase speed
    if key == GLUT_KEY_UP:
        speed += 1
    # DOWN arrow to decrease speed (minimum 1)
    elif key == GLUT_KEY_DOWN:
        speed = max(1, speed - 1)

# --- Window resize handler ---
def reshape(width, height):
    global total_width, total_height
    total_width, total_height = width, height

    # Update the viewport and projection matrix to match new size
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)

# --- GLUT setup and main loop ---
glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)  # Enable double buffering and RGB color
glutInitWindowSize(total_width, total_height)  # Initial window size
glutInitWindowPosition(100, 100)  # Window position on screen
glutCreateWindow(b"Task2: Amazing Box")  # Window title

# Registering all the functions
init()
glutDisplayFunc(display)
glutIdleFunc(update)  # Continuously called when idle (used for animation)
glutMouseFunc(MouseListener)
glutKeyboardFunc(keyboardListener)
glutSpecialFunc(specialKeyListener)
glutReshapeFunc(reshape)

# Start the main loop
glutMainLoop()
