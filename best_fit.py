import cv2
import numpy as np

def fit(img, templates, start_percent, stop_percent, threshold, analysis_component):
    img_width, img_height = img.shape[::-1]
    best_location_count = -1
    best_locations = []
    best_scale = 1

    x = []
    y = []
    if analysis_component.stopped():
        return;
    for scale in [i/100.0 for i in range(start_percent, stop_percent + 1, 3)]:
        if analysis_component.stopped():
            return;
        locations = []
        location_count = 0
        for template in templates:
            if analysis_component.stopped():
                return;
            template = cv2.resize(template, None,
                fx = scale, fy = scale, interpolation = cv2.INTER_CUBIC)
            result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
            result = np.where(result >= threshold)
            location_count += len(result[0])
            locations += [result]
        print("scale: {0}, hits: {1}".format(scale, location_count))
        x.append(location_count)
        y.append(scale)
        if analysis_component.stopped():
            return;
        if (location_count > best_location_count):
            best_location_count = location_count
            best_locations = locations
            best_scale = scale
        elif (location_count < best_location_count):
            pass

    return best_locations, best_scale