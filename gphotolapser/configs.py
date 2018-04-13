from os import system
from ConfigParser import SafeConfigParser, NoOptionError, NoSectionError, DuplicateSectionError

def num(x):
    try:
        return int(x)
    except ValueError:
        return float(x)

cfgorder=['cycle', 'az', 'iso_max', 'shutter_max', 'shutter_min_num',
        'shutter_min_denom']

cfgs={}
infs={} # (min_, max_, html_min, html_max, step, label)

cfgs['cycle']=40
infs['cycle']=(4, 60*60*1, 4, 60*60*1, 1, # 4secs to a day
        'Cycle duration (seconds)')

cfgs['az']=60
infs['az']=(0, 360, 0, 360, 1,
        'Azimuth direction of camera (degrees)')

cfgs['iso_max']=800
infs['iso_max']=(100, 99999, 100, 99999, 100,
        'Maximum ISO speed')

cfgs['shutter_max']=30
infs['shutter_max']=(0.002, 99999, 0, 99999, 1,
        'Maximum shutter speed')

cfgs['shutter_min_num']=1
infs['shutter_min_num']=(1, 30, 1, 30, 1,
        'Minimum shutter speed (num)')

cfgs['shutter_min_denom']=400
infs['shutter_min_denom']=(1, 5000, 1, 5000, 1,
        'Minimum shutter speed (denom)')


def cfg_set(valz, signalservice=True):
    global cfgs
    cycle=cfgs['cycle']
    shutter_max=cfgs['shutter_max']
    shutter_min_num=cfgs['shutter_min_num']
    shutter_min_denom=cfgs['shutter_min_denom']

    for v in valz:
        if v[0] not in cfgs:
            print('Not in cfgs: '+v[0])
            return False
        (min_, max_, html_min, html_max, step, label) = infs[v[0]]
        if v[1] < min_ or v[1] > max_:
            return False
        if v[0] == 'shutter_max':
            shutter_max=v[1]
        elif v[0] == 'cycle':
            cycle=v[1]
        elif v[0] == 'shutter_min_num':
            shutter_min_num=v[1]
        elif v[0] == 'shutter_min_denom':
            shutter_min_denom=v[1]

    # Check for some misconfigs.
    if cycle < shutter_max + 4: # 4 seconds to dl image
        return False
    elif shutter_max <= float(shutter_min_num) / shutter_min_denom:
        # TODO: It's still possible that there are no valid camera
        # configurations between range.
        return False

    for v in valz:
        cfgs[v[0]] = v[1]
    cfg_write(signalservice=signalservice)
    return True

def signal_trigger():
    system('sudo systemctl kill -s HUP --kill-who=main camera-control.service')

def cfg_write(f='timelapse.conf', signalservice=True):
    config=SafeConfigParser()
    config.read(f)

    try:
        config.add_section('main')
    except DuplicateSectionError:
        pass

    for c in cfgs:
        config.set('main', c, str(cfgs[c]))

    with open(f, 'w') as f:
        config.write(f)

    if signalservice == True:
        signal_trigger()

def cfg_load(f='timelapse.conf'):
    config=SafeConfigParser()
    config.read(f)
    #config.add_section('main')
    for c in cfgs:
        try:
            cfgs[c]=config.getint('main', c)
        except ValueError:
            try:
                cfgs[c]=config.getfloat('main', c)
            except ValueError:
                continue
        except NoOptionError:
            continue
        except NoSectionError:
            return

