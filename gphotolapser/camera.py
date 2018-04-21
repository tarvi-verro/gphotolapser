from gph import gph_cmd

def camera_settings_get():
    # Grab camera configs for aperture, iso and shutter.
    aperture_cfg=gph_cmd('get-config /main/capturesettings/aperture')
    aperture=[ camera_setting_convert(a) for a in aperture_cfg[4:-1] ]

    iso_cfg=gph_cmd('get-config /main/imgsettings/iso')
    iso=[ camera_setting_convert(i) for i in iso_cfg[4:-1] ]

    shutter_cfg=gph_cmd('get-config /main/capturesettings/shutterspeed')
    shutter=[ camera_setting_convert(s) for s in shutter_cfg[4:-1] ]
    return (aperture, iso, shutter)

def camera_setting_convert(choice):
    s=choice.split(' ')[2]
    if not s[0].isdigit():
        return s
    frac=s.split('/')
    if len(frac) == 1:
        return float(s)
    return float(frac[0])/float(frac[1])

_handler_canon_eos_40d = type("CameraHandler40D", (object,), {
    'bulb_begin': 'set-config /main/actions/bulb=1',
    'bulb_end': 'set-config /main/actions/bulb=0'
    })

_handler_canon_eos_550d = type("CameraHandler550D", (object,), {
    'bulb_begin': 'set-config-index /main/actions/eosremoterelease=2',
    'bulb_end': 'set-config-index /main/actions/eosremoterelease=4'
    })

_handlers = {
        'Canon EOS 550D': _handler_canon_eos_550d,
        'Canon EOS 40D': _handler_canon_eos_40d
        }

def camera_handler_get(cameramodel):
    try:
        return _handlers[cameramodel]
    except KeyError:
        pass

    print("Warning: your specific model %s hasn't been tested." % cameramodel)
    ms = cameramodel.split(' ')
    print(ms)

    if len(ms) == 3 and ms[0] == 'Canon' and ms[1] == 'EOS' and ms[-1][-1] == 'D':
        try:
            n = int(ms[2][:-1])
            if n < 100 and n >= 10:
                print('Guessing Canon EOS 40D style commands..')
                return _handler_canon_eos_40d
            if n < 1000 and n >= 100:
                print('Guessing Canon EOS 550D style commands..')
                return _handler_canon_eos_550d
        except ValueError:
            pass

    print('No smart guess, using Canon EOS 40D style commands..')
    return _handler_canon_eos_40d

