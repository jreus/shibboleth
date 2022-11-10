#!/usr/bin/env python

import sys
import os
import json
from pathlib import Path
import asyncio
import websockets
import sounddevice as sd
import numpy as np
from datetime import datetime

import torch

from TTS.utils.synthesizer import Synthesizer
torch.set_grad_enabled(False) # we're only doing inference

import voicesynth
import librosa # this is necessary for some reason on some systems, and breaks others... also depends when you import it..

class ShibbolethWSS(object):
    async def handler(self, websocket, path):
        print(f"Got: {websocket} : {path}")
        async for message in websocket:
            print(f"RCV: {message}")
            if message == "Handshake!":
                pass # ignore...
            else:
                if message.strip() != "":
                    self.synthesize_and_play(text=message)
                else:
                    print("...ignoring empty text...")
                await websocket.send(message) # echo message back to the client

    async def main(self, synth, system_samplerate, system_device, args):
        self.voicesynth = synth
        self.filenum = 0
        self.device_samplerate = system_samplerate
        self.device = system_device

        if args.test:
            testtext = "Please say the words as I repeat them. Shibboleths have been used throughout history in many societies as passwords, simple ways of self-identification, signaling loyalty and affinity, maintaining traditional segregation, or protecting from real or perceived threats."
            self.synthesize_and_play(testtext)

        print("Starting websockets server...")
        async with websockets.serve(self.handler, "localhost", 8765):
            await asyncio.Future()  # run forever

    def synthesize_and_play(self, text: str):
        wav,sr,wavfile = self.synthesize(text=text)

        # If DEV_SAMPLERATE != sr then we have a problem and need to resample...
        if(self.device_samplerate != sr):
            wav = librosa.resample(wav, orig_sr=sr, target_sr=self.device_samplerate)
            print(f"Resampling from {sr} to {self.device_samplerate}")
        sd.play(data=wav, samplerate=self.device_samplerate)

    def synthesize(self, text: str):
        print(f"Generating: >>{text}<<")
        filename = f"testoutput{self.filenum}.wav"
        wav, sr, outfile = self.voicesynth.synthesize(
            text, filename, "vits",
            speaker_name=None,
            language_name=None,
            clean_text=False,
            rewrite_words=None
        )
        self.filenum += 1
        return wav, sr, outfile


if __name__ == "__main__":
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
        print(sd.query_devices())
        parser.exit(0)

    INPUT_ONLY = namespace.input_only
    VOICE = namespace.voice

    parser.add_argument("--test", action="store_true", help="If present, no test sound is played.")

    parser.add_argument(
        "-d", "--output-device", type=int_or_str,
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

    if args.output_device:
        print(f"Set output device to: {args.output_device}")
        sd.default.device = args.output_device
        DEVICE = args.output_device
    else:
        DEVICE = sd.default.device[1]

    DEVICE_INFO = sd.query_devices(DEVICE)
    print(f"Using Device: {DEVICE_INFO}")

    if args.samplerate:
        # Set samplerate
        print(f"Set sample rate to: {args.samplerate}")
        sd.default.samplerate = args.samplerate
        DEV_SAMPLERATE = args.samplerate
    else:
        # Get samplerate from sounddevice
        DEV_SAMPLERATE = DEVICE_INFO['default_samplerate']

    print(f"Using Device Sample Rate: {DEV_SAMPLERATE}")

    # Check if model-path is set. Confirm files exist.
    if args.model_path is None:
        print(f"No model_path specified, using voice '{VOICE}': {DEFAULT_MODELS[args.voice]}")
        args.model_path = DEFAULT_MODELS[VOICE]['path']

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
    TTS_MODEL_NAME = args.voice
    USE_CUDA = args.use_cuda

    # print(f"Loading model: {TTS_MODEL_PATH}\nWith Config: {TTS_CONFIG_PATH}\n")
    # VOICE_SYNTH = Synthesizer(
    #     str(TTS_MODEL_PATH),
    #     str(TTS_CONFIG_PATH),
    #     use_cuda=USE_CUDA,
    # )
    # print("Done loading model")

    tts_model_spec = { 'tts_model_root_path': args.model_path, 'tts': None }
    tts_model_spec['tts'] = {
        "vits": [
            TTS_MODEL_PATH.name,
            TTS_CONFIG_PATH.name,
            None, None, None, None, None, None
        ]
    }
    VOICE_SYNTH = None
    VOICE_SYNTH = voicesynth.VoiceSynth(AUDIO_WRITE_PATH, USE_CUDA, logging.getLogger("VoiceSynthesizer"))
    #VOICE_SYNTH.load_model(TTS_MODEL_NAME, TTS_MODEL_PATH, TTS_CONFIG_PATH)
    VOICE_SYNTH.load_models(tts_model_spec)

    text = "Starting the Shibboleth, this is just a test. Please say the words as I repeat them."
    filename = f"testoutput.wav"
    wav, sr, outfile = VOICE_SYNTH.synthesize(
        text, filename, "vits",
        speaker_name=None,
        language_name=None,
        clean_text=False,
        rewrite_words=None
    )
    print(f"Finished synthesis file samplerate: {sr} - file saved: {outfile}")
    print(f"Playing with SR: {DEV_SAMPLERATE} on device: {DEVICE}")

    shib = ShibbolethWSS()
    asyncio.run(shib.main(VOICE_SYNTH, DEV_SAMPLERATE, DEVICE, args))
