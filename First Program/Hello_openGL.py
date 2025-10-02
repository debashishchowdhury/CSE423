from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *


def draw_points(x, y):
    glPointSize(5) #pixel size. by default 1 thake
    glBegin(GL_POINTS)
    glVertex2f(x,y)
    glColor3f(1.0, 1.0, 1.0)
    glVertex2f(100,100) #jekhane show korbe pixel
    glEnd()

    glBegin(GL_LINES)
    glVertex2f(50, 50)
    glVertex2f(200, 200)
    glColor3f(0, 1, 1)
    glVertex2f(100, 100)
    glColor3f(1, 0, 0)
    glVertex2f(100, 300)
    glEnd()
    
    glBegin(GL_TRIANGLES)
    glVertex2f(250, 300)
    glColor3f(1,1,1)
    glVertex2f(250, 400)
    glColor3f(0, 1, 1)
    glVertex2f(350, 300)
    glEnd()

    # glBegin(GL_QUADS)
    # glVertex2d(100, 120)
    # glColor3f(1, 0, 1)
    # glVertex2d(50, 120)
    # glColor3f(0,1,0)
    # glVertex2d(50, 140)
    # glColor3f(0, 1, 0)
    # glVertex2d(100, 140)
    # glEnd()



def iterate():
    glViewport(0, 0, 500, 500) #x_min, y_min, x_max, y_max
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0.0, 500, 0.0, 500, 0.0, 1.0) #left, right, bottom, top, near, far
    glMatrixMode (GL_MODELVIEW)
    glLoadIdentity()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity() #loads an identity matrix
    iterate()
    glColor3f(1.0, 0.0, 0.0) #konokichur color set (RGB)
    #call the draw methods here
    draw_points(250, 250)
    glutSwapBuffers()



glutInit()
glutInitDisplayMode(GLUT_RGBA)
glutInitWindowSize(500, 500) #window size
glutInitWindowPosition(00, 00)
wind = glutCreateWindow(b"CSE423 Lab1") #window name
glutDisplayFunc(showScreen) # showScreen is a callback function.

glutMainLoop()