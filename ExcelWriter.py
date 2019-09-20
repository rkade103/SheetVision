import xlsxwriter
import math
import subprocess
import csv
import json

class ExcelWriter(object):
    """Object that contains all excel file writing capabalities."""

    def __init__(self, dest_path, midi_path):
        self.filePath = dest_path
        self.midi_path = midi_path
        self.workbook = xlsxwriter.Workbook(dest_path+"/excerptSheet.xlsx")
        self.testing_workbook = xlsxwriter.Workbook(dest_path+"/testing.xlsx")
        self.raw_workbook_path = self.convert_midi_to_csv(midi_path, dest_path)
        self.COLUMN_HEADERS = ["Line number", "Note", "Note Number", "Duration", "Include? (Y/N)",
                              "Include TL", "Include Dyn.", "Include Art.", "Include N.D.", 
                              "Space for barline", "Graph Width", "Vel. Graph Width", "X-axis limit", "Image Width"]
        self.LINE_NUMBER_COL = 0
        self.NOTE_COL = 1
        self.NOTE_NUMBER_COL = 2
        self.DURATION_COL = 3
        self.INCLUDE_1 = 4
        self.INCLUDE_2 = 5
        self.INCLUDE_3 = 6
        self.INCLUDE_4 = 7
        self.INCLUDE_5 = 8
        self.SPACE_FOR_BARLINE = 9
        self.GRAPH_WIDTH_COL = 10
        self.VEL_GRAPH_COL = 11
        self.X_LIMIT_COL = 12
        self.IMG_WIDTH_COL = 13
        self.load_config_file("notes.json")

    def load_config_file(self, path):
        with open(path) as f:
            self.letter_notes = json.load(f)
    
    def add_worksheet(self, sheet_name):
        self.workbook.add_worksheet(name=sheet_name)

    def fill_column_with_array(self, sheet_name, col, array):
        worksheet = self.testing_workbook.add_worksheet(sheet_name)
        row = 0
        worksheet.write(row, col, "Python Values")
        worksheet.write(row, col+1, "Excel chart values")
        row += 1
        for item in array:
            worksheet.write(row, col, item)
            worksheet.write(row, col+1, self.spacing_function(item))
            row +=1
        self.testing_workbook.close()

    def write_excerpt_sheet(self, note_groups):
        worksheet = self.workbook.add_worksheet("Excerpt sheet")
        list_of_notes = self.get_list_of_midi_notes(self.raw_workbook_path)
        #worksheet = self.workbook.get_worksheet_by_name("Excerpt Sheet")
        self.write_headers(worksheet)
        row = 1 #skip the header.
        col = 0
        last_graph_value = 0
        for note_group in note_groups:
            for note in note_group:
                worksheet.write(row, self.LINE_NUMBER_COL, row)    #Write the line number.
                if(row <= len(list_of_notes)):
                    worksheet.write(row, self.NOTE_COL, list_of_notes[row-1])
                worksheet.write(row, self.DURATION_COL, self.get_duration_of_note(note_group, note))
                worksheet.write(row, self.INCLUDE_1, "Y")
                worksheet.write(row, self.INCLUDE_2, "Y")
                worksheet.write(row, self.INCLUDE_3, "Y")
                worksheet.write(row, self.INCLUDE_4, "Y")
                worksheet.write(row, self.INCLUDE_5, "Y")
                last_graph_value = self.spacing_function(int((note.rec.x).item()))
                worksheet.write(row, self.SPACE_FOR_BARLINE, last_graph_value)
                row += 1
        row -= 1
        worksheet.write(row, self.INCLUDE_2, "N")
        worksheet.write(row, self.INCLUDE_4, "N")
        worksheet.write(row+1, 0, "END")
        last_note = note_groups[-1][-1]
        graph_width = self.graph_width_function(math.ceil(last_graph_value) + 1)
        vel_graph_width = self.graph_width_function(math.ceil(last_graph_value) + 1, vel_graph=True)
        worksheet.write(1, self.GRAPH_WIDTH_COL, graph_width)
        worksheet.write(1, self.VEL_GRAPH_COL, vel_graph_width)
        worksheet.write(1, self.X_LIMIT_COL, math.ceil(last_graph_value) + 1)
        self.workbook.close()

    def get_duration_of_note(self, note_group, note):
        duration = None
        note_type = note.sym
        if note_type == "1":
            duration = 1
        elif note_type == "2":
            duration = 1/2
        elif note_type == "4,8":
            duration = 1/4 if len(note_group) == 1 else 1/8
        return duration

    def write_headers(self, worksheet):
        #worksheet = self.workbook.get_worksheet_by_name(sheet_name)
        col = 0
        row = 0
        for name in self.COLUMN_HEADERS:
            worksheet.write(row, col, name)
            col += 1

    def graph_width_function(self, max_graph_value, vel_graph=False):
        '''
        Given an x-input that represents the position of the last note in an image, return the width in excel units.
        '''
        y = round(24.048*max_graph_value + 117.3333) #Function calculated using existing data.
        if vel_graph:
            y -= 36
        return y
    
    def spacing_function(self, x_value):
        '''
        Given an x-input that represents the position of the last note in an image, return the width in excel units.
        '''
        y = round((0.020106*x_value - 1.34251), 2)
        return y

    def convert_midi_to_csv(self, midi_path, dest_path):
        split_name = midi_path.split("/")
        print(split_name)
        file_name = split_name[-1].split(".")[0]
        print(file_name)
        file_name = dest_path + "/" + file_name + ".csv"
        command = ["Midicsv", midi_path, file_name]
        subprocess.run(command)
        return file_name

    def get_list_of_midi_notes(self, path):
        list_of_notes = []
        with open(path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            line_count = 0
            for row in csv_reader:
                if row[2].lower().strip() == "note_on_c" and int(row[5]) != 0:
                    list_of_notes.append(self.convert_midi_to_letter(row[4].strip()))
        return list_of_notes

    def convert_midi_to_letter(self, note):
        return self.letter_notes[str(note)]

    def run(self):
        raise NotImplementedError("The run method has not been implemented yet.")
            
