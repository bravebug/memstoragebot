#!/usr/bin/env python3

from vosk import Model, KaldiRecognizer, SetLogLevel
import os
import json
import subprocess


SetLogLevel(-1)


class Recognizer:
    def __init__(self, input_file, model="vosk_model"):
        self.input_file = input_file
        self.SAMPLE_RATE = 16000
        self.model = self.create_model(model)
        self.data = self.convert_data()
        self.rec = KaldiRecognizer(self.model, self.SAMPLE_RATE)

    def create_model(self, folder):
        try:
            return Model(folder)
        except Exception:
            print("Please download the model from "
                  "https://alphacephei.com/vosk/models"
                  f" and unpack as '{folder}' in the current folder.")

    def convert_data(self):
        process = subprocess.Popen(
            [
                'ffmpeg', '-loglevel', 'quiet', '-i',
                'pipe:',
                '-ar', str(self.SAMPLE_RATE), '-ac', '1', '-f', 's16le',
                'pipe:'
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )
        process.stdin.write(self.input_file.getvalue())
        process.stdin.close()
        return process.stdout

    def to_text(self, chunk=4000):
        def to_string(obj) -> str:
            try:
                return json.loads(obj).get("text", "")
            except AttributeError:
                return ""
        res = []
        while True:
            data = self.data.read(chunk)
            if len(data) == 0:
                break
            if self.rec.AcceptWaveform(data):
                text = to_string(self.rec.Result())
            else:
                text = to_string(self.rec.PartialResult())
            res.append(text)
        text = to_string(self.rec.FinalResult())
        res.append(text)
        return " ".join(res)


if __name__ == "__main__":
    pass
