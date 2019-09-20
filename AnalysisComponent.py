import sys
import subprocess
import cv2
import time
import os
import queue
import numpy as np
from threading import Thread
from threading import Event
from best_fit import fit
from rectangle import Rectangle
from note import Note
from random import randint
from midiutil.src.midiutil.MidiFile3 import MIDIFile
from ExcelWriter import ExcelWriter
from MidiReader import MidiReader

class AnalysisComponent(Thread):
    """
    The analysis component that scans the sheet music and generates the spacing values as well as note identification and note duration.
    Adapted from the SheetVision Repo's original main.py file.
    Main changes include outputting necesary values, as well as converting the code to a class.
    """

    def __init__(self, pic_path, midi_path, dest_path, queue):
        Thread.__init__(self)

        self.img_file = pic_path
        self.destination_folder = dest_path
        self.queue = queue
        self.stop_event = Event()

        self.staff_files = [
            "resources/template/staff2.png", 
            "resources/template/staff.png"]
        self.quarter_files = [
            "resources/template/quarter.png", 
            "resources/template/solid-note.png"]
        self.sharp_files = [
            "resources/template/sharp.png"]
        self.flat_files = [
            "resources/template/flat-line.png", 
            "resources/template/flat-space.png" ]
        self.half_files = [
            "resources/template/half-space.png", 
            "resources/template/half-note-line.png",
            "resources/template/half-line.png", 
            "resources/template/half-note-space.png"]
        self.whole_files = [
            "resources/template/whole-space.png", 
            "resources/template/whole-note-line.png",
            "resources/template/whole-line.png", 
            "resources/template/whole-note-space.png"]

        self.staff_imgs = [cv2.imread(staff_file, 0) for staff_file in self.staff_files]
        self.quarter_imgs = [cv2.imread(quarter_file, 0) for quarter_file in self.quarter_files]
        self.sharp_imgs = [cv2.imread(sharp_file, 0) for sharp_file in self.sharp_files] #Error here? Removed the s
        self.flat_imgs = [cv2.imread(flat_file, 0) for flat_file in self.flat_files]
        self.half_imgs = [cv2.imread(half_file, 0) for half_file in self.half_files]
        self.whole_imgs = [cv2.imread(whole_file, 0) for whole_file in self.whole_files]

        self.staff_lower, self.staff_upper, self.staff_thresh = 50, 150, 0.51
        self.sharp_lower, self.sharp_upper, self.sharp_thresh = 50, 150, 0.6
        self.flat_lower, self.flat_upper, self.flat_thresh = 50, 150, 0.77
        self.quarter_lower, self.quarter_upper, self.quarter_thresh = 50, 150, 0.7
        self.half_lower, self.half_upper, self.half_thresh = 50, 150, 0.65
        self.whole_lower, self.whole_upper, self.whole_thresh = 50, 150, 0.75

    def locate_images(self, img, templates, start, stop, threshold):
        locations, scale = fit(img, templates, start, stop, threshold, self)
        img_locations = []
        for i in range(len(templates)):
            w, h = templates[i].shape[::-1]
            w *= scale
            h *= scale
            img_locations.append([Rectangle(pt[0], pt[1], w, h) for pt in zip(*locations[i][::-1])])
        return img_locations

    def merge_recs(self, recs, threshold):
        filtered_recs = []
        while len(recs) > 0:
            r = recs.pop(0)
            recs.sort(key=lambda rec: rec.distance(r))
            merged = True
            while(merged):
                merged = False
                i = 0
                for _ in range(len(recs)):
                    if r.overlap(recs[i]) > threshold or recs[i].overlap(r) > threshold:
                        r = r.merge(recs.pop(i))
                        merged = True
                    elif recs[i].distance(r) > r.w/2 + recs[i].w/2:
                        break
                    else:
                        i += 1
            filtered_recs.append(r)
        return filtered_recs

    def open_file(self, path):
        cmd = {'linux':'eog', 'win32':'explorer', 'darwin':'open'}[sys.platform]
        subprocess.run([cmd, path])

    def crop_photo(self, img, name, staff_recs_boxes, destination_folder, expand_y=False):
        first_x, second_x, first_y, second_y = self.get_borders(staff_recs_boxes, expand_y)
        print("FIRST_X: "+str(first_x) +"; SECOND_X: "+ str(second_x)+"; FIRST_Y: " + str(first_y) + "; SECOND_Y: "+ str(second_y))
        crop_img = img[first_y:second_y, first_x:second_x]
        cv2.imwrite(destination_folder+'/'+name, crop_img)
        return destination_folder+'/'+name

    def stop(self):
        self.stop_event.set()

    def stopped(self):
        return self.stop_event.is_set()

    def generate_cropped_photo(self, img_file, destination_folder):
        if self.stopped():
            return False
        img = cv2.imread(img_file, 0)
        img_gray = img#cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.cvtColor(img_gray,cv2.COLOR_GRAY2RGB)
        ret,img_gray = cv2.threshold(img_gray,127,255,cv2.THRESH_BINARY)
        img_width, img_height = img_gray.shape[::-1]

        if self.stopped():
            return False
        print("Matching staff image...")
        staff_recs = self.locate_images(img_gray, self.staff_imgs, self.staff_lower, self.staff_upper, self.staff_thresh)

        if self.stopped():
            return False
        print("Filtering weak staff matches...")
        staff_recs = [j for i in staff_recs for j in i]
        heights = [r.y for r in staff_recs] + [0]
        if self.stopped():
            return False
        histo = [heights.count(i) for i in range(0, max(heights) + 1)]
        avg = np.mean(list(set(histo)))
        staff_recs = [r for r in staff_recs if histo[r.y] > avg]
        if self.stopped():
            return False

        print("Merging staff image results...")
        staff_recs = self.merge_recs(staff_recs, 0.01)
        staff_recs_img = img.copy()
        for r in staff_recs:
            r.draw(staff_recs_img, (0, 0, 255), 2)
            if self.stopped():
                return False
        cv2.imwrite(destination_folder+'/staff_recs_img.png', staff_recs_img)
        print(destination_folder+'/staff_recs_img.png')
        self.crop_photo(img, "fully_cropped.png", staff_recs, destination_folder, expand_y=False)
        path = self.crop_photo(img, "padded_y.png", staff_recs, destination_folder, expand_y=True)
        cv2.destroyAllWindows()
        return path
    
    def get_borders(self, array, expand_y=False):
        max_x_value = array[0].x
        min_x_value = array[0].x
        max_y_value = array[0].y
        min_y_value = array[0].y
        
        for i in array:
            if((i.x + i.w) > max_x_value):
                max_x_value = i.x + i.w
            if(i.x < min_x_value):
                min_x_value = i.x
            if((i.y + i.h) > max_y_value):
                max_y_value = i.y + i.h
            if(i.y < min_y_value):
                min_y_value = i.y
        if expand_y:
            return int(min_x_value.item()), int(max_x_value.item()), 0, int(max_y_value.item())+80
        else:
            return int(min_x_value.item()), int(max_x_value.item()), int(min_y_value.item()), int(max_y_value.item())

    def get_max(self, array):
        max_box = array[0]
        for i in array:
            if(i.x > max_box.x):
                max_box = i
        return max_box

    def get_min(self, array):
        min_box = array[0]

    def crop_using_non_zero(self, path, destination_folder):
        this_img = cv2.imread(path)
        gray = cv2.cvtColor(this_img, cv2.COLOR_BGR2GRAY)
        gray = 255*(gray < 128).astype(np.uint8)
        coords = cv2.findNonZero(gray)
        x, y, w, h = cv2.boundingRect(coords)
        if h != 158:
            h = 158 #Makes sure all images have the same height for scaling purposes.
        rect = this_img[y:y+h, x:x+w]
        cv2.imshow("Cropped", rect)
        cv2.destroyAllWindows()
        cv2.imwrite(destination_folder+"/b&w_crop.png", rect)

    def run(self, img_file, midi_file, destination_folder):
        if self.stopped():
            return False
        self.queue.put("0|Cropping Photos...")   #Progress tracking
        #img_file = sys.argv[1:][0]
        cropped_photo = self.generate_cropped_photo(img_file, destination_folder)
        self.crop_using_non_zero(cropped_photo, destination_folder)
        if self.stopped():
            return False
        img = cv2.imread(cropped_photo, 0)
        img_gray = img#cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.cvtColor(img_gray,cv2.COLOR_GRAY2RGB)
        ret,img_gray = cv2.threshold(img_gray,127,255,cv2.THRESH_BINARY)
        img_width, img_height = img_gray.shape[::-1]
        if self.stopped():
            return False
        self.queue.put("10|Detecting staff locations...")   #Progress tracking

        print("Matching staff image...")
        staff_recs = self.locate_images(img_gray, self.staff_imgs, self.staff_lower, self.staff_upper, self.staff_thresh)
        
        if self.stopped():
            return False
        print("Filtering weak staff matches...")
        staff_recs = [j for i in staff_recs for j in i]
        heights = [r.y for r in staff_recs] + [0]
        histo = [heights.count(i) for i in range(0, max(heights) + 1)]
        avg = np.mean(list(set(histo)))
        staff_recs = [r for r in staff_recs if histo[r.y] > avg]
        if self.stopped():
            return False

        print("Merging staff image results...")
        staff_recs = self.merge_recs(staff_recs, 0.01)
        staff_recs_img = img.copy()
        for r in staff_recs:
            r.draw(staff_recs_img, (0, 0, 255), 2)
        cv2.imwrite(destination_folder+'/staff_recs_img.png', staff_recs_img)
        if self.stopped():
            return False

        print("Discovering staff locations...")
        staff_boxes = self.merge_recs([Rectangle(0, r.y, img_width, r.h) for r in staff_recs], 0.01)
        staff_boxes_img = img.copy()
        for r in staff_boxes:
            r.draw(staff_boxes_img, (0, 0, 255), 2)
        cv2.imwrite(destination_folder+'/staff_boxes_img.png', staff_boxes_img)
        if self.stopped():
            return False
    
        self.queue.put("30|Detecting sharps...")   #Progress tracking

        print("Matching sharp image...")
        sharp_recs = self.locate_images(img_gray, self.sharp_imgs, self.sharp_lower, self.sharp_upper, self.sharp_thresh)
        if self.stopped():
            return False

        print("Merging sharp image results...")
        sharp_recs = self.merge_recs([j for i in sharp_recs for j in i], 0.5)
        sharp_recs_img = img.copy()
        for r in sharp_recs:
            if self.stopped():
                return False
            r.draw(sharp_recs_img, (0, 0, 255), 2)
        cv2.imwrite(destination_folder+'/sharp_recs_img.png', sharp_recs_img)
        #self.open_file(destination_folder+'/sharp_recs_img.png')

        self.queue.put("40|Detecting flats...")   #Progress tracking

        print("Matching flat image...")
        flat_recs = self.locate_images(img_gray, self.flat_imgs, self.flat_lower, self.flat_upper, self.flat_thresh)
        if self.stopped():
            return False

        print("Merging flat image results...")
        flat_recs = self.merge_recs([j for i in flat_recs for j in i], 0.5)
        flat_recs_img = img.copy()
        for r in flat_recs:
            if self.stopped():
                return False
            r.draw(flat_recs_img, (0, 0, 255), 2)
        cv2.imwrite(destination_folder+'/flat_recs_img.png', flat_recs_img)
        #self.open_file(destination_folder+'/flat_recs_img.png')

        self.queue.put("50|Detecting quarter notes...")   #Progress tracking

        print("Matching quarter image...")
        quarter_recs = self.locate_images(img_gray, self.quarter_imgs, self.quarter_lower, self.quarter_upper, self.quarter_thresh)
        if self.stopped():
            return False

        print("Merging quarter image results...")
        quarter_recs = self.merge_recs([j for i in quarter_recs for j in i], 0.5)
        quarter_recs_img = img.copy()
        for r in quarter_recs:
            if self.stopped():
                return False
            r.draw(quarter_recs_img, (0, 0, 255), 2)
        cv2.imwrite(destination_folder+'/quarter_recs_img.png', quarter_recs_img)
        #self.open_file(destination_folder+'/quarter_recs_img.png')

        self.queue.put("60|Detecting half notes...")   #Progress tracking

        print("Matching half image...")
        half_recs = self.locate_images(img_gray, self.half_imgs, self.half_lower, self.half_upper, self.half_thresh)
        if self.stopped():
            return False

        print("Merging half image results...")
        half_recs = self.merge_recs([j for i in half_recs for j in i], 0.5)
        half_recs_img = img.copy()
        for r in half_recs:
            if self.stopped():
                return False
            r.draw(half_recs_img, (0, 0, 255), 2)
        cv2.imwrite(destination_folder+'/half_recs_img.png', half_recs_img)
        #self.open_file(destination_folder+'/half_recs_img.png')

        self.queue.put("70|Detecting whole notes...")   #Progress tracking

        print("Matching whole image...")
        whole_recs = self.locate_images(img_gray, self.whole_imgs, self.whole_lower, self.whole_upper, self.whole_thresh)
        if self.stopped():
            return False

        print("Merging whole image results...")
        whole_recs = self.merge_recs([j for i in whole_recs for j in i], 0.5)
        whole_recs_img = img.copy()
        for r in whole_recs:
            if self.stopped():
                return False
            r.draw(whole_recs_img, (0, 0, 255), 2)
        cv2.imwrite(destination_folder+'/whole_recs_img.png', whole_recs_img)
        #self.open_file(destination_folder+'/whole_recs_img.png')

        self.queue.put("80|Analyzing detected musical notation...")   #Progress tracking

        note_groups = []
        for box in staff_boxes:
            if self.stopped():
                return False
            staff_sharps = [Note(r, "sharp", box) 
                for r in sharp_recs if abs(r.middle[1] - box.middle[1]) < box.h*5.0/8.0]
            staff_flats = [Note(r, "flat", box) 
                for r in flat_recs if abs(r.middle[1] - box.middle[1]) < box.h*5.0/8.0]
            quarter_notes = [Note(r, "4,8", box, staff_sharps, staff_flats) 
                for r in quarter_recs if abs(r.middle[1] - box.middle[1]) < box.h*6.0/8.0]
            half_notes = [Note(r, "2", box, staff_sharps, staff_flats) 
                for r in half_recs if abs(r.middle[1] - box.middle[1]) < box.h*5.0/8.0]
            whole_notes = [Note(r, "1", box, staff_sharps, staff_flats) 
                for r in whole_recs if abs(r.middle[1] - box.middle[1]) < box.h*5.0/8.0]
            staff_notes = quarter_notes + half_notes + whole_notes
            staff_notes.sort(key=lambda n: n.rec.x)
            staffs = [r for r in staff_recs if r.overlap(box) > 0]
            staffs.sort(key=lambda r: r.x)
            note_color = (randint(0, 255), randint(0, 255), randint(0, 255))
            note_group = []
            i = 0; j = 0;
            while(i < len(staff_notes)):
                if self.stopped():
                    return False
                if (j < len(staffs) and i < len(staff_notes) and staff_notes[i].rec.x > staffs[j].x):
                    r = staffs[j]
                    j += 1;
                    if len(note_group) > 0:
                        note_groups.append(note_group)
                        note_group = []
                    note_color = (randint(0, 255), randint(0, 255), randint(0, 255))
                else:
                    note_group.append(staff_notes[i])
                    staff_notes[i].rec.draw(img, note_color, 2)
                    i += 1
            note_groups.append(note_group)

        for r in staff_boxes:
            r.draw(img, (0, 0, 255), 2)
        for r in sharp_recs:
            r.draw(img, (0, 0, 255), 2)
        flat_recs_img = img.copy()
        for r in flat_recs:
            r.draw(img, (0, 0, 255), 2)
        
        cv2.imwrite(destination_folder+'/res.png', img)
        #self.open_file(destination_folder+'/res.png')
   
        self.queue.put("90|Writing the excerpt sheet...")   #Progress tracking

        x_values = []
        for note_group in note_groups:
            print([ note.note + " " + note.sym + " " + str((note.rec.x).item()) for note in note_group])
            [x_values.append(int((note.rec.x).item())) for note in note_group]

        midi_reader = MidiReader(midi_file)
        list_of_notes = midi_reader.get_list_of_notes()
        writer = ExcelWriter(destination_folder, midi_file)
        writer.write_excerpt_sheet(note_groups)

        os.remove(destination_folder+'/staff_recs_img.png')
        os.remove(destination_folder+'/staff_boxes_img.png')
        os.remove(destination_folder+'/sharp_recs_img.png')
        os.remove(destination_folder+'/flat_recs_img.png')
        os.remove(destination_folder+'/quarter_recs_img.png')
        os.remove(destination_folder+'/half_recs_img.png')
        os.remove(destination_folder+'/whole_recs_img.png')

        #writer.add_worksheet("Values")
        writer.fill_column_with_array("Values", 0, x_values)
        if self.stopped():
            return False

        self.queue.put("100|Complete!")   #Progress tracking

        #midi = MIDIFile(1)
     
        #track = 0   
        #time = 0
        #channel = 0
        #volume = 65
    
        #midi.addTrackName(track, time, "Track")
        #midi.addTempo(track, time, 140)
    
        #for note_group in note_groups:
        #    duration = None
        #    for note in note_group:
        #        note_type = note.sym
        #        if note_type == "1":
        #            duration = 4
        #        elif note_type == "2":
        #            duration = 2
        #        elif note_type == "4,8":
        #            duration = 1 if len(note_group) == 1 else 0.5
        #        pitch = note.pitch
        #        midi.addNote(track,channel,pitch,time,duration,volume)
        #        time += duration

        #midi.addNote(track,channel,pitch,time,4,0)

        ## And write it to disk.
        #print("SAVING FILE TO: "+destination_folder+"/output.mid")
        #binfile = open(destination_folder+"/output.mid", 'wb')
        #midi.writeFile(binfile)
        #binfile.close()
        #open_file('output.mid')
        return True     #Used to stop the thread.
