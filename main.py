#!/usr/bin/python
import os
import sys
import time
import json
import pprint
import random
import signal
import shutil
import LPD8806
import colorsys
import threading
import traceback

# Globals
num_leds = 160
colors = {'r': 0, 'g': 0, 'b': 0, 'v': 1.0}
output_dict = {}
random.seed(time.time())


class Brightness(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.sleep_time = 0.1

    def run(self):
        while True:
            for i in range(0, 100):
                colors['v'] = i * 0.01
                self.refresh_dict()
                time.sleep(self.sleep_time)
            for i in range(100, -1, -1):
                colors['v'] = i * 0.01
                self.refresh_dict()
                time.sleep(self.sleep_time)

    def refresh_dict(self):
        if 'brightness_slider' in output_dict:
            self.sleep_time = float(output_dict['brightness_slider']) * 0.01


class ReadFile(threading.Thread):
    def __init__(self,
                 settings_file='/mnt/ram/led_settings.dict',
                 lock_file='/mnt/ram/.led_settings.dict.lock',
                 backup_file='/home/levi/funkytown_leds/led_settings.dict.backup'):
        self.settings_file = settings_file
        self.lock_file = lock_file
        self.previous_pattern = 'fader'
        threading.Thread.__init__(self)

        if not os.path.exists(settings_file):
            shutil.copyfile(backup_file, settings_file)
        if os.path.exists(self.lock_file):
            os.unlink(self.lock_file)

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
        while True:
            self.refresh_input()
            time.sleep(0.25)

    def get_lock_file(self):
        while os.path.exists(self.lock_file):
            time.sleep(0.01)
        fp = open(self.lock_file, 'w')
        fp.write("")
        fp.close()

    def release_lock_file(self):
        if os.path.exists(self.lock_file):
           os.unlink(self.lock_file)

    def refresh_input(self):
        global output_dict
        lock = threading.Lock()

        # Check to make sure the file is not open already (file size < 100 bytes)
        while os.path.getsize(self.settings_file) < 100:
            time.sleep(0.1)

        self.get_lock_file()
        lock.acquire()
        fl = open(self.settings_file, 'r')
        try:
            line = fl.readlines()[0]
            input_dict = json.loads(line)
            output_dict = self.convert(input_dict)
            #pprint.pprint(output_dict)
            if 'pattern' in output_dict:
                if self.previous_pattern != output_dict['pattern']:
                    self.previous_pattern = output_dict['pattern']
        except Exception, e:
            print "============ EXCEPTION ============"
            print "%s" % e
            print traceback.format_exc()
            print "==================================="
        finally:
            fl.close()
            lock.release()
            self.release_lock_file()


class ColorChanger(threading.Thread):
    def __init__(self):
        self.sleep_time = 0.2
        self.choice = 'white'
        threading.Thread.__init__(self)

    @staticmethod
    def set_color():
        colors['r'] = output_dict['r']
        colors['g'] = output_dict['g']
        colors['b'] = output_dict['b']

    def run(self):
        while True:
            self.refresh_dict()
            if 'color_button' in output_dict:
                if self.choice == 'rainbow':
                    self.rainbow()
                elif self.choice == 'white':
                    output_dict['r'] = 200
                    output_dict['g'] = 200
                    output_dict['b'] = 200
                    self.set_color()
                elif self.choice == 'black':
                    self.set_color()
                elif self.choice == 'solid':
                    self.set_color()
            time.sleep(self.sleep_time)

    def refresh_dict(self):
        global output_dict
        self.choice = output_dict['color_button']
        speed = float(output_dict['hue_slider']) * 0.00001
        if speed > 1 and self.choice == 'rainbow':
            self.sleep_time = speed
            print speed
        else:
            self.sleep_time = 0.1

    def rainbow(self):
        for i in range(0, 360):
            self.refresh_dict()

            if 'saturation_slider' in output_dict:
                sat = float(output_dict['saturation_slider']) / 255.000
            else:
                sat = 1.000
            if 'brightness_slider' in output_dict:
                bright = float(output_dict['brightness_slider']) / 255.000
            else:
                bright = 1.000

            (r, g, b) = colorsys.hsv_to_rgb(float(i) / 360, sat, bright)
            r = int(r * 255)
            g = int(g * 255)
            b = int(b * 255)
            colors['r'] = r
            colors['g'] = g
            colors['b'] = b
            self.refresh_dict()
            if 'color_button' in output_dict:
                if output_dict['color_button'] != 'rainbow':
                    return
            time.sleep(self.sleep_time)

        for i in range(359, -1, -1):
            self.refresh_dict()

            if 'saturation_slider' in output_dict:
                sat = float(output_dict['saturation_slider']) / 255.000
            else:
                sat = 1.0
            if 'brightness_slider' in output_dict:
                bright = float(output_dict['brightness_slider']) / 255.000
            else:
                bright = 1.000

            (r, g, b) = colorsys.hsv_to_rgb(float(i) / 360, sat, bright)
            r = int(r * 255)
            g = int(g * 255)
            b = int(b * 255)
            colors['r'] = r
            colors['g'] = g
            colors['b'] = b
            self.refresh_dict()
            if 'color_button' in output_dict:
                if output_dict['color_button'] != 'rainbow':
                    return
            time.sleep(self.sleep_time)


class Pattern(threading.Thread):
    def __init__(self, color):
        self.color = color
        self.strip = LPD8806.strand(leds=num_leds)
        self.sleep_time = 0.1
        self.choice = 'SingleTail'
        self.valid_choices = ['Fader',
                              'FadeTail',
                              'SingleTail']
        threading.Thread.__init__(self)

    def run(self):
        while True:
            self.refresh_dict()
            if self.choice == 'Fader':
                self.fader()
            elif self.choice == 'FadeTail':
                self.fade_tail()
            elif self.choice == 'SingleTail':
                self.mover()
            else:
                self.black_out()
                self.mover()
                self.black_out()

    def refresh_dict(self):
        button = str(output_dict['pattern_button'])
        self.sleep_time = float(int(output_dict['pattern_slider'])) * 0.00001
        if button in self.valid_choices:
            self.choice = button

    def black_out(self):
        self.strip.fill(0, 0, 0, start=0, end=num_leds)
        self.strip.update()
        time.sleep(0.1)

    def white_out(self):
        self.strip.fill(150, 150, 150, start=0, end=num_leds)
        self.strip.update()
        time.sleep(0.1)

    def fade_tail(self):

        def build(led, pos, diff):
            if led['led'] + 1 > num_leds - 1:
                led['led'] = 0
            else:
                led['led'] += 1
            for i in ['r', 'g', 'b']:
                led[i] = colors[i] - (diff * pos)
                if led[i] < diff:
                    led[i] = 0
            return led

        group = []
        tail = int(0.50 * num_leds)
        diff = int((255 / tail) + 2)

        # build structure
        for i in range(0, tail):
            group.append({'led': num_leds - i,
                          'r': 0,
                          'g': 0,
                          'b': 0})

        for head in range(0, num_leds):
            self.refresh_dict()
            for j in range(0, tail):
                led = build(group[j], j, diff)
                #print led
                self.strip.set(led['led'], led['r'], led['g'], led['b'])
                group[j] = led
            self.strip.update()
            time.sleep(self.sleep_time)

    def mover(self):
        # Move from beginning to end
        for i in range(0, num_leds):
            if i == 0:
                off = num_leds - 1
            else:
                off = i - 1
            self.strip.set(off, 0, 0, 0)
            self.strip.set(i, colors['r'], colors['g'], colors['b'])
            self.strip.update()
            self.refresh_dict()
            time.sleep(self.sleep_time)

        # Move from end to beginning
        for i in range(num_leds - 1, -1, -1):
            if i == num_leds - 1:
                off = 0
            else:
                off = i + 1
            self.strip.set(off, 0, 0, 0)
            self.strip.set(i, colors['r'], colors['g'], colors['b'])
            self.strip.update()
            self.refresh_dict()
            time.sleep(self.sleep_time)

    def fader(self):
        self.strip.fill(colors['r'], colors['g'], colors['b'], start=0, end=num_leds)
        self.strip.update()
        self.refresh_dict()
        time.sleep(self.sleep_time)

    def random(self):
        """ This function is not used.
            Maybe remove this or save away somewhere safe.
        """

        def build_led():
            steps = 50
            led = {'led': random.randint(0, num_leds - 1),
                   'r': 0,
                   'g': 0,
                   'b': 0,
                   'r_max': random.randint(1, 254),
                   'g_max': random.randint(1, 254),
                   'b_max': random.randint(1, 254),
                   'dir': 1,
                   'count': 0}

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

        for i in range(0, num_leds / 2):
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
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        while True:
            print "Press 0 to close application."
            #print "1. Black Out"
            #print "2. White Out"
            #print "3. fader"
            #print "4. Tail Mover"
            #print "5. Mover (single led moving)"
            #print "6. Reset Color"
            #print "7. Use HTTP input"
            #print ""
            #print "0. Exit"
            #print ""
            try:
                choice = int(raw_input("Choice: "))
                print ""
                if choice == 0:
                    print "Exiting"
                    os._exit(0)
                time.sleep(2)

            except:
                print "Invalid input."


def ctrlc():
    print "Exiting . . ."
    os._exit(0)


def main():
    print "Application will take time to start all threads."

    # Override ctrl-c to kill threads
    signal.signal(signal.SIGINT, ctrlc)
    readfile = ReadFile()
    color = ColorChanger()
    brightness = Brightness()
    leds = Pattern(color)
    print "Starting File Reader"
    readfile.start()
    time.sleep(1)
    print "Starting color"
    color.start()
    brightness.start()
    time.sleep(1)
    print "Starting leds"
    leds.start()
    print "Starting User Controls"
    user = UserInput()
    user.start()
    sys.exit(0)


if __name__ == '__main__':
    main()
