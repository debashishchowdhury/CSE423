from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random  # Add random import for traps

# =============================
# Scooby Doo: Mystery Hunt (minimal 3D prototype)
# Constraints: PyOpenGL (GL, GLUT, GLU) only — no textures/models.
# Matches the user's flow: Shaggy-only play; Scooby appears in Boost.
# 6 rooms (3 per side), clue collection, monster speeds up per clue,
# 3 health, HUD, simple cameras, simple doors.
# =============================

# ---------- Window & camera ----------
WIN_W, WIN_H = 1000, 800
ASPECT = WIN_W / float(WIN_H)
fovY = 70.0

CAM_TPS = 0
CAM_FPS = 1
# New overhead camera mode (named per request)
third_person_mode = 2
camera_mode = CAM_TPS
third_person_height = 520.0  # Initial height for birdview
third_person_angle = 0.0    # Initial horizontal angle (degrees)

# Camera rig relative offsets (TPS) - restored to better working values
TPS_DIST = 250.0  # Back to the working distance for better room view
TPS_HEIGHT = 80.0  # Back to the working height for room interior visibility

# Overhead camera parameters
OVERHEAD_HEIGHT = 520.0  # how high the camera is above the scene
OVERHEAD_BACK = 120.0    # slight tilt (pull back along facing direction)

# Global rendering toggle
NO_ROOF = True  # draw with no ceilings/roof

# ---------- World layout ----------
# World is on XY plane, Z is up.
HALL_LEN = 1800.0
HALL_HALF = 120.0        # half width of the corridor
ROOM_SIZE = 400.0        # much larger square rooms for better visibility
ROOM_GAP = 500.0         # Reduced spacing so all rooms are more visible
DOOR_W = 120.0           # even wider doors for better visibility

# Door Y coordinates for 3 rooms per side - closer together
ROOM_Y = [-ROOM_GAP, 0.0, ROOM_GAP]  # Will be [-500, 0, 500]
LEFT_X = -HALL_HALF - ROOM_SIZE * 0.5   # rooms on left side of hall
RIGHT_X = HALL_HALF + ROOM_SIZE * 0.5   # rooms on right side of hall

# House dimensions
HOUSE_WIDTH = 1200.0     # wider house to accommodate larger rooms
HOUSE_LENGTH = 2400.0    # longer house
CEILING_HEIGHT = 280.0   # even higher ceiling for better view

# ---------- Player (Scooby Doo) ----------
px, py = 0.0, -HALL_LEN * 0.25
pdir = 0.0               # yaw in degrees (0 = +Y)
pspd = 180.0             # units/sec
lives = 3
invuln_t = 0.0
game_won = False         # Win condition when monster name is revealed

player_frozen = False

DIFFICULTY = 'easy'  # 'easy', 'medium', 'hard'
monster_spawn_rate = 1.0   # multiplier for monster spawn frequency
clue_switch_rate = 1.0     # multiplier for clue switching frequency
# ---------- Clues ----------
# Clues needed to reveal monster name
monster_speed_mult = 1.0  # multiplier for monster speed
clues = []  # list of dict: {x,y,got}
TOTAL_CLUES = 3  # Only 3 clues needed to reveal monster name


clue_switch_timer = 0.0
CLUE_SWITCH_BASE = 8.0  # seconds between clue switches at easy
# Create 3 clues total: place them strategically in key rooms
# Left side: 2 clues (first and third rooms)
for i in [0, 2]:  # Skip middle room on left
    clues.append({'x': LEFT_X, 'y': ROOM_Y[i], 'got': False})
# Right side: 1 clue (middle room)
clues.append({'x': RIGHT_X, 'y': ROOM_Y[1], 'got': False})

# ---------- Monster ----------
mx, my = 0.0, HALL_LEN * 0.25
m_visible = False
m_speed_base = 60.0
m_speed = m_speed_base
m_spawn_cooldown = 3.0
m_visible_timer = 0.0
m_spawn_timer = 0.0
m_name_revealed = False
m_name = "???"

# ---------- Traps ----------
traps = []  # list of dict: {x, y, active, type, timer}
trap_spawn_timer = 0.0

def create_trap(x, y, trap_type="spike"):
    """Create a new trap at the given location"""
    traps.append({
        'x': x, 'y': y,
        'active': True,
        'type': trap_type,
        'timer': 0.0,
        'triggered': False
    })

# Create some static traps in corridors
def init_traps():
    global traps
    traps = []
    # Corridor traps
    for i in range(3):
        x = random.uniform(-HALL_HALF + 20, HALL_HALF - 20)
        y = random.uniform(-HALL_LEN * 0.4, HALL_LEN * 0.4)
        create_trap(x, y, "spike")
    # Room traps for medium/hard
    if DIFFICULTY in ("medium", "hard"):
        for side in [LEFT_X, RIGHT_X]:
            for y in ROOM_Y:
                for i in range(2):  # 2 traps per room
                    rx = side + random.uniform(-ROOM_SIZE*0.3, ROOM_SIZE*0.3)
                    ry = y + random.uniform(-ROOM_SIZE*0.3, ROOM_SIZE*0.3)
                    create_trap(rx, ry, "spike")
# Trap spawn timer
trap_spawn_timer = 0.0
init_traps()

# ---------- Achievement System ----------
achievements = {
    'first_clue': {'unlocked': False, 'name': 'First Clue', 'desc': 'Found your first clue'},
    'speed_demon': {'unlocked': False, 'name': 'Speed Demon', 'desc': 'Used Scooby boost 5 times'},
    'survivor': {'unlocked': False, 'name': 'Survivor', 'desc': 'Survived 30 seconds without taking damage'},
    'trap_dodger': {'unlocked': False, 'name': 'Trap Dodger', 'desc': 'Avoided 3 traps in one game'},
    'mystery_solver': {'unlocked': False, 'name': 'Mystery Solver', 'desc': 'Solved the mystery (collected all clues)'},
    'room_hopper': {'unlocked': False, 'name': 'Room Hopper', 'desc': 'Visited all 6 rooms'},
    'close_call': {'unlocked': False, 'name': 'Close Call', 'desc': 'Escaped from monster when at 1 health'}
}

achievement_stats = {
    'boost_count': 0,
    'damage_free_time': 0.0,
    'traps_avoided': 0,
    'rooms_visited': set(),
    'close_calls': 0
}

def check_achievements():
    """Check and unlock achievements based on game state"""
    global achievement_stats

    # First clue
    if collected_clues() >= 1:
        achievements['first_clue']['unlocked'] = True

    # Speed demon - 5 boosts used
    if achievement_stats['boost_count'] >= 5:
        achievements['speed_demon']['unlocked'] = True

    # Survivor - 30 seconds without damage
    if achievement_stats['damage_free_time'] >= 30.0:
        achievements['survivor']['unlocked'] = True

    # Trap dodger - avoided 3 traps
    if achievement_stats['traps_avoided'] >= 3:
        achievements['trap_dodger']['unlocked'] = True

    # Mystery solver - all clues collected
    if collected_clues() >= TOTAL_CLUES:
        achievements['mystery_solver']['unlocked'] = True

    # Room hopper - visited all rooms
    if len(achievement_stats['rooms_visited']) >= 6:
        achievements['room_hopper']['unlocked'] = True

    # Close call - escaped at 1 health
    if achievement_stats['close_calls'] >= 1:
        achievements['close_call']['unlocked'] = True

def update_achievement_stats(dt):
    """Update achievement tracking statistics"""
    global achievement_stats

    # Track damage-free time
    if invuln_t <= 0:  # Not recently damaged
        achievement_stats['damage_free_time'] += dt
    else:
        achievement_stats['damage_free_time'] = 0.0  # Reset on damage

    # Track room visits
    current_room = get_current_room()
    if current_room is not None:
        achievement_stats['rooms_visited'].add(current_room)

def get_current_room():
    """Get which room player is currently in (0-5) or None if in corridor"""
    for i, y in enumerate(ROOM_Y):
        # Check left rooms
        if (abs(px - LEFT_X) < ROOM_SIZE/2 and abs(py - y) < ROOM_SIZE/2):
            return i
        # Check right rooms
        if (abs(px - RIGHT_X) < ROOM_SIZE/2 and abs(py - y) < ROOM_SIZE/2):
            return i + 3
    return None

# ---------- Scooby (Boost) ----------
scooby_active = False
scooby_timer = 0.0
scooby_dur = 6.0
scooby_cd_left = 0.0
scooby_cd = 10.0

# Boost becomes available after 1 clue (since we only have 3 total now)
def boost_available():
    return collected_clues() >= 1 and scooby_cd_left <= 0.0 and not scooby_active

# ---------- Input state ----------
keys_down = set()

# ---------- Timing ----------
last_ms = 0

# ---------- Utility ----------
def clamp(v, a, b):
    return a if v < a else (b if v > b else v)

def sqr(x):
    return x * x

def dist2(x1, y1, x2, y2):
    return sqr(x1 - x2) + sqr(y1 - y2)

# simple periodic [0..1] saw wave using GLUT elapsed time
# period seconds
def saw01(period):
    t = glutGet(GLUT_ELAPSED_TIME) / 1000.0
    f = t / max(0.0001, period)
    frac = f - int(f)
    return frac

# ---------- Drawing primitives ----------
def draw_cube(s):
    glutSolidCube(s)

def draw_cylinder(base, top, h, slices=12, stacks=1):
    q = gluNewQuadric()
    gluCylinder(q, base, top, h, slices, stacks)

def draw_sphere(r, slices=12, stacks=12):
    q = gluNewQuadric()
    gluSphere(q, r, slices, stacks)

# ---------- Characters ----------
def draw_shaggy():
    # More detailed Shaggy with arms, legs, hands
    glPushMatrix()

    # Head
    glColor3f(1.0, 0.8, 0.6)  # skin color
    glPushMatrix()
    glTranslatef(0, 0, 70)
    draw_sphere(12)
    glPopMatrix()

    # Hair (messy brown)
    glColor3f(0.4, 0.2, 0.1)
    glPushMatrix()
    glTranslatef(0, 0, 78)
    glutSolidCube(18)
    glPopMatrix()

    # Torso
    glColor3f(0.2, 0.8, 0.2)  # green shirt
    glPushMatrix()
    glTranslatef(0, 0, 40)
    glScalef(1.2, 0.8, 1.8)
    glutSolidCube(24)
    glPopMatrix()

    # Arms
    glColor3f(0.2, 0.8, 0.2)  # green sleeves
    for dx in (-18, 18):
        # Upper arm
        glPushMatrix()
        glTranslatef(dx, 0, 50)
        glRotatef(20 if dx < 0 else -20, 0, 1, 0)
        draw_cylinder(4, 4, 18)
        glPopMatrix()

        # Lower arm
        glColor3f(1.0, 0.8, 0.6)  # skin
        glPushMatrix()
        glTranslatef(dx + (8 if dx > 0 else -8), 0, 32)
        glRotatef(10 if dx < 0 else -10, 0, 1, 0)
        draw_cylinder(3.5, 3.5, 15)
        glPopMatrix()

        # Hand
        glPushMatrix()
        glTranslatef(dx + (12 if dx > 0 else -12), 0, 20)
        draw_sphere(4)
        glPopMatrix()
        glColor3f(0.2, 0.8, 0.2)  # reset to green

    # Legs
    glColor3f(0.4, 0.3, 0.1)  # brown pants
    for dx in (-6, 6):
        # Upper leg (thigh) - vertical cylinder going down
        glPushMatrix()
        glTranslatef(dx, 0, 20)  # start higher
        draw_cylinder(5, 5, 20)  # vertical cylinder (no rotation needed)
        glPopMatrix()

        # Lower leg (shin) - vertical cylinder going down
        glPushMatrix()
        glTranslatef(dx, 0, 0)  # lower position
        draw_cylinder(4, 4, 18)  # vertical cylinder (no rotation needed)
        glPopMatrix()

        # Feet
        glColor3f(0.1, 0.1, 0.1)  # black shoes
        glPushMatrix()
        glTranslatef(dx, 4, -15)  # slightly forward and down
        glScalef(1.5, 2.0, 0.8)
        glutSolidCube(8)
        glPopMatrix()
        glColor3f(0.4, 0.3, 0.1)  # reset to brown

    glPopMatrix()

def draw_scooby():
    # More detailed Scooby with legs and collar
    glPushMatrix()

    # Body
    glColor3f(0.6, 0.35, 0.15)  # brown body
    glPushMatrix()
    glTranslatef(0, 0, 25)
    glScalef(1.6, 1.0, 0.8)
    draw_sphere(12)
    glPopMatrix()

    # Head
    glPushMatrix()
    glTranslatef(16, 0, 34)
    draw_sphere(8)
    glPopMatrix()

    # Ears
    glColor3f(0.5, 0.25, 0.1)  # darker brown
    for dy in (-6, 6):
        glPushMatrix()
        glTranslatef(20, dy, 38)
        glRotatef(45, 1, 0, 0)
        glScalef(0.6, 1.5, 0.4)
        glutSolidCube(6)
        glPopMatrix()

    # Collar
    glColor3f(0.0, 0.4, 0.8)  # blue collar
    glPushMatrix()
    glTranslatef(12, 0, 32)
    glRotatef(90, 0, 1, 0)
    draw_cylinder(5, 5, 8)
    glPopMatrix()

    # Collar tag
    glColor3f(0.8, 0.8, 0.0)  # yellow tag
    glPushMatrix()
    glTranslatef(12, 0, 28)
    glutSolidCube(3)
    glPopMatrix()

    # Legs
    glColor3f(0.6, 0.35, 0.15)  # brown legs
    for dx, dy in [(-8, 8), (8, 8), (-8, -8), (8, -8)]:
        glPushMatrix()
        glTranslatef(dx, dy, 10)
        glRotatef(90, 1, 0, 0)
        draw_cylinder(3, 3, 12)
        glPopMatrix()

        # Paws
        glColor3f(0.1, 0.1, 0.1)  # black paws
        glPushMatrix()
        glTranslatef(dx, dy, 0)
        draw_sphere(4)
        glPopMatrix()
        glColor3f(0.6, 0.35, 0.15)  # reset to brown

    # Tail
    glPushMatrix()
    glTranslatef(-16, 0, 30)
    glRotatef(35, 0, 1, 0)
    draw_cylinder(2, 1, 16)
    glPopMatrix()

    glPopMatrix()


def draw_monster():
    # Monster transformation stages - ALL STAGES AS TOWERING GIANTS
    clue_count = collected_clues()

    # Stage 1: Shadow Giant (0 clues) - GIANT SIZE
    if clue_count == 0:
        glPushMatrix()
        glColor3f(0.2, 0.2, 0.2)  # dark shadow
        glTranslatef(0, 0, 80)  # Much taller - giant height

        # Giant head
        draw_sphere(35)  # Massive head

        # Giant torso
        glTranslatef(0, 0, -50)
        glScalef(1.8, 1.8, 3.0)  # Wide and tall torso
        glutSolidCube(40)

        # Giant arms
        glLoadIdentity()
        glTranslatef(mx, my, 60)
        for side in [-1, 1]:
            glPushMatrix()
            glTranslatef(side * 60, 0, 0)  # Wide arm span
            glColor3f(0.15, 0.15, 0.15)  # darker arms
            glScalef(1.2, 1.2, 4.0)  # Long giant arms
            glutSolidCube(25)
            glPopMatrix()

        # Giant legs
        for side in [-1, 1]:
            glPushMatrix()
            glTranslatef(side * 25, 0, -80)  # Deep leg position
            glColor3f(0.1, 0.1, 0.1)  # dark legs
            glScalef(1.5, 1.5, 4.0)  # Massive legs
            glutSolidCube(30)
            glPopMatrix()
        glPopMatrix()

    # Stage 2: Purple Ghost Giant (1 clue) - GIANT SIZE
    elif clue_count == 1:
        glPushMatrix()
        glColor3f(0.4, 0.1, 0.6)  # purple
        glTranslatef(0, 0, 100)  # Even taller giant

        # Giant ghost head
        draw_sphere(45)  # Massive ghost head

        # Giant ghost body
        glTranslatef(0, 0, -60)
        glColor3f(0.5, 0.2, 0.7)
        glScalef(2.2, 2.2, 3.5)  # Huge ghost body
        glutSolidCube(45)

        glLoadIdentity()
        glTranslatef(mx, my, 20)
        glRotatef(-90, 1, 0, 0)
        glColor3f(0.3, 0.1, 0.5)
        draw_cylinder(40, 20, 80)  
        glPopMatrix()

    # Stage 3: Menacing Phantom Giant (2 clues) - GIANT SIZE
    elif clue_count == 2:
        glPushMatrix()
        glColor3f(0.4, 0.1, 0.6)  # darker purple
        glTranslatef(0, 0, 120)  # Towering height

        # Giant head with glowing effect
        pulse = 1.0 + 0.3 * math.sin(glutGet(GLUT_ELAPSED_TIME) * 0.003)
        glScalef(pulse, pulse, pulse)
        draw_sphere(50)  # Massive pulsing head

        # Giant middle body
        glScalef(1.0/pulse, 1.0/pulse, 1.0/pulse)  # reset scale
        glTranslatef(0, 0, -70)
        glColor3f(0.5, 0.2, 0.7)
        glScalef(2.5, 2.5, 4.0)  # Enormous body
        glutSolidCube(50)

        # Giant arms with threatening pose
        glLoadIdentity()
        glTranslatef(mx, my, 80)
        for side in [-1, 1]:
            glPushMatrix()
            glTranslatef(side * 80, 0, 0)  # Wide threatening arm span
            glRotatef(side * 20, 0, 0, 1)  # Angled threatening pose
            glColor3f(0.3, 0.1, 0.5)
            glScalef(1.5, 1.5, 5.0)  # Long menacing arms
            glutSolidCube(30)
            glPopMatrix()

        # Massive ghostly trail
        glTranslatef(0, 0, -100)
        glRotatef(-90, 1, 0, 0)
        glColor3f(0.2, 0.05, 0.4)
        draw_cylinder(50, 25, 100) 
        glPopMatrix()

    # Stage 4: Revealed Giant Villain - Old Man Jenkins (3+ clues) - GIANT SIZE
    else:
        glPushMatrix()
        # Giant Human Villain - Old Man Jenkins revealed as GIANT
        glColor3f(0.8, 0.7, 0.6)  # human skin tone
        glTranslatef(0, 0, 140)  # Towering giant height

        # Giant head - more human proportions but massive
        draw_sphere(40)  # Enormous head

        # Giant torso
        glTranslatef(0, 0, -80)  # Much bigger body spacing
        glColor3f(0.3, 0.3, 0.8)  # blue clothing
        glScalef(3.0, 2.5, 5.0)  # Massive giant body
        glutSolidCube(35)  # Huge cube

       
        glLoadIdentity()
        glTranslatef(mx, my, 100)  # Very high position for giant
        for side in [-1, 1]:
            glPushMatrix()
            glTranslatef(side * 70, 0, 0)  
            glRotatef(side * 15, 0, 0, 1)  # Slight angle for menacing look
            glColor3f(0.8, 0.7, 0.6)  # skin
            glScalef(2.0, 2.0, 6.0) 
            glutSolidCube(25)  # Huge arm cubes
            glPopMatrix()

        
        for side in [-1, 1]:
            glPushMatrix()
            glTranslatef(side * 35, 0, -120)  # Much wider stance, deeper position
            glColor3f(0.2, 0.2, 0.2)  # dark pants
            glScalef(2.5, 2.5, 6.0) 
            glutSolidCube(30)  # Massive leg cubes
            glPopMatrix()

        # Giant hands/fists for extra intimidation
        for side in [-1, 1]:
            glPushMatrix()
            glTranslatef(side * 90, 0, 60)  # At end of arms
            glColor3f(0.7, 0.6, 0.5)  # slightly darker skin for hands
            draw_sphere(15)  # Big threatening fists
            glPopMatrix()
        glPopMatrix()

    
    if clue_count < 3:
        # glColor3f(1.0, 0.0, 0.0) 
        eye_size = 8  # Bigger glowing eyes for giants
        eye_height = 80 + (clue_count * 20)  # Higher for each stage
        eye_spacing = 25  # Wider spacing for giant heads
    else:
        glColor3f(0.8, 0.8, 1.0)  # normal human eyes
        eye_size = 6  # Still big for giant human
        eye_height = 140  # At giant head level
        eye_spacing = 30  # Wide spacing for giant human head

    for dx in (-eye_spacing, eye_spacing):
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(mx + dx, my, eye_height)
        draw_sphere(eye_size)
        glPopMatrix()

# ---------- Environment ----------
def draw_floor_and_hall():
    # Main house floor - larger area (match corridor length)
    glPushMatrix()
    glTranslatef(0, 0, 0)
    glColor3f(0.5, 0.3, 0.1)  # darker wooden floor
    glScalef(1000, HALL_LEN + 200, 5)  # Make floor match corridor length plus buffer
    glutSolidCube(1.0)
    glPopMatrix()

    # House exterior walls - match corridor length
    wall_height = 150
    wall_thick = 15
    house_width = 1000
    house_length = HALL_LEN + 100  # Slightly longer than corridor for walls

    # Front and back walls (corridor end walls)
    for z_pos in [-house_length/2, house_length/2]:
        glPushMatrix()
        glTranslatef(0, z_pos, wall_height/2)
        glColor3f(0.8, 0.8, 0.7)  # exterior wall color
        glScalef(house_width, wall_thick, wall_height)
        glutSolidCube(1.0)
        glPopMatrix()

    # Left and right walls
    for x_pos in [-house_width/2, house_width/2]:
        glPushMatrix()
        glTranslatef(x_pos, 0, wall_height/2)
        glColor3f(0.8, 0.8, 0.7)
        glScalef(wall_thick, house_length, wall_height)
        glutSolidCube(1.0)
        glPopMatrix()

    # House ceiling (removed when NO_ROOF is True)
    if not NO_ROOF:
        glPushMatrix()
        glTranslatef(0, 0, wall_height + 10)
        glColor3f(0.9, 0.9, 0.9)  # white ceiling
        glScalef(house_width - 30, house_length - 30, 20)
        glutSolidCube(1.0)
        glPopMatrix()

    # Hallway floor (match corridor length)
    glPushMatrix()
    glTranslatef(0, 0, 2)
    glColor3f(0.6, 0.4, 0.2)  # lighter hallway floor
    glScalef(HALL_HALF * 2, HALL_LEN, 3)  # Make hallway floor match corridor length
    glutSolidCube(1.0)
    glPopMatrix()


def draw_room_box(cx, cy, open_to_hall=True):
    # Draw room walls (interior walls of a house)
    half = ROOM_SIZE * 0.5
    wall_height = 150  # Much taller walls than character
    door_width = 60
    door_height = 120

    # Room floor
    glPushMatrix()
    glTranslatef(cx, cy, 5)
    glColor3f(0.6, 0.4, 0.2)  # wooden floor
    glScalef(ROOM_SIZE, ROOM_SIZE, 10)
    glutSolidCube(1.0)
    glPopMatrix()

    # Wall thickness
    wall_thick = 10

    # Back wall (away from hallway)
    glPushMatrix()
    if cx < 0:  # left rooms - back wall is on left side
        glTranslatef(cx - half, cy, wall_height/2)
    else:  # right rooms - back wall is on right side
        glTranslatef(cx + half, cy, wall_height/2)
    glColor3f(0.9, 0.9, 0.8)  # light wall color
    glScalef(wall_thick, ROOM_SIZE, wall_height)
    glutSolidCube(1.0)
    glPopMatrix()

    # Side walls
    for side in [-1, 1]:
        wy = cy + side * half
        glPushMatrix()
        glTranslatef(cx, wy, wall_height/2)
        glColor3f(0.9, 0.9, 0.8)
        glScalef(ROOM_SIZE, wall_thick, wall_height)
        glutSolidCube(1.0)
        glPopMatrix()

    # Front wall (towards hallway) with door opening
    door_half = door_width * 0.5

    # Wall segments beside the door
    if cx < 0:  # left rooms
        wall_x = cx + half
    else:  # right rooms
        wall_x = cx - half

    # Bottom wall segment
    glPushMatrix()
    glTranslatef(wall_x, cy - half, wall_height/2)
    glColor3f(0.9, 0.9, 0.8)
    glScalef(wall_thick, ROOM_SIZE - door_width, wall_height)
    glutSolidCube(1.0)
    glPopMatrix()

    # Top wall segment
    glPushMatrix()
    glTranslatef(wall_x, cy + half, wall_height/2)
    glColor3f(0.9, 0.9, 0.8)
    glScalef(wall_thick, ROOM_SIZE - door_width, wall_height)
    glutSolidCube(1.0)
    glPopMatrix()

    # Top part above door
    glPushMatrix()
    glTranslatef(wall_x, cy, door_height + (wall_height - door_height)/2)
    glColor3f(0.9, 0.9, 0.8)
    glScalef(wall_thick, door_width, wall_height - door_height)
    glutSolidCube(1.0)
    glPopMatrix()

    # Door frame
    glColor3f(0.4, 0.2, 0.1)  # dark brown frame
    frame_thick = 5

    # Door frame sides
    for side in [-1, 1]:
        glPushMatrix()
        glTranslatef(wall_x, cy + side * door_half, door_height/2)
        glScalef(frame_thick, frame_thick, door_height)
        glutSolidCube(1.0)
        glPopMatrix()

    # Door frame top
    glPushMatrix()
    glTranslatef(wall_x, cy, door_height + frame_thick/2)
    glScalef(frame_thick, door_width, frame_thick)
    glutSolidCube(1.0)
    glPopMatrix()

    # Actual door
    glColor3f(0.6, 0.3, 0.1)  # brown door
    glPushMatrix()
    if cx < 0:
        glTranslatef(wall_x - 3, cy, door_height/2)
    else:
        glTranslatef(wall_x + 3, cy, door_height/2)
    glScalef(6, door_width - 10, door_height - 10)
    glutSolidCube(1.0)
    glPopMatrix()

    # Door handle
    glColor3f(0.8, 0.8, 0.2)  # golden handle
    glPushMatrix()
    if cx < 0:
        glTranslatef(wall_x - 6, cy + 15, 70)
    else:
        glTranslatef(wall_x + 6, cy + 15, 70)
    draw_sphere(3, 6, 6)
    glPopMatrix()


def draw_all_rooms():
    for y in ROOM_Y:
        # left and right rooms
        glPushMatrix(); draw_room_box(LEFT_X, y); glPopMatrix()
        glPushMatrix(); draw_room_box(RIGHT_X, y); glPopMatrix()

def draw_house_decorations():
    """Add simple decorations to make the house more lively using only basic shapes"""

    # Hallway decorations - simple shapes only
    # Potted plants along the hallway
    for y in [-400, -200, 0, 200, 400]:
        for x in [-HALL_HALF - 30, HALL_HALF + 30]:
            # Pot
            glColor3f(0.4, 0.2, 0.1)  # brown pot
            glPushMatrix()
            glTranslatef(x, y, 15)
            draw_cylinder(12, 8, 20, 8, 1)
            glPopMatrix()

            # Plant
            glColor3f(0.2, 0.6, 0.2)  # green plant
            glPushMatrix()
            glTranslatef(x, y, 30)
            draw_sphere(8, 6, 6)
            glPopMatrix()

    # Simple wall decorations - using cubes as "paintings"
    for i, y in enumerate([-300, 0, 300]):
        # Left wall paintings
        glColor3f(0.8, 0.6, 0.4)  # frame color
        glPushMatrix()
        glTranslatef(-HALL_HALF - 15, y, 80)
        glScalef(5, 40, 30)
        glutSolidCube(1)
        glPopMatrix()

        # Picture inside frame
        colors = [(0.8, 0.6, 0.4), (0.6, 0.8, 0.4), (0.8, 0.4, 0.6)]  # More natural colors
        glColor3f(*colors[i])
        glPushMatrix()
        glTranslatef(-HALL_HALF - 12, y, 80)
        glScalef(2, 35, 25)
        glutSolidCube(1)
        glPopMatrix()

        # Right wall paintings
        glColor3f(0.8, 0.6, 0.4)  # frame color
        glPushMatrix()
        glTranslatef(HALL_HALF + 15, y, 80)
        glScalef(5, 40, 30)
        glutSolidCube(1)
        glPopMatrix()

        # Picture inside frame
        glColor3f(*colors[i])
        glPushMatrix()
        glTranslatef(HALL_HALF + 12, y, 80)
        glScalef(2, 35, 25)
        glutSolidCube(1)
        glPopMatrix()

    # Room decorations - furniture inside rooms
    for y in ROOM_Y:
        # Left rooms - add simple furniture
        room_half = ROOM_SIZE * 0.5

        # Table in left room
        glColor3f(0.6, 0.4, 0.2)  # brown table
        glPushMatrix()
        glTranslatef(LEFT_X - 30, y, 35)
        glScalef(60, 40, 5)
        glutSolidCube(1)
        glPopMatrix()

        # Table legs
        for dx, dy in [(-25, -15), (25, -15), (-25, 15), (25, 15)]:
            glPushMatrix()
            glTranslatef(LEFT_X - 30 + dx, y + dy, 17)
            draw_cylinder(3, 3, 30, 6, 1)
            glPopMatrix()

        # Chair in left room
        glColor3f(0.5, 0.3, 0.1)
        glPushMatrix()
        glTranslatef(LEFT_X + 40, y, 20)
        glScalef(30, 30, 40)
        glutSolidCube(1)
        glPopMatrix()

        # Right rooms - different furniture
        # Bookshelf in right room
        glColor3f(0.4, 0.3, 0.2)
        glPushMatrix()
        glTranslatef(RIGHT_X + 40, y, 50)
        glScalef(25, 80, 100)
        glutSolidCube(1)
        glPopMatrix()

        # Books on shelf
        for i, book_y in enumerate([y-25, y, y+25]):
            colors = [(0.8, 0.6, 0.4), (0.6, 0.8, 0.4), (0.8, 0.4, 0.6)]  # More natural colors
            glColor3f(*colors[i])
            glPushMatrix()
            glTranslatef(RIGHT_X + 50, book_y, 60 + i*15)
            glScalef(8, 15, 12)
            glutSolidCube(1)
            glPopMatrix()

    # Simple chandelier in center of hallway (will just float if NO_ROOF=True — ok)
    glColor3f(0.8, 0.8, 0.2)  # golden chandelier
    glPushMatrix()
    glTranslatef(0, 0, CEILING_HEIGHT - 30)
    draw_sphere(15, 8, 8)
    glPopMatrix()

    # Chandelier arms
    for angle in range(0, 360, 60):
        glPushMatrix()
        glTranslatef(0, 0, CEILING_HEIGHT - 30)
        glRotatef(angle, 0, 0, 1)
        glTranslatef(20, 0, 0)
        draw_cylinder(2, 2, 15, 6, 1)
        # Small light
        glColor3f(1.0, 1.0, 0.8)
        glTranslatef(0, 0, -10)
        draw_sphere(4, 6, 6)
        glColor3f(0.8, 0.8, 0.2)
        glPopMatrix()


# ---------- Clues ----------
def collected_clues():
    return sum(1 for c in clues if c['got'])

# ---------- Traps ----------
def draw_traps():
    """Draw all active traps with visual effects"""
    t = glutGet(GLUT_ELAPSED_TIME) / 1000.0

    for trap in traps:
        if not trap['active']:
            continue

        glPushMatrix()
        glTranslatef(trap['x'], trap['y'], 0)

        if trap['type'] == "spike":
            # Animated spike trap
            if trap['triggered']:
                # Spikes extended - red danger
                glColor3f(1.0, 0.2, 0.2)
                spike_height = 25
            else:
                # Spikes retracted - brown floor
                glColor3f(0.6, 0.4, 0.2)
                spike_height = 5

            # Base plate
            glPushMatrix()
            glTranslatef(0, 0, 2)
            glScalef(2.0, 2.0, 0.2)
            glutSolidCube(15)
            glPopMatrix()

            # Spikes (4 corners)
            for dx, dy in [(-8, -8), (8, -8), (-8, 8), (8, 8)]:
                glPushMatrix()
                glTranslatef(dx, dy, spike_height/2)
                glScalef(0.3, 0.3, spike_height/15)
                glutSolidCube(15)
                glPopMatrix()

        glPopMatrix()

def update_traps(dt):
    """Update trap states and check collisions"""
    global px, py, health, trap_spawn_timer

    # Randomly spawn new traps over time (max 6 traps at once)
    # As difficulty increases, traps spawn more frequently
    trap_spawn_timer += dt * clue_switch_rate
    if trap_spawn_timer > 5.0 and len(traps) < 6:
        x = random.uniform(-HALL_HALF + 20, HALL_HALF - 20)
        y = random.uniform(-HALL_LEN * 0.4, HALL_LEN * 0.4)
        create_trap(x, y, "spike")
        trap_spawn_timer = 0.0

    for trap in traps:
        if not trap['active']:
            continue

        trap['timer'] += dt

        # Check player collision
        dx, dy = px - trap['x'], py - trap['y']
        dist_sq = dx*dx + dy*dy

        # Mark if player is actually stepping on the trap (tight collision)
        if dist_sq < 20*20:  # Actually on the trap
            trap['player_on'] = True
        else:
            trap['player_on'] = False

        if dist_sq < 30*30:  # Close to trap
            if trap['type'] == "spike":
                # Trigger spikes with a delay
                if not trap['triggered'] and trap['timer'] > 0.5:
                    trap['triggered'] = True
                    # Damage player if still on trap when triggered
                    if dist_sq < 20*20:
                        # Track close call if player at low health
                        if lives == 1:
                            achievement_stats['close_calls'] += 1

                        # lives -= 1
                        # if lives <= 0:
                        #     reset_game()
        else:
            # Reset trap when player moves away
            if trap['triggered']:
                trap['triggered'] = False
                trap['timer'] = 0.0
                # Player successfully avoided triggered trap
                achievement_stats['traps_avoided'] += 1

def draw_clues_and_pickup():
    pulse = 0.5 + 0.5 * abs(0.5 - saw01(1.5)) * 2.0  # glow 0..1
    picked = 0
    for i, c in enumerate(clues):
        if not c['got']:
            # Different colors for each clue based on room
            colors = [
                (1.0, 0.2, 0.2),  # red
                (0.2, 1.0, 0.2),  # green
                (0.2, 0.2, 1.0),  # blue
                (1.0, 1.0, 0.2),  # yellow
                (1.0, 0.2, 1.0),  # magenta
                (0.2, 1.0, 1.0),  # cyan
            ]
            color = colors[i % len(colors)]

            # Draw floating, rotating clue - BIGGER AND MORE VISIBLE
            glPushMatrix()
            glTranslatef(c['x'], c['y'], 20 + 8 * abs(0.5 - saw01(2.0)))  # higher floating motion
            glRotatef(glutGet(GLUT_ELAPSED_TIME) * 0.05 * (i + 1), 0, 0, 1)  # rotation

            # Main clue body - MUCH BIGGER
            glColor3f(color[0] * pulse, color[1] * pulse, color[2] * pulse)
            draw_sphere(15)  # Much bigger clue sphere

            # Sparkle effect - BIGGER
            glColor3f(1.0, 1.0, 1.0)
            for angle in range(0, 360, 45):  # More sparkles
                glPushMatrix()
                glRotatef(angle, 0, 0, 1)
                glTranslatef(20, 0, 0)  # Further out sparkles
                draw_sphere(4)  # Bigger sparkles
                glPopMatrix()

            glPopMatrix()

            # pickup check (no sqrt) - MUCH BIGGER pickup range for easier collection
            if dist2(px, py, c['x'], c['y']) < sqr(35.0):  # Much larger pickup range
                c['got'] = True
                picked += 1
    return picked

# ---------- Monster logic ----------
def target_for_monster():
    # If Scooby is active, monster targets Scooby proxy slightly away from player
    if scooby_active:
        return px + 70.0, py
    return px, py


def try_spawn_monster(dt):
    global m_visible, m_spawn_timer, m_visible_timer
    if m_visible:
        return
    m_spawn_timer -= dt
    if m_spawn_timer <= 0.0:
        m_visible = True
        m_visible_timer = 3.0 + collected_clues() * 0.7
        place_monster_away()
        m_spawn_timer = 1.2 * max(0.3, 1.0 - 0.12 * collected_clues())  # reset timer


def place_monster_away():
    global mx, my
    # appear ahead or behind in corridor boundary
    ahead = 1 if saw01(1000.0) > 0.5 else -1
    my = clamp(py + ahead * 300.0, -HALL_LEN*0.45, HALL_LEN*0.45)
    mx = clamp(px + (HALL_HALF - 30.0) * (1 if px < 0 else -1), -HALL_HALF+20.0, HALL_HALF-20.0)

def update_monster(dt):
    global mx, my, m_visible, m_visible_timer, m_speed, monster_speed_mult
    if not m_visible:
        return

    # If player is safe in a room, monster waits in corridor
    if is_player_in_room():
        # Monster lurks near the room entrance but doesn't enter
        # Find which room player is in and wait outside
        for y in ROOM_Y:
            half = ROOM_SIZE * 0.5
            if (LEFT_X - half <= px <= LEFT_X + half) and (y - half <= py <= y + half):
                # Player in left room - monster waits outside
                mx = LEFT_X + half + 30
                my = y + half + 20
                break
            elif (RIGHT_X - half <= px <= RIGHT_X + half) and (y - half <= py <= y + half):
                # Player in right room - monster waits outside
                mx = RIGHT_X - half - 30
                my = y + half + 20
                break
        m_visible_timer -= dt * 0.5  # Timer decreases slower when waiting
        if m_visible_timer <= 0.0:
            m_visible = False
        return

    # Normal monster behavior in corridor
    # speed scales with clues
    m_speed = (m_speed_base + 40.0 * collected_clues()) * monster_speed_mult
    if scooby_active:
        m_speed *= 0.6  # distracted/slow
    tx, ty = target_for_monster()

    # Only chase if target is in corridor (not in room)
    target_half = ROOM_SIZE * 0.5
    target_in_room = False
    for y in ROOM_Y:
        if ((LEFT_X - target_half <= tx <= LEFT_X + target_half) or
            (RIGHT_X - target_half <= tx <= RIGHT_X + target_half)) and (y - target_half <= ty <= y + target_half):
            target_in_room = True
            break

    if not target_in_room:
        # move toward target only if it's in corridor
        dx, dy = tx - mx, ty - my
        d2 = dx*dx + dy*dy
        if d2 > 1.0:
            invd = 1.0 / (d2 ** 0.5)
            mx += dx * invd * m_speed * dt
            my += dy * invd * m_speed * dt

    m_visible_timer -= dt
    if m_visible_timer <= 0.0:
        m_visible = False

def check_player_hit():
    global lives, invuln_t, m_visible
    if not m_visible:
        return
    if invuln_t > 0.0:
        return

    # Check if player is safe inside a room
    if is_player_in_room():
        return  # Monster can't attack in rooms

    if dist2(px, py, mx, my) < sqr(24.0):
        lives -= 1
        invuln_t = 1.4
        m_visible = False

def is_player_in_room():
    """Check if player is safely inside any room (not just at the door)"""
    half = ROOM_SIZE * 0.5
    door_threshold = 25  # Distance from door where player is still vulnerable

    for y in ROOM_Y:
        # Left room
        if (LEFT_X - half <= px <= LEFT_X + half) and (y - half <= py <= y + half):
            # Check if player is deep inside room (away from door)
            if py < y + half - door_threshold:
                return True

        # Right room
        if (RIGHT_X - half <= px <= RIGHT_X + half) and (y - half <= py <= y + half):
            # Check if player is deep inside room (away from door)
            if py < y + half - door_threshold:
                return True

    return False

# ---------- Game & camera update ----------
def reset_game():
    global px, py, pdir, lives, invuln_t, game_won
    global mx, my, m_visible, m_spawn_timer, m_visible_timer
    global m_name, m_name_revealed
    global scooby_active, scooby_timer, scooby_cd_left
    global TPS_DIST, TPS_HEIGHT
    # DO NOT reset DIFFICULTY, monster_speed_mult, clue_switch_rate here!

    for c in clues:
        c['got'] = False
    px, py = 0.0, -HALL_LEN * 0.25
    pdir = 0.0
    lives = 3
    invuln_t = 0.0
    game_won = False
    m_visible = False
    m_spawn_timer = 1.0
    m_visible_timer = 0.0
    m_name_revealed = False
    m_name = "???"
    scooby_active = False
    scooby_cd_left = 0.0


    # Camera settings
    TPS_DIST = 250.0
    TPS_HEIGHT = 80.0

def update_player(dt):
    global px, py, pdir, player_frozen
    # If frozen, don't allow movement
    if player_frozen:
        return

    move = 0.0
    strafe = 0.0
    rot = 0.0

    # WASD for movement relative to player direction
    if b'w' in keys_down: move += 1.0
    if b's' in keys_down: move -= 1.0
    if b'a' in keys_down: strafe -= 1.0
    if b'd' in keys_down: strafe += 1.0
    if b't' in keys_down: rot -= 0.4  # Rotate right (clockwise)
    if b'f' in keys_down: rot += 0.4  # Rotate left (counterclockwise)

    pdir += rot
    rad = math.radians(pdir)
    fx = math.sin(rad)
    fy = math.cos(rad)
    nx = math.sin(rad + math.pi/2)
    ny = math.cos(rad + math.pi/2)
    # Only slow down if player is actually stepping on a trap
    slow_factor = 1.0
    for trap in traps:
        if trap.get('player_on', False):
            slow_factor = 0.3  # Significantly slow down
            break
    speed = pspd * (1.2 if scooby_active else 1.0) * slow_factor

    px += (fx * move + nx * strafe) * speed * dt
    py += (fy * move + ny * strafe) * speed * dt
    # Collision with corridor/rooms: clamp inside corridor or inside any room
    px, py = collide_world(px, py)
    # After movement, check for trap collision in rooms
    if DIFFICULTY in ("medium", "hard"):
        for trap in traps:
            # Only check traps inside rooms
            for room_y in ROOM_Y:
                if ((trap['x'], trap['y']) == (LEFT_X, room_y) or (trap['x'], trap['y']) == (RIGHT_X, room_y)):
                    if abs(px - trap['x']) < 20 and abs(py - trap['y']) < 20:
                        player_frozen = True
                        return

def collide_world(nx, ny):
    """Enhanced collision system for walls and furniture"""
    player_radius = 15  # Player collision radius

    # World boundaries - keep player within reasonable bounds
    world_half = 1000
    nx = clamp(nx, -world_half, world_half)
    ny = clamp(ny, -world_half, world_half)

    # Check if player is trying to enter a room through a door
    door_half = DOOR_W * 0.5
    room_half = ROOM_SIZE * 0.5

    for room_y in ROOM_Y:
        # Check door entry for left rooms
        left_door_x = LEFT_X + room_half  # Door is on the right side of left room (facing corridor)
        if (left_door_x - 30 <= nx <= left_door_x + 30 and
            room_y - door_half <= ny <= room_y + door_half):
            # Player is in door area for left room - allow free movement
            # Clamp Y to door height to prevent slipping through corners
            ny = clamp(ny, room_y - door_half, room_y + door_half)
            return nx, ny

        # Check door entry for right rooms
        right_door_x = RIGHT_X - room_half  # Door is on the left side of right room (facing corridor)
        if (right_door_x - 30 <= nx <= right_door_x + 30 and
            room_y - door_half <= ny <= room_y + door_half):
            # Player is in door area for right room - allow free movement
            ny = clamp(ny, room_y - door_half, room_y + door_half)
            return nx, ny

    # Check furniture collisions in each room
    for room_y in ROOM_Y:
        # Left room furniture collision
        if (LEFT_X - room_half <= nx <= LEFT_X + room_half and
            room_y - room_half <= ny <= room_y + room_half):

            # Table collision (table at LEFT_X - 30, room_y, size 60x40)
            table_x, table_y = LEFT_X - 30, room_y
            table_w, table_h = 60, 40
            if (table_x - table_w*0.5 - player_radius <= nx <= table_x + table_w*0.5 + player_radius and
                table_y - table_h*0.5 - player_radius <= ny <= table_y + table_h*0.5 + player_radius):
                # Push player away from table
                dx = nx - table_x
                dy = ny - table_y
                if abs(dx) > abs(dy):
                    nx = table_x + (table_w*0.5 + player_radius) * (1 if dx > 0 else -1)
                else:
                    ny = table_y + (table_h*0.5 + player_radius) * (1 if dy > 0 else -1)

            # Chair collision (chair at LEFT_X + 40, room_y, size 30x30)
            chair_x, chair_y = LEFT_X + 40, room_y
            chair_size = 30
            if (chair_x - chair_size*0.5 - player_radius <= nx <= chair_x + chair_size*0.5 + player_radius and
                chair_y - chair_size*0.5 - player_radius <= ny <= chair_y + chair_size*0.5 + player_radius):
                # Push player away from chair
                dx = nx - chair_x
                dy = ny - chair_y
                if abs(dx) > abs(dy):
                    nx = chair_x + (chair_size*0.5 + player_radius) * (1 if dx > 0 else -1)
                else:
                    ny = chair_y + (chair_size*0.5 + player_radius) * (1 if dy > 0 else -1)

        # Right room furniture collision
        if (RIGHT_X - room_half <= nx <= RIGHT_X + room_half and
            room_y - room_half <= ny <= room_y + room_half):

            # Bookshelf collision (bookshelf at RIGHT_X + 40, room_y, size 25x80)
            shelf_x, shelf_y = RIGHT_X + 40, room_y
            shelf_w, shelf_h = 25, 80
            if (shelf_x - shelf_w*0.5 - player_radius <= nx <= shelf_x + shelf_w*0.5 + player_radius and
                shelf_y - shelf_h*0.5 - player_radius <= ny <= shelf_y + shelf_h*0.5 + player_radius):
                # Push player away from bookshelf
                dx = nx - shelf_x
                dy = ny - shelf_y
                if abs(dx) > abs(dy):
                    nx = shelf_x + (shelf_w*0.5 + player_radius) * (1 if dx > 0 else -1)
                else:
                    ny = shelf_y + (shelf_h*0.5 + player_radius) * (1 if dy > 0 else -1)

    # Wall collision system
    # Check if player is in corridor area
    if -HALL_HALF - 50 <= nx <= HALL_HALF + 50:  # Expanded corridor area for door access
        # In main corridor, keep within hallway bounds but allow door access
        if abs(nx) <= HALL_HALF:
            # Pure corridor - apply corridor end wall collision
            ny = clamp(ny, -HALL_LEN*0.5 + player_radius, HALL_LEN*0.5 - player_radius)
            nx = clamp(nx, -HALL_HALF + player_radius, HALL_HALF - player_radius)
            return nx, ny
        else:
            # Near room entrances - check for door access
            for room_y in ROOM_Y:
                # Check if trying to access left room door
                if (nx < -HALL_HALF and
                    room_y - door_half <= ny <= room_y + door_half):
                    # Clamp Y to door height
                    ny = clamp(ny, room_y - door_half, room_y + door_half)
                    return nx, ny

                # Check if trying to access right room door
                if (nx > HALL_HALF and
                    room_y - door_half <= ny <= room_y + door_half):
                    ny = clamp(ny, room_y - door_half, room_y + door_half)
                    return nx, ny

            # Not accessing door, push back to corridor
            if nx < -HALL_HALF:
                nx = -HALL_HALF + player_radius
            elif nx > HALL_HALF:
                nx = HALL_HALF - player_radius
            # Also apply corridor end wall collision here
            ny = clamp(ny, -HALL_LEN*0.5 + player_radius, HALL_LEN*0.5 - player_radius)
            return nx, ny

    # Check room boundaries and walls
    for room_y in ROOM_Y:
        # Left room boundary check
        if (LEFT_X - room_half <= nx <= LEFT_X + room_half and
            room_y - room_half <= ny <= room_y + room_half):

            # Keep player inside room with padding, but allow door exit
            room_left = LEFT_X - room_half + player_radius
            room_right = LEFT_X + room_half - player_radius
            room_bottom = room_y - room_half + player_radius
            room_top = room_y + room_half - player_radius

            # Allow exit through door
            if (nx >= LEFT_X + room_half - 30 and
                room_y - door_half <= ny <= room_y + door_half):
                # Exiting through door
                return nx, ny

            nx = clamp(nx, room_left, room_right)
            ny = clamp(ny, room_bottom, room_top)
            return nx, ny

        # Right room boundary check
        if (RIGHT_X - room_half <= nx <= RIGHT_X + room_half and
            room_y - room_half <= ny <= room_y + room_half):

            # Keep player inside room with padding, but allow door exit
            room_left = RIGHT_X - room_half + player_radius
            room_right = RIGHT_X + room_half - player_radius
            room_bottom = room_y - room_half + player_radius
            room_top = room_y + room_half - player_radius

            # Allow exit through door
            if (nx <= RIGHT_X - room_half + 30 and
                room_y - door_half <= ny <= room_y + door_half):
                # Exiting through door
                return nx, ny

            nx = clamp(nx, room_left, room_right)
            ny = clamp(ny, room_bottom, room_top)
            return nx, ny

    # Default: keep in corridor bounds
    nx = clamp(nx, -HALL_HALF + player_radius, HALL_HALF - player_radius)
    ny = clamp(ny, -HALL_LEN*0.5 + player_radius, HALL_LEN*0.5 - player_radius)

    return nx, ny


def update_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, ASPECT, 0.1, 5000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    rad = math.radians(pdir)
    if camera_mode == CAM_TPS:
        # Look at the character from behind and above like the image
        tx, ty, tz = px, py, 40.0  # Look at player

        # --- Clamp camera distance if player is in a room ---
        cam_dist = TPS_DIST
        cam_height = TPS_HEIGHT
        room_idx = get_current_room()
        if room_idx is not None:
            # Get room center
            if room_idx < 3:
                room_cx = LEFT_X
                room_cy = ROOM_Y[room_idx]
            else:
                room_cx = RIGHT_X
                room_cy = ROOM_Y[room_idx - 3]
            room_half = ROOM_SIZE * 0.5
            # Compute max distance from player to wall in camera direction
            dx = -math.sin(rad)
            dy = -math.cos(rad)
            # Find intersection with room bounds
            max_dist = TPS_DIST
            for sign in [-1, 1]:
                # X wall
                if dx != 0:
                    wx = room_cx + sign * room_half
                    t = (wx - px) / dx
                    if t > 0:
                        wy = py + t * dy
                        if room_cy - room_half <= wy <= room_cy + room_half:
                            max_dist = min(max_dist, t)
                # Y wall
                if dy != 0:
                    wy = room_cy + sign * room_half
                    t = (wy - py) / dy
                    if t > 0:
                        wx = px + t * dx
                        if room_cx - room_half <= wx <= room_cx + room_half:
                            max_dist = min(max_dist, t)
            # Pull camera in if needed
            cam_dist = min(TPS_DIST, max_dist - 10.0)  # 10 units padding from wall
            cam_dist = max(40.0, cam_dist)  # Don't get too close

        cx = px - math.sin(rad) * cam_dist
        cy = py - math.cos(rad) * cam_dist
        cz = cam_height
        gluLookAt(cx, cy, cz, tx, ty, tz, 0, 0, 1)
    elif camera_mode == third_person_mode:
        # Birdview: camera orbits at set height and angle
        board_cx, board_cy = 0.0, 0.0  # Center of board
        orbit_radius = 800.0           # Distance from center
        rad_angle = math.radians(third_person_angle)
        cx = board_cx + math.cos(rad_angle) * orbit_radius
        cy = board_cy + math.sin(rad_angle) * orbit_radius
        cz = third_person_height
        tx, ty, tz = board_cx, board_cy, 0.0  # Look at center of board
        gluLookAt(cx, cy, cz, tx, ty, tz, 0, 0, 1)
    else:  # FPS camera
        # Place camera just in front of and above player's head
        cam_offset = 18.0  # forward from player center
        head_height = 70.0 # height of player's eyes
        cam_x = px + math.sin(rad) * cam_offset
        cam_y = py + math.cos(rad) * cam_offset
        cam_z = head_height
        # Look further ahead from camera position
        look_x = cam_x + math.sin(rad) * 40.0
        look_y = cam_y + math.cos(rad) * 40.0
        look_z = head_height
        gluLookAt(cam_x, cam_y, cam_z, look_x, look_y, look_z, 0, 0, 1)



def switch_clues():
    """Randomly move unclamed clues to a new room."""
    available_rooms = []
    for i, y in enumerate(ROOM_Y):
        available_rooms.append(('left', i))
        available_rooms.append(('right', i))
    for c in clues:
        if not c['got']:
            # Pick a random room different from current
            while True:
                side, idx = random.choice(available_rooms)
                if (side == 'left' and c['x'] != LEFT_X) or (side == 'right' and c['x'] != RIGHT_X):
                    break
            if side == 'left':
                c['x'] = LEFT_X
                c['y'] = ROOM_Y[idx]
            else:
                c['x'] = RIGHT_X
                c['y'] = ROOM_Y[idx]



# ---------- HUD ----------
def draw_hud():
    glDisable(GL_LIGHTING)
    # Lives and clues
    x0, y0 = 10, WIN_H - 30
    draw_text(x0, y0, f"Lives: {lives}")
    draw_text(x0, y0 - 28, f"Clues: {collected_clues()}/{TOTAL_CLUES}")
    draw_text(x0, y0 - 56, f"Difficulty: {DIFFICULTY.title()}")
    # Safety status
    if is_player_in_room():
        # glColor3f(0.2, 1.0, 0.2)  # Green for safe
        draw_text(x0, y0 - 84, "STATUS: SAFE IN ROOM")
        glColor3f(1.0, 1.0, 1.0)  # Reset to white
    else:
        # glColor3f(1.0, 0.3, 0.3)  # Red for danger
        draw_text(x0, y0 - 84, "STATUS: CORRIDOR (DANGER)")
        glColor3f(1.0, 1.0, 1.0)  # Reset to white

    # Boost status
    boost_str = "Ready" if boost_available() else ("Active" if scooby_active else f"CD: {scooby_cd_left:0.1f}s")
    draw_text(x0, y0 - 112, f"Boost: {boost_str}")

    # Instructions
    # glColor3f(0.8, 0.8, 0.8)  # Gray for instructions
    draw_text(x0, y0 - 140, "WASD: Move  Arrows: Camera  1: TPS  2: FPS  U: Overhead  B: Boost  R: Restart")
    draw_text(x0, y0 - 168, "Enter rooms through doors for safety!")

    glColor3f(1.0, 1.0, 1.0)  # Reset to white

    # Monster name when revealed
    if m_name_revealed:
        draw_text(10, 20, f"Monster: {m_name}")

    # Recent achievements (show up to 3 most recently unlocked)
    unlocked_achievements = [name for name, data in achievements.items() if data['unlocked']]
    if unlocked_achievements:
        # glColor3f(1.0, 1.0, 0.0)  # Yellow for achievements
        draw_text(x0, y0 - 196, f"Achievements: {len(unlocked_achievements)}/7")
        # Show last few unlocked
        for i, achievement_name in enumerate(unlocked_achievements[-3:]):
            achievement = achievements[achievement_name]
            draw_text(x0, y0 - 224 - i*20, f"✓ {achievement['name']}")
        glColor3f(1.0, 1.0, 1.0)  # Reset to white

    glEnable(GL_LIGHTING)

# ---------- GLUT glue ----------
def draw_text(x, y, text, font=None):
    """Draw text at screen coordinates using GLUT bitmap font"""
    if font is None:
        try:
            from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
            font = GLUT_BITMAP_HELVETICA_18
        except:
            # Fallback - disable text rendering if font unavailable
            return

    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    # Set up an orthographic projection that matches window coordinates
    gluOrtho2D(0, 1000, 0, 800)  # left, right, bottom, top


    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Draw text at (x, y) in screen coordinates
    try:
        glRasterPos2f(x, y)
        for ch in text:
            glutBitmapCharacter(font, ord(ch))
    except:
        # Silently fail if font rendering doesn't work
        pass

    # Restore original projection and modelview matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def keyboard_down(k, x, y):
    global camera_mode, third_person_height, third_person_angle
    global DIFFICULTY, monster_spawn_rate, clue_switch_rate, monster_speed_mult
    global player_frozen

    keys_down.add(k)
    if k == b'1': camera_mode = CAM_TPS
    if k == b'2': camera_mode = CAM_FPS
    if k == b'u':
        camera_mode = third_person_mode
        third_person_height = 520.0
        third_person_angle = 0.0
    if k == b'r': reset_game()
    if k == b'b' and boost_available():
        activate_boost()
    # Difficulty controls
    if k == b'm':  # Medium
        DIFFICULTY = 'medium'
        monster_speed_mult = 1.5
        clue_switch_rate = 1.5
        init_traps()  # <--- ADD THIS LINE
    if k == b'n':  # Hard
        DIFFICULTY = 'hard'
        monster_speed_mult = 2.0
        clue_switch_rate = 2.2
        init_traps()  # <--- ADD THIS LINE
    if k == b'v':  # Easy (reset)
        DIFFICULTY = 'easy'
        monster_speed_mult = 1.0
        clue_switch_rate = 1.0
    # if k == b'9' and player_frozen:
    #     player_frozen = False

def keyboard_up(k, x, y):
    if k in keys_down:
        keys_down.remove(k)

def special_down(key, x, y):
    # Camera controls with arrow keys - back to working ranges
    global pdir, TPS_DIST, TPS_HEIGHT, third_person_height, third_person_angle
    if camera_mode == third_person_mode:
        # Up/down control height, left/right control horizontal rotation
        if key == GLUT_KEY_UP:
            third_person_height = min(1200.0, third_person_height + 20.0)
        elif key == GLUT_KEY_DOWN:
            third_person_height = max(100.0, third_person_height - 20.0)
        elif key == GLUT_KEY_LEFT:
            third_person_angle = (third_person_angle + 10.0) % 360
        elif key == GLUT_KEY_RIGHT:
            third_person_angle = (third_person_angle - 10.0) % 360
        return

    # Ignore arrows while in overhead "third_person_mode"
    if camera_mode == third_person_mode:
        return

    if key == GLUT_KEY_LEFT:
        pdir += 4.0  # Rotate camera left
    elif key == GLUT_KEY_RIGHT:
        pdir -= 4.0  # Rotate camera right
    elif key == GLUT_KEY_UP:
        TPS_DIST = max(150.0, TPS_DIST - 20.0)  # Move camera closer (better min range)
        TPS_HEIGHT = max(40.0, TPS_HEIGHT - 5.0)  # Also lower camera slightly
    elif key == GLUT_KEY_DOWN:
        TPS_DIST = min(400.0, TPS_DIST + 20.0)  # Move camera further (reasonable max)
        TPS_HEIGHT = min(150.0, TPS_HEIGHT + 5.0)  # Also raise camera slightly (better max)

def mouse(button, state, x, y):
    pass

# ---------- Boost/Scooby ----------
def activate_boost():
    global scooby_active, scooby_timer, scooby_cd_left
    scooby_active = True
    scooby_timer = scooby_dur
    scooby_cd_left = scooby_cd
    # Track achievement
    achievement_stats['boost_count'] += 1

# ---------- Main loop ----------
def init_gl():
    glClearColor(0.1, 0.05, 0.15, 1)  # Dark purple background
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    # Brighter, warmer lighting for better colors
    # glLightfv(GL_LIGHT0, GL_POSITION, (1.0, 0.4, 0.8, 0.0))
    # glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.2, 1.2, 1.0, 1.0))  # Brighter, slightly warm
    # glLightfv(GL_LIGHT0, GL_AMBIENT, (0.4, 0.4, 0.4, 1.0))  # More ambient light

def update(dt):
    global invuln_t, m_spawn_timer, m_visible_timer, scooby_timer, scooby_active, scooby_cd_left, m_name, m_name_revealed, game_won
    if lives <= 0 or game_won:
        return
    update_player(dt)
    update_traps(dt)  # Add trap system update
    update_achievement_stats(dt)  # Track achievements
    # Clues
    global clue_switch_timer
    new_pickups = draw_clues_and_pickup.__wrapped_pickups if hasattr(draw_clues_and_pickup, '__wrapped_pickups') else 0
    clue_switch_timer -= dt
    if clue_switch_timer <= 0.0:
        switch_clues()
        clue_switch_timer = CLUE_SWITCH_BASE / clue_switch_rate
    # Monster spawning/logic
    try_spawn_monster(dt)
    update_monster(dt)
    # Collision
    check_player_hit()
    if invuln_t > 0.0: invuln_t -= dt
    # Scooby timers
    if scooby_active:
        scooby_timer -= dt
        if scooby_timer <= 0.0:
            scooby_active = False
    if scooby_cd_left > 0.0:
        scooby_cd_left -= dt
    # Reveal name when all clues collected
    if not m_name_revealed and collected_clues() >= TOTAL_CLUES:
        m_name_revealed = True
        m_name = "Old Man Jenkins"
        game_won = True  # Player wins when monster identity is revealed!

    # Check for achievements
    check_achievements()

def display():
    # compute dt
    global last_ms
    now = glutGet(GLUT_ELAPSED_TIME)
    if last_ms == 0: last_ms = now
    dt = (now - last_ms) / 1000.0
    dt = clamp(dt, 0.0, 0.05)
    last_ms = now

    # logic update
    update(dt)

    # ---- render ----
    # Always set default background color at start of frame
    glClearColor(0.1, 0.05, 0.15, 1)  # Default dark purple background

    glViewport(0, 0, WIN_W, WIN_H)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    update_camera()

    # Dynamic lighting based on game state
    clue_count = collected_clues()
    t = glutGet(GLUT_ELAPSED_TIME) / 1000.0

    # Base lighting changes with monster proximity and clues
    monster_dist = math.sqrt((px - mx)**2 + (py - my)**2)

    if lives == 1:
        glClearColor(0.1, 0.01, 0.2, 2)  

    draw_floor_and_hall()
    draw_all_rooms()
    draw_house_decorations()  # Add house decorations instead of outdoor
    draw_traps()  # Add trap drawing

    # Draw clues (and do pickup in logic path)
    draw_clues_and_pickup()

    # Player
    glPushMatrix()
    glTranslatef(px, py, 0)
    glRotatef(pdir, 0, 0, 1)
    draw_shaggy()
    glPopMatrix()

    # Scooby when active
    if scooby_active:
        glPushMatrix()
        glTranslatef(px + 30.0, py - 20.0, 0)
        draw_scooby()
        glPopMatrix()

    # Monster
    if m_visible:
        glPushMatrix()
        glTranslatef(mx, my, 0)
        draw_monster()
        glPopMatrix()

    # HUD
    draw_hud()

    # Game over block
    if lives <= 0:
        glDisable(GL_LIGHTING)
        glClearColor(1.0, 0.0, 0.0, 1.0)  # Pure red
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        draw_text(WIN_W//2 - 80, WIN_H//2, "GAME OVER — press R to reset")
        glEnable(GL_LIGHTING)
    elif game_won:
        glDisable(GL_LIGHTING)
        draw_text(WIN_W//2 - 120, WIN_H//2 + 20, f"YOU WON! Monster was: {m_name}")
        draw_text(WIN_W//2 - 80, WIN_H//2 - 20, "Press R to play again")
        glEnable(GL_LIGHTING)

    glutSwapBuffers()
    glutPostRedisplay()

# Monkey patch to let logic know how many were picked in this frame without extra globals
# (Not essential to gameplay; safe no-op if ignored.)
old_draw_clues = draw_clues_and_pickup
def draw_clues_and_pickup_wrapper():
    picked = old_draw_clues()
    draw_clues_and_pickup.__wrapped_pickups = picked
    return picked
draw_clues_and_pickup = draw_clues_and_pickup_wrapper

def reshape(w, h):
    global WIN_W, WIN_H, ASPECT
    WIN_W, WIN_H = max(1, w), max(1, h)
    ASPECT = WIN_W / float(WIN_H)

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutCreateWindow(b"Scooby Doo: Mystery Hunt - OpenGL Prototype (Overhead 'U', No Roof)")

    init_gl()
    reset_game()

    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard_down)
    glutKeyboardUpFunc(keyboard_up)
    glutSpecialFunc(special_down)
    glutReshapeFunc(reshape)
    glutMouseFunc(mouse)

    glutMainLoop()

if __name__ == '__main__':
    main()
