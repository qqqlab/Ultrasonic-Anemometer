# autobaud.Serial extends pyserial's serial.Serial with:
# - port search
# - autobaud
# - non blocking readline 

import serial # pip install pyserial
import time
import sys
import glob

class Serial(serial.Serial):
    #list all possible serial ports
    def list_ports():
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            patterns = ('/dev/tty[A-Za-z]*', '/dev/ttyUSB*')
            ports = [glob.glob(pattern) for pattern in patterns]
            ports = [item for sublist in ports for item in sublist]  # flatten
        elif sys.platform.startswith('darwin'):
            patterns = ('/dev/*serial*', '/dev/ttyUSB*', '/dev/ttyS*')
            ports = [glob.glob(pattern) for pattern in patterns]
            ports = [item for sublist in ports for item in sublist]  # flatten
        else:
            raise EnvironmentError('Unsupported platform')
        return ports

    #list available serial ports
    def all_available_ports():
        ports = []
        for port in Serial.list_ports():
            try:
                ser = serial.Serial(port)
                ser.close()
                ports.append(port)
            except:
                pass
        return ports

    #returns first available serial port
    def first_available_port():
        for port in Serial.list_ports():
            try:
                ser = serial.Serial(port)
                ser.close()
                return port
            except:
                pass
        return None
        
    #try to find baudrate of pre-opened port
    #sets (and returns) baudrate on success
    def ascii_autobaud(self):
        saved_baudrate = self.baudrate
        saved_timeout = self.timeout
        self.timeout = 0
        for baudrate in [115200, 57600, 38400, 19200, 9600]:
            #print("trying",baudrate)
            self.baudrate = baudrate
            self.reset_input_buffer()
            ccnt = 0
            acnt = 0
            start = time.time()
            while time.time() - start < 2.0 and ccnt<100:
                byte = self.read(1)
                if not byte:
                    time.sleep(0.01)
                    continue
                ccnt += 1
                #print(byte)
                v = int.from_bytes(byte)
                if v == 0 or v >= 128:
                    #print("not ascii")
                    acnt = 0
                    continue
                acnt += 1
                if acnt >= 10:
                     #print("ok",ccnt-10)
                     self.timeout = saved_timeout
                     return baudrate
        self.baudrate = saved_baudrate
        self.timeout = saved_timeout
            
    #non blocking readline()
    readline_nb_data = ""
    def readline_nb(self):
        if self.in_waiting == 0 :
            return None
        try:
            self.readline_nb_data += self.read(self.in_waiting).decode('ascii')
        except:
            pass
        if not "\n" in self.readline_nb_data :
            return None
        p = self.readline_nb_data.partition("\n")
        self.readline_nb_data = p[2]
        return p[0].rstrip("\r")
        
    #is connection sending gps nmea data?
    def is_gps(self):
        linecount = 0
        okcount = 0
        start = time.time()
        while time.time() - start < 2.0:
            line = self.readline_nb()
            if line:
                #print(line)
                linecount +=1
                if linecount>5:
                    return False
                if line[0]=='$' and line[6]==',' and line[-3]=='*':
                    okcount += 1
                    if okcount>2:
                        return True
                else:
                    okcount = 0
        return False
        
#end class Serial2 ----------------------------------------------------------------------------

if __name__ == "__main__" :
    #print("list ports", Serial2.list_ports())
    #print("first port", Serial2.first_available_port())
    #print("all ports", Serial2.all_available_ports())

    print("autobaud scanning all serial ports...")
    for port in Serial.all_available_ports():
        ser = Serial(port)
        autobaud = ser.ascii_autobaud()
        print("port", port, "autobaud",autobaud)
