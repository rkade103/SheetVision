import json
from mido import MidiFile

class MidiReader(object):

    def __init__(self, path):
        self.path = path
        self.midoObj = MidiFile(path)
        self.load_config_file("resources/notes.json")

    def load_config_file(self, path):
        with open(path) as f:
            self.letter_notes = json.load(f)

    def get_list_of_notes(self):
        list_of_notes = []
        for track in self.midoObj.tracks:
            for msg in track:
                if not msg.is_meta:
                    if msg.type == "note_on":
                        if msg.velocity != 0:
                            list_of_notes.append(self.convert_midi_to_letter(msg.note))
        return list_of_notes

    def convert_midi_to_letter(self, note):
        return self.letter_notes[str(note)]