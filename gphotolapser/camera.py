from gph import gph_cmd

def camera_settings_get():
    # Grab camera configs for aperture, iso and shutter.
    aperture_cfg=gph_cmd('get-config /main/capturesettings/aperture')
    aperture=[ camera_setting_convert(a) for a in aperture_cfg[3:] ]

    iso_cfg=gph_cmd('get-config /main/imgsettings/iso')
    iso=[ camera_setting_convert(i) for i in iso_cfg[3:] ]

    shutter_cfg=gph_cmd('get-config /main/capturesettings/shutterspeed')
    shutter=[ camera_setting_convert(s) for s in shutter_cfg[3:] ]
    return (aperture, iso, shutter)

def camera_setting_convert(choice):
    s=choice.split(' ')[2]
    if not s[0].isdigit():
        return s
    frac=s.split('/')
    if len(frac) == 1:
        return float(s)
    return float(frac[0])/float(frac[1])

