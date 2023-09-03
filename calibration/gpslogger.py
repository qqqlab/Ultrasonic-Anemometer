# log to file: received serial ascii lines together with gps position received on second serial port

# pip install pyserial pynmea2

import autobaud
import pynmea2  
import time
import datetime



#OPTIONAL CONFIG, if used set both port and baud
gps_port = None #"COM9"
gps_baud = None #9600
log_port = None #"COM10"
log_baud = None #115200


#Parse nmea data, and store last received values
class Gps(autobaud.Serial):
    ser = None
    
    tim = None
    lat = None
    lon = None
    spd = None
    alt = None
    dir = None
    sat = None
    
    data = ""
    
    def update(self):
        line = self.readline_nb()
        if line:
            try:
                msg = pynmea2.parse( line )  
                if (hasattr(msg, 'latitude') and hasattr(msg, 'longitude')):
                    self.lat = msg.latitude
                    self.lon = msg.longitude        
                if (hasattr(msg, 'spd_over_grnd_kmph')):
                    self.spd = msg.spd_over_grnd_kmph
                if (hasattr(msg, 'altitude')):
                    self.alt = msg.altitude                
                if (hasattr(msg, 'true_track')):
                    self.dir = msg.true_track  
                if (hasattr(msg, 'datetime')):
                    self.tim = msg.datetime 
                if (hasattr(msg, 'num_sats')):
                    self.sat = msg.num_sats
            except pynmea2.ParseError as e:
                pass
                   
while not gps_port or not log_port:
    print("Scanning serial ports...")
    for port in autobaud.Serial.all_available_ports():
        ser = autobaud.Serial(port)
        baud = ser.ascii_autobaud()
        is_gps = None
        if baud:
            is_gps = ser.is_gps()
            if not gps_port and is_gps:
                gps_port = port
                gps_baud = baud
            if not log_port and not is_gps:
                log_port = port
                log_baud = baud    
        print("port", port, "autobaud", baud, "is_gps", is_gps)
        ser.close()

    
print("Opening ports...")
print("GPS:", gps_port, gps_baud)
gps = Gps(gps_port, gps_baud)
print("LOG:", log_port, log_baud)
log = autobaud.Serial(log_port, log_baud)


fn = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+"-log.txt"
f = open(fn,"w")
f.write("ts\tgps_tim\tgps_lat\tgps_lon\tgps_alt\tgps_spd\tgps_dir\r\n");
f.flush()
print("Logger started. Filename", fn)

def logline(line):
    global f, ts, gps
    ts = time.time()
    f.write(str(ts) + "\t" + str(gps.tim or "") + "\t" + str(gps.lat or "") + "\t" + str(gps.lon or "") + "\t" + str(gps.alt or "") + "\t" + str(gps.spd or "") + "\t" + str(gps.dir or "") + "\t" + line + "\r\n")    
    f.flush()
    #print(str(ts) + "\t" + str(gps.tim or "") + "\t" + str(gps.lat or "") + "\t" + str(gps.lon or "") + "\t" + str(gps.alt or "") + "\t" + str(gps.spd or "") + "\t" + str(gps.dir or "") + "\t" + line + "\r\n")    
    print("sat:" + str(gps.sat or "") + " v:" + str(gps.spd or "") + " " + line)

ts = time.time()
while True:
    #update gps coordinates
    gps.update()
    
    #save received log info
    line = log.readline_nb()
    if line:
        logline(line)
        
    #timeout -> log a line    
    if time.time() - ts > 1.0:    
        logline("")
