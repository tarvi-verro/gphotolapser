#!/bin/python2
# coding=UTF-8

from datetime import datetime
import signal
from time import sleep
from gph import gph_shoot, gph_open, gph_close, gph_cmd
from math import pi, ceil
from camera import camera_settings_get
from luminance import luminance_settings_get, luminance_calculate, luminance_estimate, luminance_settings_get_bulb
from luminance_calculate import luminance_calculate
from configs import cfgs, infs, cfg_load
from monotonic_time import monotonic_time, monotonic_alarm

daemon_alive = True

# Enable gph.
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

print(model[2])

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
    cv = cfgs['cycle']
    cfg_load()
    if cv != cfgs['cycle']:
        print('Cycle length changed, updating reftime.')
        cycle_reftime = monotonic_time()
    print('Reloaded configurations.')

# Reload conf signal
signal.signal(signal.SIGHUP, sighup_handler)

cfg_load()

print(cfgs)


while daemon_alive:
    t = monotonic_time()
    ref_delta = (t - cycle_reftime) % cfgs['cycle']
    remain = cfgs['cycle'] - ref_delta

    lumi_est=luminance_calculate('/srv/camera')

    (t_aperture, t_iso, t_shutter) = luminance_settings_get(lumi_est, aperture,
            iso, shutter, iso_max=cfgs['iso_max'], shutter_max=cfgs['shutter_max'],
            shutter_min=(float(cfgs['shutter_min_num'])/cfgs['shutter_min_denom']))

    t_bulb = luminance_settings_get_bulb(lumi_est, aperture[t_aperture], iso[t_iso],
            shutter_max=cfgs['shutter_max'],
            shutter_min=(float(cfgs['shutter_min_num'])/cfgs['shutter_min_denom']))

    print('est:{} (aperture:{}, iso:{}, shutter:{}, bulb:{})'.format(lumi_est,
        aperture[t_aperture], iso[t_iso], shutter[t_shutter], t_bulb))

    gph_cmd('set-config-index /main/capturesettings/aperture=%i' % t_aperture)
    gph_cmd('set-config-index /main/imgsettings/iso=%i' % t_iso)
    # '1' sets to 1 second but '01' sets to 30 seconds (which is what we want)
    # Though set-config-index shouldn't have this problem.
    gph_cmd('set-config-index /main/capturesettings/shutterspeed=%02i' % t_shutter)

    sh=shutter[t_shutter]

    monotonic_alarm(t + remain)
    if False:
        gph_cmd('set-config-index /main/actions/eosremoterelease=2') # Press Full
        sleep(0.2)
        gph_cmd('set-config-index /main/actions/eosremoterelease=4') # Release Full

        gph_cmd('wait-event-and-download %is' % (ceil(sh) + 3),
                timeout=(ceil(sh) + 3.5)) # Should download the image
    else:
        if t_bulb > 5.0:
            gph_cmd('set-config-index /main/capturesettings/shutterspeed=0') # Bulb
            t = monotonic_time()
            gph_cmd('set-config /main/actions/bulb=1')
            monotonic_alarm(t + t_bulb)
            gph_cmd('set-config /main/actions/bulb=0')
            gph_cmd('wait-event-and-download %is' % (ceil(sh) + 3),
                    timeout=(ceil(sh) + 3.5)) # Should download the image
        else:
            gph_cmd('capture-image-and-download', timeout=(ceil(sh) + 5.0))

# Our job here is done
gph_close()

