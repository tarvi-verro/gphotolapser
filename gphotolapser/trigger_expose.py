from gph import gph_cmd
from pyexiv2 import ImageMetadata, XmpTag
from math import floor
from monotonic_time import monotonic_time, monotonic_alarm

_saving_file_response = 'Saving file as '

def trigger_capture(camera, shutter, start_time = (monotonic_time() + 0.05),
        meta=[], download_timeout=5.0):
    monotonic_alarm(start_time)
    o = gph_cmd('capture-image-and-download', timeout=shutter + download_timeout)

    s = filter(lambda x: x.startswith(_saving_file_response), o)
    if len(s) != 1:
        print("Couldn't retrieve file at the end of capture.")
        raise IOError

    filename = s[0][len(_saving_file_response):]

    exifd = ImageMetadata(filename)
    exifd.read()

    # Add a piece of debug info to exif header
    meta.append(('TriggerStartTime', start_time))
    for (name, value) in meta:
        tag = 'Xmp.xmp.GPhotolapser.' + name
        exifd[tag] = XmpTag(tag, value=str(value))
    exifd.write();

    return filename

def trigger_expose_bulb(camera, bulb, start_time = (monotonic_time() + 0.05),
        meta=[], download_timeout=3.5):
    end_time = start_time + bulb

    monotonic_alarm(start_time)
    gph_cmd(camera.bulb_begin)

    monotonic_alarm(end_time)
    gph_cmd(camera.bulb_end)

    o = gph_cmd('wait-event-and-download %is' % int(floor(download_timeout)),
            timeout=download_timeout) # Should download the image

    s = filter(lambda x: x.startswith(_saving_file_response), o)
    if len(s) != 1:
        print("Couldn't retrieve file at the end of bulb exposure.")
        raise IOError

    filename = s[0][len(_saving_file_response):]

    exifd = ImageMetadata(filename)
    exifd.read()

    # Add a piece of debug info to exif header
    meta.append(('BulbHoldTime', bulb))
    meta.append(('TriggerStartTime', start_time))
    for (name, value) in meta:
        tag = 'Xmp.xmp.GPhotolapser.' + name
        exifd[tag] = XmpTag(tag, value=str(value))
    exifd.write();

    return filename

