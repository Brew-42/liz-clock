from waveshare_epd import epd7in5_V2
from PIL import Image

# Initialize the display
epd = epd7in5_V2.EPD()
epd.init()
epd.Clear()

# Load your PNG
image = Image.open("first_boot.png")
image = image.convert("1")  # convert to 1‑bit for e‑ink

# Display it
epd.display(epd.getbuffer(image))
epd.sleep()
