#!/bin/python2
# coding=UTF-8

from datetime import datetime
from sys import argv
from os.path import isfile
import signal
from time import sleep
from gph import gph_shoot, gph_open, gph_close, gph_cmd, gph_debug_set
from camera import camera_settings_get, camera_handler_get
from luminance import luminance_settings_get, luminance_calculate, luminance_estimate
from luminance_calculate import luminance_calculate
from configs import cfgs, infs, cfg_load
from monotonic_time import monotonic_time
from trigger_expose import trigger_capture, trigger_expose_bulb
import argparse

parser = argparse.ArgumentParser(description=('Start a timelapse with a '
    + 'connected camera.'))

parser.add_argument('--configuration', '-c',dest='cfgfile', required=False,
        type=argparse.FileType('r'))
parser.add_argument('--gphoto-log', '-g', dest='gphotolog', required=False,
        type=argparse.FileType('a', 1))
args = parser.parse_args()

daemon_alive = True

# Enable gph.
if args.gphotolog:
    print('Logging gphoto2 command to %s.' % args.gphotolog.name)
    gph_debug_set(args.gphotolog)

gph_open()

# Print camera model cause we're happy.
model=gph_cmd('get-config /main/status/cameramodel')
# Hack to sometimes get around some weird error.
if len(model) == 0:
    print('Failed getting camera model, reloading and trying again..')
    sleep(0.1)
    gph_close()
    sleep(0.1)
    gph_open()
    sleep(0.1)
    model=gph_cmd('get-config /main/status/cameramodel')

cameramodel = model[3].split(' ', 1)[1]
print('Camera: ' + cameramodel)
camera = camera_handler_get(cameramodel)

try:
    sc=gph_cmd('get-config /main/status/shuttercounter')
    print('Shutter counter: ' + sc[3].split(' ', 1)[1])

    im=gph_cmd('get-config /main/imgsettings/imageformat')
    print('Image format: ' + im[3].split(' ', 1)[1])

    wb=gph_cmd('get-config /main/imgsettings/whitebalance')
    print('White balance: ' + wb[3].split(' ', 1)[1])

    ps=gph_cmd('get-config /main/capturesettings/picturestyle')
    print('Picture style: ' + ps[3].split(' ', 1)[1])

    cs=gph_cmd('get-config /main/imgsettings/colorspace')
    print('Colour space: ' + cs[3].split(' ', 1)[1])
except IndexError:
    print("Couldn't retrieve some additional info from camera.")

# Configure camera
gph_cmd('set-config-index /main/settings/capturetarget=1')
gph_cmd('set-config-index /main/capturesettings/autoexposuremode=3') # Dial Manual
gph_cmd('set-config-index /main/capturesettings/shutterspeed=0') # Bulb
gph_cmd('set-config-index /main/capturesettings/drivemode=0') # Single

(aperture, iso, shutter) = camera_settings_get()

# End-of-timelapse command
def daemon_end(signum, frame):
    global daemon_alive
    daemon_alive = False
    print('Stopping camera control..')
    try:
        gph_cmd('set-config-index /main/actions/eosremoterelease=4') # Release Full
        gph_cmd('wait-event-and-download 3s', timeout=4) # Should download the image
    except IOError:
        print('IOError on gphoto2 --- camera probably unplugged.')
    gph_close()
    exit(0)

# Activate signal for terminating the daemon
signal.signal(signal.SIGTERM, daemon_end)


# Reference time for precise cycles
cycle_reftime = monotonic_time()

def sighup_handler(signum, frame):
    if not args.cfgfile:
        print('No configuration file to reload (received SIGHUP).')

    cv = cfgs['cycle']

    args.cfgfile.seek(0)
    cfg_load(fp=args.cfgfile)

    if cv != cfgs['cycle']:
        print('Cycle length changed, updating reftime.')
        cycle_reftime = monotonic_time()
    print('Reloaded configurations.')

# Reload conf signal
signal.signal(signal.SIGHUP, sighup_handler)

if args.cfgfile:
    cfg_load(fp=args.cfgfile)

print(cfgs)

# The accuracy errors should be at most 10%
bulb_min = 3
bulb_lag = 0.1
print("Bulb lag: {}, minimum bulb value: {}".format(bulb_lag, bulb_min))

while daemon_alive:
    t = monotonic_time()
    ref_delta = (t - cycle_reftime) % cfgs['cycle']
    remain = cfgs['cycle'] - ref_delta

    lumi_est=luminance_calculate('./')

    (t_aperture, t_iso, t_shutter, bulb) = luminance_settings_get(lumi_est, aperture,
            iso, shutter, iso_max=cfgs['iso_max'], shutter_max=cfgs['shutter_max'],
            shutter_min=(float(cfgs['shutter_min_num'])/cfgs['shutter_min_denom']),
            bulb_min=bulb_min)

    print('est:{} (aperture:{}, iso:{}, shutter:{}, bulb:{})'.format(lumi_est,
        aperture[t_aperture], iso[t_iso], shutter[t_shutter], bulb))

    # Get some status info from camera
    try:
        bat=gph_cmd('get-config /main/status/batterylevel')[3].split(' ', 1)[1]
        print('battery: ' + bat)
    except IndexError:
        print("Couldn't retrieve battery information.")

    # Configure the next frame
    gph_cmd('set-config-index /main/capturesettings/aperture=%i' % t_aperture)
    gph_cmd('set-config-index /main/imgsettings/iso=%i' % t_iso)
    # '1' sets to 1 second but '01' sets to 30 seconds (which is what we want)
    # Though set-config-index shouldn't have this problem.
    gph_cmd('set-config-index /main/capturesettings/shutterspeed=%02i' % t_shutter)

    sh=shutter[t_shutter]

    meta=[('LuminanceTarget', lumi_est)]

    try:
        if bulb != None:
            meta.append(('BulbLag', bulb_lag))
            of = trigger_expose_bulb(camera, bulb + bulb_lag, start_time = t + remain,
                    meta=meta)
        else:
            of = trigger_capture(camera, sh, start_time = t + remain,
                    meta=meta)
    except IOError:
        pass

# Our job here is done
gph_close()

