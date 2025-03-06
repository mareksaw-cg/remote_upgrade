#--version0.971_240225--    
from machine import Pin

def fwrite(valstr):
    f = open('rstate.dat', 'w')
    f.write(valstr)
    f.close()

roupin = Pin(17, Pin.OUT)

f = open('rstate.dat')
rstate = int(f.read())
f.close()

if not rstate:
    roupin.value(1)
else:
    fwrite('0')
    
_PASSWD = const('zp987-')
#url = const('https://onedrive.live.com/download?cid=7A40866E01A106BA&resid=7A40866E01A106BA%21137441&authkey=AN0DlSOfEB27VcE')
_URL = const('https://raw.githubusercontent.com/mareksaw-cg/remote_upgrade/main/cat/main.py')
_CTRL_STR1 = const('#--version')

_STRINGS = const(("""<!DOCTYPE html>
<html>
    <head></head>
    <body>%s</body>
</html>
""","""<form action="/upgrade">
  <label for="pwd">Passwd:</label>
  <input type="password" id="pwd" name="pwd" minlength="5">&nbsp;&nbsp;
  <input type="submit" value="UPGRADE">
</form>
""","""<form action="%s">
    <input type="submit" value="RESET" />
</form>
""","Wiatrak-holender1","klumpioky03"))

from machine import I2C, Timer, RTC
from network import WLAN, STA_IF
from framebuf import FrameBuffer, MONO_HLSB
from urequests import get
from gc import collect, mem_free
from sh1106 import SH1106_I2C
from bme280 import BME280
from time import sleep

i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
i2c1 = I2C(1, sda=Pin(14), scl=Pin(15), freq=400000)

bmesup = Pin(13, Pin.OUT, value=1)
#bmesup.on()
pir = Pin(28, Pin.IN)
led = Pin('LED', Pin.OUT, value=1)
#led.on()
modpin = Pin(16, Pin.OUT)
p20 = Pin(20, Pin.IN, Pin.PULL_UP)
p21 = Pin(21, Pin.IN, Pin.PULL_UP)
neopin = Pin(2, Pin.OUT)

print(i2c.scan(), i2c1.scan())
if 60 in i2c.scan():
    lcd = True
    display = SH1106_I2C(128, 64, i2c)
    display.flip()
    display.fill(0)
    display.text('Start...', 0, 0, 1)
    display.show()
else:
    lcd = False

sleep(6)
roupin.value(0)

collect()

#rp2.country('DE')
bme280 = BME280(i2c=i2c1)
wlan = WLAN(STA_IF)
wlan.active(True)
wlan.connect(_STRINGS[3], _STRINGS[4])
'''
if lcd:
    display.text('WLAN aktywny', 0, 10, 1)
    display.show()
'''
import ntptimerp3 as ntptimem
#from neopixel import NeoPixel
from os import rename, remove
from uping import ping

#np = NeoPixel(neopin, 1)

tim = Timer()
tim1 = Timer()
rtc = RTC()

if lcd:
    display.text('Deklaracje OK', 0, 20, 1)
    display.show()

run1 = True
lcdcount = int(0)
lcdon = bool(1)
getdata = False
servok = False
modovr1 = bool(0)
rouovr1 = bool(0)
glk1 = bool(0)
nlk1 = bool(0)
nokcount = int(4)
#npval = 10
ucc = int(0)

modem = bool(0)
router = bool(0)
svolt = 0
bvolt = 0
samp = 0
bamp = 0
frapow = 0
avcur = 0
chp = int(0)
lrst = 'RESTART'
result_str = 'GENERAL ERROR'

collect()
'''
def checksum(msg):
    v = 21
    for c in msg:
        v ^= ord(c)
    return v
'''
# OBSŁUGA PRZYCISKÓW, TYMCZASOWO NIEAKTYWNA - BRAK NEOPIXELA
'''
def p20_int(Pin):
    global npval
    p20.irq(handler=None)
    npval += 10
    npval = 250 if npval > 250 else npval
    print(npval)
    sleep(0.3)
    p20.irq(trigger=Pin.IRQ_FALLING, handler=p20_int)
    
def p21_int(Pin):
    global npval
    p21.irq(handler=None)
    npval -= 10
    npval = 0 if npval < 0 else npval
    print(npval)
    sleep(0.3)
    p21.irq(trigger=Pin.IRQ_FALLING, handler=p21_int)
'''
def chkping(url):
    print('ping ' + url)
    return ping(url, count=1, timeout=350, quiet=True)[1]

def download_in_chunks(url, chunk_size=512):
    global result_str, proceed
    try:
        response = get(url, stream=True, timeout=4)
        proceed = True
    except:
        result_str = 'GET ERROR'
        proceed = False
    if proceed:
        try:
            while True:
                try:
                    chunk = response.raw.read(chunk_size)
                except:
                    response.close()
                    proceed = False
                    result_str = 'RESPONSE ERROR'
                    break
                #print(chunk)
                if not chunk:  # No more data
                    result_str = 'OK'
                    response.close()
                    break
                yield chunk
        finally:
            response.close()

def connect():
    global solarip, wifi
    if lcd: display.fill(0)
    wtext = 'WLAN'
    if not wlan.active(): wlan.active(True)
    if not wlan.isconnected(): wlan.connect(_STRINGS[3], _STRINGS[4])
    for n in range(6):
        if wlan.isconnected():
            print('ifconf:', wlan.ifconfig())
            ip = wlan.ifconfig()[0]
            if lcd:
                display.text('WLAN OK', 0, 0, 1)
                display.text('IP: ' + ip, 0, 20, 1)
                display.show()
            wifi = True
            if ip == '10.0.0.56':
                solarip = '10.0.0.36:1411'
            else:
                solarip = '46.187.185.38:1411'
            print('SOLARIP= ' + solarip)
            break
        print('connecting...')
        if lcd:
            display.text(wtext, 0, 0, 1)
            display.show()
            wtext += '.'
        sleep(4)
    else:
        wlan.active(False)
        wifi = False
        print('no network!')
        if lcd:
            display.fill(0)
            display.text('Brak sieci!', 0, 0, 1)
            display.show()
        sleep(5)
    
def getntp():
    print('getntp')
    global ntpok
    ntpok = False
    if wlan.isconnected():
        if ntptimem.settime():
            ntpok = True
   
def get_solar1():
    global getdata
    getdata = False
    if wlan.isconnected():
        try:
            print(p, t)
            r = get("http://" + solarip + "/parameters?" + str(t) + ";" + str(p) + ';' + str(roupin.value()) + ';' + str(modpin.value()), timeout=2)
            data = r.content
            r.close()
            print('Data sent!')
            getdata = True
            print('Solar OK')
            print(data)
            return data            
        except:
            try:
                r.close()
            except:
                pass
            print('Data ERROR')
            return b''
    else:
        return b''

def ch_conn(timer):
    if not wlan.isconnected():
        if not wlan.active(): wlan.active(True)
        if wifi:
            wlan.connect(_STRINGS[3], _STRINGS[4])
            print('Ponowne laczenie!')
        else:
            connect()
    else:
        print('WLAN OK!')
    
def draw_minus(x=0, scale=1):
    display.fill_rect(x, 24 // scale, 18 // scale, 8 // scale, 1)
    
def draw_dot(x, scale=1):
    display.fill_rect(x, 56 // scale, 8 // scale, 8 // scale, 1)
    
def draw_digit(digit, x, y=0, scale=1):
    if digit == 1: code = 80
    if digit == 2: code = 55
    if digit == 3: code = 87
    if digit == 4: code = 90
    if digit == 5: code = 79
    if digit == 6: code = 111
    if digit == 7: code = 81
    if digit == 8: code = 127
    if digit == 9: code = 95
    if digit == 0: code = 125
    
    mask = 1
    if code & mask:
        display.fill_rect(x, y, 48 // scale, 8 // scale, 1)
    mask = mask * 2
    if code & mask:
        display.fill_rect(x, y + (24 // scale), 48 // scale, 8 // scale, 1)
    mask = mask * 2
    if code & mask:
        display.fill_rect(x, y + (56 // scale), 48 // scale, 8 // scale, 1)
    mask = mask * 2
    if code & mask:
        display.fill_rect(x, y, 8 // scale, 32 // scale, 1)
    mask = mask * 2
    if code & mask:
        display.fill_rect(x + (40 // scale), y, 8 // scale, 32 // scale, 1)
    mask = mask * 2
    if code & mask:
        display.fill_rect(x, y + (32 // scale), 8 // scale, 32 // scale, 1)
    mask = mask * 2
    if code & mask:
        display.fill_rect(x + (40 // scale), y + (32 // scale), 8 // scale, 32 // scale, 1)
        
def show_face(facenum):
    f = open('buzka' + str(facenum) + '.pbm', 'rb')
    f.readline()
    f.readline()
    f.readline()
    data = bytearray(f.read())
    fbuf = FrameBuffer(data, 128, 64, MONO_HLSB)
    display.blit(fbuf, 0, 0)
    display.show()
    
def show_heart(x, y):
    f = open('serce2.pbm', 'rb')
    f.readline()
    f.readline()
    f.readline()
    data = bytearray(f.read())
    fbuf = FrameBuffer(data, 11, 11, MONO_HLSB)
    display.blit(fbuf, x, y)
    
def tick(timer):
    
    global run1, lcdon, lcdcount, dec, uni, fra, t, h, p, dech, unih, frapow, avcur, servok, router, modem, svolt, bvolt, samp, bamp, nokcount, modovr1, rouovr1, glk1, nlk1, ucc, modpin, roupin, chp
    
    (year, month, mday, wday, hour, minute, second, msecs) = rtc.datetime()
    
    hh = '0' + str(hour) if hour < 10 else str(hour)
    mm = '0' + str(minute) if minute < 10 else str(minute)
    
    print(lcdcount, lcdon, modovr1, rouovr1)
    
    if second == 0:
        collect()
        '''
        print(mem_free())
        if hour < 7 or hour > 21:
            np[0] = (npval, npval, npval)
            np.write()
        else:
            np[0] = (0, 0, 0)
            np.write()
        '''    
        
    if run1 or not second % 20:

        print('Pomiar...')
        t = round(float(bme280.temperature[:-1]), 1)
        h = int(float(bme280.humidity[:-1]))
        p = round(float(bme280.pressure[:-3]), 1)

        dec = abs(int(t)) // 10
        uni = abs(int(t)) % 10
        fra = int(10 * (t - int(t)))
        
        dech = abs(int(h)) // 10
        unih = abs(int(h)) % 10
            
    if run1 or second == 16 or second == 46:
        run1 = 0
        servok = False
        data = get_solar1()
        if data != b'': data = data.split(b'\n')[3].decode('utf-8')[10:-7].split(';')
        
        if getdata and data[len(data) - 1] == 'OK':
            svolt = float(data[0])
            samp = float(data[1])
            bvolt = float(data[2])
            bamp = float(data[3])
            glk = str(data[4])
            nlk = str(data[5])
            chp = float(data[6])
            rouovr = str(data[7])
            glk1 = True if glk == 'True' else False
            nlk1 = True if nlk == 'True' else False
            rouovr1 = True if rouovr == 'True' else False
            print(svolt, samp, bvolt, bamp, modovr1, rouovr1, glk1, nlk1, chp)
            servok = True
            nokcount = 4
            ucc = 0
            refcur = chp
            
            if svolt > 19.31:
                frapow = (svolt * samp /1000) / 40
                avcur = ((0.75 * svolt) - 13.5) * 1250 * 0.6
                
                if avcur > 600 and bamp < refcur:
                    if not router: router = 1
                    elif router and avcur > 800 and bamp < refcur:
                        if not modem: modem = 1
                            
                print(frapow, avcur, refcur)

            if bamp > refcur and modem and router: modem = 0                
            elif bamp > refcur and router and not modem: router = 0
            
        else:
            print('get error')
            nokcount -= 1
            ucc += 1
            if ucc > 65:
                fwrite('1')               
                machine.reset()
            if nokcount < 3: modem = 0
            if not nokcount:
                router = 0
                nokcount = 4
                
    if nlk1:
        modem = 0
    if glk1:
        router = 0
        modem = 0
    '''
    if modovr1:
        if bvolt < 12.2:
            if not ping('8.8.8.8'):
                modovr1 = 0
    '''    
    if not second % 2:
        modpin.value(modem or modovr1)
    else:
        roupin.value(router or rouovr1)
    '''    
    if not glk1:
        if not nlk1:
            modpin.value(modem or modovr1)
        else:
            modpin.value(0)
            sleep(0.3)            
        roupin.value(router or rouovr1)
    else:
        modpin.value(0)
        sleep(0.3)
        roupin.value(0)
        
    if hour < 5 and not second:
        if modem:
            modpin.value(0)
            sleep(0.5)
        if router and not rouovr1:
            roupin.value(0)
    '''
    if hour < 6 and not second:
        if modem: modem = 0
        if modovr1: modovr1 = 0
        if router and not rouovr1:
            router = 0
            
    if lcd and lcdon:
        
        display.fill(0)        
        display.text('T', 0, 0, 1)
        display.text('E', 0, 8, 1)
        display.text('M', 0, 16, 1)
        display.text('P', 0, 24, 1)
        
        display.text('W', 0, 36, 1)
        display.text('I', 0, 46, 1)
        display.text('G', 0, 56, 1)
        display.text('AKUM:', 60, 36, 1)
        
        if dec: draw_digit(dec, 15, scale=2)
        draw_digit(uni, 45, scale=2)
        draw_dot(72, scale=2)
        draw_digit(fra, 79, scale=2)
        
        if dech: draw_digit(dech, 15, 36, scale=4)
        draw_digit(unih, 30, 36, scale=4)
        display.text('%', 46, 36, 1)        
        
        if second % 2: show_heart(112, 0)
    
        display.text(str(hh) + ':' + str(mm), 15, 56, 1)
        display.text(str(bvolt) + 'V', 60, 46, 1)
        display.text(str(round(bamp/1000, 1)) + 'A', 60, 56, 1)
        
        if wlan.isconnected(): display.text('WI', 113, 24, 1)
        if ntpok: display.text('NT', 113, 14, 1)
        if servok: display.text('OK', 113, 34, 1)
        if modpin.value() == 1: display.text('MO', 113, 44, 1)
        if roupin.value() == 1: display.text('RT', 113, 54, 1)

    elif lcd:
        show_face(5)
        
    if lcd: display.show()
    
    if not minute % 15 and not second:
        getntp()
    
    if not pir.value():
        lcdcount += 1
        if lcdcount > 90 and lcdon:
            lcdon = False
            lcdcount = 0
        if lcdcount > 90 and not lcdon:
            display.poweroff()
    if pir.value() and not lcdon:
        display.poweron()
        lcdon = True
        lcdcount = 0
    if pir.value() and lcdon:
        lcdcount = 0
        
connect()
sleep(1)
getntp()
sleep(2)
tim.init(freq=1, mode=Timer.PERIODIC, callback=tick)
tim1.init(freq=0.015, mode=Timer.PERIODIC, callback=ch_conn)
(year, month, mday, wday, hour, minute, second, msecs) = rtc.datetime()
lrst = str(mday) + '.' + str(month) + '.' + str(year) + ' ' +str(hour) + ':' +str(minute)
#p20.irq(trigger=Pin.IRQ_FALLING, handler=p20_int)
#p21.irq(trigger=Pin.IRQ_FALLING, handler=p21_int)

from server import webserver

app = webserver()

@app.route('/')
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[0] % (str(t) + ';' + str(p) + '<br>' + 'MEM:' + str(mem_free()) + ';<br>ROUPIN: ' + str(roupin.value()) + ' MODPIN: '  + str(modpin.value()) + ';<br>ROUOVR: ' + str(rouovr1) + ' MODOVR: '  + str(modovr1) + ';<br>AVCUR: ' + str(avcur) + ' BAMP: '  + str(bamp) + ';<br>LAST RESTART: ' + lrst + ';<br><a href="resetconf">RESTART</a>;<br><a href="upgradeconf">UPGRADE</a>'))

@app.route('/params')
async def index(request, response):
    await response.start_html()
    await response.send(str(t) + ';' + str(p) + ';' + str(h))

@app.route('/pins')
# zwraca stan pinow sterujacych modemem i routerem
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[0] % (str(roupin.value()) + ';' + str(modpin.value()) + ';' + lrst.split(" ")[1]))

@app.route('/modem')
# zalacza modem na stale
async def index(request, response):
    global modovr1
    modovr1 = not modovr1
    print(modovr1)
    respstr = 'OK1' if modovr1 else 'OK0'
    await response.start_html()
    await response.send(_STRINGS[0] % respstr)
  
@app.route('/modemchk')
async def index(request, response):
    await response.start_html()
    respstr = 'OK1' if modovr1 else 'OK0'
    await response.send(_STRINGS[0] % respstr)

@app.route('/router')
# zalacza router na stale
async def index(request, response):
    global rouovr1
    rouovr1 = not rouovr1
    print(rouovr1)
    respstr = 'OK1' if rouovr1 else 'OK0'
    await response.start_html()
    await response.send(_STRINGS[0] % respstr)
   
@app.route('/routerchk')
async def index(request, response):
    await response.start_html()
    respstr = 'OK1' if rouovr1 else 'OK0'
    await response.send(_STRINGS[0] % respstr)
   
@app.route('/resetconf')
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[0] % _STRINGS[2] % 'reset')

@app.route('/reset')
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[0] % 'OK RESET')
    sleep(1)
    fwrite('1')
    machine.reset()
    
@app.route('/lockreset')
# zalacza router na stale
async def index(request, response):
    global modem, router
    await response.start_html()
    modem = 0
    router = 0
    #if not modovr1: modpin.value(0)
    #sleep(0.6)
    #if not rouovr1: roupin.value(0)
    respstr = 'OK ' + 'M=' + str(modem) + ' R=' + str(router)
    await response.send(_STRINGS[0] % respstr)

@app.route('/msolaroff')
async def index(request, response):
    global modem
    modem = 0
    modpin.value(0)
    await response.start_html()
    await response.send(_STRINGS[0] % 'OK')

@app.route('/upgradeconf')
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[0] % _STRINGS[1])
    
@app.route('/upgrade')
async def index(request, response):
    print('upgrade')
    tim.deinit()
    tim1.deinit()
    collect()
    await response.start_html()
    qs1 = request.query_string.decode('utf-8').split('=')[1]
    if qs1 == _PASSWD:
        print('passok')
        await response.send(_STRINGS[0] % 'downloading...')
        with open("_main.py", "wb") as f:
            print('start')
            for data_chunk in download_in_chunks(_URL):
                if data_chunk.startswith(_CTRL_STR1): init_str = True    
                f.write(data_chunk)
        await response.start_html()
        await response.send(_STRINGS[0] % ('downloaded...'))
        collect()
        print('downloaded')
        end_str = True
                
        if init_str and end_str:
            rename('_main.py', 'main.py')
            result_str = 'OK RENAME'
            #fileop('main.err', wr_error('NEW FIRMWARE\n'), 'a')
        
        await response.start_html()
        await response.send(_STRINGS[0] % result_str)
    else:
        await response.send(_STRINGS[0] % 'WRONG PASS')        
    tim.init(freq=1, mode=Timer.PERIODIC, callback=tick)
    tim1.init(freq=0.015, mode=Timer.PERIODIC, callback=ch_conn)

if wifi:
    app.run(host='0.0.0.0', port=1412)
else:
    print('Serwer zatrzymany')
    sleep(30)
    fwrite('1')
    machine.reset()
#--$FE--
