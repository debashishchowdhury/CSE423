from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random

fovY = 100  # Field of view
GRID_LENGTH = 500  # Length of grid lines
tile_size = 50

# Camera related variables
camera_position = (0, 500, 500)
camera_radius = 600
camera_angle = 0
camera_height = 300
first_person_mode = False

#Player related variables
player_start_position = (0, 0, 0)
player_current_position = [0, 0, 0]
player_angle = 90   # facing angle
player_speed = 10
player_radius = 30  # approximate player size in X-Y plane
player_remaining_life = 5
score = 0

#Bullet related variables
missed_bullets = 0
maximum_bullets_miss = 10
bullet_speed = 5
bullet_radius = 3   # small bullet cube
bullets = []

#Enemy related variables
enemy_speed = 0.2
enemies = []

#Cheat mode variables
cheat_mode = False
automatic_gun_follow = False
cheat_fire_counter = 0   # rate limiter for cheat bullets
cheat_fire_ready = False
CHEAT_FIRE_RATE = 4    # fire at no of frames
CHEAT_ANGLE_THRESHOLD = 180  # firing around a specific angle

game_over = False

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    # Save current matrix mode
    current_mode = glGetIntegerv(GL_MATRIX_MODE)

    # Switch to projection
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)

    # Switch to modelview
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Draw text
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

    # Restore modelview
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)

    # Restore projection
    glPopMatrix()

    # Restore whichever mode was active before
    glMatrixMode(current_mode)

def keyboardListener(key, x, y):
    global player_current_position, player_angle, player_speed, GRID_LENGTH, cheat_mode, automatic_gun_follow
    # Move forward
    if key == b'w':
        forward_move_angle = math.radians(player_angle)
        new_x = player_current_position[0] - math.cos(forward_move_angle) * player_speed
        new_y = player_current_position[1] - math.sin(forward_move_angle) * player_speed
        # Check boundaries
        if -GRID_LENGTH < new_x < GRID_LENGTH and -GRID_LENGTH < new_y < GRID_LENGTH:
            player_current_position[0] = new_x
            player_current_position[1] = new_y
    # Move backward 
    elif key == b's':
        backward_move_angle = math.radians(player_angle)
        new_x = player_current_position[0] + math.cos(backward_move_angle) * player_speed
        new_y = player_current_position[1] + math.sin(backward_move_angle) * player_speed
        # Check boundaries
        if -GRID_LENGTH < new_x < GRID_LENGTH and -GRID_LENGTH < new_y < GRID_LENGTH:
            player_current_position[0] = new_x
            player_current_position[1] = new_y
    # Rotate gun left 
    elif key == b'a':
        player_angle += 5   # degrees
    # Rotate gun right
    elif key == b'd':
        player_angle -= 5   # degrees
    # for cheat mode control
    elif key == b'c':
        cheat_mode = not cheat_mode
        if cheat_mode:
            print("Cheat mode:", "ON")
        else:
            print("Cheat mode:", "OFF")
    # for automatic_gun_follow
    elif key == b'v':
        if cheat_mode and first_person_mode:
            automatic_gun_follow = not automatic_gun_follow
            if automatic_gun_follow:
                print("Automatic Gun Follow:", "ON")
            else:
                print("Automatic Gun Follow", "OFF")
    elif key == b'r':
        restart_game()

def specialKeyListener(key, x, y):
    global camera_height, camera_angle
    if key == GLUT_KEY_LEFT:
        camera_angle -= 2
    elif key == GLUT_KEY_RIGHT:
        camera_angle += 2
    elif key == GLUT_KEY_UP:
        camera_height += 10
    elif key == GLUT_KEY_DOWN:
        if camera_height > 50:
            camera_height -= 10

def mouseListener(button, state, x, y):
    global first_person_mode, bullets

    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN: # will change camera mode from third person (default) to first person
        first_person_mode = not first_person_mode
    elif button == GLUT_LEFT_BUTTON and state == GLUT_DOWN: # will shoot bullets
        if cheat_mode or missed_bullets < maximum_bullets_miss: # when cheat mode on will shoot infinite bullets
            bullets.append({
                "bullet_x": player_current_position[0],
                "bullet_y": player_current_position[1],
                "bullet_z": 100,   # chest/gun 
                "bullet_angle": player_angle,
                "cheat_mode_bullet": False
            })

def setupCamera():
    global first_person_mode, cheat_mode, automatic_gun_follow
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()

    if first_person_mode:
        gluPerspective(100, 1.25, 0.1, 1500)
    else:
        gluPerspective(fovY, 1.25, 0.1, 1500)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    if first_person_mode:
        # First-person camera
        head_x = player_current_position[0]
        head_y = player_current_position[1]
        head_z = player_current_position[2] + 150  # head height
        player_rotation = math.radians(player_angle)

        if cheat_mode:
            if automatic_gun_follow:
                # Head view with following the gun
                center_x = head_x - math.cos(player_rotation) * 100
                center_y = head_y - math.sin(player_rotation) * 100
                center_z = head_z
            else:
                # Head view without following the gun
                base_angle = math.radians(90)   # fixed forward
                center_x = head_x - math.cos(base_angle) * 100
                center_y = head_y - math.sin(base_angle) * 100
                center_z = head_z
        else:
            # Normal FP, always players facing direction 
            center_x = head_x - math.cos(player_rotation) * 100
            center_y = head_y - math.sin(player_rotation) * 100
            center_z = head_z

        gluLookAt(head_x, head_y, head_z,
                  center_x, center_y, center_z,
                  0, 0, 1)
    else:
        # Third person mode
        cam_angle_rad = math.radians(camera_angle)
        eye_x = player_current_position[0] + camera_radius * math.cos(cam_angle_rad)
        eye_y = player_current_position[1] + camera_radius * math.sin(cam_angle_rad)
        eye_z = camera_height

        gluLookAt(eye_x, eye_y, eye_z,
                  player_current_position[0],
                  player_current_position[1],
                  player_current_position[2] + 90,  
                  0, 0, 1)

def idle():
    if not game_over:
        move_enemies()
        game_collisions()
        player_cheat_mode()
    glutPostRedisplay()

# Grid and walls
def draw_grid_board():
    global GRID_LENGTH, tile_size

    for i in range(-GRID_LENGTH, GRID_LENGTH, tile_size):
        for j in range(-GRID_LENGTH, GRID_LENGTH, tile_size):
            if (i // tile_size + j // tile_size) % 2 == 0:
                glColor3f(1, 1, 1) # white
            else:
                glColor3f(0.7, 0.5, 0.95) # light purple

            #. drawing single tile, square
            glBegin(GL_QUADS)
            glVertex3f(i, j, 0)
            glVertex3f(i + tile_size, j, 0)
            glVertex3f(i + tile_size, j + tile_size, 0)
            glVertex3f(i, j + tile_size, 0)
            glEnd()

def draw_walls():
    global GRID_LENGTH
    wall_height = 120

    # Four distinct colors
    colors = [
        (0, 0, 1),          # Blue
        (0, 1, 0),          # Green
        (0.53, 0.81, 0.92), # Sky Blue
        (1, 1, 1)           # White
    ]
    # Four walls (Bottom, Top, Left, Right)
    walls = [
        (-GRID_LENGTH, -GRID_LENGTH,  GRID_LENGTH, -GRID_LENGTH),  
        (-GRID_LENGTH,  GRID_LENGTH,  GRID_LENGTH,  GRID_LENGTH),  
        (-GRID_LENGTH, -GRID_LENGTH, -GRID_LENGTH,  GRID_LENGTH),  
        ( GRID_LENGTH, -GRID_LENGTH,  GRID_LENGTH,  GRID_LENGTH)   
    ]
    glBegin(GL_QUADS)
    for i in range(len(walls)):
        x1, y1, x2, y2 = walls[i]
        r, g, b = colors[i]
        glColor3f(r, g, b)
        # vertical rectangle for wall, bottom, left, right || top, right, left
        glVertex3f(x1, y1, 0)
        glVertex3f(x2, y2, 0)
        glVertex3f(x2, y2, wall_height)
        glVertex3f(x1, y1, wall_height)
    glEnd()

# Player drawing
def draw_player():
    glPushMatrix()
    glTranslatef(player_current_position[0], player_current_position[1], player_current_position[2])  

    if not game_over:
        glRotatef(player_angle, 0, 0, 1)  #Player will stand normally
    else:
        glRotatef(90, 1, 0, 0)  #Player will lay down on the floor

    if first_person_mode:
        # Only draw the gun in first-person mode
        glColor3f(0.844, 0.844, 0.844)
        glPushMatrix()
        glTranslatef(0, 0, 100)
        glRotatef(-90, 0, 1, 0)
        gluCylinder(gluNewQuadric(), 12, 7, 80, 10, 10)
        glPopMatrix()
    else:
        # body
        glColor3f(0.1, 0.5, 0.1)
        glPushMatrix()
        glTranslatef(0, 0, 90)
        glScalef(0.5, 1, 1)      # X, Y, Z scale taller in Z axis
        glutSolidCube(60)
        glPopMatrix()
        
        # head
        glColor3f(0, 0, 0)
        glPushMatrix()
        glTranslatef(0, 0, 150)
        gluSphere(gluNewQuadric(), 25, 10, 10)
        glPopMatrix()
        
        # left leg
        glColor3f(0, 0, 1)
        glPushMatrix()
        glTranslatef(-15, -15, 0)
        gluCylinder(gluNewQuadric(), 7, 12, 60, 10, 10)
        glPopMatrix()
        
        # right leg
        glColor3f(0, 0, 1)
        glPushMatrix()
        glTranslatef(-15, 15, 0)
        gluCylinder(gluNewQuadric(), 7, 12, 60, 10, 10)
        glPopMatrix()
        
        # gun
        glColor3f(0.753, 0.753, 0.753)
        glPushMatrix()
        glTranslatef(0, 0, 100)
        glRotatef(-90, 0, 1, 0)
        gluCylinder(gluNewQuadric(), 12, 7, 80, 10, 10)
        glPopMatrix()
        
        # left hand
        glColor3f(1, 0.878, 0.741)
        glPushMatrix()
        glTranslatef(-20, -25, 100)
        glRotatef(-90, 0, 1, 0)
        gluCylinder(gluNewQuadric(), 10, 6, 30, 10, 10)
        glPopMatrix()
        
        # right hand
        glColor3f(1, 0.878, 0.741)
        glPushMatrix()
        glTranslatef(-20, 25, 100)
        glRotatef(-90, 0, 1, 0)
        gluCylinder(gluNewQuadric(), 10, 6, 30, 10, 10)
        glPopMatrix()
    
    glPopMatrix()
# Draw bullets and shooting
def draw_and_shoot_bullets():
    global bullets, missed_bullets, game_over, score, cheat_fire_ready

    if game_over: # if game over no shooting and drawing bullets
        return
    
    # Bullet creation
    if cheat_mode:
        # Fire bullets automatically when cheat mode is on
        if cheat_fire_ready: # this comes from cheat_mode() which allows to fire 
            rad = math.radians(player_angle)
            offset_distance = 40 # bullet create just infront of player
            bullet_x = player_current_position[0] + math.cos(rad) * offset_distance
            bullet_y = player_current_position[1] + math.sin(rad) * offset_distance
            bullet_z = 100

            bullets.append({
                "bullet_x": bullet_x,
                "bullet_y": bullet_y,
                "bullet_z": bullet_z,
                "bullet_angle": player_angle,
                "cheat_mode_bullet": True
            })
            cheat_fire_ready = False

    #Bullet movement, and drawing
    current_bullets = []
    for i in bullets:
        # Move bullet forward
        bullet_angle = math.radians(i["bullet_angle"])
        i["bullet_x"] -= math.cos(bullet_angle) * bullet_speed
        i["bullet_y"] -= math.sin(bullet_angle) * bullet_speed

        # Check if outside grid
        if abs(i["bullet_x"]) > GRID_LENGTH or abs(i["bullet_y"]) > GRID_LENGTH:
            if cheat_mode == False and i["cheat_mode_bullet"] == False:  # count only in normal mode only
                missed_bullets += 1
            continue # no bullet drawing if cheat mode on

        # Draw bullet
        glColor3f(1, 0, 0)
        glPushMatrix()
        glTranslatef(i["bullet_x"], i["bullet_y"], i["bullet_z"])
        glutSolidCube(7)
        glPopMatrix()

        current_bullets.append(i)

    bullets = current_bullets

    # Game over condition
    if not cheat_mode and missed_bullets >= maximum_bullets_miss:
        game_over = True
        print("GAME OVER — You ran out of bullets!")

#draw enemies and movement
def draw_enemies():
    global enemies
    # Always make sure we have exactly 5 enemies
    while len(enemies) < 5:
        safe_distance = 350
        enemy_angle = random.uniform(0, 2 * math.pi)
        distance_from_player = random.uniform(safe_distance, GRID_LENGTH - 55)

        enemy_x = player_current_position[0] + distance_from_player * math.cos(enemy_angle)
        enemy_y = player_current_position[1] + distance_from_player * math.sin(enemy_angle)

        # Clamp inside grid
        enemy_x = max(-GRID_LENGTH + 55, min(GRID_LENGTH - 55, enemy_x))
        enemy_y = max(-GRID_LENGTH + 55, min(GRID_LENGTH - 55, enemy_y))

        enemies.append({
            'x': enemy_x, 'y': enemy_y, 'z': 0,
            'ememy_size': 30,
            'phase': random.uniform(0, 2*math.pi) # for breathing animation
        })

    # Draw each enemy with breathing effect
    for i in enemies:
        glPushMatrix()
        glTranslatef(i['x'], i['y'], i['z']) #  move towards enemy pos

        # Breathing: radius changes with sine wave like up down
        body_radius = i['ememy_size'] + 5 * math.sin(i['phase'])
        head_radius = 10 + 2 * math.sin(i['phase'])

        glTranslatef(0, 0, 50)
        glColor3f(1, 0, 0)
        gluSphere(gluNewQuadric(), body_radius, 20, 20)  # body
        glTranslatef(0, 0, 50)
        glColor3f(0, 0, 0)
        gluSphere(gluNewQuadric(), head_radius, 30, 30)  # head

        glPopMatrix()

        # Update breathing phase
        i['phase'] += 0.03

def move_enemies():
    global enemies, player_current_position, enemy_speed

    # enemy moves towards the player
    for enemy in enemies:
        # Vector from enemy to player
        dx = player_current_position[0] - enemy['x']
        dy = player_current_position[1] - enemy['y']
        distance = math.sqrt(dx*dx + dy*dy)

        if distance > 0:
            step_x = (dx / distance) * enemy_speed
            step_y = (dy / distance) * enemy_speed
            # enemy moves closer to player
            enemy['x'] += step_x
            enemy['y'] += step_y

#collision between enemy and bullet, and player and enemy
def game_collisions():
    global bullets, enemies, score, player_remaining_life, game_over
    # Bullet, Enemy collision
    remaining_bullets = [] # bullets that didn’t hit anything

    for bullet in bullets:
        bullet_hits_enemy = False # to see if bullet hits an enemy
        for enemy in enemies:
            # Distance bullet and enemy in X-Y plane
            dx = bullet["bullet_x"] - enemy['x']
            dy = bullet["bullet_y"] - enemy['y']
            enemy_radius = enemy['ememy_size'] + 5  # body radius + breathing margin
            distance = math.sqrt(dx**2 + dy**2) # straight-line distance between bullet and enemy in the XY-plane

            #if distance is less than sum of bullet and enemy radious it will hit
            if distance <= (bullet_radius + enemy_radius):
                score += 1
                print(f"Enemy destroyed! Score: {score}")
                # Respawn enemy far from player
                safe_distance = 350
                angle = random.uniform(0, 2*math.pi) # random direction 
                distance_from_player = random.uniform(safe_distance, GRID_LENGTH - 55)
                enemy['x'] = int(player_current_position[0] + distance_from_player * math.cos(angle))
                enemy['y'] = int(player_current_position[1] + distance_from_player * math.sin(angle))
                enemy['phase'] = random.uniform(0, 2*math.pi) # resetting breathing 

                # Clamp to grid
                enemy['x'] = max(-GRID_LENGTH + 55, min(GRID_LENGTH - 55, enemy['x']))
                enemy['y'] = max(-GRID_LENGTH + 55, min(GRID_LENGTH - 55, enemy['y']))

                bullet_hits_enemy = True # mark that bullet hits an enemy
                break  # one bullet hits only one enemy so stop checking other enemies for this bullet

        if not bullet_hits_enemy:
            remaining_bullets.append(bullet)

    bullets = remaining_bullets

    # Player, enemy collision
    for enemy in enemies:
        dx = player_current_position[0] - enemy['x']
        dy = player_current_position[1] - enemy['y']
        enemy_radius = enemy['ememy_size'] + 5
        distance = math.sqrt(dx**2 + dy**2) # straight-line distance between player and enemy in the XY-plane
        
        #if the dis is less than the sum of enemy and player radious, collison happens
        if distance <= (player_radius + enemy_radius):
            player_remaining_life -= 1
            print(f"Player hit! Remaining life: {player_remaining_life}")
            if player_remaining_life == 0:
                game_over = True
                print("GAME OVER. Player has no life left!")

            # Respawn enemy far from player 
            safe_distance = 350
            angle = random.uniform(0, 2*math.pi)
            distance_from_player = random.uniform(safe_distance, GRID_LENGTH - 55)
            enemy['x'] = int(player_current_position[0] + distance_from_player * math.cos(angle))
            enemy['y'] = int(player_current_position[1] + distance_from_player * math.sin(angle))
            enemy['phase'] = random.uniform(0, 2*math.pi)

            # Clamp to grid
            enemy['x'] = max(-GRID_LENGTH + 55, min(GRID_LENGTH - 55, enemy['x']))
            enemy['y'] = max(-GRID_LENGTH + 55, min(GRID_LENGTH - 55, enemy['y']))

#cheat mode
def player_cheat_mode():
    global player_angle, cheat_fire_counter, cheat_fire_ready
    if cheat_mode:
    # Continuous rotation (around Z)
        player_angle += 4
        if player_angle >= 360:
            player_angle -= 360
        # Find the nearest enemies
        if enemies:
            nearest_enemy = min(enemies, key=lambda e: math.hypot(
                e['x'] - player_current_position[0],
                e['y'] - player_current_position[1]
            ))
            dx = nearest_enemy['x'] - player_current_position[0]
            dy = nearest_enemy['y'] - player_current_position[1]
            # the direction from the player to the nearest enemy in the XY-plane
            angle_to_enemy = math.degrees(math.atan2(dy, dx))

            # Normalize angle difference
            angle_diff = (angle_to_enemy - player_angle + 360) % 360 # difference between gun and enemy
            if angle_diff > 180:
                angle_diff -= 360

            # If aligned within threshold flag for bullet spawn
            if abs(angle_diff) < CHEAT_ANGLE_THRESHOLD: # ready to fire
                cheat_fire_counter += 1 
                if cheat_fire_counter >= CHEAT_FIRE_RATE:
                    cheat_fire_ready = True   # Tell draw_and_shoot_bullets() system to fire
                    cheat_fire_counter = 0
            else:
                cheat_fire_counter = 0

# resets all global variables
def restart_game():
    global player_start_position, player_current_position, player_angle, player_remaining_life, score, missed_bullets
    global bullets, enemies, cheat_mode, automatic_gun_follow, first_person_mode, game_over, camera_angle, camera_height

    player_start_position = (0, 0, 0)
    player_current_position = [0, 0, 0]
    player_angle = 90   
    player_remaining_life = 5
    score = 0
    missed_bullets = 0
    bullets = []
    enemies = []
    cheat_mode = False
    automatic_gun_follow = False
    first_person_mode = False
    game_over = False
    camera_angle = 0
    camera_height = 200

# Main screen
def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    setupCamera()
    draw_grid_board()
    draw_walls()
    draw_player()
    draw_and_shoot_bullets()
    draw_enemies()

    #game infomrations
    draw_text(10, 770, f"Player Life Remaining: {player_remaining_life}")
    draw_text(10, 740, f"Game Score: {score}")
    draw_text(10, 710, f"Player Bullet Missed: {missed_bullets}")

    if game_over:
        draw_text(400, 600, "GAME OVER — Press R to Restart", font=GLUT_BITMAP_TIMES_ROMAN_24)

    glutSwapBuffers()

# Main function
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"3D OpenGL Intro")

    glEnable(GL_DEPTH_TEST)

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__ == "__main__":
    main()