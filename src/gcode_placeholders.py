# October 28th 2025
# Script fills in "variables" on gcode code to 3d printer so we can altar speed, length, width, etc..


class GCodePlaceholders:

    def __init__(self, mode,  X_initial, Y_initial, Z_initial, ΔX, ΔY, ΔZ, XBound, YBound, ZBound, Speed):
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
        self.mode = int(mode)
        self.output_file = "3d-printer_scan_pattern_output.txt"

        if(self.Xinit >= 0 and self.Xinit <= self.XBound
            and self.Yinit >= 0 and self.Yinit <= self.YBound
            and self.Zinit >= 0 and self.Zinit <= self.Zbound):

            self.createGCode()
            self.Scan()

        else:
            print("The initial locations exceeds the Bounds")
    
    def createGCode(self):

        with open(self.output_file, "w") as f:
            f.write('G21\r\nG90\r\n')
            f.write(f"{'G1 X'}{self.Xinit}{' Y'}{self.Yinit}{' Z'}{self.Zinit}{' F'}{self.speed}{'\r\n'}")
            # f.write('G91\r\n')

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
                while(inc < 5 and x >= 0 and x <= self.XBound
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
                while(inc < 5 and x >= 0 and x <= self.XBound
                      and y >= 0 and y <= self.YBound 
                      and z >= 0 and z <= self.Zbound):
                    
                    f.write(f"{'G1 X'}{x}{' F'}{self.speed}{'\r\n'}")
                    
                    if(inc % 2 == 0):
                        x = self.Xinit
                    else:
                        x = self.Xinit + self.X
                    inc = inc + 1

            print("Filled file written to", self.output_file)


# if __name__ == "__main__":
    # parameters = 
    # outputfile = GCodePlaceholders(1, 5, 5, 10, 20, 0, 200, 200, 150, 12000)










        

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
