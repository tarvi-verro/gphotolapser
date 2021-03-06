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
from configs import cfgs, infs, cfg_load, cfg_write
from monotonic_time import monotonic_time
from trigger_expose import trigger_capture, trigger_expose_bulb
from math import floor
import argparse

parser = argparse.ArgumentParser(description=('Start a timelapse with a '
    + 'connected camera.'))

parser.add_argument('--configuration', '-c',dest='cfgfile', required=False,
        type=argparse.FileType('r'))
parser.add_argument('--gphoto-log', '-g', dest='gphotolog', required=False,
        type=argparse.FileType('a', 1))
parser.add_argument('--configuration-template', '-t', action='store_true', dest='template',
        required=False, help='create configuration template timelapse.conf '
        + 'and exit')
args = parser.parse_args()

daemon_alive = True

# Export the template
if args.template:
    cfg_write(f='timelapse.conf', signalservice=False);
    print('Exported configuration template \'timelapse.conf\'.');
    exit(0)

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


# Reference time for precise cycles. The offset of '+ 5' makes sure that the
# beginning of the first cycle starts sooner than cfgs['cycle'] seconds.
#
cycle_reftime = monotonic_time() + 5

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

def expose(start_time, meta, bulb):
    try:
        if bulb != None:
            meta.append(('BulbLag', cfgs['bulb_lag']))
            of = trigger_expose_bulb(camera, bulb + cfgs['bulb_lag'],
                    start_time = start_time, meta=meta,
                    download_timeout=cfgs['download_timeout'])
        else:
            of = trigger_capture(camera, sh, start_time = start_time,
                    meta=meta, download_timeout=cfgs['download_timeout'])
    except IOError:
        pass


while daemon_alive:
    t = monotonic_time()
    ref_delta = (t - cycle_reftime) % cfgs['cycle']
    remain = cfgs['cycle'] - ref_delta

    lumi_est=luminance_calculate('./')

    (t_aperture, t_iso, t_shutter, bulb) = luminance_settings_get(lumi_est, aperture,
            iso, shutter, iso_max=cfgs['iso_max'], shutter_max=cfgs['shutter_max'],
            shutter_min=(float(cfgs['shutter_min_num'])/cfgs['shutter_min_denom']),
            bulb_min=cfgs['bulb_min'])

    # Get some status info from camera
    status=''
    try:
        bat=gph_cmd('get-config /main/status/batterylevel')[3].split(' ', 1)[1]
        status += ' battery: ' + bat
    except IndexError:
        print("Couldn't retrieve battery information.")

    # Configure the next frame
    gph_cmd('set-config-index /main/capturesettings/aperture=%i' % t_aperture)
    gph_cmd('set-config-index /main/imgsettings/iso=%i' % t_iso)
    # '1' sets to 1 second but '01' sets to 30 seconds (which is what we want)
    # Though set-config-index shouldn't have this problem.
    gph_cmd('set-config-index /main/capturesettings/shutterspeed=%02i' % t_shutter)

    sh=shutter[t_shutter]

    meta=[('LuminanceTarget', lumi_est), ('CycleRefTime', cycle_reftime)]

    # Calculate number of extras
    shutter_speed = sh
    if bulb != None:
        shutter_speed = bulb + cfgs['bulb_lag']

    t_capture = shutter_speed + cfgs['download_timeout']
    extras_possible = max(0, int(floor(cfgs['cycle'] / t_capture)) - 1)
    extras = min(cfgs['extras_per_cycle'], extras_possible)
    n = extras + 1

    # Print info about frame to be taken
    print('est:{} (aperture:{}, iso:{}, shutter:{}, bulb:{}, n:{}),{}'.format(lumi_est,
        aperture[t_aperture], iso[t_iso], shutter[t_shutter], bulb, n,
        status))

    # Take the picture(s)
    cycle_start = t + remain
    last_frame = cycle_start + cfgs['cycle'] / n * extras
    t = monotonic_time()

    while t < last_frame:
        frame_ref_delta = (t - cycle_start) % (cfgs['cycle'] / n)
        frame_remain = cfgs['cycle'] / n - frame_ref_delta
        frame_start = t + frame_remain

        expose(frame_start, meta, bulb)
        t = monotonic_time()

# Our job here is done
gph_close()

