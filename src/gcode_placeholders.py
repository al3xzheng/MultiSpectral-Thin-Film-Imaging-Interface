

from math import sqrt

"""
    The Backend Logic: Responsible for calculating the physical toolpath
    and the theoretical timing (Time Vector) of the scan pattern.
    """


class GCodePlaceholders:

    def __init__(self, mode,  X_initial, Y_initial, Z_initial, ΔX, ΔY, ΔZ, XBound, YBound, ZBound, Speed, Acceleration, Jerk, n_x, n_y):
        self.Xinit = X_initial
        self.Yinit = Y_initial
        self.Zinit = Z_initial
        self.X = ΔX
        self.Y = ΔY
        self.Z = ΔZ
        self.XBound = XBound
        self.YBound = YBound
        self.Zbound = ZBound
        self.speed = Speed
        self.acceleration = Acceleration
        self.jerk = Jerk
        self.mode = int(mode)
        self.output_file = "3d-printer_scan_pattern_output.txt"
        self.n_x = n_x
        self.n_y = n_y

        self.numIterations = 20000

        #TODO 
        self.N_x = n_x
        self.N_y = n_y

        if(self.Xinit >= 0 and self.Xinit <= self.XBound
            and self.Yinit >= 0 and self.Yinit <= self.YBound
            and self.Zinit >= 0 and self.Zinit <= self.Zbound):

            self.createGCode()
            self.Scan()
            self.endPrint()

        else:
            print("The initial locations exceeds the Bounds")
        
        self.timeVector = self.createTimeVector()
        print(self.timeVector)

    def createTimeVector(self):
                    
        speed = self.speed/60

        case1 = []
        case2 = []
        xDistance =[]
        xTimes = []
        yDistance = []
        yTimes = []

        # xDistance is size of n_x - 1
        for i in range(1, self.n_x):
            xDistance.append(i*self.X//self.n_x)
        # yDistance is size of n_y - 1
        for i in range(1, abs(self.n_y)):
            yDistance.append(i*abs(self.Y)//self.n_y)

        if(self.mode == 2):

            # Assume hor motion first applies:
            # Implement algorithm
            for val in (yDistance):
                if(val <= speed**2/(2*self.acceleration)):
                    case1.append(sqrt(val*2/self.acceleration))
                elif(val <= self.Y - (speed**2 - self.jerk**2)/(2*self.acceleration)):
                    print(val)
                    case1.append((val - speed**2/(2*self.acceleration))/speed + speed/self.acceleration)
                    print((val - speed**2/(2*self.acceleration))/speed)
                elif(val <= self.Y):
                    k = val - self.Y + (speed**2 - self.jerk**2)/(2*self.acceleration)
                    # Taking the greater root, more checks necessary later.
                    case1.append((speed + sqrt(speed**2 - 2*self.acceleration*k))/self.acceleration)

            for val in (yDistance):
                if(val <= (speed**2 - self.jerk**2)/(2*self.acceleration)):
                    case2.append((-self.jerk + sqrt(self.jerk**2 + 2*self.acceleration *val))/self.acceleration)
                elif(val <= self.Y - (speed**2 - self.jerk**2)/(2*self.acceleration)):
                    case2.append((val - (speed**2 - self.jerk**2)/(2*self.acceleration))/speed)
                elif(val <= self.Y):
                    k = val - self.Y + (speed**2 - self.jerk**2)/(2*self.acceleration)
                    # Taking the greater root, more checks necessary later.
                    case2.append((speed + sqrt(speed**2 - 2*self.acceleration*k))/self.acceleration)

            for val in (xDistance):
                if(val <= speed**2/(2*self.acceleration)):
                    xTimes.append((-self.jerk + sqrt(self.jerk**2 + 2*self.acceleration *val))/self.acceleration)
                elif(val <= self.X - (speed**2 - self.jerk**2)/(2*self.acceleration)):
                    xTimes.append((val - (speed**2 - self.jerk**2)/(2*self.acceleration))/speed)
                elif(val <= self.X):
                    k = val - self.X + (speed**2 - self.jerk**2)/(2*self.acceleration)
                    # Taking the greater root, more checks necessary later.
                    xTimes.append((speed + sqrt(speed**2 - 2*self.acceleration*k))/self.acceleration)

            yTimes.append(case1)
            yTimes.append(case2)

            timeVector = [0]

            # Total amount of nodes to image. The first node of the timeVector is at time 0.
            N = (self.n_x-1)*(self.N_x-1) + (self.n_y-1)*self.N_y + 1

            # case 1: time vector population, populates for the first line, including the corner node.
            # This means the algorithm goes to the end.
            # 
            for i in range(self.n_y-1):
                timeVector.append(yTimes[0][i] + timeVector[i-1])

            # 
            next = self.n_y
            segment = 1
            for i in range(self.n_y, N):
                if(i == next):
                    if(segment == 0):
                        next = next + self.n_y-1
                        segment = 1
                    else:
                        next = next + self.n_x-1
                        segment = 0        

                if(~segment):
                    timeVector.append(xTimes[i + self.n_x-1 - next]+ timeVector[i-1])
                else:
                    timeVector.append(yTimes[1][i + self.n_y-1 - next] + timeVector[i-1])

        elif(self.mode == 1):

            # Assume hor motion first applies:
            # Implement algorithm
            for val in (xDistance):
                if(val <= speed**2/(2*self.acceleration)):
                    case1.append(sqrt(val*2/self.acceleration))
                elif(val <= self.X - (speed**2 - self.jerk**2)/(2*self.acceleration)):
                    # print(val)
                    case1.append((val - speed**2/(2*self.acceleration))/speed+speed/self.acceleration)
                    # print((val - speed**2/(2*self.acceleration))/speed)
                elif(val <= self.X):
                    k = val - self.X + (speed**2 - self.jerk**2)/(2*self.acceleration)
                    # Taking the greater root, more checks necessary later.
                    timeOffset = speed/self.acceleration + (self.X - speed**2/self.acceleration + self.jerk**2/(2*self.acceleration))/speed
                    case1.append((speed + sqrt(speed**2 - 2*self.acceleration*k))/self.acceleration + timeOffset)

            for val in (xDistance):
                if(val <= (speed**2 - self.jerk**2)/(2*self.acceleration)):
                    case2.append((-self.jerk + sqrt(self.jerk**2 + 2*self.acceleration *val))/self.acceleration)
                elif(val <= self.X - (speed**2 - self.jerk**2)/(2*self.acceleration)):
                    case2.append((val - (speed**2 - self.jerk**2)/(2*self.acceleration))/speed + (speed-self.jerk)/self.acceleration)
                elif(val <= self.X):
                    k = val - self.X + (speed**2 - self.jerk**2)/(2*self.acceleration)
                    # Taking the greater root, more checks necessary later.
                    timeOffset = (speed-self.jerk)/self.acceleration + (self.X - (speed**2-self.jerk**2)/self.acceleration)/speed
                    case2.append((speed + sqrt(speed**2 - 2*self.acceleration*k))/self.acceleration)

            for val in (yDistance):
                if(val <= speed**2/(2*self.acceleration)):
                    yTimes.append((-self.jerk + sqrt(self.jerk**2 + 2*self.acceleration *val))/self.acceleration)
                elif(val <= self.Y - (speed**2 - self.jerk**2)/(2*self.acceleration)):
                    yTimes.append((val - (speed**2 - self.jerk**2)/(2*self.acceleration))/speed + (speed-self.jerk)/self.acceleration)
                elif(val <= self.Y):
                    k = val - self.Y + (speed**2 - self.jerk**2)/(2*self.acceleration)
                    # Taking the greater root, more checks necessary later.
                    timeOffset = (speed-self.jerk)/self.acceleration + (self.Y - (speed**2-self.jerk**2)/self.acceleration)/speed
                    yTimes.append((speed + sqrt(speed**2 - 2*self.acceleration*k))/self.acceleration + timeOffset)

            xTimes.append(case1)
            xTimes.append(case2)

            timeVector = [0]

            # Total amount of nodes to image. The first node of the timeVector is at time 0.
            N = (self.n_x-1)*(self.N_x-1) + (self.n_y-1)*self.N_y + 1

            # case 1: time vector population, populates for the first line, including the corner node.
            # This means the algorithm goes to the end.
            # 
            for i in range(self.n_x-1):
                timeVector.append(xTimes[0][i] + timeVector[i-1])

            # 
            next = self.n_x
            segment = 1
            for i in range(self.n_x, N):
                if(i == next):
                    if(segment == 0):
                        next = next + self.n_x-1
                        segment = 1
                    else:
                        next = next + self.n_y-1
                        segment = 0        

                if(~segment):
                    timeVector.append(yTimes[i + self.n_y-1 - next]+ timeVector[i-1])
                else:
                    timeVector.append(xTimes[1][i + self.n_x-1 - next] + timeVector[i-1])

        return timeVector

    
    def createGCode(self):

        with open(self.output_file, "w") as f:
            f.write('G21\r\nG90\r\n')
            f.write(f"{'G1 X'}{self.Xinit}{' Y'}{self.Yinit}{' Z'}{self.Zinit}{' F'}{self.speed}{'\r\n'}")
            #"jerk":  jerk is the slowest speed the printer can move before it decides to completely stop. (Stops and turns).
            f.write(f"{'M205 X'}{self.jerk}{' Y'}{self.jerk}{'\r\n'}")
            #acceleration: mm/s²
            f.write(f"{'M204 T'}{self.acceleration}{'\r\n'}")
            f.write('M118 START\r\n') 
    
    def endPrint(self):
        with open(self.output_file, "a") as f:
            f.write('M118 END\r\n')

    def Scan(self):
        if(self.mode == 1):
            x = self.Xinit + self.X
            y = self.Yinit + self.Y
            z = self.Zinit + self.Z

            increment = 0

            with open(self.output_file, "a") as f:
                while(x >= 0 and x <= self.XBound
                      and y >=0 and y <= self.YBound
                      and z >= 0 and z <= self.Zbound):
                                    
                    if(increment%2 == 0):
                        f.write(f"{'G1 X'}{x}{' F'}{self.speed}{'\r\n'}")
                    elif(increment%2 == 1):
                        f.write(f"{'G1 Y'}{y}{' F'}{self.speed}{'\r\n'}")
                        if(x == self.Xinit):
                            x = self.Xinit + self.X
                        else:
                            x = self.Xinit    
                    
                    increment = increment + 1

                    y = y + self.Y
                    
            print("Filled file written to", self.output_file)
        
        elif(self.mode == 2):
            x = self.Xinit + self.X
            y = self.Xinit + self.Y
            z = self.Zinit + self.Z

            increment = 0

            with open(self.output_file, "a") as f:
                while(x >= 0 and x <= self.XBound
                    and y >= 0 and y <= self.XBound
                    and z >= 0 and z <= self.Zbound):
                    
                    if(increment%2 == 0):
                        f.write(f"{'G1 Y'}{y}{' F'}{self.speed}{'\r\n'}")
                    elif(increment%2 == 1):
                        f.write(f"{'G1 X'}{x}{' F'}{self.speed}{'\r\n'}")
                        if(y == self.Yinit):
                            y = self.Yinit + self.Y
                        else:
                            y = self.Yinit                    

                    increment = increment + 1


                    x = x + self.X
                    # z = z + self.Z
            print("Filled file written to", self.output_file)

        elif(self.mode == 3):
            x = self.Xinit
            y = self.Yinit + self.Y
            z = self.Zinit

            inc = 0;

            with open(self.output_file, "a") as f:
                while(inc < self.numIterations and x >= 0 and x <= self.XBound
                      and y >= 0 and y <= self.YBound 
                      and z >= 0 and z <= self.Zbound):
                    
                    f.write(f"{'G1 Y'}{y}{' F'}{self.speed}{'\r\n'}")
                    
                    if(inc % 2 == 0):
                        y = self.Yinit
                    else:
                        y = self.Yinit + self.Y
                    inc = inc + 1

            print("Filled file written to", self.output_file)
        
        elif(self.mode == 4):
            x = self.Xinit + self.X
            y = self.Yinit
            z = self.Zinit

            inc = 0;

            with open(self.output_file, "a") as f:
                while(inc < self.numIterations and x >= 0 and x <= self.XBound
                      and y >= 0 and y <= self.YBound 
                      and z >= 0 and z <= self.Zbound):
                    
                    f.write(f"{'G1 X'}{x}{' F'}{self.speed}{'\r\n'}")
                    
                    if(inc % 2 == 0):
                        x = self.Xinit
                    else:
                        x = self.Xinit + self.X
                    inc = inc + 1

            print("Filled file written to", self.output_file)


if __name__ == "__main__":
    #def __init__(self, mode,  X_initial, Y_initial, Z_initial, ΔX, ΔY, ΔZ, XBound, YBound, ZBound, Speed, acceleration, jerk, n_x, n_y):
    # Acceleration [units/s/s], speed [units/min], Jerk [units/s]. Units are set in mm, as in G21
    test = GCodePlaceholders(1 ,50, 50, 0, 100, -20, 0, 200, 200, 150, 12000, 700, 4, 3, 3)
        

    # # Safety bound implementation.
    # relativeMotion = True
    # Xvalue = 0
    # Yvalue = 0

    # # Input file name
    # input_file = "RasterScan.txt" 
    # output_file = "RasterScanFilled.txt"    

    # with open(input_file, "r") as f:
    #     code = f.read()

    # output_file = code.format(**self.values)

    # i = 0;
    # length = len(code)

    # while(i < length):
    #     if(code[i] == 13):
    #         #if G90 or G91, set the marker appropraitely s.t. the next one read replaces the values, then set the flag back.
    #         # Absolute
    #         if(code[i-3,i] == 'G90'):
    #             relativeMotion = False
    #         elif(code[i-3,i] == 'G91'):
    #             relativeMotion = True
    #         #increment adn decrement.

    #     elif(code[i] == 'X'):
    #         if(relativeMotion):
    #             Xvalue = Xvalue + int(code[i+1, findEndOfWord(code, i)])
    #         else:
    #             Xvalue = int(code[i+1, findEndOfWord(code, i)])

    #     elif(code[i] == 'Y'):
    #         if(relativeMotion):
    #             Yvalue = Yvalue + int(code[i+1, findEndOfWord(code, i)])
    #         else:
    #             Yvalue = int(code[i+1, findEndOfWord(code, i)])

    #     if(Xvalue > 205 or Yvalue > 250):
    #         print("The print/motion exceeds the bounds of the 3d-printer bed")

    #     i = i+ 1
