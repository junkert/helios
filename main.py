#!/usr/bin/python
import LPD8806
import colorsys
import time
import math
import threading
import signal
import Queue
import sys
import os
import json
import traceback
import random
import pprint

# Globals
num_leds = 155
frequency = 0.03
colors = {'r': 0, 'g': 0, 'b': 0, 'v': 1.0}
output_dict = {'pattern':'TailMover', 'pattern_speed': '526', 'g': 24, 'color_button': 'solid', 'color_speed': '674', 'html': {'color_vale': '#a01818'}, 'r': 160, 'b': 24}

random.seed(time.time())

class Value(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.sleep_time = 0.1
    def run(self):
        while True:
            for i in range(0, 100):
                colors['v'] = i * 0.01
                self.RefreshTime()
                time.sleep(self.sleep_time)
            for i in range(100, -1, -1):
                colors['v'] = i * 0.01
                self.RefreshTime()
                time.sleep(self.sleep_time)

    def RefreshTime(self):
        if 'bright_slider' in output_dict:
            self.sleep_time = float(output_dict['bright_slider']) * 0.01



class ReadFile(threading.Thread):
    def __init__(self, queue, settings_file='/mnt/ram/led_settings.dict'):
        self.settings_file = settings_file
        self.queue = queue
        threading.Thread.__init__(self)

    def convert(self, input_dict):
        if isinstance(input_dict, dict):
            return ({self.convert(key): self.convert(value)
                    for key, value in input_dict.iteritems()})
        elif isinstance(input_dict, list):
            return [self.convert(element) for element in input_dict]
        elif isinstance(input_dict, unicode):
            return input_dict.encode('utf-8')
        else:
            return input_dict

    def run(self):
        self.previous_pattern = 'Fader'
        while True:
            self.refresh_input()
            time.sleep(0.25)

    def refresh_input(self):
        global output_dict
        lock = threading.Lock()
        lock.acquire()
        fl = open(self.settings_file, 'r')
        try:
            line = fl.readlines()[0]
            input_dict = json.loads(line)
            output_dict = self.convert(input_dict)
            if 'pattern' in output_dict:
                if self.previous_pattern != output_dict['pattern']:
                    self.queue.put(output_dict['pattern'])
                    self.previous_pattern = output_dict['pattern']
        except Exception, e:
            print e
            print "EXCEPTION"
            a = 1
        finally:
            fl.close()
            lock.release() 

class ColorChanger(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.sleep_time = 0.2
        self.RefreshDict()

    def SetColor(self):
        colors['r'] = output_dict['r']
        colors['g'] = output_dict['g']
        colors['b'] = output_dict['b']
        time.sleep(self.sleep_time)

    def run(self):
        while True:
            self.RefreshDict()
            if 'color_button' in output_dict:
                if output_dict['color_button'] == 'rainbow':
                    self.rainbow()
                if output_dict['color_button'] == 'white':
                    output_dict['r'] = 200
                    output_dict['g'] = 200
                    output_dict['b'] = 200
                    self.SetColor()
                if output_dict['color_button'] == 'black':
                    self.SetColor()
                if output_dict['color_button'] == 'solid':
                    self.SetColor()
            self.RefreshDict()
            time.sleep(self.sleep_time)

    def RefreshDict(self):
        if 'color_speed' in output_dict:
            if output_dict['color_speed']:
                self.sleep_time = float(output_dict['color_speed']) * 0.00001

    def rainbow(self):
        sat = 1.0
        bright = 1.0
        for i in range(0, 360):
            self.RefreshDict()
            if 'sat_speed' in output_dict:
                sat = float(float(output_dict['sat_speed']) / 100.0000)
            else:
                sat = 1.0
            bright = float(output_dict['bright_slider']) * 0.01
            (r, g, b) = colorsys.hsv_to_rgb(float(i)/360, sat, bright)
            r = int(r * 255)
            g = int(g * 255)
            b = int(b * 255)
            colors['r'] = r
            colors['g'] = g
            colors['b'] = b
            self.RefreshDict()
            if 'color_button' in output_dict:
                if output_dict['color_button'] != 'rainbow':
                    return
            time.sleep(self.sleep_time)

        for i in range(359, -1, -1):
            self.RefreshDict()
            if 'sat_speed' in output_dict:
                sat = float(float(output_dict['sat_speed']) / 100.0000)
            else:
                sat = 1.0
            bright = float(output_dict['bright_slider']) * 0.01
            (r, g, b) = colorsys.hsv_to_rgb(float(i)/360, sat, bright)
            r = int(r * 255)
            g = int(g * 255)
            b = int(b * 255)
            colors['r'] = r
            colors['g'] = g
            colors['b'] = b
            self.RefreshDict()
            if 'color_button' in output_dict:
                if output_dict['color_button'] != 'rainbow':
                    return
            time.sleep(self.sleep_time)


class LEDPattern(threading.Thread):
    def __init__(self, queue, color):
        self.color = color
        self.strip = LPD8806.strand(leds=num_leds)
        self.queue = queue
        self.sleep_time = 0.1
        threading.Thread.__init__(self)

    def run(self):
        choice = 4
        while True:
            if self.queue.qsize() > 0:
                choice = self.queue.get()
            self.GetSleep()
            if choice == 1:
                self.BlackOut()
            elif choice == 2:
                self.WhiteOut()
            elif choice == 3:
                self.Fader()
            elif choice == 4:
                self.TailMover()
            elif choice == 5:
                self.SingleMover()
            elif choice == 6:
                self.color.rainbow()
            elif choice == 7:
                self.Random()
            else:
                self.BlackOut()
                self.SingleMover()
                self.BlackOut()

    def GetSleep(self):
        if 'pattern_speed' in output_dict:
            if output_dict['pattern_speed']:
                self.sleep_time = float(int(output_dict['pattern_speed'])) * 0.000001

    def BlackOut(self):
        self.strip.fill(0, 0, 0, start=0, end=num_leds)
        self.strip.update()
        time.sleep(0.1)
    
    def WhiteOut(self):
        self.strip.fill(150, 150, 150, start=0, end=num_leds)
        self.strip.update()
        time.sleep(0.1)


    def TailMover(self, sleep_time=0.10, tail=32):
        def build(led, pos, diff):
            if led['led'] + 1 > num_leds-1:
                led['led'] = 0
            else:
                led['led'] += 1
            for i in ['r', 'g', 'b']:
                led[i] = colors[i] - (diff * pos)
                if led[i] < (diff):
                    led[i] = 0
            return led

        group = []
        tail = int(0.25*num_leds)
        diff = int((255 / tail) + 2)
        # build struct
        for i in range(0, tail):
            group.append({'led': num_leds-i,
                          'r': 0,
                          'g': 0,
                          'b': 0})

        while True:
            for head in range(0,num_leds):
                self.GetSleep()
                # Check Queue
                if self.queue.qsize() > 0:
                    return
                for j in range (0, tail):
                    led = build(group[j], j, diff)
                    #print led
                    self.strip.set(led['led'], led['r'], led['g'], led['b'])
                    group[j] = led
                self.strip.update()
                time.sleep(self.sleep_time)

    def SingleMover(self):
        # up
        off = 0
        for i in range(0,num_leds):
            if self.queue.qsize() > 0:
                return
            if i == 0:
                off = num_leds - 1
            else:    
                off = i - 1
            self.strip.set(off, 0, 0, 0)
            self.strip.set(i, colors['r'], colors['g'], colors['b'])
            self.strip.update()
            self.GetSleep()
            time.sleep(self.sleep_time)
        # down
        for i in range(num_leds-1, -1, -1):
            if self.queue.qsize() > 0:
                return
            if i == num_leds - 1:
                off = 0
            else:
                off = i + 1
            self.strip.set(off, 0, 0, 0)
            self.strip.set(i, colors['r'], colors['g'], colors['b'])
            self.strip.update()
            self.GetSleep()
            time.sleep(self.sleep_time)
        

    def Fader(self):
        self.strip.fill(colors['r'], colors['g'], colors['b'], start=0, end=num_leds)
        self.strip.update()
        self.GetSleep()
        time.sleep(self.sleep_time)

    def Random(self, step=3):

        def build_led():
            steps = 50
            led = { 'led': random.randint(0, num_leds-1),
                     'r': 0,
                     'g': 0,
                     'b': 0,
                     'r_max': random.randint(1,254),
                     'g_max': random.randint(1,254),
                     'b_max': random.randint(1,254),
                     'dir': 1,
                     'count': 0
                     }
            led['max_val'] = max(led['r_max'], led['g_max'], led['b_max']) + 3
            if led['max_val'] > 254:
                led['max_val'] = 255
            led['r_dec'] = led['r_max'] / steps
            led['g_dec'] = led['g_max'] / steps
            led['b_dec'] = led['b_max'] / steps
            #if led['r'] < 200 and led['g'] < 200 and led['b'] < 200:
            #    v = random.sample(['r', 'g', 'b'], 1)
            #    led[v[0]] = random.randint(200, 255)
            print led
            return led

        leds = []
        self.strip.fill(0, 0, 0, start=0, end=num_leds) 
        self.strip.update()

        for i in range(0,num_leds / 2):
            led = build_led()
            leds.append(led)

        while True:
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
            print "3. Fader"
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
            except:
                print "You can only choose numbers!"

class SocketInput(threading.Thread):
    def __init__(self, port=9999):
        pass
    def run(self):
        while True:
            time.sleep(1)    

# functions
def ctrlc(signal, frame):
    print "Exiting . . ."
    os._exit(0)

def main():
    print ("Bootup may take up to 10 seconds as threads must "
           "start in order and sequentially.")
    # Override ctrl-c to kill threads
    signal.signal(signal.SIGINT, ctrlc)
    queue = Queue.Queue()
    readfile = ReadFile(queue)
    color = ColorChanger()
    value = Value()
    leds = LEDPattern(queue, color)
    print "Starting File Reader"
    readfile.start()
    time.sleep(1)
    print "Starting color"
    color.start()
    #value.start()
    time.sleep(1)
    print "Starting leds"
    leds.start()
    print "Starting User Controls"
    user = UserInput(queue)
    user.start()
    sys.exit(0)

if __name__ == '__main__':
    main()
