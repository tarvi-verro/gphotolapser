from gph import gph_cmd
from pyexiv2 import ImageMetadata, XmpTag
from math import ceil
from monotonic_time import monotonic_time, monotonic_alarm

_saving_file_response = 'Saving file as '

def trigger_capture(camera, shutter, start_time = (monotonic_time() + 0.05)):
    monotonic_alarm(start_time)
    o = gph_cmd('capture-image-and-download', timeout=(ceil(shutter) + 5.0))

    s = filter(lambda x: x.startswith(_saving_file_response), o)
    if len(s) != 1:
        print("Couldn't retrieve file at the end of capture.")
        raise IOError

    filename = s[0][len(_saving_file_response):]

    exifd = ImageMetadata(filename)
    exifd.read()

    # Add a piece of debug info to exif header
    tag='Xmp.xmp.GPhotolapser.TriggerStartTime'
    exifd[tag] = XmpTag(tag, value=str(start_time))
    exifd.write();

    return filename

def trigger_expose_bulb(camera, bulb, start_time = (monotonic_time() + 0.05)):
    end_time = start_time + bulb

    monotonic_alarm(start_time)
    gph_cmd(camera.bulb_begin)

    monotonic_alarm(end_time)
    gph_cmd(camera.bulb_end)

    o = gph_cmd('wait-event-and-download %is' % 3,
            timeout=(3.5)) # Should download the image

    s = filter(lambda x: x.startswith(_saving_file_response), o)
    if len(s) != 1:
        print("Couldn't retrieve file at the end of bulb exposure.")
        raise IOError

    filename = s[0][len(_saving_file_response):]

    exifd = ImageMetadata(filename)
    exifd.read()

    # Add a piece of debug info to exif header
    tag='Xmp.xmp.GPhotolapser.BulbHoldTime'
    exifd[tag] = XmpTag(tag, value=str(bulb))
    tag='Xmp.xmp.GPhotolapser.TriggerStartTime'
    exifd[tag] = XmpTag(tag, value=str(start_time))
    exifd.write();

    return filename

