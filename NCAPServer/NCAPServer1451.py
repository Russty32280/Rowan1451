#!/usr/bin/env python

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import time
import _thread
import sys
#from grove.gpio import GPIO
#from grove.i2c import Bus
#from grove.factory import Factory


NCAPS_Name = "Process001"
AddressType = "1"
Address = "172.24.125.154" # TODO: Make this a function which will obtain current IP Address
NCAPS_ID = "1"
NumTIM = "1"
TIM_ID = "1"
NumChan = "3"
XDCR_ChanID_Array = "(1;2;3)"
XDCR_ChanNameArray = "(\"Temp000001\",\"Valve00001\",\"PresSw0001\")"
ResponseTopic = "RUSMARTLAB/NCAPC001"
AlertEnable = False


#####GROVE SENSORS######
'''
charmap = {
    '0': 0x3f,
    '1': 0x06,
    '2': 0x5b,
    '3': 0x4f,
    '4': 0x66,
    '5': 0x6d,
    '6': 0x7d,
    '7': 0x07,
    '8': 0x7f,
    '9': 0x6f,
    'A': 0x77,
    'B': 0x7f,
    'b': 0x7C,
    'C': 0x39,
    'c': 0x58,
    'D': 0x3f,
    'd': 0x5E,
    'E': 0x79,
    'F': 0x71,
    'G': 0x7d,
    'H': 0x76,
    'h': 0x74,
    'I': 0x06,
    'J': 0x1f,
    'K': 0x76,
    'L': 0x38,
    'l': 0x06,
    'n': 0x54,
    'O': 0x3f,
    'o': 0x5c,
    'P': 0x73,
    'r': 0x50,
    'S': 0x6d,
    't': 0x78,
    'U': 0x3e,
    'V': 0x3e,
    'Y': 0x66,
    'Z': 0x5b,
    '-': 0x40,
    '_': 0x08,
    ' ': 0x00
}

ADDR_AUTO = 0x40
ADDR_FIXED = 0x44
STARTADDR = 0xC0
BRIGHT_DARKEST = 0
BRIGHT_DEFAULT = 2
BRIGHT_HIGHEST = 7


def CRC(data):
    crc = 0xff
    for s in data:
        crc ^= s
        for _ in range(8):
            if crc & 0x80:
                crc <<= 1
                crc ^= 0x131
            else:
                crc <<= 1
    return crc


class GrovePiezoVibrationSensor(GPIO):
    def __init__(self, pin):
        super(GrovePiezoVibrationSensor, self).__init__(pin, GPIO.IN)
        self._on_detect = None

    @property
    def on_detect(self):
        return self._on_detect

    @on_detect.setter
    def on_detect(self, callback):
        if not callable(callback):
            return

        if self.on_event is None:
            self.on_event = self._handle_event

        self._on_detect = callback

    def _handle_event(self, pin, value):
        if value:
            if callable(self._on_detect):
                self._on_detect()


class GroveTemperatureHumiditySensorSHT3x(object):

    def __init__(self, address=0x44, bus=None):
        self.address = address

        # I2C bus
        self.bus = Bus(bus)

    def read(self):
        # high repeatability, clock stretching disabled
        self.bus.write_i2c_block_data(self.address, 0x24, [0x00])

        # measurement duration < 16 ms
        time.sleep(0.016)

        # read 6 bytes back
        # Temp MSB, Temp LSB, Temp CRC, Humididty MSB, Humidity LSB, Humidity CRC
        data = self.bus.read_i2c_block_data(self.address, 0x00, 6)

        if data[2] != CRC(data[:2]):
            raise ValueError("temperature CRC mismatch")
        if data[5] != CRC(data[3:5]):
            raise ValueError("humidity CRC mismatch")


        temperature = data[0] * 256 + data[1]
        celsius = -45 + (175 * temperature / 65535.0)
        humidity = 100 * (data[3] * 256 + data[4]) / 65535.0

        return celsius, humidity


class GroveMiniPIRMotionSensor(GPIO):
    def __init__(self, pin):
        super(GroveMiniPIRMotionSensor, self).__init__(pin, GPIO.IN)
        self._on_detect = None

    @property
    def on_detect(self):
        return self._on_detect

    @on_detect.setter
    def on_detect(self, callback):
        if not callable(callback):
            return

        if self.on_event is None:
            self.on_event = self._handle_event

        self._on_detect = callback

    def _handle_event(self, pin, value):
        if value:
            if callable(self._on_detect):
                self._on_detect()

class Grove4DigitDisplay(object):
    colon_index = 1

    def __init__(self, clk, dio, brightness=BRIGHT_DEFAULT):
        self.brightness = brightness

        self.clk = GPIO(clk, direction=GPIO.OUT)
        self.dio = GPIO(dio, direction=GPIO.OUT)
        self.data = [0] * 4
        self.show_colon = False

    def clear(self):
        self.show_colon = False
        self.data = [0] * 4
        self._show()

    def show(self, data):
        if type(data) is str:
            for i, c in enumerate(data):
                if c in charmap:
                    self.data[i] = charmap[c]
                else:
                    self.data[i] = 0
                if i == self.colon_index and self.show_colon:
                    self.data[i] |= 0x80
                if i == 3:
                    break
        elif type(data) is int:
            self.data = [0, 0, 0, charmap['0']]
            if data < 0:
                negative = True
                data = -data
            else:
                negative = False
            index = 3
            while data != 0:
                self.data[index] = charmap[str(data % 10)]
                index -= 1
                if index < 0:
                    break
                data = int(data / 10)

            if negative:
                if index >= 0:
                    self.data[index] = charmap['-']
                else:
                    self.data = charmap['_'] + [charmap['9']] * 3
        else:
            raise ValueError('Not support {}'.format(type(data)))
        self._show()

    def _show(self):
        with self:
            self._transfer(ADDR_AUTO)

        with self:
            self._transfer(STARTADDR)
            for i in range(4):
                self._transfer(self.data[i])

        with self:
            self._transfer(0x88 + self.brightness)

    def update(self, index, value):
        if index < 0 or index > 4:
            return

        if value in charmap:
            self.data[index] = charmap[value]
        else:
            self.data[index] = 0

        if index == self.colon_index and self.show_colon:
            self.data[index] |= 0x80

        with self:
            self._transfer(ADDR_FIXED)

        with self:
            self._transfer(STARTADDR | index)
            self._transfer(self.data[index])

        with self:
            self._transfer(0x88 + self.brightness)


    def set_brightness(self, brightness):
        if brightness > 7:
            brightness = 7

        self.brightness = brightness
        self._show()

    def set_colon(self, enable):
        self.show_colon = enable
        if self.show_colon:
            self.data[self.colon_index] |= 0x80
        else:
            self.data[self.colon_index] &= 0x7F
        self._show()

    def _transfer(self, data):
        for _ in range(8):
            self.clk.write(0)
            if data & 0x01:
                self.dio.write(1)
            else:
                self.dio.write(0)
            data >>= 1
            time.sleep(0.000001)
            self.clk.write(1)
            time.sleep(0.000001)

        self.clk.write(0)
        self.dio.write(1)
        self.clk.write(1)
        self.dio.dir(GPIO.IN)

        while self.dio.read():
            time.sleep(0.001)
            if self.dio.read():
                self.dio.dir(GPIO.OUT)
                self.dio.write(0)
                self.dio.dir(GPIO.IN)
        self.dio.dir(GPIO.OUT)

    def _start(self):
        self.clk.write(1)
        self.dio.write(1)
        self.dio.write(0)
        self.clk.write(0)

    def _stop(self):
        self.clk.write(0)
        self.dio.write(0)
        self.clk.write(1)
        self.dio.write(1)

    def __enter__(self):
        self._start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop()


##### END GROVE SENSORS#####
'''




# MQTT Callback Functions

def on_connect(mqttc, obj, flags, rc):
    print("rc: " + str(rc))


def on_message(mqttc, obj, msg):
    print(msg.topic + " " + str(msg.qos) + " " + msg.payload.decode('UTF-8'))
    MsgDict = MessageParse(msg.payload.decode('UTF-8'))
    print(MsgDict)
    if MsgDict["NetSvcType"] == '1':
        if MsgDict["NetSvcID"] == '3':
            _thread.start_new_thread(Thread132, (tuple(MsgDict.items()), ('ResponseTopic', ResponseTopic)))
        elif MsgDict["NetSvcID"] == '5':
            _thread.start_new_thread(Thread152, (tuple(MsgDict.items()), ('ResponseTopic', ResponseTopic)))
        elif MsgDict["NetSvcID"] == '6':
            _thread.start_new_thread(Thread162, (tuple(MsgDict.items()), ('ResponseTopic', ResponseTopic)))
    elif MsgDict["NetSvcType"] == '2':
        if MsgDict["NetSvcID"] == '1':
            _thread.start_new_thread(Thread212, (tuple(MsgDict.items()), ('ResponseTopic', ResponseTopic)))
        elif MsgDict["NetSvcID"] == '7':
            _thread.start_new_thread(Thread272, (tuple(MsgDict.items()), ('ResponseTopic', ResponseTopic)))
    elif MsgDict["NetSvcType"] == '4':
        if MsgDict["NetSvcID"] == '1':
            _thread.start_new_thread(Thread412, (tuple(MsgDict.items()), ('ResponseTopic', ResponseTopic)))
        elif MsgDict["NetSvcID"] == '2':
            _thread.start_new_thread(Thread422, (tuple(MsgDict.items()), ('ResponseTopic', ResponseTopic)))


def on_publish(mqttc, obj, mid):
    print("mid: " + str(mid))


def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


def on_log(mqttc, obj, level, string):
    print(string)




# Parsing Engine
def MessageParse(msg):
    parse = msg.split(",")
    NetSvcType = parse[0]
    NetSvcID =  parse[1]
    MsgType =  parse[2]
    MsgLength =  parse[3]
    if NetSvcType == '1':
        if NetSvcID == '3':
            NCAPC_ID = parse[4]
            return{'NetSvcType':NetSvcType, 'NetSvcID':NetSvcID, 'MsgType':MsgType, 'MsgLength':MsgLength, 'NCAPC_ID':NCAPC_ID}
        elif NetSvcID == "5":
            ErrorCode = parse[4]
            NCAPC_ID = parse[5]
            return{'NetSvcType':NetSvcType, 'NetSvcID':NetSvcID, 'MsgType':MsgType, 'MsgLength':MsgLength, 'ErrorCode':ErrorCode, 'NCAPC_ID':NCAPC_ID}
        elif NetSvcID == "6":
            NCAPS_ID = parse[4]
            TIM_ID = parse[5]
            return{'NetSvcType':NetSvcType, 'NetSvcID':NetSvcID, 'MsgType':MsgType, 'MsgLength':MsgLength, 'NCAPS_ID':NCAPS_ID,  'TIM_ID':TIM_ID}
        elif NetSvcID == "7":
            NCAPC_ID = parse[4]
            NCAPS_ID = parse[5]
            TIM_ID = parse[6]
            NumChan = parse[7]
            XDCR_ChanID_Array = parse[8]
            return{'NetSvcType':NetSvcType, 'NetSvcID':NetSvcID, 'MsgType':MsgType, 'MsgLength':MsgLength, 'NCAPC_ID':NCAPC_ID, 'NCAPS_ID':NCAPS_ID, 'TIM_ID':TIM_ID, 'NumChan':NumChan, 'XDCR_ChanID_Array':XDCR_ChanID_Array}
    elif NetSvcType == '2':
        if NetSvcID == '1':
            NCAPS_ID = parse[4]
            TIM_ID = parse[5]
            XDCR_ChanID = parse[6]
            Timeout = parse[7]
            Mode = parse[8]
            return{'NetSvcType':NetSvcType, 'NetSvcID':NetSvcID, 'MsgType':MsgType, 'MsgLength':MsgLength, 'NCAPS_ID':NCAPS_ID, 'TIM_ID':TIM_ID, 'XDCR_ChanID':XDCR_ChanID, 'Timeout':Timeout, 'Mode':Mode}
        elif NetSvcID == '7':
            NCAPS_ID = parse[4]
            TIM_ID = parse[5]
            XDCR_ChanID = parse[6]
            WriteActuatorData = parse[7]
            Timeout = parse[8]
            Mode = parse[9]
            return{'NetSvcType':NetSvcType, 'NetSvcID':NetSvcID, 'MsgType':MsgType, 'MsgLength':MsgLength, 'NCAPS_ID':NCAPS_ID, 'TIM_ID':TIM_ID, 'XDCR_ChanID':XDCR_ChanID, 'WriteActuatorData':WriteActuatorData, 'Timeout':Timeout, 'Mode':Mode}
    elif NetSvcType == '4':
        if NetSvcID == '1':
            NCAPC_ID = parse[4]
            NCAPS_ID = parse[5]
            TIM_ID = parse[6]
            NumChan = parse[7]
            XDCR_ChanID = parse[8]
            AlertMinMaxArray = parse[9]
            return{'NetSvcType':NetSvcType, 'NetSvcID':NetSvcID, 'MsgType':MsgType, 'MsgLength':MsgLength, 'NCAPC_ID':NCAPC_ID, 'NCAPS_ID':NCAPS_ID, 'TIM_ID':TIM_ID, 'NumChan':NumChan, 'XDCR_ChanID':XDCR_ChanID, 'AlertMinMaxArray':AlertMinMaxArray}
        elif NetSvcID == '2': #THIS IS 100% WRONG
            NCAPC_ID = parse[4]
            NCAPS_ID = parse[5]
            TIM_ID = parse[6]
            NumChan = parse[7]
            XDCR_ChanID = parse[8]
            AlertMinMaxArray = parse[9]
            return{'NetSvcType':NetSvcType, 'NetSvcID':NetSvcID, 'MsgType':MsgType, 'MsgLength':MsgLength, 'NCAPC_ID':NCAPC_ID, 'NCAPS_ID':NCAPS_ID, 'TIM_ID':TIM_ID, 'NumChan':NumChan, 'XDCR_ChanID':XDCR_ChanID, 'AlertMinMaxArray':AlertMinMaxArray}



def Thread132(MSG_Tuple, SenderInfo):
    print(MSG_Tuple)
    print(SenderInfo)
    MSG = dict(MSG_Tuple)
    print(MSG)
    response = '1,3,2,25,' + NCAPS_Name + ',' + AddressType + ',' + Address
    #mqtt_send(str(SenderInfo[1]), response)
    publish.single(ResponseTopic, response, hostname="broker.emqx.io")

def Thread152(MSG_Tuple, SenderInfo):
    #MSG = dict(map(None, MSG_Tuple))
    # TODO: Add the TIM Discovery Function
    response = '1,5,2,39,' + '0,' + NCAPS_ID + ',' + NumTIM + ',' + '1' + ','+ "BatchRx001"
    publish.single(ResponseTopic, response, hostname="broker.emqx.io")

def Thread162(MSG_Tuple, SenderInfo):
    #MSG = dict(map(None, MSG_Tuple))
    response = '1,6,2,55,' + '0,' + NCAPS_ID + ',' + TIM_ID + ',' + NumChan + ',' + XDCR_ChanID_Array + ',' + XDCR_ChanNameArray
    publish.single(ResponseTopic, response, hostname="broker.emqx.io")

def Thread212(MSG_Tuple, SenderInfo):
    print("In Thread212")
    MSG = dict(MSG_Tuple)
    ReadSensorData = "0"
    if MSG["TIM_ID"] == '1':
        if MSG["XDCR_ChanID"] == '1':
            #ReadSensorData = str(round(sensor.temperature,2))
            ReadSensorData = "1234"
    response = '2,1,1,N,0,' + NCAPS_ID + ',' + TIM_ID + ',' + MSG["XDCR_ChanID"] + ',' + ReadSensorData + ',' + time.strftime("%H:%M:%S", time.localtime())
    print(response)
    publish.single(ResponseTopic, response, hostname="broker.emqx.io")

def Thread272(MSG_Tuple, SenderInfo):
    MSG = dict(MSG_Tuple)
    if MSG["TIM_ID"] == '1':
        if MSG["XDCR_ChanID"] == '2':
            print(str(MSG["WriteActuatorData"]))
            display.show(MSG["WriteActuatorData"])
    response = '2,7,2,19,0,' + NCAPS_ID + ',' + TIM_ID + ',' + MSG["XDCR_ChanID"]
    publish.single(ResponseTopic, response, hostname="broker.emqx.io")

def Thread412(MSG_Tuple, SenderInfo):
    MSG = dict(MSG_Tuple)
    if MSG["NCAPC_ID"] == "1":
        global AlertEnable
        AlertEnable = True
    response = '4,1,2,29,0,' + MSG["NCAPC_ID"] + ',' + "11" + ',' + NCAPS_ID + ',' + TIM_ID + ',' + '1,' + MSG["XDCR_ChanID"]
    publish.single(ResponseTopic, response, hostname="broker.emqx.io")

def Thread422(MSG_Tuple, SenderInfo):
    MSG = dict(MSG_Tuple)
    if MSG["NCAPC_ID"] == "1":
        global AlertEnable
        AlertEnable = False
    response = '4,2,2,29,0,' + MSG["NCAPC_ID"] + ',' + "11" + ',' + NCAPS_ID + ',' + TIM_ID + ',' + '1,' + MSG["XDCR_ChanID"]
    publish.single(ResponseTopic, response, hostname="broker.emqx.io")




def SendAlert(SubscriptionID, Value):
    #TargetClients = CheckSubscriberList(SubscriptionID)
    if AlertEnable == True:
        TargetClients = ["NCAPC001"]
    else:
        TargetClients = None
    if TargetClients != None:
        for Clients in TargetClients:
            AlertString = "4,2,4,23," + NCAPS_ID + ',' + TIM_ID + ',' + '3' + ',' + SubscriptionID + ',' + Value
            publish.single(ResponseTopic, AlertString, hostname="broker.emqx.io")

'''
def CheckSubscriberList(SubscriptionID):
    #TODO Possibly add value to check against mins/max
    if


def AddSubscriber(NCAPC_ID, SubscriptionID):

'''






# MQTT Client Initialization
mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe
# Uncomment to enable debug messages
# mqttc.on_log = on_log
mqttc.connect("broker.emqx.io", 1883, 60)
mqttc.subscribe("RUSMARTLAB/NCAPS001", 0)

#pir = GroveMiniPIRMotionSensor(5)
#display = Grove4DigitDisplay(16, 17)
#sensor = Factory.getTemper("NTC-ADC", 0)
#RPI.gpio.analogWrite(12,120)
#grovepi.analogWrite(12, 120)
'''
def callbackPIR():
    print('PIR Motion detected.')

pir.on_detect = callbackPIR

piv = GrovePiezoVibrationSensor(12)

def callbackPiezo():
    print('Piezo Detected.')
    # hard coded event ID of 11 per spreadsheet
    SendAlert("11", "1")
    #time.sleep(1)

piv.on_detect = callbackPiezo

'''

# Start the Client Loop
mqttc.loop_start()
while True:
    publish.single("RUSMARTLAB/Heartbeat", "NCAPS001,1", hostname="broker.emqx.io")
    print("Published Heartbeat")
    time.sleep(10)
mqttc.loop_stop()
