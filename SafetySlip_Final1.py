import threading
import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

#Green LED
GPIO.setup(18, GPIO.OUT)

#Red LED  
GPIO.setup(13, GPIO.OUT)

#Yellow LED
GPIO.setup(19, GPIO.OUT)

#Blue LED
GPIO.setup(16, GPIO.OUT)

#Button
GPIO.setup(21, GPIO.IN, pull_up_down = GPIO.PUD_UP)

#class IOException(Exception):
 #   pass

def process_State(state):
    #Green Light
    if state == 2:
        GPIO.output(18, True)
        time.sleep(1)
        GPIO.output(18, False)
        time.sleep(1)
    #Red Light
    elif state == 1:
        GPIO.output(13, True)
        time.sleep(1)
        GPIO.output(13, False)
        time.sleep(1)
    #Yellow Light
    elif state ==-1:
        GPIO.output(19, True)
        time.sleep(1)
        GPIO.output(19, False)
        time.sleep(1)
    #Yellow Light Blinking(When nothing happens)
    elif state == 4:
        GPIO.output(19, True)
        time.sleep(.25)
        GPIO.output(19, False)
        time.sleep(.25)
        GPIO.output(19, True)
        time.sleep(.25)
        GPIO.output(19, False)
        time.sleep(.25)       

def read_button_Status():
    global switch
    global gtfo
    global reset
    global pause_switch
    #If button is pressed, Keep returning true (make state 'active')
    while(True):
        if(GPIO.input(21) == False):
            GPIO.output(18, True)
            GPIO.output(13, True)
            time.sleep(.5)
            GPIO.output(18, False)
            GPIO.output(13, False)
            timer = 15
            #Exit entire System
            while(GPIO.input(21) == False): #Button pressed
                time.sleep(.1)
                timer = timer - 1
                
                if timer == 0:
                    GPIO.output(16, False)
                    GPIO.output(13, False)
                    GPIO.output(19, False)
                    GPIO.output(18, False)
                    
                    switch = False
                    gtfo = True
                    reset = 0
                    exit()
            #Switch global variable
            if switch == True:
                switch = False
                pause_state()
            else:
                #PAUSE CRITICAL SECTION
                pause_switch = 1
                time.sleep(.1)
                switch = True
                startup()
                pause_switch = 0
                #END PAUSE CRITICAL SECTION
            reset = 0            
                
    
def process_line(myList): #RETURN INT ; myList is an integer list
    voltage = False #boolean declaring whether we are in 0 or 8 state
    full_cycles = 0 #how many times we have gone 0 -> 8 -> 0
    threshold = 6
    def process_digit(n, voltsOn): #n - integer voltsOn- Boolean RETURN INTEGER
        """
        0 = normal step (or cancel attempt to state change)
        1 = digit recieved that should initiate state change attempt
        """
        if n >= 6 and voltsOn or n < 6 and not voltsOn:
            return 0
        else: #attempt to change state
            return 1
    def look_ahead(subList, voltsOn): #RETURN BOOL ; subList is an integer list
        """
        Function to look ahead and determine if state change need to occur

        Assume we will switch until proven wrong
        """
        doSwitch = True
        if len(subList) < 5:
            return False
        for i in subList:
            if voltsOn:
                if i >= threshold:#was 6
                    doSwitch = False
                    break
                else:
                    doSwitch = True
            else:
                if i < threshold: #was 6
                    doSwitch = False
                    break
                else:
                    doSwitch = True
        return doSwitch
    def determine_light(cycles, voltsOn):#Return an integer ; cycles - int ; voltsOn - boolean
        """ 
        1 = red; -1 = yellow; 2 = green; 3 = cautious continue; 4 = all_zeros
        """
        if cycles == 0 and not voltsOn: #nothing ever turned on
            return 4
        elif cycles > 1 or cycles == 1 and voltsOn: #second voltage
            return 1
        elif cycles == 1 and not voltsOn: #single reading
            return 2
        else:
            return -1
    for i in range(len(myList)):
        result = process_digit(myList[i], voltage)
        if result == 1:
            if look_ahead(myList[i:min(i+5, len(myList))],voltage):
                voltage = not voltage
                if not voltage:
                    full_cycles += 1
    return determine_light(full_cycles, voltage)

#===================================Listener================================================================

AO_pin = 0 #flame sensor AO connected to ADC chanannel 0
# change these as desired - they're the pins connected from the
# SPI port on the ADC to the Cobbler
SPICLK = 11
SPIMISO = 9
SPIMOSI = 10
SPICS = 8

#port init
def init():
          GPIO.setwarnings(False)
          GPIO.setmode(GPIO.BCM)
          # set up the SPI interface pins
          GPIO.setup(SPIMOSI, GPIO.OUT)
          GPIO.setup(SPIMISO, GPIO.IN)
          GPIO.setup(SPICLK, GPIO.OUT)
          GPIO.setup(SPICS, GPIO.OUT)
          pass

#read SPI data from MCP3008(or MCP3204) chip,8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)  

        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):

                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin, True)
        
        adcout >>= 1       # first bit is 'null' so drop it
        return adcout

def startup():
         #Startup: TURNS ON EACH LIGHT AND THEN OFF
         GPIO.output(16,False)
         GPIO.output(16,True)
         time.sleep(.5)
         GPIO.output(18,True)
         time.sleep(.5)
         GPIO.output(19,True)
         time.sleep(.5)
         GPIO.output(13,True)
         time.sleep(.5)
         GPIO.output(16,False)
         GPIO.output(18,False)
         GPIO.output(19,False)
         GPIO.output(13,False)
         
def pause_state():
         GPIO.output(16,True)
         GPIO.output(18,True)
         GPIO.output(19,True)
         GPIO.output(13,True)
         #Quick Blink of LEDs
         time.sleep(.2)
         GPIO.output(16,False)
         GPIO.output(18,False)
         GPIO.output(19,False)
         GPIO.output(13,False)
         time.sleep(.2)
         GPIO.output(16,True)
         GPIO.output(18,True)
         GPIO.output(19,True)
         GPIO.output(13,True)
         time.sleep(.2)
         GPIO.output(16,False)
         GPIO.output(18,False)
         GPIO.output(19,False)
         GPIO.output(13,False)
         
def exit_state():
         GPIO.output(16,True)
         GPIO.output(18,True)
         GPIO.output(19,True)
         GPIO.output(13,True)
         time.sleep(.5)
         GPIO.output(16,False)
         time.sleep(.5)
         GPIO.output(18,False)
         time.sleep(.5)
         GPIO.output(19,False)
         time.sleep(.5)
         GPIO.output(13,False)
         
def main(volts):
         
         try:
             volts = []
             state = 0
             global switch
             global gtfo
             global reset
             global pause_switch
             reset = 1
             init()
             time.sleep(2)
             readlength = 80
             readTime = 0.05
             onOff = True
             #print ("will detect voltage")
             while True:
                 #Pause State
                 if gtfo == True:
                     exit_state()
                     exit()
                 while(pause_switch >0):
                     continue

                 while(switch):
                     
                     #Blue LED ON
                     GPIO.output(16, False)
                     time.sleep(.1)
                     GPIO.output(16, True)
                     time.sleep(.2)
                     GPIO.output(16,False)
                     time.sleep(.2)
                     GPIO.output(16, True)
                     pause_switch = 0
                     
                     while len(volts)<readlength:
                                        
                         ad_value = readadc(AO_pin, SPICLK, SPIMOSI, SPIMISO, SPICS)
                         voltage= ad_value*(3.3/1024)*5
                         print("***********")
                         print (" Voltage is: " + str(voltage) +" V")
                         print("***********")
                  
                         print(' ')
                         x = 1/reset
                         time.sleep(readTime)
                         if voltage > 6.00: #IF VALUE > 8 ADDS 8 TO ARRAY, ELSE 0
                             volts.append(8)
                         else:
                             volts.append(0)
                             
                 #State will be 0-Green 1-Red 2-Yellow
                     for i in range(len(volts)):
                         print (volts[i])
                     result = process_line(volts)
                     process_State(result)
                     volts = []
                     time.sleep(1)
                     GPIO.output(18, False)
                     GPIO.output(19, False)
                     GPIO.output(13, False)
                 
                     #Blue LED OFF
                     GPIO.output(16, False)
         except Exception as e:
             main(volts)        

if __name__ =='__main__':
         try:
                  global switch
                  global reset
                  global pause_switch
                  gtfo = False
                  switch = True
                  reset = 1
                  pause_switch = 0
                  #Startup light show!
                  startup()
                  
                  #Thread creation
                  button_thread = threading.Thread(target=read_button_Status)
                  volts = []
                  button_thread.start()
                  main(volts)
                  
         except KeyboardInterrupt:
                  pass
GPIO.cleanup()
