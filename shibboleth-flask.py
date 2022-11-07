#!/usr/bin/env python3

'''
Shibboleth Web Interface
(c) J Chaim Reus 2022

run using:
export FLASK_APP=server && export FLASK_ENV=development && flask --app shibboleth-flask run

or

python shibboleth-flask.py

The website should run at localhost:3000
'''

import sys
import os
import json
from pathlib import Path
import numpy as np
import flask
from werkzeug.utils import secure_filename
from datetime import datetime

from voicesynth import VoiceSynth

app = flask.Flask(__name__)
app.app_context()
SERVE_HOST = '0.0.0.0'
flask.g.VOICE_SYNTH = None
flask.g.FILE_NUM = 0

import argparse
import logging

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


# python shibboleth-flask.py --model-path ../../../outputs/checkpoints/hifi54_390k/
# Parse list-devices
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    "-l", "--list-devices",
    action="store_true",
    help="Show list of audio devices and exit"
)

parser.add_argument("--input_only", action="store_true", help="If present, no synthesis is done - only text input to the texteditor GUI.")

parser.add_argument("-v", "--voice", type=str, default="effiamir", help="The voice to use: effiamir | amir | effi")

namespace, remaining_args = parser.parse_known_args()

if namespace.list_devices:
    import sounddevice as sd
    print(sd.query_devices())
    parser.exit(0)

INPUT_ONLY = namespace.input_only

parser.add_argument(
    "--output-device", type=int_or_str,
    help="Output audio device (numeric ID or substring)"
)
parser.add_argument("-r", "--samplerate", type=int, help="sampling rate")
parser.add_argument("-b", "--blocksize", type=int, help="blocksize")

parser.add_argument(
    "--model-path",
    type=Path,
    default=None,
    help='Path to root directory of TTS model. Files expected in this dir: model_file.pth, config.json, and more depending on model type'
)

parser.add_argument(
    "--output-path",
    type=Path,
    default="tmp/wav",
    help="Audio write / temp file output directory.",
)

parser.add_argument("--use-cuda", type=bool, help="Run model on CUDA.", default=False)

args = parser.parse_args(remaining_args)

DEFAULT_MODELS = {
    "effiamir": {
        "path": Path("../outputs/checkpoints/efam48_220k/").resolve()
    },
    "amir": {
        "path": Path("../outputs/checkpoints/hf54-50_amir50_300k/").resolve()
    },
    "effi": {
        "path": Path("../outputs/checkpoints/effi50_160k/").resolve()
    },
}

# Check if model-path is set. Confirm files exist.
if args.model_path is None:
    print(f"No model_path specified, using voice '{args.voice}': {DEFAULT_MODELS[args.voice]}")
    args.model_path = DEFAULT_MODELS[args.voice]['path']

if args.model_path.exists():
    for checkpoint in args.model_path.glob('*.pth'):
        TTS_MODEL_PATH = checkpoint
    for config in args.model_path.glob('*.json'):
        TTS_CONFIG_PATH = config
else:
    raise Error(f"Model Path Does Not Exist: {args.model_path}")

# Set up TTS model.
AUDIO_WRITE_PATH = args.output_path.resolve() # audio renders go here
TTS_MODEL_TYPE = "vits"
USE_CUDA = args.use_cuda
tts_model_spec = { 'tts_model_root_path': args.model_path, 'tts': None }
tts_model_spec['tts'] = {
    "vits": [
        TTS_MODEL_PATH.name,
        TTS_CONFIG_PATH.name,
        None, None, None, None, None, None
    ]
}

VOICE_SYNTH = VoiceSynth(AUDIO_WRITE_PATH, USE_CUDA, logging.getLogger("VoiceSynthesizer"))
VOICE_SYNTH.load_models(tts_model_spec)

# Serve Static Files
@app.route("/<path:name>")
def fetch_static(name):
    return flask.send_from_directory(
        "static/", name, as_attachment=False
    )

#create our "home" route using the "index.html" page
@app.route('/', methods = ['GET'])
def home():
    #return render_template('index.html', names=["The Voice of Authority","The Voice of Reason"], wishes=["I love you...","What is love?"], message="Test Message..")
    return flask.render_template('index.html', names=["",""], wishes=["",""], message="")


# Set a post method to send text data updates.
@app.route('/', methods = ['POST'])
def recv_text():
    print("recv_text() with", flask.request.json)

    res = flask.request.json
    txt = res['text']
    cmd = res['cmd']
    print(f"Got '{txt}'")
    # Synthesize & Play Audio
    wav,sr,wavfile = synthesize(text=txt, filenum=FILE_NUM, synth=VOICE_SYNTH)
    FILE_NUM +=1
    sd.play(wav, sr)
    return flask.jsonify({'response': "Success!", 'received': txt})


def synthesize(text: str, filenum: int, synth: VoiceSynth):
    print(f"Generating: >>{text}<<")
    filename = f"testoutput{filenum}.wav"
    wav, sr, outfile = synth.synthesize(
        text, filename, "vits",
        speaker_name=None,
        language_name=None,
        clean_text=False,
        rewrite_words=None
    )
    return wav, sr, outfile


app.run(port=3000, debug=True, host=SERVE_HOST, ssl_context='adhoc')
