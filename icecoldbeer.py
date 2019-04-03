# icecoldbeer.py
# Ice Cold Beer Game
# by Dan Davies dan.m.davies@gmail.com
# April 1, 2019

import pygame, sys
from pygame.locals import *
import math

# frames per second
FPS = 30

# define the window area
WINDOWWIDTH = 700
WINDOWHEIGHT = 700

# define the playing area
LEFTLIMIT = 145
RIGHTLIMIT = 547
TOPLIMIT = 10
BOTTOMLIMIT = WINDOWHEIGHT - 10

# set colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (185, 185, 185)
BROWN = (204, 102, 0) # for game machine background
RED = (255, 0, 0) # for scores and ball remaining
LIGHTYELLOW = (255, 255, 204) # for target goal
SILVER = (224, 224, 224) # ball
TITLESHADOWCOLOR = GRAY
TITLETEXTCOLOR = WHITE

# set background image
backgroundImg = pygame.image.load('background.png')

class Hole:
	posx: int
	posy: int
	radius: int

def main():
	global FPSCLOCK, DISPLAYSURF, TEXTFONT, SCOREFONT, OOPSFONT

	pygame.init()
	FPSCLOCK = pygame.time.Clock()
	DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT), 0, 32)
	pygame.display.set_caption('Ice Cold Beer')

	# text fonts
	TEXTFONT = pygame.font.Font('freesansbold.ttf', 18)
	SCOREFONT = pygame.font.Font('freesansbold.ttf', 24)
	OOPSFONT = pygame.font.Font('freesansbold.ttf', 19) # to display "OOPS" when the ball goes in a hole

	# define the lever nut starting positions
	LEFTNUTSETUPHEIGHT = BOTTOMLIMIT + 40 # setup height is the height where the lever picks up the ball, off the field
	RIGHTNUTSETUPHEIGHT = BOTTOMLIMIT + 50
	LEFTNUTSTARTINGHEIGHT = 570
	RIGHTNUTSTARTINGHEIGHT = 585

	# define lever width and movement speed and maximum gap they can have
	LEVERWIDTH = 10
	LEVERSETUPSPEED = 5 # lever speed when it is setting up the game
	LEVERSPEED = 2 # lever speed during gameplay

	MAXLEVERGAP = 60 # maximum distance between the left and right lever nuts

	# define score display positions and number of digits
	BALLSREMAININGDISPLAYTOPLEFT = (223, 562)
	CURRENTSCOREDISPLAYTOPLEFT = (221, 590)
	TOTALSCOREDISPLAYTOPLEFT = (221, 619)
	BALLSREMAININGDIGITS = 1
	CURRENTSCOREDIGITS = 3
	TOTALSCOREDIGITS = 4

	# ball radius
	BALLRADIUS = 8

	# friction threshold of the ball - it needs at least this acceleration to move from rest
	BALLFRICTIONTHRESHOLD = 0.05

	# define positions of the control nuts that move the lever up and down
	leftNutHeight = BOTTOMLIMIT - 10 + 50
	rightNutHeight = BOTTOMLIMIT + 50

	# define ball starting position
	ballStartPosx = RIGHTLIMIT - BALLRADIUS
	ballStartPosy = BOTTOMLIMIT - BALLRADIUS - int(LEVERWIDTH/2)
	ballPosx = ballStartPosx
	ballPosy = ballStartPosy
	ballVelx = 0
	ballAccy = 10 # downward acceleration of the ball in freefall, used to calculate rolling acceleration

	ballInPlay = False # ball starts out of play to begin the game

	gameStart = False # the game has not started yet (setup phase, player is not in control)

	displayOops = False # boolean to tell whether to display "OOPS" instead of the total score

	# balls remaining variables
	STARTINGBALLSREMAINING = 3
	ballsRemaining = STARTINGBALLSREMAINING

	# define holes (positions, radii)
	holeList = getHoleList()

	# define goals
	goalList = getGoalList()

	# all holes including goal holes
	allHoles = holeList + goalList

	# define target goal
	targetGoal = goalList[0]
	goalFlashOn = True # whether the goal is flashing "on"
	goalFlashTime = 0 # how long the goal flash has been on
	MAXGOALFLASHTIME = 0.5 # how long to flash the goal (seconds)

	# score variables
	currentScore = (goalList.index(targetGoal)+1)* 100
	SCOREREDUCTIONINCREMENT = 10
	totalScore = 0
	currentScoreTime = 0
	MAXSCORETIME = 3 # seconds

	showIntro = True # intro screen with instructions

	resetGame = False

	while True:

		DISPLAYSURF.fill(WHITE)

		# draw the playing field
		DISPLAYSURF.blit(pygame.transform.scale(backgroundImg, (WINDOWWIDTH, WINDOWHEIGHT)), (0,0))

		# draw remaining balls text
		drawText(numToStr(ballsRemaining, BALLSREMAININGDIGITS), SCOREFONT, BALLSREMAININGDISPLAYTOPLEFT, RED)

		# draw current score text
		drawText(numToStr(currentScore, CURRENTSCOREDIGITS), SCOREFONT, CURRENTSCOREDISPLAYTOPLEFT, RED)

		# draw total score text
		if not displayOops:
			drawText(numToStr(totalScore, TOTALSCOREDIGITS), SCOREFONT, TOTALSCOREDISPLAYTOPLEFT, RED)
		else:
			# display 'oops' instead of total score. This happens when the ball goes into a hole.
			# display until the ball is in play again
			drawText('OOPS', OOPSFONT, TOTALSCOREDISPLAYTOPLEFT, RED)
			displayOops = not ballInPlay

		# draw holes
		for hole in allHoles:
			pygame.draw.circle(DISPLAYSURF, BLACK, (hole.centerx, hole.centery), hole.radius, 0)

		# flash the target hole
		if goalFlashOn:
			# draw the goal hole as flashing
			pygame.draw.circle(DISPLAYSURF, LIGHTYELLOW, (targetGoal.centerx, targetGoal.centery), targetGoal.radius, 0)
			
		# increment the flash time and change the flashing status when MAXGOALFLASHTIME is reached
		goalFlashTime += 1/FPS
		if goalFlashTime >= MAXGOALFLASHTIME:
			goalFlashTime = 0
			goalFlashOn = not goalFlashOn

		# show the intro screen
		if showIntro:
			showIntroMessage()
			showIntro = False

		# move the lever nuts
		# keep track of original nut positions
		originalLeftNutHeight = leftNutHeight
		originalRightNutHeight = rightNutHeight
		if not ballInPlay:
			# the ball is not in play - bring the levers down to the starting position
			if leftNutHeight < LEFTNUTSETUPHEIGHT:
				leftNutHeight += LEVERSETUPSPEED
			if rightNutHeight < RIGHTNUTSETUPHEIGHT:
				rightNutHeight += LEVERSETUPSPEED

			# if either nut has exceeded the starting position, adjust it to the starting position
			if leftNutHeight > LEFTNUTSETUPHEIGHT:
				leftNutHeight = LEFTNUTSETUPHEIGHT
			if rightNutHeight > RIGHTNUTSETUPHEIGHT:
				rightNutHeight = RIGHTNUTSETUPHEIGHT

			# if both nuts have reached the setup position, put the ball in play
			if leftNutHeight == LEFTNUTSETUPHEIGHT and rightNutHeight == RIGHTNUTSETUPHEIGHT:
				ballPosx = ballStartPosx
				ballInPlay = True
		else:
			if not gameStart:
				# the game is still in setup phase the the player does not have control until the lever moves to 
				# its starting position

				# move the lever up to its starting position
				if leftNutHeight > LEFTNUTSTARTINGHEIGHT:
					leftNutHeight -= LEVERSETUPSPEED
				if rightNutHeight > RIGHTNUTSTARTINGHEIGHT:
					rightNutHeight -= LEVERSETUPSPEED

				# if both nuts have reached or exceeded the starting position, give player control by setting gameStart to True
				if leftNutHeight <= LEFTNUTSTARTINGHEIGHT and rightNutHeight <= RIGHTNUTSTARTINGHEIGHT:
					gameStart = True
			else:
				# game has started and player is in control - let the player move the lever
				keystate = pygame.key.get_pressed()
				if keystate[K_1]:
					leftNutHeight -= LEVERSPEED
				if keystate[K_q]:
					leftNutHeight += LEVERSPEED
				if keystate[K_EQUALS]:
					rightNutHeight -= LEVERSPEED
				if keystate[K_LEFTBRACKET]:
					rightNutHeight += LEVERSPEED

				# check to make sure lever nuts haven't left the playing area
				for nutHeight in (leftNutHeight, rightNutHeight):
					if not (TOPLIMIT <= nutHeight <= BOTTOMLIMIT):
						# reset the nut positions
						leftNutHeight = originalLeftNutHeight
						rightNutHeight = originalRightNutHeight

				# make sure the lever nuts are never more than MAXLEVERGAP away from each other
				if abs(leftNutHeight - rightNutHeight) > MAXLEVERGAP:
					# reset the nut positions
					leftNutHeight = originalLeftNutHeight
					rightNutHeight = originalRightNutHeight

		# move ball
		# keep track of original ball position in case it moves out of the playing field
		originalBallPosx = ballPosx

		tanLeverAngle = (rightNutHeight - leftNutHeight) / (RIGHTLIMIT - LEFTLIMIT) # tangent of lever angle
		ballAccx = ballAccy * tanLeverAngle # horizontal acceleration of the ball

		# if both the velocity and acceleration of the ball are too small, the ball is stopped by friction		
		if math.fabs(ballVelx) <= BALLFRICTIONTHRESHOLD and math.fabs(ballAccx) <= BALLFRICTIONTHRESHOLD:
			# ball gets stopped by friction
			ballVelx = 0
		else:
			ballVelx += ballAccx

		# update x position of ball
		ballPosx += int(ballVelx)
		
		# check if ball left the playing field
		if ballPosx < LEFTLIMIT + BALLRADIUS:
			ballPosx = LEFTLIMIT + BALLRADIUS
			ballVelx = 0

		elif ballPosx > RIGHTLIMIT - BALLRADIUS:
			ballPosx = RIGHTLIMIT - BALLRADIUS
			ballVelx = 0

		# update y position of ball
		ballPosxRatio = (ballPosx - LEFTLIMIT) / (RIGHTLIMIT - LEFTLIMIT) # ratio (0 - 1) of how far along the ball is from left to right
		ballPosy = math.ceil(leftNutHeight + ((rightNutHeight - leftNutHeight) * ballPosxRatio)) - int(LEVERWIDTH/2) - BALLRADIUS
		ballPosy += 1 # lower the ball by one pixel to ensure contact with the lever (otherwise it sometimes floats by one pixel)

		# check for hole collision
		if ballInPlay:
			hole = checkHoleCollision(ballPosx, ballPosy, BALLRADIUS, allHoles)
			if hole != None:
				# ball went in a hole
				if hole == targetGoal:
					# ball went into the target goal 
					# add score to total score - needs animation
					totalScore += currentScore

					# check if this is the final goal
					if targetGoal == goalList[-1]:
						# final goal - player wins!
						showWinMessage()
						resetGame = True
					else:
						# update target goal to the next goal
						targetGoal = goalList[goalList.index(targetGoal) + 1]

						# update current score
						currentScore = (goalList.index(targetGoal)+1)* 100
				else:
					# ball went in a regular hole
					ballsRemaining -= 1

					# show "oops" display
					displayOops = True

					if ballsRemaining == 0:
						# game over
						showLoseMessage()
						displayOops = False
						resetGame = True
				ballInPlay = False
				gameStart = False

		# draw the lever
		pygame.draw.line(DISPLAYSURF, SILVER, (LEFTLIMIT, leftNutHeight), (RIGHTLIMIT, rightNutHeight), LEVERWIDTH)

		# draw ball
		if ballInPlay:
			pygame.draw.circle(DISPLAYSURF, SILVER, (ballPosx, ballPosy), BALLRADIUS,0)

		# update the score timer
		if gameStart:
			currentScoreTime += 1/FPS
			if currentScoreTime >= MAXSCORETIME:
				if currentScore <= 0:
					currentScore = 0
				else:
					currentScore -= SCOREREDUCTIONINCREMENT
				currentScoreTime = 0

		# check for exit game
		checkForExit()

		# update display and increment clock
		pygame.display.update()
		FPSCLOCK.tick(FPS)

		if resetGame:
			ballsRemaining = STARTINGBALLSREMAINING
			targetGoal = goalList[0]
			currentScore = (goalList.index(targetGoal)+1)* 100
			totalScore = 0
			resetGame = False

def getGoalList():
	# define the center locations and radii of the goals
	goalCoordinatesList = ((350, 486, 8), (481, 472, 8), (220, 436, 8), (415, 399, 8), (297, 339, 8),
		(471, 278, 8),(358, 246, 8), (240, 215, 8), (422, 170, 8), (313, 143, 8))
	return createHoleList(goalCoordinatesList)

def getHoleList():
	# define the center locations and radii of the holes
	holeCoordinatesList = ((203, 482, 11), (177, 448, 11), (164, 409, 12), (257, 469, 11), (302, 467, 12),
		(350, 453, 11), (403, 475, 11), (497, 520, 11), (525, 473, 11), (539, 446, 12), (495, 442, 11),
		(447, 453, 11), (410, 439, 11), (251, 415, 11), (538, 408, 11), (452, 400, 12), (353, 407, 12),
		(314, 392, 11), (225, 379, 12), (286, 373, 11), (336, 371, 11), (498, 356, 12), (425, 358, 11),
		(391, 356, 11), (263, 351, 11), (197, 340, 11), (369, 340, 11), (472, 324, 11), (515, 305, 11),
		(445, 302, 11), (231, 326, 12), (182, 313, 11), (267, 312, 11), (164, 285, 13), (297, 289, 11),
		(360, 294, 11), (333, 271, 13), (386, 271, 13), (418, 278, 11), (523, 279, 11), (523, 279, 11),
		(169, 227, 13), (210, 243, 11), (240, 254, 11), (271, 243, 11), (307, 247, 11), (418, 247, 13),
		(471, 230, 11), (498, 254, 11), (538, 252, 12), (197, 215, 11), (282, 214, 11), (333, 224, 12),
		(386, 223, 12), (422, 208, 11), (359, 201, 11), (210, 188, 11), (219, 153, 13),(241, 179, 11),
		(314, 184, 11), (291, 163, 12), (335, 163, 12), (378, 171, 11), (445, 190, 11), (467, 170, 11),
		(522, 163, 12), (269, 144, 11), (358, 143, 11), (399, 150, 11), (444, 150, 11), (421, 131, 12),
		(291, 124, 13), (336, 124, 13))
	return createHoleList(holeCoordinatesList)

def createHoleList(coordinatesList):
	# creates a list of holes from the input hole coordinates
	# used by getHoleList() and getHoleList()
	holeList = []
	for coordinates in coordinatesList:
		hole = Hole()
		hole.centerx, hole.centery, hole.radius = coordinates
		holeList.append(hole)
	return holeList	

def checkHoleCollision(ballPosx, ballPosy, ballRadius, holeList):
	# check for a collision with any hole
	# a hole collision occurs if more than 80% of the ball diameter covers a hole
	THRESHOLDCOVERAGE = 0.8
	for hole in holeList:
		d = getDistance((ballPosx, ballPosy), (hole.centerx, hole.centery))
		
		# coverage is what ratio of the ball's diameter is covering the hole
		if d > hole.radius + ballRadius:
			coverage = 0
		elif d < hole.radius - ballRadius:
			coverage = 1
		else:
			coverage = 1 - ( (d + ballRadius - hole.radius) / (2 * ballRadius) )

		if coverage >= THRESHOLDCOVERAGE:
			# ball goes in hole - return the hole it goes in
			return hole
	return None

def getDistance(p1, p2):
	return math.sqrt( ((p2[0] - p1[0])**2) + ((p2[1] - p1[1])**2) )

def numToStr(number, length):
	# returns a string of the number in the designated length by adding 0's to the left
	numStr = str(number)
	while len(numStr) < length:
		numStr = '0' + numStr
	return numStr

def drawText(text, font, topLeft, color):
	# draws text at the location topLeft

	# clear the previous text
	fontSurface = font.render(text, True, BLACK)

	# draw the text
	surfaceObj = font.render(text, True, RED, BLACK)
	rectObj = surfaceObj.get_rect(topleft = topLeft)
	DISPLAYSURF.blit(surfaceObj, rectObj)

def checkForSpacePress():
	# check events for KEYUP event
	checkForExit()
	keystate = pygame.key.get_pressed()
	return keystate[K_SPACE]

def makeTextObjs(text, font, color):
	surf = font.render(text, True, color)
	return surf, surf.get_rect()

def showTextBox(text):
	# display a text box in the center of the screen
	lineList = text.splitlines()
	numLines = len(lineList)
	for lineIndx in range(len(lineList)):
		line = lineList[lineIndx]
		surfaceObj = TEXTFONT.render(line, True, GRAY, BLACK)
		rectObj = surfaceObj.get_rect()
		spacing = rectObj.height
		rectObj.center = (int(WINDOWWIDTH/2), int(WINDOWHEIGHT/2) - (spacing * numLines) + (spacing * (lineIndx+1)))
		DISPLAYSURF.blit(surfaceObj, rectObj)

	# wait for user to press any key
	while not checkForSpacePress():
		pygame.display.update()
		FPSCLOCK.tick()

def showIntroMessage():
	# show introductory message
	introText = "Ice Cold Beer\n\n Press '1' and 'q' to move the left side up and down.\n\nPress '=' and '[' to move the right side up and down."
	introText += '\n\n Try to get the ball in the flashing goal!'
	introText += '\n\n Press [SPACE] to begin.'
	showTextBox(introText)
	showIntro = False


def showWinMessage():
	# show winning message
	winText = 'YOU WIN!!\n\nCONGRATULATIONS!!!'
	winText += '\n\n Press [SPACE] to play again.'
	showTextBox(winText)

def showLoseMessage():
	loseText = 'Thanks for playing.'
	loseText += '\n\n Press [SPACE] to play again.'
	showTextBox(loseText)

def checkForExit():
	# check for exit
	for event in pygame.event.get():
		if event.type == QUIT:
			pygame.quit()
			sys.exit()

if __name__ == '__main__':
	main()