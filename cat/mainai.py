#--version0.982_stable_async_tinyweb_270426--
DEBUG = False

import machine
from machine import Pin, I2C, RTC
from network import WLAN, STA_IF
import uasyncio as asyncio
from gc import collect, mem_free
from time import sleep, ticks_ms, ticks_diff

from urequests import get
from framebuf import FrameBuffer, MONO_HLSB

from sh1106 import SH1106_I2C
from bme280 import BME280

import ntptimerp3 as ntptimem
from uping import ping
from os import rename

# --------------------------
# Helpers / Diagnostics
# --------------------------

def debug_print(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)

def fwrite(valstr):
    try:
        with open('rstate.dat', 'w') as f:
            f.write(valstr)
    except Exception as e:
        debug_print("fwrite error:", e)

def read_rstate(default=0):
    try:
        with open('rstate.dat', 'r') as f:
            s = f.read().strip()
            return int(s) if s else default
    except Exception:
        fwrite(str(default))
        return default

def crash_log(where, exc):
    # Keep it tiny and safe
    try:
        cause = machine.reset_cause() if hasattr(machine, "reset_cause") else -1
        with open("crash.log", "a") as f:
            f.write("----\n")
            f.write("where: %s\n" % where)
            f.write("reset_cause: %s\n" % str(cause))
            f.write("mem_free: %s\n" % str(mem_free()))
            f.write("exc: %s\n" % repr(exc))
    except:
        pass

def safe_get(url, timeout=3):
    try:
        r = get(url, timeout=timeout)
        data = r.content
        r.close()
        return data
    except Exception as e:
        debug_print("safe_get error:", url, e)
        return None

def download_in_chunks(url, chunk_size=512, timeout=5):
    resp = None
    try:
        resp = get(url, stream=True, timeout=timeout)
        while True:
            chunk = resp.raw.read(chunk_size)
            if not chunk:
                break
            yield chunk
    finally:
        try:
            if resp:
                resp.close()
        except:
            pass

# --------------------------
# Constants / Config
# --------------------------

_STRINGS = (
"""<!DOCTYPE html>
<html><head></head><body>%s</body></html>
""",
"""<form action="/upgrade">
  <label for="pwd">Passwd:</label>
  <input type="password" id="pwd" name="pwd" minlength="5">&nbsp;&nbsp;
  <input type="submit" value="UPGRADE">
</form>
""",
"""<form action="%s">
    <input type="submit" value="RESET" />
</form>
""",
"Wiatrak-holender1",  # SSID
"klumpioky03",        # PASS
"zp987-",             # Upgrade passwd
"https://raw.githubusercontent.com/mareksaw-cg/remote_upgrade/main/cat/main.py",
"#--version",
)

# intervals
TICK_MS        = 1000
CONNCHK_MS     = 67000
NTP_MS         = 15 * 60 * 1000
GC_MS          = 15 * 60 * 1000
LCD_OFF_TICKS  = 90             # 90 seconds at 1Hz

LCD_ON_FROM_H  = 8              # hour >= 8
LCD_ON_TO_H    = 21             # hour < 21

IRQ_DEBOUNCE_MS = 250

# --------------------------
# Hardware init
# --------------------------

roupin = Pin(17, Pin.OUT)
modpin = Pin(16, Pin.OUT)

bmesup = Pin(13, Pin.OUT, value=1)
pir    = Pin(28, Pin.IN)
led    = Pin('LED', Pin.OUT, value=1)

p20    = Pin(20, Pin.IN, Pin.PULL_UP)
p21    = Pin(21, Pin.IN, Pin.PULL_UP)

neopin = Pin(2, Pin.OUT, value=0)

i2c  = I2C(0, sda=Pin(0),  scl=Pin(1),  freq=400000)
i2c1 = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)

rtc = RTC()

# --------------------------
# Boot / relay state logic
# --------------------------

rstate = read_rstate(default=0)
if not rstate:
    roupin.value(1)
else:
    fwrite('0')

# LCD detect/init
lcd = False
display = None

faces = {}
heart_fb = None

print("I2C0:", i2c.scan(), "I2C1:", i2c1.scan())
if 60 in i2c.scan():
    try:
        lcd = True
        display = SH1106_I2C(128, 64, i2c)
        display.flip()
        display.fill(0)
        display.text("Start...", 0, 0, 1)
        display.show()
    except Exception as e:
        lcd = False
        display = None
        crash_log("lcd_init", e)

sleep(6)
roupin.value(0)
collect()

# --------------------------
# Sensor/WiFi init
# --------------------------

bme280 = BME280(i2c=i2c1)

wlan = WLAN(STA_IF)
wlan.active(True)
wlan.connect(_STRINGS[3], _STRINGS[4])

# --------------------------
# Cached PBM FrameBuffers
# --------------------------

def _load_pbm_fb(path, w, h):
    with open(path, "rb") as f:
        f.readline(); f.readline(); f.readline()  # header lines
        data = bytearray(f.read())
    return FrameBuffer(data, w, h, MONO_HLSB)

def load_assets():
    global faces, heart_fb
    if not lcd:
        return
    try:
        # load only what you actually use
        faces[5] = _load_pbm_fb("buzka5.pbm", 128, 64)
        heart_fb = _load_pbm_fb("serce2.pbm", 11, 11)
    except Exception as e:
        crash_log("load_assets", e)

load_assets()

# --------------------------
# State variables (close to yours)
# --------------------------

run1 = True
lcdcount = 0
lcdon = True

getdata = False
servok = False

modovr1 = False
rouovr1 = False
glk1 = False
nlk1 = False

nokcount = 4
ucc = 0

modem = False
router = False

svolt = 0.0
bvolt = 0.0
samp  = 0.0
bamp  = 0.0

frapow = 0.0
avcur  = 0.0
chp    = 0.0

ntpok = False
wifi = False
solarip = "10.0.0.36:1411"

t = 0.0
h = 0
p = 0.0
dec = uni = fra = 0
dech = unih = 0

lrst = "RESTART"
loopt = 0

chg = False
_last_irq20 = 0
_last_irq21 = 0

line1 = "error"
try:
    with open('main.py', 'r') as f:
        line1 = f.readline().split('--')[1][7:]
except:
    pass

# --------------------------
# IRQ handlers (SAFE)
# --------------------------

def p20_irq(pin):
    global chg, _last_irq20
    now = ticks_ms()
    if ticks_diff(now, _last_irq20) > IRQ_DEBOUNCE_MS:
        chg = True
        _last_irq20 = now

def p21_irq(pin):
    global chg, _last_irq21
    now = ticks_ms()
    if ticks_diff(now, _last_irq21) > IRQ_DEBOUNCE_MS:
        chg = False
        _last_irq21 = now

# --------------------------
# Network connect / NTP
# --------------------------

def connect():
    global solarip, wifi
    try:
        if lcd:
            display.fill(0)
        if not wlan.active():
            wlan.active(True)
        if not wlan.isconnected():
            wlan.connect(_STRINGS[3], _STRINGS[4])

        for n in range(6):
            if wlan.isconnected():
                cfg = wlan.ifconfig()
                ip = cfg[0]
                wifi = True
                solarip = '10.0.0.36:1411' if ip == '10.0.0.56' else '46.187.185.38:1411'
                print("ifconf:", cfg)
                print("SOLARIP:", solarip)
                if lcd:
                    display.text("WLAN OK", 0, 0, 1)
                    display.text("IP: " + ip, 0, 20, 1)
                    display.show()
                return True

            if lcd:
                display.text("WLAN" + "." * n, 0, 0, 1)
                display.show()
            sleep(4)

        wlan.active(False)
        wifi = False
        if lcd:
            display.fill(0)
            display.text("Brak sieci!", 0, 0, 1)
            display.show()
        sleep(2)
        return False

    except Exception as e:
        crash_log("connect", e)
        wifi = False
        return False

def getntp():
    global ntpok
    ntpok = False
    try:
        if wlan.isconnected():
            ntpok = True if ntptimem.settime() else False
    except Exception as e:
        crash_log("getntp", e)
        ntpok = False

# --------------------------
# Solar fetch + parse (lower churn)
# --------------------------

def get_solar_parameters(temp, pres):
    global getdata
    getdata = False
    if not wlan.isconnected():
        return None

    url = "http://%s/parameters?%s;%s;%d;%d" % (
        solarip, str(temp), str(pres), roupin.value(), modpin.value()
    )
    raw = safe_get(url, timeout=2)
    if raw is None:
        return None

    try:
        # get 4th line (index 3) with minimal splitting
        start = 0
        for _ in range(3):
            nl = raw.find(b'\n', start)
            if nl < 0:
                break
            start = nl + 1
        end = raw.find(b'\n', start)
        if end < 0:
            end = len(raw)
        line = raw[start:end]

        # isolate between '>' and '<' if HTML-ish
        gt = line.find(b'>')
        lt = line.rfind(b'<')
        content = line[gt+1:lt] if (gt >= 0 and lt > gt) else line

        parts = content.decode("utf-8", "ignore").split(';')
        getdata = True
        return parts
    except Exception as e:
        crash_log("solar_parse", e)
        return None

# --------------------------
# OLED helpers
# --------------------------

def draw_dot(x, scale=1):
    display.fill_rect(x, 56 // scale, 8 // scale, 8 // scale, 1)

def draw_digit(digit, x, y=0, scale=1):
    if digit == 1: code = 80
    elif digit == 2: code = 55
    elif digit == 3: code = 87
    elif digit == 4: code = 90
    elif digit == 5: code = 79
    elif digit == 6: code = 111
    elif digit == 7: code = 81
    elif digit == 8: code = 127
    elif digit == 9: code = 95
    else: code = 125  # 0

    mask = 1
    if code & mask: display.fill_rect(x, y, 48 // scale, 8 // scale, 1)
    mask <<= 1
    if code & mask: display.fill_rect(x, y + (24 // scale), 48 // scale, 8 // scale, 1)
    mask <<= 1
    if code & mask: display.fill_rect(x, y + (56 // scale), 48 // scale, 8 // scale, 1)
    mask <<= 1
    if code & mask: display.fill_rect(x, y, 8 // scale, 32 // scale, 1)
    mask <<= 1
    if code & mask: display.fill_rect(x + (40 // scale), y, 8 // scale, 32 // scale, 1)
    mask <<= 1
    if code & mask: display.fill_rect(x, y + (32 // scale), 8 // scale, 32 // scale, 1)
    mask <<= 1
    if code & mask: display.fill_rect(x + (40 // scale), y + (32 // scale), 8 // scale, 32 // scale, 1)

def show_face(num):
    fb = faces.get(num, None)
    if fb:
        display.blit(fb, 0, 0)

def show_heart(x, y):
    if heart_fb:
        display.blit(heart_fb, x, y)

# --------------------------
# Main logic blocks
# --------------------------

def lcd_allowed(hour):
    return (hour >= LCD_ON_FROM_H) and (hour < LCD_ON_TO_H)

def update_power_outputs(second):
    # keep your alternating scheme
    if (second % 2) == 0:
        modpin.value(1 if (modem or modovr1) else 0)
    else:
        roupin.value(1 if (router or rouovr1) else 0)

def update_pir_lcd_logic(hour):
    global lcdcount, lcdon
    if not lcd:
        return

    if not pir.value():
        lcdcount += 1
        if lcdcount > LCD_OFF_TICKS and lcdon:
            lcdon = False
            lcdcount = 0
        elif lcdcount > LCD_OFF_TICKS and (not lcdon):
            # only power off; repeated calls are OK but we keep it minimal
            try:
                display.poweroff()
            except:
                pass
    else:
        # motion detected
        if not lcdon:
            if lcd_allowed(hour):
                try:
                    display.poweron()
                except:
                    pass
                lcdon = True
            lcdcount = 0
        else:
            lcdcount = 0

def update_lcd(hour, minute, second):
    if not lcd:
        return

    if not lcdon:
        display.fill(0)
        show_face(5)
        display.show()
        return

    # draw full screen (still 1 Hz, OK); cached PBMs reduce heap churn
    display.fill(0)
    display.text('T', 0, 0, 1);  display.text('E', 0, 8, 1)
    display.text('M', 0, 16, 1); display.text('P', 0, 24, 1)

    display.text('W', 0, 36, 1); display.text('I', 0, 46, 1)
    display.text('G', 0, 56, 1)
    display.text('AKUM:', 60, 36, 1)

    if dec:
        draw_digit(dec, 15, scale=2)
    draw_digit(uni, 45, scale=2)
    draw_dot(72, scale=2)
    draw_digit(fra, 79, scale=2)

    if dech:
        draw_digit(dech, 15, 36, scale=4)
    draw_digit(unih, 30, 36, scale=4)
    display.text('%', 46, 36, 1)

    if second % 2:
        show_heart(112, 0)

    display.text("%02d:%02d" % (hour, minute), 15, 56, 1)
    display.text("%.2fV" % (bvolt,), 60, 46, 1)
    display.text("%.1fA" % (round(bamp/1000.0, 1),), 60, 56, 1)

    if wlan.isconnected(): display.text('WI', 113, 24, 1)
    if ntpok:            display.text('NT', 113, 14, 1)
    if servok:           display.text('OK', 113, 34, 1)
    if modpin.value():   display.text('MO', 113, 44, 1)
    if roupin.value():   display.text('RT', 113, 54, 1)
    if neopin.value():   display.text('C', 46, 46, 1)

    display.show()

# --------------------------
# Periodic async tasks (SAFE)
# --------------------------

async def tick_task():
    global run1, t, h, p, dec, uni, fra, dech, unih
    global servok, nokcount, ucc, frapow, avcur, modem, router
    global svolt, samp, bvolt, bamp, glk1, nlk1, rouovr1, chp, loopt

    next_t = ticks_ms()
    while True:
        t0 = ticks_ms()
        try:
            (year, month, mday, wday, hour, minute, second, msecs) = rtc.datetime()

            # Sensor read (30s)
            if run1 or (second % 30) == 0:
                temp = round(float(bme280.temperature[:-1]), 1)
                hum  = int(float(bme280.humidity[:-1]))
                pres = round(float(bme280.pressure[:-3]), 1)
                t, h, p = temp, hum, pres

                dec = abs(int(t)) // 10
                uni = abs(int(t)) % 10
                fra = int(10 * (t - int(t)))
                dech = abs(int(h)) // 10
                unih = abs(int(h)) % 10

            # Solar fetch (16 and 46 sec)
            if run1 or second in (16, 46):
                run1 = False
                servok = False

                parts = get_solar_parameters(t, p)
                if parts and parts[-1] == "OK":
                    try:
                        svolt = float(parts[0]); samp = float(parts[1])
                        bvolt = float(parts[2]); bamp = float(parts[3])
                        glk1  = (parts[4] == "True")
                        nlk1  = (parts[5] == "True")
                        chp   = float(parts[6])
                        rouovr1 = (parts[7] == "True")

                        servok = True
                        nokcount = 4
                        ucc = 0
                        refcur = chp

                        if svolt > 19.31:
                            frapow = (svolt * samp / 1000.0) / 40.0
                            avcur  = ((0.75 * svolt) - 13.5) * 1250.0 * 0.6

                            if avcur > 600 and bamp < refcur:
                                if not router:
                                    router = True
                                elif router and avcur > 800 and bamp < refcur:
                                    if not modem:
                                        modem = True

                        if bamp > refcur and modem:
                            modem = False
                        elif bamp > refcur and router and (not modem):
                            router = False

                    except Exception as e:
                        crash_log("solar_apply", e)
                        servok = False
                else:
                    # soft recovery instead of reset
                    nokcount -= 1
                    ucc += 1

                    if ucc > 65:
                        ucc = 0
                        connect()

                    if nokcount < 3:
                        modem = False
                    if nokcount <= 0:
                        router = False
                        nokcount = 4

                # GC after heavy parsing/network
                collect()

            # lockouts
            if nlk1:
                modem = False
            if glk1:
                router = False
                modem = False

            # early morning forced off
            if (hour < 6) and (second == 0):
                modem = False
                if router and (not rouovr1):
                    router = False

            # outputs
            update_power_outputs(second)
            neopin.value(1 if chg else 0)

            # LCD
            update_lcd(hour, minute, second)
            update_pir_lcd_logic(hour)

        except Exception as e:
            crash_log("tick_task", e)

        loopt = ticks_diff(ticks_ms(), t0)

        # drift-minimized scheduling
        next_t = (next_t + TICK_MS) & 0x3FFFFFFF
        dt = ticks_diff(next_t, ticks_ms())
        if dt > 0:
            await asyncio.sleep_ms(dt)
        else:
            await asyncio.sleep_ms(0)

async def connchk_task():
    next_t = ticks_ms()
    while True:
        try:
            if not wlan.isconnected():
                if not wlan.active():
                    wlan.active(True)
                wlan.connect(_STRINGS[3], _STRINGS[4])
                await asyncio.sleep_ms(2000)
                if not wlan.isconnected():
                    connect()
        except Exception as e:
            crash_log("connchk_task", e)

        next_t = (next_t + CONNCHK_MS) & 0x3FFFFFFF
        dt = ticks_diff(next_t, ticks_ms())
        if dt > 0:
            await asyncio.sleep_ms(dt)
        else:
            await asyncio.sleep_ms(0)

async def ntp_gc_task():
    next_ntp = ticks_ms()
    next_gc  = ticks_ms()
    while True:
        now = ticks_ms()
        if ticks_diff(now, next_ntp) >= 0:
            next_ntp = (next_ntp + NTP_MS) & 0x3FFFFFFF
            getntp()
        if ticks_diff(now, next_gc) >= 0:
            next_gc = (next_gc + GC_MS) & 0x3FFFFFFF
            collect()
        await asyncio.sleep_ms(250)

# --------------------------
# Startup: connect, time, IRQs
# --------------------------

connect()
sleep(1)
getntp()

(year, month, mday, wday, hour, minute, second, msecs) = rtc.datetime()
lrst = "%d.%d.%d %d:%02d.%02d" % (mday, month, year, hour, minute, second)

p20.irq(trigger=Pin.IRQ_FALLING, handler=p20_irq)
p21.irq(trigger=Pin.IRQ_FALLING, handler=p21_irq)

# --------------------------
# TinyWeb server routes
# --------------------------

from server import webserver
app = webserver()

@app.route('/')
async def index(req, resp):
    await resp.start_html()
    body = (
        "{};{}<br>"
        "MEM:{};<br>"
        "ROUPIN:{} MODPIN:{};<br>"
        "ROUOVR:{} MODOVR:{};<br>"
        "AVCUR:{} BAMP:{};<br>"
        "LAST RESTART:{};<br>"
        "LOOP EX TIME:{}ms;<br>"
        "<a href='resetconf'>RESTART</a>;<br>"
        "<a href='upgradeconf'>UPGRADE</a><br>"
        "FIRMWARE:{}"
    ).format(t, p, mem_free(),
             roupin.value(), modpin.value(),
             rouovr1, modovr1,
             avcur, bamp,
             lrst, loopt, line1)
    await resp.send(_STRINGS[0] % body)

@app.route('/params')
async def params(req, resp):
    await resp.start_html()
    await resp.send(str(t) + ';' + str(p) + ';' + str(h))

@app.route('/pins')
async def pins(req, resp):
    await resp.start_html()
    await resp.send(_STRINGS[0] % (str(roupin.value()) + ';' + str(modpin.value()) + ';' + lrst.split(" ")[1]))

@app.route('/modem')
async def modem_toggle(req, resp):
    global modovr1
    modovr1 = not modovr1
    await resp.start_html()
    await resp.send(_STRINGS[0] % ('OK1' if modovr1 else 'OK0'))

@app.route('/modemchk')
async def modem_chk(req, resp):
    await resp.start_html()
    await resp.send(_STRINGS[0] % ('OK1' if modovr1 else 'OK0'))

@app.route('/router')
async def router_toggle(req, resp):
    global rouovr1
    rouovr1 = not rouovr1
    await resp.start_html()
    await resp.send(_STRINGS[0] % ('OK1' if rouovr1 else 'OK0'))

@app.route('/routerchk')
async def router_chk(req, resp):
    await resp.start_html()
    await resp.send(_STRINGS[0] % ('OK1' if rouovr1 else 'OK0'))

@app.route('/charge')
async def charge_toggle(req, resp):
    global chg
    chg = not chg
    await resp.start_html()
    await resp.send(_STRINGS[0] % ('OK1' if chg else 'OK0'))

@app.route('/resetconf')
async def resetconf(req, resp):
    await resp.start_html()
    await resp.send(_STRINGS[0] % (_STRINGS[2] % 'reset'))

@app.route('/reset')
async def reset(req, resp):
    await resp.start_html()
    await resp.send(_STRINGS[0] % 'OK RESET')
    await asyncio.sleep_ms(500)
    fwrite('1')
    machine.reset()

@app.route('/lockreset')
async def lockreset(req, resp):
    global modem, router
    modem = False
    router = False
    await resp.start_html()
    await resp.send(_STRINGS[0] % ('OK M=%s R=%s' % (modem, router)))

@app.route('/modemon')
async def modemon(req, resp):
    global modem
    modem = True
    await resp.start_html()
    await resp.send(_STRINGS[0] % 'OK MODEM ON')

@app.route('/msolaroff')
async def msolaroff(req, resp):
    global modem
    modem = False
    modpin.value(0)
    await resp.start_html()
    await resp.send(_STRINGS[0] % 'OK')

@app.route('/upgradeconf')
async def upgradeconf(req, resp):
    await resp.start_html()
    await resp.send(_STRINGS[0] % _STRINGS[1])

@app.route('/upgrade')
async def upgrade(req, resp):
    await resp.start_html()

    # tinyweb gives query_string as bytes: b"pwd=...."
    try:
        qs = req.query_string.decode("utf-8")
        pwd = qs.split("=", 1)[1] if "=" in qs else ""
    except:
        pwd = ""

    if pwd != _STRINGS[5]:
        await resp.send(_STRINGS[0] % "WRONG PASS")
        return

    await resp.send(_STRINGS[0] % "downloading...")
    collect()

    init_ok = False
    end_ok  = True

    try:
        with open("_main.py", "wb") as f:
            for chunk in download_in_chunks(_STRINGS[6]):
                if (not init_ok) and chunk.startswith(_STRINGS[7].encode()):
                    init_ok = True
                f.write(chunk)
    except Exception as e:
        crash_log("upgrade_download", e)
        end_ok = False

    collect()

    if init_ok and end_ok:
        try:
            rename("_main.py", "main.py")
            await resp.send(_STRINGS[0] % "OK RENAME")
        except Exception as e:
            crash_log("upgrade_rename", e)
            await resp.send(_STRINGS[0] % "RENAME ERROR")
    else:
        await resp.send(_STRINGS[0] % "DOWNLOAD ERROR")

# --------------------------
# Run: schedule tasks, start server, run loop
# --------------------------

try:
    loop = asyncio.get_event_loop()
    loop.create_task(tick_task())
    loop.create_task(connchk_task())
    loop.create_task(ntp_gc_task())

    if wifi:
        app.run(host="0.0.0.0", port=1412, loop_forever=False)
        loop.run_forever()
    else:
        print("Serwer zatrzymany")
        sleep(30)
        fwrite('1')
        machine.reset()

except Exception as e:
    crash_log("top_level", e)
    machine.reset()

#--$FE--
