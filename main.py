#!/usr/bin/python
import LPD8806
import time
import math
import threading
import traceback
import signal
import Queue
import sys
import os
import json
import random
import stat

# import pprint

# Globals

#web_file = '/tmp/led_settings.dict'
web_file = '/mnt/ram/led_settings.dict'

#spi_dev = '/tmp/spi_tmp'
spi_dev = '/dev/spidev0.0'

num_leds = 160
frequency = 0.03
random.seed(time.time())

class SystemState(object):
    def __init__(self, lock, queue):
        self.lock = lock
        self.queue = queue
        # Defaults
        self.pattern = 3
        self.previous_pattern = 3
        self.pattern_speed = 1
        self.color_button = 'rainbow'
        self.color_speed = 674
        self.html = {'color_value': '#a01818'}
        self.r = 1
        self.g = 1
        self.b = 1
        self.r_color = 1
        self.g_color = 1
        self.b_color = 1

    @classmethod
    def _convert(cls, input_dict):
        if isinstance(input_dict, dict):
            return ({cls._convert(key): cls._convert(value)
                    for key, value in input_dict.iteritems()})
        elif isinstance(input_dict, list):
            return [cls._convert(element) for element in input_dict]
        elif isinstance(input_dict, unicode):
            return input_dict.encode('utf-8')
        else:
            return input_dict

    def set(self, input_dict=None):
        try:
            self.lock.acquire()
            output_dict = {}
            fl = open(web_file, 'w')
            if not input_dict:
                input_dict = self.__dict__
            for key, value in input_dict.iteritems():
                if key == 'lock' or key == 'thread' or key == 'queue':
                    continue
                else:
                    output_dict[key] = value
            fl.write(json.JSONEncoder().encode(output_dict))
        except Exception, e:
            print e
            print traceback.format_exc()
        finally:
            st = os.stat(web_file)
            os.chmod(web_file,
                     (st.st_mode |
                      stat.S_IWOTH |
                      stat.S_IROTH |
                      stat.S_IWGRP |
                      stat.S_IRGRP))
            fl.close()
            self.lock.release()

    def get(self):
        try:
            self.lock.acquire()
            output_dict = {}
            fl = open(web_file, 'r')
            line = fl.readlines()[0]
            input_dict = self._convert(json.loads(self._convert(line)))
            for key, value in input_dict.iteritems():
                if (key == 'html' or
                        key == 'previous_pattern' or
                        key == 'lock' or
                        key == 'thread'):
                    continue
                elif key == 'pattern':
                    if value != self.previous_pattern:
                        self.queue.put(input_dict['pattern'])
                        output_dict['previous_pattern'] = value
                        output_dict[key] = value
                        continue
                output_dict[key] = value
            for key, value in output_dict.iteritems():
                self.__dict__[key] = value
        except Exception, e:
            print e
            print traceback.format_exc()
        finally:
            self.lock.release()
            fl.close()
            return self.__dict__


class FileThread(threading.Thread):
    def __init__(self, queue, system_state):
        threading.Thread.__init__(self)
        self.system_state = system_state
        self.queue = queue

    @classmethod
    def _convert(cls, input_dict):
        if isinstance(input_dict, dict):
            return ({cls._convert(key): cls._convert(value)
                    for key, value in input_dict.iteritems()})
        elif isinstance(input_dict, list):
            return [cls._convert(element) for element in input_dict]
        elif isinstance(input_dict, unicode):
            return input_dict.encode('utf-8')
        else:
            return input_dict

    def run(self):
        while True:
            if (not os.path.exists(web_file) or
                    os.path.getsize(web_file) < 10):
                self.write()
            self.read()
            time.sleep(1)

    def write(self):
        fl = open(web_file, 'w')
        try:
            fl.write(json.JSONEncoder().encode(self.system_state.get()))
        except Exception, e:
            print e
            print traceback.format_exc()
        finally:
            fl.close()

    def read(self):
        fl = open(web_file, 'r')
        try:
            output_dict = {}
            line = fl.readlines()[0]
            input_dict = self._convert(json.loads(line))
            for key, value in input_dict.iteritems():
                if key == 'html' or key == 'previous_pattern':
                    continue
                elif key == 'pattern':
                    if value != self.system_state.previous_pattern:
                        self.queue.put(input_dict['pattern'])
                        output_dict['previous_pattern'] = value
                        output_dict[key] = value
                        continue
                output_dict[key] = value
            self.system_state.set(output_dict)
        except Exception, e:
            print e
            print traceback.format_exc()
        finally:
            fl.close()


class ColorChanger(threading.Thread):
    def __init__(self, system_state):
        threading.Thread.__init__(self)
        self.system_state = system_state
        self.sleep_time = 0.05
        self.color_speed = 0.0005
        self.current_state = self.system_state.get()

    def run(self):
        while True:
            if self.current_state['color_button'] == 'rainbow':
                self.rainbow()
            elif self.current_state['color_button'] == 'white':
                self.current_state['r_color'] = 200
                self.current_state['g_color'] = 200
            elif self.current_state['color_button'] == 'black':
                self.current_state['r_color'] = 1
                self.current_state['g_color'] = 1
                self.current_state['b_color'] = 1
            elif self.current_state['color_button'] == 'solid':
                self.current_state['r_color'] = self.current_state['r']
                self.current_state['g_color'] = self.current_state['g']
                self.current_state['b_color'] = self.current_state['b']
            self.system_state.set(self.current_state)
            time.sleep(self.sleep_time)

    def rainbow(self, freq=0.075):
        for i in range(0, (2**8)):
            self.current_state = self.system_state.get()
            for z in range(1, 255):
                self.current_state['r_color'] = int(math.sin(freq*i + 0) * 127 + 128) - z
                if self.current_state['r_color'] < 0:
                    self.current_state['r_color'] = 0
                self.current_state['g_color'] = int(math.sin(freq*i + 2) * 127 + 128) - z
                if self.current_state['g_color'] < 0:
                    self.current_state['g_color'] = 0
                self.current_state['b_color'] = int(math.sin(freq*i + 4) * 127 + 128) - z
                if self.current_state['b_color'] < 0:
                    self.current_state['b_color'] = 0
                if self.current_state['color_button'] != 'rainbow':
                    return
                self.system_state.set(self.current_state)
                if self.current_state['b'] == 0 or self.current_state['r'] == 0 or self.current_state['g'] == 0:
                    print "WTF"
                self.refresh_sleep()
                time.sleep(self.sleep_time/1000000000)

            for z in range(255, 1, -1):
                self.current_state['r_color'] = int(math.sin(freq*i + 0) * 127 + 128) - z
                if self.current_state['r_color'] < 0:
                    self.current_state['r_color'] = 0
                self.current_state['g_color'] = int(math.sin(freq*i + 2) * 127 + 128) - z
                if self.current_state['g_color'] < 0:
                    self.current_state['g_color'] = 0
                self.current_state['b_color'] = int(math.sin(freq*i + 4) * 127 + 128) - z
                if self.current_state['b_color'] < 0:
                    self.current_state['b_color'] = 0
                if self.current_state['color_button'] != 'rainbow':
                    return
                self.system_state.set(self.current_state)
                if self.current_state['b'] == 0 or self.current_state['r'] == 0 or self.current_state['g'] == 0:
                    print "WTF"
                self.refresh_sleep()
                time.sleep(self.sleep_time/1000000000)

    def refresh_sleep(self):
        self.sleep_time = float(int(self.current_state['color_speed'])) * 0.001


class LEDPattern(threading.Thread):
    def __init__(self, queue, color, system_state):
        threading.Thread.__init__(self)
        self.strip = LPD8806.strand(leds=num_leds)
        self.queue = queue
        self.color = color
        self.system_state = system_state
        self.current_state = self.system_state.get()
        self.sleep_time = 0.05

    def run(self):
        choice = 3
        while True:
            self.current_state = self.system_state.get()
            if self.queue.qsize() > 0:
                choice = self.queue.get()
            self.refresh_sleep()
            if choice == 1 or choice == 2 or choice == 6:
                self.solid()
            elif choice == 3:
                self.fader()
            elif choice == 4:
                self.tail_mover()
            elif choice == 5:
                self.single_mover()
            elif choice == 7:
                self.random()
            elif choice == 8:
                self.breathe()
            else:
                self.solid()

    def refresh_sleep(self):
        if self.current_state['pattern_speed']:
            self.sleep_time = float(int(self.current_state['pattern_speed']) * 0.001)
        else:
            self.sleep_time = 0.1

    def solid(self):
        self.strip.fill(self.current_state.r_color,
                        self.current_state.g_color,
                        self.current_state.b_color,
                        start=0,
                        end=num_leds)
        self.strip.update()
        self.refresh_sleep()
        time.sleep(self.sleep_time)

    def tail_mover(self):
        def build(led_num, pos, diff_in):
            if led_num['led'] + 1 > num_leds-1:
                led_num['led'] = 0
            else:
                led_num['led'] += 1
            led_num['r'] = int((self.current_state['r_color'] / diff_in) * led_num['led'] - pos)
            led_num['g'] = int((self.current_state['g_color'] / diff_in) * led_num['led'] - pos)
            led_num['b'] = int((self.current_state['b_color'] / diff_in) * led_num['led'] - pos)
            for v in ('r', 'g', 'b'):
                if led_num[v] < 0:
                    led_num[v] = 0
                elif led_num[v] > 255:
                    led_num[v] = 0

        group = []
        tail = int(0.25*num_leds)
        diff = int((255 / tail) + 2)

        # build structure
        for i in range(0, tail):
            group.append({'led': num_leds-i,
                          'r': 0,
                          'g': 0,
                          'b': 0})
        while True:
            for head in range(0, num_leds):
                if self.queue.qsize() > 0:
                    return
                for j in range(0, tail):
                    led = build(group[j], j, diff)
                    #print led
                    self.strip.set(led['led'], led['r'], led['g'], led['b'])
                    self.strip.set(int(math.fabs(led['led'] - diff)), 0, 0, 0)
                    group[j] = led
                self.strip.update()
                self.refresh_sleep()
                time.sleep(self.sleep_time)

    def single_mover(self):
        # move up
        for i in range(0, num_leds):
            self.strip.set(i, 0, 0, 0)

        for i in range(0, num_leds):
            self.refresh_sleep()
            self.current_state = self.system_state.get()
            if self.queue.qsize() > 0:
                return
            if i == 0:
                off = num_leds - 1
            else:
                off = i - 1
            self.strip.set(off, 0, 0, 0)
            self.strip.set(i,
                           self.current_state['r_color'],
                           self.current_state['g_color'],
                           self.current_state['b_color'])
            self.strip.update()
            self.refresh_sleep()
            self.current_state = self.system_state.get()
            time.sleep(self.sleep_time)
        # move down
        for i in range(num_leds-1, -1, -1):
            self.current_state = self.system_state.get()
            if self.queue.qsize() > 0:
                return
            if i == num_leds - 1:
                off = 0
            else:
                off = i + 1
            self.strip.set(off, 0, 0, 0)
            self.strip.set(i,
                           self.current_state['r_color'],
                           self.current_state['g_color'],
                           self.current_state['b_color'])
            self.strip.update()
            self.refresh_sleep()
            time.sleep(self.sleep_time)

    def fader(self):
        self.strip.fill(self.current_state['r_color'],
                        self.current_state['g_color'],
                        self.current_state['b_color'], start=0, end=num_leds)
        self.strip.update()
        self.refresh_sleep()
        time.sleep(self.sleep_time)

    def breathe(self):
        color = {}
        for i in (1, 255):
            color['r_color'] = self.current_state['r_color'] - i
            color['g_color'] = self.current_state['g_color'] - i
            color['b_color'] = self.current_state['b_color'] - i
            self.strip.fill(color['r_color'], color['g_color'], color['b_color'], start=0, end=num_leds)
            self.strip.update()
            self.refresh_sleep()
            time.sleep(self.sleep_time*0.001)

    def random(self):
        def build_led():
            steps = 50
            led_num = {'led': random.randint(0, num_leds-1),
                       'r': 0,
                       'g': 0,
                       'b': 0,
                       'r_max': random.randint(1, 254),
                       'g_max': random.randint(1, 254),
                       'b_max': random.randint(1, 254),
                       'dir': 1,
                       'count': 0}

            led_num['max_val'] = max(led_num['r_max'], led_num['g_max'], led_num['b_max']) + 3
            if led_num['max_val'] > 254:
                led_num['max_val'] = 255
            led_num['r_dec'] = led_num['r_max'] / steps
            led_num['g_dec'] = led_num['g_max'] / steps
            led_num['b_dec'] = led_num['b_max'] / steps
            #if led['r'] < 200 and led['g'] < 200 and led['b'] < 200:
            #    v = random.sample(['r', 'g', 'b'], 1)
            #    led[v[0]] = random.randint(200, 255)
            return led_num

        leds = []
        self.strip.fill(0, 0, 0, start=0, end=num_leds)
        self.strip.update()

        for i in range(0, num_leds / 2):
            led = build_led()
            leds.append(led)

        while True:
            self.current_state = self.system_state.get()
            for i in range(0, len(leds)):
                led = leds[i]
                if led['dir'] > 0:
                    if (led['count'] * led['r_dec']) % led['r_max'] == 0:
                        led['r'] += 1
                    if led['count'] % led['g_dec'] == 0:
                        led['g'] += 1
                    if led['count'] % led['b_dec'] == 0:
                        led['b'] += 1
                else:
                    if led['count'] % led['r_dec'] == 0:
                        led['r'] -= 1
                    if led['count'] % led['g_dec'] == 0:
                        led['g'] -= 1
                    if led['count'] % led['b_dec'] == 0:
                        led['b'] -= 1

                led['count'] += 1

                if (led['r'] >= led['max_val'] or
                        led['g'] >= led['max_val'] or
                        led['b'] >= led['max_val']):
                    led['dir'] = -1
                    led['count'] = 0

                if (led['r'] <= 0 and
                        led['g'] <= 0 and
                        led['b'] <= 0):
                    leds[i] = build_led()
                    led = leds[i]

                self.strip.set(led['led'], led['r'], led['g'], led['b'])
                leds[i] = led
            self.strip.update()
            time.sleep(0.005)


class UserInput(threading.Thread):
    def __init__(self, queue):
        self.queue = queue
        threading.Thread.__init__(self)

    def run(self):
        while True:
            print "Choose Pattern"
            print "1. Black Out"
            print "2. White Out"
            print "3. fader"
            print "4. Tail Mover"
            print "5. Mover (single led moving)"
            print "6. Reset Color"
            print "7. Use HTTP input"
            print ""
            print "0. Exit"
            print ""
            try:
                choice = int(raw_input("Pattern: "))

                if choice == 0:
                    print "Exiting"
                    os._exit(0)

                print "User chose pattern %d" % choice
                print "Sleeping 5 seconds for user input to keep from rapid change."
                self.queue.put(choice)
                time.sleep(2)
            except TypeError:
                print "You can only choose numbers!"


# functions
def ctrlc(sig, frame):
    print "Exiting . . ."
    os._exit(0)


def main():

    # Override ctrl-c to kill threads
    signal.signal(signal.SIGINT, ctrlc)
    lock = threading.Lock()
    queue = Queue.Queue()
    system_state = SystemState(lock, queue)
    system_state.set()
    #filethread = FileThread(queue, system_state)
    color = ColorChanger(system_state)
    leds = LEDPattern(queue, color, system_state)
    #print "Starting File Reader/Writer"
    #filethread.start()
    print "Starting color"
    color.start()
    print "Starting leds"
    leds.start()
    print "Starting User Controls"
    user = UserInput(queue)
    user.start()
    sys.exit(0)

if __name__ == '__main__':
    main()
