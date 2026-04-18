import random
import sqlite3
import os
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from waveshare_epd import epd7in5_V2

# ============================================================
# CONFIGURATION
# ============================================================

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480

# Time block
TIME_FONT_PATH = "Inter-Medium.ttf"
TIME_FONT_SIZE = 52
TIME_POS = (40, 40)

# Quote block
QUOTE_FONT_PATH = "Alice-Regular.ttf"
QUOTE_FONT_SIZE_MAX = 36
QUOTE_FONT_SIZE_MIN = 18
QUOTE_MAX_WIDTH = SCREEN_WIDTH - 120

# Attribution block
ATTR_FONT_PATH = "Inter-Regular.ttf"
ATTR_FONT_SIZE = 24
ATTR_RIGHT_MARGIN = 90
ATTR_BOTTOM_MARGIN = 40
ATTR_MAX_WIDTH = 500
ATTR_LINE_SPACING = 4

DB_PATH = "quotes.db"

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def text_width(font, text):
    return font.getbbox(str(text))[2] - font.getbbox(str(text))[0]

def text_height(font, text):
    return font.getbbox("Ay")[3] - font.getbbox("Ay")[1]

def wrap_text(text, font, max_width):
    if not text:
        return []
    words = str(text).split(" ")
    lines, current = [], []
    for w in words:
        test = " ".join(current + [w])
        if text_width(font, test) <= max_width:
            current.append(w)
        else:
            if current:
                lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))
    return lines

# ============================================================
# CORE RENDERING
# ============================================================

def render_quote(now_time, author, source, text, is_general):
    img = Image.new("1", (SCREEN_WIDTH, SCREEN_HEIGHT), 255)
    draw = ImageDraw.Draw(img)

    try:
        time_font = ImageFont.truetype(TIME_FONT_PATH, TIME_FONT_SIZE)
        attr_font = ImageFont.truetype(ATTR_FONT_PATH, ATTR_FONT_SIZE)
    except OSError:
        time_font = attr_font = ImageFont.load_default()

    # 1. Time display (general quotes only)
    time_bottom_limit = 40
    if is_general:
        hour = now_time.hour % 12 or 12
        time_str = f"{hour}:{now_time.minute:02d}"
        draw.text(TIME_POS, time_str, font=time_font, fill=0)
        time_bottom_limit = TIME_POS[1] + text_height(time_font, time_str) + 30

    # 2. Attribution formatting
    if author and source and str(source).strip() and source != author:
        full_attr_str = f"~ {author}, {source}"
    elif author:
        full_attr_str = f"~ {author}"
    else:
        full_attr_str = ""

    attr_lines = wrap_text(full_attr_str, attr_font, ATTR_MAX_WIDTH)
    attr_line_h = text_height(attr_font, "Ay")
    total_attr_h = len(attr_lines) * (attr_line_h + ATTR_LINE_SPACING)

    attr_y_start = SCREEN_HEIGHT - ATTR_BOTTOM_MARGIN - total_attr_h
    attr_top_limit = attr_y_start - 30

    # 3. Quote shrink-to-fit
    max_allowed_h = attr_top_limit - time_bottom_limit
    current_size = QUOTE_FONT_SIZE_MAX

    final_lines, final_font, final_line_h = [], None, 0

    while current_size >= QUOTE_FONT_SIZE_MIN:
        try:
            test_font = ImageFont.truetype(QUOTE_FONT_PATH, current_size)
        except OSError:
            test_font = ImageFont.load_default()

        test_lines = wrap_text(text, test_font, QUOTE_MAX_WIDTH)
        test_line_h = text_height(test_font, "Ay") + 8
        total_h = len(test_lines) * test_line_h

        if total_h <= max_allowed_h or current_size == QUOTE_FONT_SIZE_MIN:
            final_lines = test_lines
            final_font = test_font
            final_line_h = test_line_h
            break

        current_size -= 2

    # 4. Vertical centering
    total_quote_h = len(final_lines) * final_line_h
    ideal_center_y = time_bottom_limit + ((max_allowed_h - total_quote_h) // 2)
    quote_y = max(ideal_center_y, time_bottom_limit)

    # 5. Draw quote
    for i, line in enumerate(final_lines):
        lw = text_width(final_font, line)
        draw.text(((SCREEN_WIDTH - lw) // 2, quote_y + i * final_line_h),
                  line, font=final_font, fill=0)

    # 6. Draw attribution
    current_ay = attr_y_start
    for line in attr_lines:
        aw = text_width(attr_font, line)
        draw.text((SCREEN_WIDTH - ATTR_RIGHT_MARGIN - aw, current_ay),
                  line, font=attr_font, fill=0)
        current_ay += attr_line_h + ATTR_LINE_SPACING

    return img

# ============================================================
# DATA SELECTION
# ============================================================

def get_quote_for_time(now):
    minute_val = now.hour * 60 + now.minute

    if not os.path.exists(DB_PATH):
        return ("System", "Error", "DB Missing", True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # General quote probability
    is_general = random.random() < 0.20

    try:
        if is_general:
            cursor.execute("""
                SELECT author, source, text
                FROM quotes
                WHERE minute_of_day IS NULL
                   OR minute_of_day = -1
                   OR tag LIKE '%general%'
            """)
            results = cursor.fetchall()
            if not results:
                is_general = False

        if not is_general:
            cursor.execute("""
                SELECT author, source, text
                FROM quotes
                WHERE minute_of_day = ?
            """, (minute_val,))
            results = cursor.fetchall()

        if not results:
            cursor.execute("""
                SELECT author, source, text
                FROM quotes
                ORDER BY RANDOM()
                LIMIT 1
            """)
            results = cursor.fetchall()
            is_general = True

    except:
        conn.close()
        return ("System", "Error", "DB Error", True)

    conn.close()
    author, source, text = random.choice(results)
    return author, source, text, is_general

# ============================================================
# FIRST BOOT QUOTE
# ============================================================

def show_first_boot_quote():
    now = datetime.now()
    author = "Mary Shelley"
    source = ""
    text = "Hello, World.  ~ Brian Kernighan ~ 1978 \n\n  The beginning is always today."
    is_general = True

    # Add these lines to push it to the hardware:
    epd = epd7in5_V2.EPD()
    epd.init()
    epd.display(epd.getbuffer(image))
    epd.sleep()

# ============================================================
# MAIN LOOP
# ============================================================

def debug_loop():
    last_minute = -1
    print("Windows DEBUG Mode: Creating unique file for every minute...")

    while True:
        now = datetime.now()

        if now.minute != last_minute:
            author, source, text, is_general = get_quote_for_time(now)
            image = render_quote(now, author, source, text, is_general)

            timestamp = now.strftime("%Y-%m-%d_%I-%M-%p")
            filename = f"debug_{timestamp}.png"

            image.save(filename)
            print(f"[{now.strftime('%I:%M %p')}] Saved: {filename}")

#            os.startfile(filename)
            last_minute = now.minute

        time.sleep(1)

def main_loop():
    last_minute = -1
    print("Literary Clock is now running on the Pi...")

    # 1. Initialize the screen hardware object
    # This tells the script which driver to use (the 7.5 inch V2)
    epd = epd7in5_V2.EPD()

    while True:
        now = datetime.now()

        # Only update when the minute actually changes
        if now.minute != last_minute:
            print(f"[{now.strftime('%I:%M %p')}] New minute detected. Updating...")
            
            # 2. Get the quote and render the image (your existing functions)
            author, source, text, is_general = get_quote_for_time(now)
            image = render_quote(now, author, source, text, is_general)

            try:
                # 3. Wake up the screen
                epd.init()
                
                # 4. Hourly "Deep Clean" 
                # Doing a full Clear once an hour prevents "ghosting" (shadows of old quotes)
                if now.minute == 0:
                    print("Performing hourly screen refresh...")
                    epd.Clear()
                
                # 5. Push the image to the screen
                # 'getbuffer' converts your 'image' into data the hardware understands
                epd.display(epd.getbuffer(image))
                
                # 6. Put the screen to sleep
                # This is CRITICAL. It turns off the power to the screen panel 
                # to prevent long-term damage while it's just sitting there.
                epd.sleep()
                
                print(f"[{now.strftime('%I:%M %p')}] Screen update complete.")
                
            except Exception as e:
                print(f"Hardware Error on the Pi: {e}")

            last_minute = now.minute

        # Wait 1 second before checking if the minute has changed again
        time.sleep(1)

# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    print("Initializing...")
#    show_first_boot_quote()
    try:
        main_loop()
    except KeyboardInterrupt:
        print("Stopped.")
