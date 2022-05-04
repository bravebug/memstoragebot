#!/usr/bin/env python3

from vosk import Model, KaldiRecognizer, SetLogLevel
import os
import json
import subprocess


SetLogLevel(-1)


def speech_to_text(input_file):
    if not os.path.exists("model"):
        print("Please download the model from "
              "https://alphacephei.com/vosk/models"
              " and unpack as 'model' in the current folder.")
        exit(1)
    
    sample_rate = 16000
    model = Model("model")
    rec = KaldiRecognizer(model, sample_rate)
    
    process = subprocess.Popen(
        [
            'ffmpeg', '-loglevel', 'quiet', '-i',
            'pipe:',
            '-ar', str(sample_rate), '-ac', '1', '-f', 's16le',
            # '-'
            'pipe:'
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,)
    process.stdin.write(input_file.getvalue())
    process.stdin.close()
    res = []
    while True:
        data = process.stdout.read(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            res.append(json.loads(rec.Result()).get("text"))
        # else:
            # res.append(json.loads(rec.PartialResult()).get("text"))
    return " ".join(res)


if __name__ == "__main__":
    speech_to_text("sff")
