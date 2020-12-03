import time
import Jetson.GPIO as GPIO
import math

# Pin 16 & 18 Used for Communication
# gpio200, gpio38

outStatus = 0
start = 0
count = 0
lastCountEnd = 0
countMax = 2 # in seconds how often pulses will occur
chanInput = 16
chanOutput = 18
peerSpotted = 0
peerInitialDiff = 0
clockResets = 0
refractoryRange = 0#0.5 # 1 # in terms of pi. 
adjustmentFactor = 0.5 # scalar to be multiplied to your adjustment; here if you don't want to adjust large amounts every time
accuracyMargin = 0 # in terms of pi; disable accuracyMargin for systems with more than 2 nodes! scale by minimizing adjustmentFactor
divisionFactor = 2 # not used anymore



# This function operates as the counter. The sleep statement is required to avoid crashing the nanos.
def counter():
	global count, countMax, start, lastCountEnd, outStatus, clockResets
	start = time.time()
	lastCountEnd = time.time()
	a = 1
	while a == 1:
		count=time.time()
		if count - lastCountEnd >= countMax:
			lastCountEnd = count
			clockResets = clockResets + 1
			GPIO.output(chanOutput, GPIO.HIGH)
			outStatus = 1;
			clockDiff = count - start
			# clockIteration = round(clockDiff/countMax) # old way of doing things, now we are iterating a value
			print("Clock Switch Time " + str(round(count,2)) + "; Iteration " + str(round(clockResets)))
		elif outStatus == 1 and count - lastCountEnd >= countMax/20:
			GPIO.output(chanOutput, GPIO.LOW)
			outStatus = 0;
		time.sleep(0.0001) # Probably can be larger



# This function adjusts the phase; the -0.02 pi is to account for processing delays, doesn't work perfectly
def adjust(phase):
	global lastCountEnd, divisionFactor, adjustmentFactor
	if phase < math.pi:
		adjustment = -phase
	elif phase == math.pi:
		adjustment = 0
	elif phase > math.pi: # and phase < 2 * math.pi - accuracyMargin * math.pi:
		adjustment = -phase + 2 * math.pi - 0.02 * math.pi# 0.02


	lastCountEnd = lastCountEnd + adjustment * adjustmentFactor
	print("Adjustment of " + str(round(adjustment * adjustmentFactor/math.pi,2)) + " pi performed (" + str(adjustment * adjustmentFactor / 2 / math.pi * countMax) + " seconds)")



# This function is called when the Jetson detects rising edge. Unfortunately, it is not limited to the input pin & I can't figure out how to do so.
# Making a refractory range would cause instability, so I just use 0.
def align(chanInput):
	global count, countMax, lastCountEnd, peerSpotted, peerInitialDiff, accuracyMargin, refractoryRange
	detectTime = time.time()
	phaseForPrint = (detectTime - lastCountEnd)/countMax * 2
	phase = phaseForPrint * math.pi
	if phaseForPrint > 0.02: # 0.02:
		print("Another unsynchronized counter detected, phase diff =  " + str(phaseForPrint) + " pi")
		peerSpotted = 1;
		peerInitialDiff = phase;
	if phaseForPrint > refractoryRange: # and phaseForPrint < 2 * math.pi - accuracyMargin:
		adjust(phase)



# Setups, events, counter call, and cleanup
def main():
	global chanInput, chanOutput	

	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(chanInput, GPIO.IN)
	GPIO.setup(chanOutput, GPIO.OUT, initial=GPIO.LOW)
	GPIO.setwarnings(False)
	GPIO.add_event_detect(chanInput, GPIO.RISING, callback=align, bouncetime=100)

	counter()

	GPIO.cleanup()



if __name__ == '__main__':
    main()