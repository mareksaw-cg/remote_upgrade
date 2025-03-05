#--version0.997.5_050325--
# UWAGA!!! Przy bledach wskazania napiecia INA219 sprawdz poprawnosc polaczenia masy zasilania!!!
# UWAGA!!! Sprawdz czy zapisujesz plik na urzadzeniu czy w OneDrive! Objaw - program dziala w Thonny a nie dziala po restarcie!
try:
    f = open('main.py', 'r')
    line1 = f.readline().split('--')[1][7:]
    f.close()
except:
    line1 = 'error'
    
from micropython import const

_STRINGS = const(("""<!DOCTYPE html>
<html>
    <head><title>Parametry stacji zasilania</title><meta http-equiv="refresh" content="600"></head>
    <body><h1>Aktualne parametry:</h1>
        <table border="1"> <tr><th>PAR</th><th>U[V]</th><th>I[mA]</th></tr> %s </table>
    </body>
</html>
""", """<!DOCTYPE html>
<html>
    <head></head>
    <body>%s</body>
</html>
""", """<form action="%s">
    <input type="submit" value="CHANGE" />
</form>
""", """<form action="%s">
    <input type="submit" value="RESET" />
</form>
""", """<form action="/chpwrite">
  <label for="chpval">CHP=&nbsp;</label>
  <input type="text" id="chpval" name="chpval">&nbsp;&nbsp;
  <input type="submit" value="USTAW">
</form>
""", """<form action="/upgrade">
  <label for="pwd">Passwd:</label>
  <input type="password" id="pwd" name="pwd" minlength="5">&nbsp;&nbsp;
  <input type="submit" value="UPGRADE">
</form>
""", """<form action="/readsrcconf">
  <label for="pwd">Passwd:</label>
  <input type="password" id="pwd" name="pwd" minlength="5">&nbsp;&nbsp;
  <input type="submit" value="DOWNLOAD">
</form>
""", """<form action="/readerrconf">
  <label for="pwd">Passwd:</label>
  <input type="password" id="pwd" name="pwd" minlength="5">&nbsp;&nbsp;
  <input type="submit" value="DOWNLOAD">
</form>
""", "https://raw.githubusercontent.com/mareksaw-cg/remote_upgrade/main/clock_8x8/w5500/main.py", "zp987-", "#--version"))

#_PASSWD = const('zp987-')
#_SRCURL = const('https://onedrive.live.com/download?resid=7A40866E01A106BA%21137386&authkey=!AKX-JpKATav5IZ8')
#_SRCURL = const('https://raw.githubusercontent.com/mareksaw-cg/remote_upgrade/main/clock_8x8/w5500/main.py')
#_CTRL_STR1 = const('#--version')
#ctrl_str2 = (chr(36) + chr(70) + chr(69) + chr(45) + chr(45)).encode()

from machine import I2C, Pin
from gc import collect, mem_free

wdten = True
lan = True

beeppin = Pin(28, Pin.OUT)
pir = Pin(2, Pin.IN)
led = Pin(25 if lan else 'LED', Pin.OUT, value=1)
#tvin = Pin(9, Pin.IN, Pin.PULL_UP)
#chr_en = Pin(5, Pin.OUT, value=0)

i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
i2cscan = i2c.scan()

inaok = False
ina2ok = False

if 64 or 69 in i2cscan:
    try:
        collect()
        from ina219l import INA219
        if 64 in i2cscan:
            ina = INA219(0.1, i2c, 3.1, 0x40)
            inaok = True
            ina.configure()
            print('INA OK')
        if 69 in i2cscan:
            ina2 = INA219(0.1, i2c, 3.1, 0x45)
            ina2ok = True
            ina2.configure()
            print('INA2 OK')        
    except:
        print('can not import ina219')
        
else:
    print('no INA219')
    
if 56 in i2cscan:
    try:
        collect()
        from pcf8574 import PCF8574
        pcf = PCF8574(i2c, 0x38)
        print('pcf ok')
        pcfok = True
    except:
        print('pcf error')
        pcfok = False
else:
    print('no pcf')
    pcfok = False    
    
if 35 in i2cscan:
    try:
        collect()
        from bh1750 import BH1750
        print('bh ok')
        bh = BH1750(i2c)
        bh.set_mode(BH1750.CONT_LOWRES)
        bhok = True
    except:
        print('bh1750 error')
        bhok = False
else:
    print('no bh')
    bhok = False
    
if 60 in i2cscan:
    collect()
    try:
        from ssd1306 import SSD1306_I2C
        lcddisplay = SSD1306_I2C(128, 64, i2c)
        lcddisplay.fill(0)
        lcddisplay.text('Boot OK', 0, 0, 1)
        if inaok and ina2ok: lcddisplay.text('INA OK', 0, 10, 1)
        lcddisplay.show()
        lcd = True
        print('LCD OK')
    except:
        lcd = False
else:
    print('no lcd')
    lcd = False
    
collect()

from machine import SPI, Timer, RTC, WDT
from network import WIZNET5K #, STA_IF, AP_IF

rtc = RTC()

wlan = WIZNET5K()
wlan.active(True)

spi = SPI(1, baudrate=1000000, polarity=0, phase=0, sck=Pin(14), mosi=Pin(15))
cs = Pin(13, Pin.OUT)

from max7219 import Matrix8x8

display = Matrix8x8(spi, cs, 4)
display.brightness(0)
display.text('Glup', 0, 0, 1)
display.show()
    
lcdcount = int(0)
rstcount = int(0)
curcount = int(0)
lmove = 'RESET'
lcdon = True
ntpok = False
wifi = False
modovr = False
rouovr = False
roupin = False
modpin = False
pcf0count = int(0)
p13 = int(0)

volt = 0
amp = 0
volt2 = 0
amp2 = 0
qs = '0;0'
clr = ''

init_str = False
end_str = False
result_str = 'GENERAL ERROR'
proceed = False

f = open('backup.dat')
enday, outday, glk, nlk, pws, chp, ch_en, sau, pau, tvmins, frdisable, pcf0 = [int(i) for i in f.read().split(';')]
f.close()

print(enday, outday, glk, nlk, pws, chp, ch_en, sau, pau, tvmins, frdisable, pcf0)

collect()

from time import sleep
import ntptimerp3 as ntptimem
from urequests import get as urequestsget
from os import rename, remove
from uping import ping

def flash(dur):
    led.on()
    sleep(dur)
    led.off()

def beep(repeat=1, duration=0.06, pause=0.3):
    for n in range(repeat):
        beeppin.value(1)
        sleep(duration)
        beeppin.value(0)
        sleep(pause)

def checksum(msg):
    v = 21
    for c in msg: v ^= ord(c)
    return v

def getntp1():
    print('getntp')
    global ntpok
    ntpok = False
    if wlan.isconnected():
        if ntptimem.settime():
            ntpok = True
            
def show8x8(hour, minute, second, ntpstate):    
    
    display.fill(0)
    
    if lcdon:    
        display.text(str(hour // 10), 1, 0, 1)
        display.text(str(hour % 10), 8, 0, 1)
        display.text(str(minute // 10), 17, 0, 1)
        display.text(str(minute % 10), 24, 0, 1)
        display.vline(0, 0, (second // 7), 1)
        
        if second % 2:
            display.pixel(16, 2, 1)
            display.pixel(16, 5, 1)
            
        if ntpstate:
            display.pixel(31, 7, 1)

    display.show()
'''
def wr_backup():
    f = open('backup.dat', 'w')
    f.write(str(int(enday)) + ';' + str(int(outday)) + ';' + str(int(glk))  + ';' + str(int(nlk)) + ';' + str(int(pws)) + ';' + str(int(chp)) + ';' + str(int(ch_en)) + ';' + str(int(sau)) + ';' + str(int(pau)) + ';' + str(int(tvmins)) + ';' + str(int(frdisable)) + ';' + str(int(pcf0)))
    f.close()
'''    
def fileop(path, content, action):
    with open(path, action) as f:
        f.write(content)
        
def wr_error(msg):
    return str(mday) + '.' + str(month) + '.' + str(year) + ' ' + str(hh) + ':' + str(mm) + '.' + str(ss) + '    ' + msg
    
def get_pins():
    print('pins')
    global roupin, modpin, clr
    r = urequestsget("http://10.0.0.56:1412/pins", timeout=2)
    data = r.content
    r.close()
    if ';' in data:
        data = data.decode().split('<body>')[1].split('</body>')[0].split(';')
        roupin = bool(int(data[0]))
        modpin = bool(int(data[1]))
        clr = data[2]
        
def switch_solar():
    global pws
    pws = not pws
    sstr = '/solar1' if pws else '/mains1'
    r = urequestsget("http://10.0.0.8:8099" + sstr, timeout=3)
    data = r.content
    r.close()
    if 'SOLAR' in data: pws = True
    if 'MAINS' in data: pws = False
'''    
def tickwdt(timer):
    wdt.feed()
'''    
def send_signal(msg):
    r = urequestsget("http://10.0.0.13:8041/signal?msg=" + msg.replace(' ', '+'), timeout=3)
    sleep(0.1)
    r.close()
    
def reset_cat():
    global modovr, rouovr
    modovr = False
    rouovr = False
    r = urequestsget("http://10.0.0.56:1412/reset", timeout=3)
    data = r.content
    r.close()
    return data

def download_in_chunks(url, chunk_size=512):
    global result_str, proceed
    try:
        response = urequestsget(url, stream=True, timeout=4)
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

def tick(timer):

    global year, month, mday, hh, mm, ss, volt2, amp2, volt, amp, chp, lcdon, lcdcount, enday, outday, lux, lmove, pcf0, pcf0count, pws, sau, pau, rstcount, tvmins, curcount, frdisable, rping, p13

    wdt.feed()
    (year, month, mday, wday, hh, mm, ss, msecs) = rtc.datetime()
    
    sound = True
    
    if not pir.value():
        lcdcount+= 1 if lcdcount < 62 else 0
        if lcdcount == 62:
            sound = False
            if lcdon:
                lcdon = False
                display.off()
                print('disp off')
                if lcd: lcddisplay.poweroff()
    else:
        lmove = str(hh) + ':' + str(mm)
        lcdcount = 0
        if not lcdon:
            lcdon = True
            display.init()
            print('disp on')
            if lcd: lcddisplay.poweron()
    
    show8x8(hh, mm, ss, ntpok)
    
    '''
    Pomiar energii
    '''
    if inaok and ina2ok:
        #PARAMETRY SOLAR
        volt = round(ina.supply_voltage(), 2)
        amp = ina.current()
        pows = volt * amp
        enday += pows
        #PARAMETRY AKU
        volt2 = round(ina2.supply_voltage(), 2)
        amp2 = ina2.current()
        powa = volt2 * amp2
        if amp2 < 0:
            outday += (0.7 * powa)
        else:
            outday += powa        
    
    print(lcdcount, lcdon, hh, mm, ss, volt, amp, volt2, amp2, pows/1000, powa/1000, enday, outday, pcf0, pws, sau, frdisable)
    
    if volt2 < 12.2 and modpin and not modovr:
        r = urequestsget("http://10.0.0.56:1412/msolaroff", timeout=3)
        data = r.content
        r.close()
        sleep(0.5)
        get_pins()
    
    if ss == 0:
        
        collect()
        
        rstcount += 1
        if rstcount == 10:
            app.shutdown()
            sleep(1)
            app.run(host='0.0.0.0', port=1411)
        if rstcount > 19:
            fileop('main.err', wr_error('server not responding\n'), 'a')
            machine.reset()
        
        if not mm % 15:
            if not mm and sound: beep(1, 0.35, 0)
            elif sound: beep(mm // 15)
            if modovr:
                if not ping('8.8.8.8', count=1, timeout=400, quiet=True)[1]:
                    reset_cat()
                    fileop('main.err', wr_error('CAT RESET NO PING AND MODOVR\n'), 'a')
            
        if volt > 20.9 and ((pows - (int(pws) * 6000)) < abs(powa)):
            reset_cat()
            fileop('main.err', wr_error('ROUTER RELAY ERROR'), 'a')
            
        if amp == 0 and amp2 == 0:
            curcount += 1
        else:
            curcount = 0
        if curcount > 5:
            fileop('main.err', wr_error('INA reading zeros\n'), 'a')
            machine.reset()

    if ss == 5:
        print('chk tv/backup/ntp')
        rping = ping('10.0.0.95', count=1, timeout=400, quiet=True)[1]
        if rping:
            tvmins += 1
            if not frdisable:
                frdisable = True
                r = urequestsget("http://10.0.0.8:8099/frstop", timeout=1)
                data = r.content
                r.close()

        if not rping and frdisable:
            frdisable = False
            r = urequestsget("http://10.0.0.8:8099/frstart", timeout=1)
            data = r.content
            r.close()
            
        if mm and not mm % 11:
            display.init()
            fileop('backup.dat', str(int(enday)) + ';' + str(int(outday)) + ';' + str(int(glk))  + ';' + str(int(nlk)) + ';' + str(int(pws)) + ';' + str(int(chp)) + ';' + str(int(ch_en)) + ';' + str(int(sau)) + ';' + str(int(pau)) + ';' + str(int(tvmins)) + ';' + str(int(frdisable)) + ';' + str(int(pcf0)), 'w')
            getntp1()
        
    if hh == 23 and mm == 59 and ss > 57:
        
        ina.reset()
        ina2.reset()
        ina.configure()
        ina2.configure()
        if bhok:
            bh.off()
            bh.reset()
        enday = 0
        outday = 0
        chp = -800
        tvmins = 0
        fileop('backup.dat', str(int(enday)) + ';' + str(int(outday)) + ';' + str(int(glk))  + ';' + str(int(nlk)) + ';' + str(int(pws)) + ';' + str(int(chp)) + ';' + str(int(ch_en)) + ';' + str(int(sau)) + ';' + str(int(pau)) + ';' + str(int(tvmins)) + ';' + str(int(frdisable)) + ';' + str(int(pcf0)), 'w')
        
    if not ss % 15:
        try:
            lux = int(bh.luminance(BH1750.CONT_LOWRES)) if bhok else 0
        except:
            lux = 200
        bright = 15 if lux // 250 > 15 else lux // 250
        if lcdon: display.brightness(bright)
                     
    if not ss % 2:
        if lcd and lcdon:
            lcddisplay.fill(0)
            lcddisplay.text('L=' + str(lux) + 'lx W:' + str(wlan.isconnected()), 0, 0, 1)
            lcddisplay.text('U=' + str(volt) + 'V' + ' I=' + str(amp) + 'mA', 0, 12, 1)
            lcddisplay.text('+E=' + str(round(enday / 3600000, 3)) + 'Wh', 0, 24, 1)
            lcddisplay.text('BAT:-E=' + str(round(outday / 3600000, 3)) + 'Wh', 0, 44, 1)
            lcddisplay.text('U=' + str(volt2) + 'V' + ' I=' + str(amp2) + 'mA', 0, 56, 1)
            lcddisplay.text('.', (ss // 8) * 8, 32, 1)
            lcddisplay.show()
        
    if ss == 11 or ss == 41:
        if sau:
            if not pws and volt > 19.3:
                switch_solar()
                print('solar on')
            if pws and amp2 > chp:
                switch_solar()
                print('solar off')
    '''                
    if ss == 20 and not mm % 2:
        refvolt = volt
        if pau:
            if volt > 18.31 and amp2 <= chp and amp2 < 0:
    #            chp = - (abs(amp2) // 100) * 100
                chp = amp2 + 150
                if chp > 0: chp = 0

    if ss == 21 or ss == 51:            
        if pau:
            if volt > 18.31 and amp2 < 0 and amp2 > chp:
                chp = amp2 + 100
                if chp > 0: chp = 0
#                chp += 100 if chp < 0 else 0
                paucount += 1
            else:
                paucount = 0
    '''
    if ss == 19 or ss == 49:        
        if pau and volt > 18.26 and amp2 < 0:
                chp = amp2 + 125
                if chp > 0: chp = 0        
        
        get_pins()
        
        if not pcf0 and roupin and (modpin or nlk) and volt > 19.01:
            pcf0count += 1
            if pcf0count == 3:
                pcf0 = True
                pcf.pin(0, pcf0)
                
        if pcf0 and not roupin and not modpin and amp2 > chp:
            pcf0count -= 1
            if pcf0count == 0:
                pcf0 = False
                pcf.pin(0, pcf0)
            pcf0count = 0 if pcf0count < 0 else pcf0count
    
    flash(0.01)   
'''
Koniec obslugi timera
'''
led.off()
beep(1, 0.01)

while not wlan.isconnected():
    print('waiting for lan')
    sleep(1)

wifi = True
print('ifconf:', wlan.ifconfig())

display.fill(0)
display.text('IP', 0, 0, 1)
display.show()

while not ntpok:
    getntp1()
    sleep(0.5)
    
print('ntp ok')
display.text('NT', 16, 0, 1)
display.show()

(year, month, mday, wday, hh, mm, ss, msecs) = rtc.datetime()
rsttime = str(hh) + ':' + str(mm) + ' ' + str(ss)

collect()
tim = Timer()

from server import webserver

app = webserver()

@app.route('/msmsms')
async def index(request, response):
    print('serwer')
    global rstcount
    await response.start_html()
    rows = ['<tr><td>%s</td><td>%s</td><td>%d</td></tr>' % ('PVM', volt, amp), '<tr><td>%s</td><td>%s</td><td>%d</td></tr>' % ('BAT', volt2, amp2), '<tr><td>%s</td><td colspan="2">%s</td></tr>' % ('+E', round(enday / 3600000, 3)), '<tr><td>%s</td><td colspan="2">%s</td></tr>' % ('-E', round(outday / 3600000, 3)), '<tr><td>%s</td><td colspan="2">%s</td></tr>' % ('POW', round((volt * amp / 1000), 1)), '<tr><td>%s</td><td colspan="2">%s</td></tr>' % ('POB', round((volt2 * amp2 / 1000), 1)), '<tr><td><a href="modemconf">%s</a></td><td colspan="2">%s</td></tr>' % ('MOV', str(modovr)), '<tr><td><a href="routerconf">%s</a></td><td colspan="2">%s</td></tr>' % ('ROV', str(rouovr)), '<tr><td><a href="glockconf">%s</a></td><td colspan="2">%s</td></tr>' % ('GLK', str(glk)), '<tr><td><a href="nlockconf">%s</a></td><td colspan="2">%s</td></tr>' % ('MLK', str(nlk)), '<tr><td>%s</td><td colspan="2">%s</td></tr>' % ('QST', qs), '<tr><td><a href="pwrswconf">%s</a></td><td colspan="2">%s</td></tr>' % ('PWS', str(pws)), '<tr><td><a href="solautconf">%s</a></td><td colspan="2">%s</td></tr>' % ('SAU', str(sau)), '<tr><td><a href="chpset">%s</a></td><td colspan="2">%s</td></tr>' % ('CHP', str(chp)), '<tr><td><a href="priautconf">%s</a></td><td colspan="2">%s</td></tr>' % ('PAU', (str(pau))),'<tr><td>%s</td><td colspan="2">%s</td></tr>' % ('TON', str(rping)), '<tr><td>%s</td><td colspan="2">%s</td></tr>' % ('TVT', str(tvmins)), '<tr><td>%s</td><td colspan="2">%s</td></tr>' % ('FRD', str(frdisable)), '<tr><td>%s</td><td colspan="2">%s</td></tr>' % ('P13', str(p13)), '<tr><td>%s</td><td colspan="2">%s</td></tr>' % ('LUX', str(lux)), '<tr><td><a href="resetconf">%s</a></td><td colspan="2">%s</td></tr>' % ('LRS', (rsttime + ';' + str(rstcount))), '<tr><td><a href="catreset">%s</a></td><td colspan="2">%s</td></tr>' % ('CLR', clr), '<tr><td>%s</td><td colspan="2">%s</td></tr>' % ('LMV', lmove), '<tr><td><a href="pcf0conf">%s</a></td><td colspan="2">%s</td></tr>' % ('PC0', str(pcf0)), '<tr><td>%s</td><td colspan="2">%s</td></tr>' % ('PIN', str(roupin) + ';' + str(modpin)), '<tr><td>%s</td><td colspan="2">%s</td></tr>' % ('FWV', line1), '<tr><td>%s</td><td colspan="2"><a href="readsrc">%s</a></td></tr>' % ('SRC', 'READ'), '<tr><td>%s</td><td colspan="2"><a href="readerrconf">%s</a></td></tr>' % ('ERR', 'READ'), '<tr><td>%s</td><td colspan="2"><a href="upgradeconf">%s</a></td></tr>' % ('FMW', 'UPGRADE'), '<tr><td>%s</td><td colspan="2"><a href="alert">%s</a></td></tr>' % ('ALM', 'START'), '<tr><td>%s</td><td colspan="2">%s</td></tr>' % ('MEM', str(mem_free())), '<tr><td>%s</td><td colspan="2">%s</td></tr>' % ('LDT', str(hh) + ':' + str(mm) + ' ' + str(ss))]
    sresponse = _STRINGS[0] % '\n'.join(rows)
    await response.send(sresponse)
    rstcount = 0
'''  
@app.route('/beep')
async def index(request, response):
    await response.start_html()
    beep(2)
    await response.send(_STRINGS[1] % 'OK')
'''   
@app.route('/alert')
async def index(request, response):
    await response.start_html()
    beep(10, 0.5, 0.5)
    await response.send(_STRINGS[1] % 'OK')
   
@app.route('/time')
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[1] % (str(hh) + ':' + str(mm) + '.' + str(ss)))
'''
@app.route('/data')
async def index(request, response):
    global qs
    print(qs)
    await response.start_html()
    await response.send(html1 % qs)
'''
@app.route('/routerconf')
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[1] % _STRINGS[2] % 'router1')

@app.route('/router1')
async def index(request, response):
    global rouovr
    r = urequestsget("http://10.0.0.56:1412/router", timeout=3)
    data = r.content
    r.close()
    if 'OK1' in data: rouovr = True
    if 'OK0' in data: rouovr = False
    await response.start_html()
    await response.send(_STRINGS[1] % 'OK')
    
@app.route('/modemconf')
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[1] % _STRINGS[2] % 'modem1')

@app.route('/modem1')
async def index(request, response):
    global modovr
    r = urequestsget("http://10.0.0.56:1412/modem", timeout=3)
    data = r.content
    r.close()
    if 'OK1' in data: modovr = True
    if 'OK0' in data: modovr = False
    await response.start_html()
    await response.send(_STRINGS[1] % 'OK')

@app.route('/glock1')
async def index(request, response):
    global glk
    await response.start_html()
    glk = not glk
    await response.send(_STRINGS[1] % 'OK')

@app.route('/glockconf')
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[1] % _STRINGS[2] % 'glock1')
'''
@app.route('/tvlockconf')
async def index(request, response):
    await response.start_html()
    await response.send(html1 % buthtml % 'tvlock1')
    
@app.route('/tvlock1')
# ustawia blokade zalaczenia chromecasta
async def index(request, response):
    global ch_en
    await response.start_html()
    ch_en = not ch_en
    chr_en.value(ch_en)
    await response.send(html1 % 'OK')
'''
@app.route('/pwrswconf')
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[1] % _STRINGS[2] % 'pwrsw')

@app.route('/pwrsw')
async def index(request, response):
    switch_solar()
    await response.start_html()
    await response.send(_STRINGS[1] % 'OK')
    
@app.route('/resetconf')
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[1] % _STRINGS[3] % 'reset')

@app.route('/reset')
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[1] % 'OK RESET')
    sleep(1)
    fileop('main.err', wr_error('RESET via web\n'), 'a')
    machine.reset()

@app.route('/nlock1')
async def index(request, response):
    global nlk
    await response.start_html()
    nlk = not nlk
    await response.send(_STRINGS[1] % 'OK')

@app.route('/nlockconf')
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[1] % _STRINGS[2] % 'nlock1')
    
@app.route('/pcf0')
async def index(request, response):
    global pcf0
    pcf0 = not pcf0
    pcf.pin(0, pcf0)
    await response.start_html()
    await response.send(_STRINGS[1] % 'OK' + str(pcf0))
    
@app.route('/pcf0conf')
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[1] % _STRINGS[2] % 'pcf0')
    
@app.route('/solaut')
async def index(request, response):
    global sau
    await response.start_html()
    sau = not sau
    await response.send(_STRINGS[1] % 'OK' + str(sau))
    
@app.route('/solautconf')
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[1] % _STRINGS[2] % 'solaut')
    
@app.route('/priaut')
async def index(request, response):
    global pau
    await response.start_html()
    pau = not pau
    await response.send(_STRINGS[1] % 'OK' + str(pau))
    
@app.route('/priautconf')
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[1] % _STRINGS[2] % 'priaut')
        
@app.route('/chpwrite')
async def index(request, response):
    global chp
    await response.start_html()
    qs1 = request.query_string.decode('utf-8')
    qs1 = qs1.split('=')[1]
    if qs1: chp = int(qs1)
    if chp > 0: chp = 0
    await response.send(_STRINGS[1] % 'OK' + str(chp))
    
@app.route('/signal')
async def index(request, response):
    await response.start_html()
    qs1 = request.query_string.decode('utf-8')
    qs = qs1.split('=')
    print('send signal')
    if qs[0] == 'msg': send_signal(qs[1])
    await response.send(_STRINGS[1] % 'OK' + qs[1])
    
@app.route('/chpset')
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[1] % _STRINGS[4])
    
@app.route('/parameters')
async def index(request, response):
    print('parameters')
    global qs, rstcount, modpin, roupin
    qs = request.query_string.decode('utf-8')
    if qs != '':
        print(qs)
        partemp = qs.split(';')
        roupin = bool(int(partemp[2]))
        modpin = bool(int(partemp[3]))
    pstring = str(volt) + ';' + str(amp) + ';' + str(volt2) + ';' + str(amp2) + ';' + str(glk) + ';' + str(nlk) + ';' + str(chp) + ';' + str(rouovr) + ';OK'
    await response.start_html()
    await response.send(_STRINGS[1] % pstring)
    rstcount = 0
    
@app.route('/catreset')
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[1] % _STRINGS[2] % 'catreset1')

@app.route('/catreset1')
async def index(request, response):
    await response.start_html()
    data = reset_cat()
    if 'OK' in data: await response.send(_STRINGS[1] % 'OK')    
    
@app.route('/readsrcconf')
async def index(request, response):
    collect()
    qs1 = request.query_string.decode('utf-8').split('=')[1]
    if qs1 == _STRINGS[9]: await response.send_file('main.py', max_age=0)
    
@app.route('/readsrc')
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[1] % _STRINGS[6])

@app.route('/readerrconf')
async def index(request, response):
    collect()
    #qs1 = request.query_string.decode('utf-8').split('=')[1]
    #if qs1 == _PASSWD: await response.send_file('main.err', max_age=0)
    await response.send_file('main.err', max_age=0)
'''    
@app.route('/readerr')
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[1] % _STRINGS[7])
'''
@app.route('/upgradeconf')
async def index(request, response):
    await response.start_html()
    await response.send(_STRINGS[1] % _STRINGS[5])

@app.route('/upgrade')
async def index(request, response):
    tim.deinit()
    collect()
    await response.start_html()
    qs1 = request.query_string.decode('utf-8').split('=')[1]
    if qs1 == _STRINGS[9]:
        await response.send(_STRINGS[1] % 'downloading...')
        with open("_main.py", "wb") as f:
            print('start')
            for data_chunk in download_in_chunks(_STRINGS[8]):
                if data_chunk.startswith(_STRINGS[10]): init_str = True    
                f.write(data_chunk)
                wdt.feed()
        await response.start_html()
        await response.send(_STRINGS[1] % ('downloaded...'))
        collect()
        print('downloaded')
        end_str = True
                
        if init_str and end_str:
            rename('_main.py', 'main.py')
            result_str = 'OK RENAME'
            fileop('main.err', wr_error('NEW FIRMWARE\n'), 'a')
        
        await response.start_html()
        await response.send(_STRINGS[1] % result_str)
    else:
        await response.send(_STRINGS[1] % 'WRONG PASS')        
    tim.init(freq=1, mode=Timer.PERIODIC, callback=tick)

lux = int(bh.luminance(BH1750.CONT_LOWRES)) if bhok else 0
rping = ping('10.0.0.95', count=1, timeout=300, quiet=True)[1]
p13 = ping('10.0.0.13', count=1, timeout=300, quiet=True)[1]

if wdten: wdt = WDT(timeout=8001)

fileop('main.err', wr_error('START\n'), 'a')

try:
    send_signal('W5500 RESTART')
except:
    fileop('main.err', wr_error('SIGNAL send error\n'), 'a')

tim.init(freq=1, mode=Timer.PERIODIC, callback=tick)
'''
if not lan:
    tim1 = Timer()
    tim1.init(freq=0.0025, mode=Timer.PERIODIC, callback=ch_conn)
'''    
if wifi:
    app.run(host='0.0.0.0', port=1411)
    print('serwer uruchomiony')
else:
    print('Serwer zatrzymany')
    sleep(30)
    fileop('main.err', wr_error('no network after boot\n'), 'a')
    machine.reset()
#'<tr><td><a href="tvlockconf">%s</a></td><td colspan="2">%s</td></tr>' % ('CHD', str(ch_en)), 
#--$FE--
