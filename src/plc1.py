"""
FP plc1.py
"""

from minicps.devices import PLC
from utils import PLC1_DATA, PLC1_PROTOCOL, PLC1_ADDR, STATE
from utils import PLC2_ADDR, PLC3_ADDR
from utils import PLC_PERIOD_SEC   # PLC_SAMPLES
from utils import TANK_M, BOTTLE_M, SENSOR2_THRESH
import time
import logging
import os
from socket import error as socket_error

# tag addresses
SENSOR1 = ('SENSOR1-LL-tank', 1)
ACTUATOR1 = ('ACTUATOR1-MV', 1)
# interlocks to plc2 and plc3
SENSOR2_1 = ('SENSOR2-FL', 1)  # to be sent to PLC2
SENSOR2_2 = ('SENSOR2-FL', 2)  # to be received from PLC2
SENSOR3_1 = ('SENSOR3-LL-bottle', 1)  # to be sent to PLC3
SENSOR3_3 = ('SENSOR3-LL-bottle', 3)  # to be received from PLC3


class FPPLC1(PLC):

    # boot process
    def pre_loop(self, sleep=0.1):
        print 'DEBUG: FP PLC1 enters pre_loop'

        time.sleep(sleep)

    def main_loop(self):
        """plc1 main loop.
                    - reads values from sensors
                    - drives actuator according to the control strategy
                    - updates its enip server
                    - logs the control strategy events (info, exceptions)
                """

        print 'DEBUG: FP PLC1 enters main_loop.'
        print
        # FYI: BSD-syslog format (RFC 3164), e.g. <133>Feb 25 14:09:07 webserver syslogd: restart   PRI <Facility*8+Severity>, HEADER (timestamp host), MSG (program/process message)
        
        logging.basicConfig(filename='logs/plc1.log', format='%(levelname)s %(asctime)s '+PLC1_ADDR+' '+PLC1_ADDR+' %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.DEBUG)
        # count = 0
        # while (count <= PLC_SAMPLES):
        
        while True:
            
            if not os.path.exists('logs/plc1.log'):
                print("******************LOG FILE WAS DELETED")
                print("******************LOG FILE WAS DELETED")
                print("******************LOG FILE WAS DELETED")
               
                for handler in logging.root.handlers[:]:
                    logging.root.removeHandler(handler)
                logging.basicConfig(filename='logs/plc1.log', format='%(levelname)s %(asctime)s '+PLC1_ADDR+' '+PLC1_ADDR+' %(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.DEBUG)
                logging.warning("LOG FILE MANIPULATION: Log file was deleted, new file created.")
            
            print("sensor: ", SENSOR1)
            liquidlevel_tank = float(self.get(SENSOR1))   # physical process simulation (sensor 1 reads value)
            print 'DEBUG PLC1 - liquid level of tank (SENSOR 1): %.5f' % liquidlevel_tank
            self.send(SENSOR1, liquidlevel_tank, PLC1_ADDR) # network process simulation (value of sensor 1 is stored as enip tag)

            if liquidlevel_tank <= TANK_M['LowerBound']:
                print "INFO PLC1 - liquid level of tank (SENSOR 1) under LowerBound: %.2f <= %.2f -> close mv (ACTUATOR 1)." % (
                    liquidlevel_tank, TANK_M['LowerBound'])
                logging.info("Liquid level of tank (SENSOR 1) under LowerBound: %.2f <= %.2f -> close mv (ACTUATOR 1)." % (
                    liquidlevel_tank, TANK_M['LowerBound']))
                self.set(ACTUATOR1, 0)   # CLOSE actuator mv
                self.send(ACTUATOR1, 0, PLC1_ADDR)

            # read from PLC2
            try:
                flowlevel = float(self.receive(SENSOR2_2, PLC2_ADDR))
                print "DEBUG PLC1 - receive flowlevel (SENSOR 2): %f" % flowlevel
                self.send(SENSOR2_1, flowlevel, PLC1_ADDR)

                if flowlevel >= SENSOR2_THRESH:
                    print "INFO PLC1 - Flow level (SENSOR 2) over SENSOR2_THRESH:  %.2f >= %.2f -> close mv (ACTUATOR 1)." % (
                        flowlevel, SENSOR2_THRESH)
                    logging.info("Flow level (SENSOR 2) over SENSOR2_THRESH:  %.2f >= %.2f -> close mv (ACTUATOR 1)." % (
                        flowlevel, SENSOR2_THRESH))
                    self.set(ACTUATOR1, 0)     # CLOSE actuator mv
                    self.send(ACTUATOR1, 0, PLC1_ADDR)
                else:
                    logging.info(
                        "Flow level (SENSOR 2) under SENSOR2_THRESH:  %.2f < %.2f -> leave mv status (ACTUATOR 1)." % (
                            flowlevel, SENSOR2_THRESH))

            except:
                logging.warning("Flow level (SENSOR 2) is not received. Program is unable to proceed properly")
                

            # read from PLC3
            try:
                liquidlevel_bottle = float(self.receive(SENSOR3_3, PLC3_ADDR))
                print "DEBUG PLC1 - receive liquid level of bottle (SENSOR 3): %f" % liquidlevel_bottle
                self.send(SENSOR3_1, liquidlevel_bottle, PLC1_ADDR)

                if liquidlevel_bottle >= BOTTLE_M['UpperBound']:
                    print "INFO PLC1 - Liquid level (SENSOR 3) over BOTTLE_M['UpperBound']:  %.2f >= %.2f -> close mv (ACTUATOR 1)." %(
                        liquidlevel_bottle,BOTTLE_M['UpperBound'])
                    logging.info("Liquid level (SENSOR 3) over BOTTLE_M['UpperBound']:  %.2f >= %.2f -> close mv (ACTUATOR 1)." %(
                        liquidlevel_bottle,BOTTLE_M['UpperBound']))
                    self.set(ACTUATOR1, 0)     # CLOSE actuator mv
                    self.send(ACTUATOR1, 0, PLC1_ADDR)

                elif liquidlevel_bottle < BOTTLE_M['UpperBound'] and liquidlevel_tank > TANK_M['LowerBound']:
                    print "INFO PLC1 - Liquid level (SENSOR 3) under BOTTLE_M['UpperBound']: %.2f < %.2f ->  open mv (ACTUATOR 1)." %(
                        liquidlevel_bottle, BOTTLE_M['UpperBound'])
                    logging.info("Liquid level (SENSOR 3) under BOTTLE_M['UpperBound']: %.2f < %.2f -> open mv (ACTUATOR 1)." %(
                        liquidlevel_bottle, BOTTLE_M['UpperBound']))
                    self.set(ACTUATOR1, 1)  # OPEN actuator mv
                    self.send(ACTUATOR1, 1, PLC1_ADDR)
            except:
                logging.warning("Liquid level (SENSOR 3) is not received. Program is unable to proceed properly")
               

            time.sleep(PLC_PERIOD_SEC)
            # count += 1

        print 'DEBUG FP PLC1 shutdown'


if __name__ == "__main__":
    plc1 = FPPLC1(
        name='plc1',
        state=STATE,
        protocol=PLC1_PROTOCOL,
        memory=PLC1_DATA,
        disk=PLC1_DATA)