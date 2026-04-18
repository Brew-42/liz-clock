from waveshare_epd import epd7in5_V2
from PIL import Image, ImageDraw, ImageFont

try:
    epd = epd7in5_V2.EPD()
    epd.init()
    epd.Clear()

    # Create a blank image (800x480)
    image = Image.new('1', (epd.width, epd.height), 255)  # 255 = White
    draw = ImageDraw.Draw(image)
    
    # Just a simple test line
    draw.text((10, 10), "Mico and Gem's Help - B, B & D's ....Fabulous Clock Online....Hello WORLD!", fill=0) # 0 = Black

    epd.display(epd.getbuffer(image))
    epd.sleep()
    print("Success! Check the screen.")

except Exception as e:
    print(f"Error: {e}")