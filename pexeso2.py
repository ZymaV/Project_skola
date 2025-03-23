import random, pygame, sys, sqlite3
from pygame.locals import *
import tkinter as tk
from tkinter import simpledialog, messagebox

# ----- Global Constants & Configuration -----
FPS = 30
WINDOWWIDTH = 640
WINDOWHEIGHT = 480
REVEALSPEED = 8  # Speed for the reveal/cover animations
BOXSIZE = 40     # Size of each card in pixels
GAPSIZE = 10     # Gap between cards in pixels
BOARDWIDTH = 6   # Number of columns
BOARDHEIGHT = 6  # Number of rows
assert (BOARDWIDTH * BOARDHEIGHT) % 2 == 0, 'Board must have an even number of boxes.'

XMARGIN = int((WINDOWWIDTH - (BOARDWIDTH * (BOXSIZE + GAPSIZE))) / 2)
YMARGIN = int((WINDOWHEIGHT - (BOARDHEIGHT * (BOXSIZE + GAPSIZE))) / 2)

# Colors (R, G, B)
GRAY     = (100, 100, 100)
NAVYBLUE = ( 60,  60, 100)
WHITE    = (255, 255, 255)
RED      = (255,   0,   0)
GREEN    = (  0, 255,   0)
BLUE     = (  0,   0, 255)
YELLOW   = (255, 255,   0)
ORANGE   = (255, 128,   0)
PURPLE   = (255,   0, 255)
CYAN     = (  0, 255, 255)

BGCOLOR = NAVYBLUE
LIGHTBGCOLOR = GRAY
BOXCOLOR = WHITE
HIGHLIGHTCOLOR = BLUE

# Pexeso icon definitions
DONUT = 'donut'
SQUARE = 'square'
DIAMOND = 'diamond'
OVAL = 'oval'
#Ald 1

ALLCOLORS = (RED, GREEN, BLUE, YELLOW, ORANGE, PURPLE, CYAN)
ALLSHAPES = (DONUT, SQUARE, DIAMOND, OVAL) #Ald 2
assert len(ALLCOLORS) * len(ALLSHAPES) * 2 >= BOARDWIDTH * BOARDHEIGHT, "Board is too big for the number of shapes/colors defined."

# Global display variable (set in main)
DISPLAYSURF = None

# ----- Database Function (Score Saving) -----
def save_score(player_name, score, turns, game_time):
    """Save the player's score, turns, and game time into the database."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS scores (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        points INTEGER NOT NULL,
                        turns INTEGER NOT NULL,
                        time REAL NOT NULL)''')
    cursor.execute("INSERT INTO scores (username, points, turns, time) VALUES (?, ?, ?, ?)",
                   (player_name, score, turns, game_time))
    conn.commit()
    conn.close()

# ----- Login Functions -----
def validate_login(username, password):
    """Check loginInfo.db for the user. If the user does not exist, register them."""
    conn = sqlite3.connect("loginInfo.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT NOT NULL)")
    cursor.execute("SELECT password FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    if row is None:
        # Register new user
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    else:
        if row[0] == password:
            conn.close()
            return True
        else:
            conn.close()
            return False

def login():
    """Prompt the user to log in using tkinter dialogs."""
    root = tk.Tk()
    root.withdraw()
    username = simpledialog.askstring("Login", "Enter username:")
    password = simpledialog.askstring("Login", "Enter password:", show="*")
    if username is None or password is None:
        sys.exit()  # Exit if user cancels the login dialog
    if validate_login(username, password):
        return username
    else:
        messagebox.showerror("Login Failed", "Invalid credentials, please try again.")
        root.destroy()
        return login()

# ----- Pexeso Helper Functions -----
def generateRevealedBoxesData(val):
    """Create a 2D list of booleans with dimensions BOARDWIDTH x BOARDHEIGHT."""
    return [[val] * BOARDHEIGHT for _ in range(BOARDWIDTH)]

def getRandomizedBoard():
    icons = []
    for color in ALLCOLORS:
        for shape in ALLSHAPES:
            icons.append((shape, color))
    random.shuffle(icons)
    numIconsUsed = int(BOARDWIDTH * BOARDHEIGHT / 2)
    icons = icons[:numIconsUsed] * 2  # Create two of each
    random.shuffle(icons)
    
    board = []
    for x in range(BOARDWIDTH):
        column = []
        for y in range(BOARDHEIGHT):
            column.append(icons.pop())
        board.append(column)
    return board

def splitIntoGroupsOf(groupSize, theList):
    result = []
    for i in range(0, len(theList), groupSize):
        result.append(theList[i:i + groupSize])
    return result

def leftTopCoordsOfBox(boxx, boxy):
    left = boxx * (BOXSIZE + GAPSIZE) + XMARGIN
    top = boxy * (BOXSIZE + GAPSIZE) + YMARGIN
    return (left, top)

def getBoxAtPixel(x, y):
    for boxx in range(BOARDWIDTH):
        for boxy in range(BOARDHEIGHT):
            left, top = leftTopCoordsOfBox(boxx, boxy)
            boxRect = pygame.Rect(left, top, BOXSIZE, BOXSIZE)
            if boxRect.collidepoint(x, y):
                return (boxx, boxy)
    return (None, None)

def drawIcon(shape, color, boxx, boxy):
    quarter = int(BOXSIZE * 0.25)
    half = int(BOXSIZE * 0.5)
    left, top = leftTopCoordsOfBox(boxx, boxy)
    if shape == DONUT:
        pygame.draw.circle(DISPLAYSURF, color, (left + half, top + half), half - 5)
        pygame.draw.circle(DISPLAYSURF, BGCOLOR, (left + half, top + half), quarter - 5)
    elif shape == SQUARE:
        pygame.draw.rect(DISPLAYSURF, color, (left + quarter, top + quarter, BOXSIZE - half, BOXSIZE - half))
    elif shape == DIAMOND:
        pygame.draw.polygon(DISPLAYSURF, color, (
            (left + half, top),
            (left + BOXSIZE - 1, top + half),
            (left + half, top + BOXSIZE - 1),
            (left, top + half)
        ))
    elif shape == OVAL:
        pygame.draw.ellipse(DISPLAYSURF, color, (left, top + quarter, BOXSIZE, half))
#Ald 3

def getShapeAndColor(board, boxx, boxy):
    return board[boxx][boxy]

def drawBoxCovers(board, boxes, coverage):
    for box in boxes:
        left, top = leftTopCoordsOfBox(box[0], box[1])
        pygame.draw.rect(DISPLAYSURF, BGCOLOR, (left, top, BOXSIZE, BOXSIZE))
        shape, color = getShapeAndColor(board, box[0], box[1])
        drawIcon(shape, color, box[0], box[1])
        if coverage > 0:
            pygame.draw.rect(DISPLAYSURF, BOXCOLOR, (left, top, coverage, BOXSIZE))
    pygame.display.update()
    pygame.time.wait(int(1000 / FPS))

def revealBoxesAnimation(board, boxesToReveal):
    for coverage in range(BOXSIZE, -REVEALSPEED - 1, -REVEALSPEED):
        drawBoxCovers(board, boxesToReveal, coverage)

def coverBoxesAnimation(board, boxesToCover):
    for coverage in range(0, BOXSIZE + REVEALSPEED, REVEALSPEED):
        drawBoxCovers(board, boxesToCover, coverage)

def drawBoard(board, revealed):
    for boxx in range(BOARDWIDTH):
        for boxy in range(BOARDHEIGHT):
            left, top = leftTopCoordsOfBox(boxx, boxy)
            if not revealed[boxx][boxy]:
                pygame.draw.rect(DISPLAYSURF, BOXCOLOR, (left, top, BOXSIZE, BOXSIZE))
            else:
                shape, color = getShapeAndColor(board, boxx, boxy)
                drawIcon(shape, color, boxx, boxy)
    pygame.display.update()

def drawHighlightBox(boxx, boxy):
    left, top = leftTopCoordsOfBox(boxx, boxy)
    pygame.draw.rect(DISPLAYSURF, HIGHLIGHTCOLOR, (left - 5, top - 5, BOXSIZE + 10, BOXSIZE + 10), 4)
    pygame.display.update()

def startGameAnimation(board):
#ter    
    coveredBoxes = generateRevealedBoxesData(False)
    boxes = [(x, y) for x in range(BOARDWIDTH) for y in range(BOARDHEIGHT)]
    random.shuffle(boxes)
    boxGroups = splitIntoGroupsOf(50, boxes)
    drawBoard(board, coveredBoxes)
    for boxGroup in boxGroups:
        revealBoxesAnimation(board, boxGroup)
        pygame.time.wait(2000)
        coverBoxesAnimation(board, boxGroup)

def gameWonAnimation(board):
    coveredBoxes = generateRevealedBoxesData(True)
    color1 = LIGHTBGCOLOR
    color2 = BGCOLOR
    for i in range(13):
        color1, color2 = color2, color1  # Swap colors
        DISPLAYSURF.fill(color1)
        drawBoard(board, coveredBoxes)
        pygame.display.update()
        pygame.time.wait(300)

def hasWon(revealedBoxes):
    for row in revealedBoxes:
        if False in row:
            return False
    return True

# ----- Screen Drawing Functions -----
def draw_start_menu(player_name):
    DISPLAYSURF.fill((0, 0, 0))
    font = pygame.font.SysFont('arial', 40)
    title = font.render('Pexeso', True, (255, 255, 255))
    prompt = font.render('Press SPACE to Start', True, (255, 255, 255))
    user_text = pygame.font.SysFont('arial', 20).render(f'Logged in as: {player_name}', True, (255, 255, 255))
    DISPLAYSURF.blit(title, (WINDOWWIDTH / 2 - title.get_width() / 2,
                              WINDOWHEIGHT / 2 - title.get_height() / 2 - 40))
    DISPLAYSURF.blit(prompt, (WINDOWWIDTH / 2 - prompt.get_width() / 2,
                              WINDOWHEIGHT / 2 - prompt.get_height() / 2 + 20))
    DISPLAYSURF.blit(user_text, (10, 10))
    pygame.display.update()

def draw_game_over_screen(score, turns, time_value):
    DISPLAYSURF.fill((0, 0, 0))
    font = pygame.font.SysFont('arial', 40)
    title = font.render('Game Over', True, (255, 255, 255))
    score_text = font.render('Score: ' + str(score), True, (255, 255, 255))
    turns_text = font.render('Turns: ' + str(turns), True, (255, 255, 255))
    time_text = font.render('Time: ' + str(round(time_value, 2)), True, (255, 255, 255))
    prompt = font.render('Press R to Restart or Q/ESC to Quit', True, (255, 255, 255))
    DISPLAYSURF.blit(title, (WINDOWWIDTH / 2 - title.get_width() / 2,
                              WINDOWHEIGHT / 2 - title.get_height() / 2 - 100))
    DISPLAYSURF.blit(score_text, (WINDOWWIDTH / 2 - score_text.get_width() / 2,
                                  WINDOWHEIGHT / 2 - score_text.get_height() / 2 - 40))
    DISPLAYSURF.blit(turns_text, (WINDOWWIDTH / 2 - turns_text.get_width() / 2,
                                  WINDOWHEIGHT / 2 - turns_text.get_height() / 2))
    DISPLAYSURF.blit(time_text, (WINDOWWIDTH / 2 - time_text.get_width() / 2,
                                 WINDOWHEIGHT / 2 - time_text.get_height() / 2 + 40))
    DISPLAYSURF.blit(prompt, (WINDOWWIDTH / 2 - prompt.get_width() / 2,
                              WINDOWHEIGHT / 2 - prompt.get_height() / 2 + 100))
    pygame.display.update()

# ----- Main Game Implementation -----
def run_pexeso_game():
    SCORE = 0
    SCORETURN = 0
    timer = 0
    clock = pygame.time.Clock()
    dt = 0

    mainBoard = getRandomizedBoard()
    revealedBoxes = generateRevealedBoxesData(False)
    firstSelection = None  # Store the (boxx, boxy) of the first card clicked

    # Start game animation
    startGameAnimation(mainBoard)

    font = pygame.font.SysFont('Calibri', 15, True, False)
    running = True
    while running:
        mouseClicked = False
        dt = clock.tick(30) / 1000
        timer += dt

        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            elif event.type == MOUSEMOTION:
                mousex, mousey = event.pos
            elif event.type == MOUSEBUTTONUP:
                mousex, mousey = event.pos
                mouseClicked = True

        mousex, mousey = pygame.mouse.get_pos()

        DISPLAYSURF.fill(BGCOLOR)
        drawBoard(mainBoard, revealedBoxes)

        boxx, boxy = getBoxAtPixel(mousex, mousey)
        if boxx is not None and boxy is not None:
            if not revealedBoxes[boxx][boxy]:
                drawHighlightBox(boxx, boxy)
            if not revealedBoxes[boxx][boxy] and mouseClicked:
                revealBoxesAnimation(mainBoard, [(boxx, boxy)])
                revealedBoxes[boxx][boxy] = True
                if firstSelection is None:
                    firstSelection = (boxx, boxy)
                else:
                    shape1, color1 = getShapeAndColor(mainBoard, firstSelection[0], firstSelection[1])
                    shape2, color2 = getShapeAndColor(mainBoard, boxx, boxy)
                    if shape1 == shape2 and color1 == color2:
                        SCORE += 5
                        SCORETURN += 1
                    else:
                        if SCORE > 0:
                            SCORE -= 1
                        SCORETURN += 1
                        pygame.time.wait(1000)
                        coverBoxesAnimation(mainBoard, [firstSelection, (boxx, boxy)])
                        revealedBoxes[firstSelection[0]][firstSelection[1]] = False
                        revealedBoxes[boxx][boxy] = False
                    firstSelection = None

        # Display Score, Turns, and Time on the game screen
        score_text = font.render("Score: " + str(SCORE), True, (0, 0, 0))
        DISPLAYSURF.blit(score_text, (560, 0))
        turn_text = font.render("Turns: " + str(SCORETURN), True, (0, 0, 0))
        DISPLAYSURF.blit(turn_text, (560, 20))
        time_text = font.render("Time: " + str(round(timer, 2)), True, (0, 0, 0))
        DISPLAYSURF.blit(time_text, (560, 40))

        pygame.display.update()

        if hasWon(revealedBoxes):
            gameWonAnimation(mainBoard)
            running = False

    return SCORE, SCORETURN, timer

# ----- Main State Machine -----
def main():
    global DISPLAYSURF
    pygame.init()
    pygame.font.init()
    DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
    pygame.display.set_caption('Pexeso with Start & Game Over Screens')
    
    # Prompt the user to log in before starting the game loop.
    player_name = login()
    
    game_state = "start_menu"
    final_score = 0
    final_turns = 0
    final_time = 0

    while True:
        if game_state == "start_menu":
            draw_start_menu(player_name)
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                    pygame.quit()
                    sys.exit()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                game_state = "pexeso"
                pygame.event.clear()
                
        elif game_state == "pexeso":
            final_score, final_turns, final_time = run_pexeso_game()
            # Save the score using the logged-in player's name.
            save_score(player_name, final_score, final_turns, final_time)
            game_state = "game_over"
            
        elif game_state == "game_over":
            draw_game_over_screen(final_score, final_turns, final_time)
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                    pygame.quit()
                    sys.exit()
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                game_state = "start_menu"
                pygame.event.clear()
            elif keys[pygame.K_q]:
                pygame.quit()
                sys.exit()
                
        pygame.time.wait(int(1000 / FPS))

if __name__ == '__main__':
    main()
