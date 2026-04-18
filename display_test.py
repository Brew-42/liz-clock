#!/usr/bin/env python3
import time
from waveshare_epd import epd7in5_V2
from PIL import Image

epd = epd7in5_V2.EPD_7IN5_V2()
pd7in5_V2.EPD()
epd.init()
epd.Clear()

image = Image.open('first_boot.png')
epd.display(epd.getbuffer(image))

time.sleep(2)
epd.sleep()
