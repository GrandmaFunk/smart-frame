from inky import Inky7Colour
from inky.auto import auto
from PIL import Image, ImageFont, ImageDraw #PIL library for drawing
from datetime import date, datetime, timedelta
import pytz
import pickle
import time
import random
import json
from google.cloud import firestore
import threading
import signal
import RPi.GPIO as GPIO
from os.path import exists

def send_last_update():
    print('Sending last update...')

    # Send update to database
    last_update = db.collection('memos').document('last_update')
    last_update.update({u'date':firestore.SERVER_TIMESTAMP})

    # Pickle the date internaly for reference in case device loses power
    pickle.dump(now.date(), open('logs/last_update_day.p', 'wb'))

def get_memo_manually():
    return db.collection('memos').document('memo').get().to_dict()

def send_blink():
    # Toggles the "blink" record in the database
    print('Checking blink status...')
    blink = db.collection('memos').document('blink')
    blink_status = blink.get().to_dict()['blink']
    if blink_status == False:
        blink.update({u'status':True})
        return True
    else: 
        print('Blink status is already True')
        return False

def write_memo(memo):

    clean()

    width = 600
    height = 448

    # Create display
    inky_display = Inky7Colour()

    # Set border color
    inky_display.set_border(inky_display.WHITE)

    if is_image(memo):

        img = Image.open('imgs/' + memo['memo'])
        w,h = img.size

        h_new = 448
        w_new = int( (float(w) / h) * h_new)
        w_cropped = 600

        img = img.resize( (w_new, h_new), resample=Image.LANCZOS)

        x0 = (w_new - w_cropped) / 2
        x1 = x0 + w_cropped
        y0 = 0
        y1 = h_new
        img = img.crop((x0, y0, x1, y1))

        print('Displaying image...')
    else:
        # Make white background
        img = Image.open('imgs/white.jpg')
        img = img.crop((0, 0, width, height))
        img = img.convert('P')
        draw = ImageDraw.Draw(img)

        # Set font
        try:
            import os, random
            fonts = os.listdir('fonts')
            fonts = [font for font in fonts if font.endswith('.ttf')]
            font_type = random.choice(fonts)
            print('Chose font: ', font_type)
        except Exception as ex:
            print('Error while selecting a random font.')
            font_type = 'roboto.ttf'
        
        message = memo['memo']

        # Determine approppriate number of characters per line
        try:
            import textwrap

            if len(message) > 250:
                cap = 40
            elif len(message) > 200:
                cap = 35
            elif len(message) > 150:
                cap = 30
            elif len(message) > 100:
                cap = 25
            elif len(message) > 70:
                cap = 20
            else:
                cap = 15
            message = textwrap.wrap(message, width=cap, break_long_words=False)

        except Exception as ex:
            print('Error during textwrap to determine line char limit')
            message = ['Something went wrong, but I still like you.']

        margin = 30

        # Determine appropriate font size
        for font_size in [160, 132, 110, 92, 82, 72, 52, 42, 32, 26, 22, 18, 12, 10, 8]:
            font = ImageFont.truetype('fonts/' + font_type, font_size)
            w = font.getsize(max(message, key=len))[0]
            h = 0
            for line in message:
                h += font.getsize(line)[1]

            # If a font size fits, break the loop
            if (w < (width - margin) )  & (h < (height - margin)):
                break

        #Center the text
        try:
            x = (width / 2) - (w / 2)
            y = (height / 2) - (h / 2)
        except Exception as ex:
            print('Error during text centering')
            x = 0
            y = 0

        # Draw message, set the text color and font
        draw.text( (x, y), '\n'.join(message), inky_display.BLACK, font)
    
    print('Displaying message...')
    inky_display.set_image(img, saturation=0.7)
    inky_display.show()

    pickle.dump(memo, open('logs/last_memo.p', 'wb'))

def load_last_check():
    try:
        last_update_day = pickle.load( open('logs/last_update_day.p', 'rb'))
        last_memo = pickle.load( open('logs/last_memo.p', 'rb'))
    except (Exception, OSError) as ex:
        print('Error loading log files. Defaulting to 2021/01/01')
        last_update_day = date(2021, 1, 1)
        last_memo = None
        
    return last_update_day, last_memo    

def clean():
    print('Cleaning display...')
    import subprocess
    subprocess.run(['python3', 'clear.py'])

def get_boot_memo(last_memo):
    try:
        # Check For Internet
        import urllib.request
        urllib.request.urlopen('http://google.com')
        pre_memo = "I'm connected to the internet and " 
    except Exception as ex:
        pre_memo = "I'm not connected to the internet but "
    
    if last_memo == None:
        # If Initial Load
        print('First load...')
        memo = "I have power! I'll write messages here just for you. I'll load your very first message now..."

    else:
        print('Generating return message...')
        memo = random.choice(["it's nice to see you again. Let me fetch an update.",
                "it's good to be back. Let's reconnect.",
                "this is some top-notch electricty. Hang tight.",
                "I'll get us back on track in no time!",
                "it's show time! Here we go..."])
    memo = {'memo': pre_memo + memo}
    return memo

def is_image(memo):
    # Check if memo is an image
    # If it is an image and is not already downloaded, download file
     
    if memo['memo'][-4:] == '.jpg' or memo['memo'][-4:] == '.png':
        if not exists('imgs/' + memo['memo']):
            print('New image detected. Downloading file...')
            bucket_name = json.load(open('.secrets/vars.json'))['bucket_name']
            from google.cloud import storage
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(memo['memo'])
            blob.download_to_filename('imgs/' + memo['memo'])

        return True
    else:
        return False

def connect_to_firestore():
    cloud_project = json.load(open('.secrets/vars.json'))['cloud_project']
    db = firestore.Client(project=cloud_project)
    return db

def on_memo_update(memos, changes, read_time):

    if ((now.date() - last_update_day).days > 1) or (last_memo == None):
        print('Loading boot message...')
        boot_memo = get_boot_memo(last_memo)
        write_memo(boot_memo)
        time.sleep(10)

    print('Callback received...')

    try:
        memo = memos[0].to_dict()
    except Exception as e:
        print(e)
        memo = {'memo': "The message I received looks weird but I'll try harder next time!"}

    if (memo != last_memo):
        locked = pickle.load(open('logs/locked.p', 'rb'))
        if not locked:
            write_memo(memo)
            send_last_update()
        else:
            print('Display is locked.')
    else:
        print('Display is already up to date...')
    
    callback_done.set()

def unlock():
    print('Unlocking...')
    pickle.dump(False, open('logs/locked.p', 'wb'))

def lock():
    print('Locking...')
    pickle.dump(True, open('logs/locked.p', 'wb'))

def handle_button(pin):
        label = labels[buttons.index(pin)]
        print(label)
        locked = pickle.load(open('logs/locked.p', 'rb'))
        if label == 'A':
            if locked:
                unlock()
                write_memo(get_memo_manually())
            else:
                lock()
                image = random.choice(['dad2.jpg', 'mom1.jpg'])
                write_memo({'memo': image})
        elif label == 'B':
            if locked:
                unlock()
                write_memo(get_memo_manually())
            else:
                lock()
                image = random.choice(['pop1.jpg', 'pop2.jpg'])
                write_memo({'memo': image})
        elif label == 'C':
            if send_blink():
                messages = ['Your blink was sent!',
                'Reaching out now...',
                'Pinging...',
                'Sending out a blink!']
                _, last_memo = load_last_check()
                write_memo({'memo': random.choice(messages)})
                time.sleep(20)
                write_memo(last_memo)
            else:
                messages = ['Your last blink is still active.',
                'Still no response from the previous blink.',
                'A previous blink is already set.',
                'Sorry, still no update on the last blink.']
                _, last_memo = load_last_check()
                write_memo({'memo': random.choice(messages)})
                time.sleep(20)
                write_memo(last_memo)

        elif label == 'D':
            if locked:
                unlock()
                write_memo(get_memo_manually())
            else:
                lock()
                write_memo({'memo':'instructions.jpg'})


# Load init variables
print('Loading variables...')
last_update_day, last_memo = load_last_check()
unlock()
db = connect_to_firestore()
est = pytz.timezone('US/Eastern')
now = est.localize(datetime.now())

# Set up buttons   
buttons = [5, 6, 16, 24]
labels = ['A', 'B', 'C', 'D']
GPIO.setmode(GPIO.BCM)
GPIO.setup(buttons, GPIO.IN, pull_up_down=GPIO.PUD_UP)
for pin in buttons:
    GPIO.add_event_detect(pin, GPIO.FALLING, handle_button, bouncetime=250)

# Set callbacks for memo change
print('Setting memo handler...')
callback_done = threading.Event()
db = connect_to_firestore()
memo_query = db.collection(u'memos').document(u'memo')
memo_watch = memo_query.on_snapshot(on_memo_update)

signal.pause()