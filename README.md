Helios
==============

Helios is a web driven LED controller for the Raspberry Pi and LPD8806 RGB-LED rope.

---
REQUIREMENTS:

1. Raspberry Pi v2
2. JQuery >= 2.0.2
3. LPD8806 - Levi Junkert's fork
4. SPIDEV for Python

---
INSTALLATION

1. Download this repo to your home directory.
2. Download JQuery into ~/this_project/www/
3. Install spidev for Raspberry Pi: http://www.raspberrypi.org/phpBB3/viewtopic.php?f=44&t=56669
4. Install lighttpd: http://www.penguintutor.com/linux/light-webserver
5. Link /var/www to ~/this_project/www
6. Create a RAM drive for the webapp to communicate with the python app:
  - Add the following to /etc/fstab
``
tmpfs           /mnt/ram        tmpfs defaults,noatime,mode=1777,nosuid,size=10M 0 0
``
7. Start the app: ~/this_project/main.py

