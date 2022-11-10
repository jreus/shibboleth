#!/usr/bin/env python

import sys
import os
import json
from pathlib import Path
import librosa # this is necessary for some reason...
#import numpy as np
from datetime import datetime
#import torch

if __name__ == "__main__":
    import argparse
    import logging
    import sounddevice as sd

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

    namespace, remaining_args = parser.parse_known_args()

    if namespace.list_devices:
        print(sd.query_devices())
        parser.exit(0)

    parser.add_argument(
        "-d", "--output-device", type=int_or_str,
        help="Output audio device (numeric ID or substring)"
    )

    parser.add_argument(
        "--wav",
        type=Path,
        required=True,
        default=None,
        help='Path to wav file to play.'
    )

    args = parser.parse_args(remaining_args)
    DEVICE=None

    if args.output_device:
        # Set output device
        print(f"Set output device to: {args.output_device}")
        sd.default.device = args.output_device

    DEVICE = sd.default.device
    DEV_INFO = sd.query_devices(DEVICE)
    print(f"Device info: {DEV_INFO}")
    print(f"Device Sample Rate is: {DEV_INFO['default_samplerate']}")
    # Load file...
    DEV_SAMPLERATE=DEV_INFO['default_samplerate']
    wavdata, sr = librosa.load(str(args.wav.resolve()))  #, sr=DEV_SR)
    print(f"Loaded file: {args.wav.resolve()} with sr 22050 and data {wavdata.shape}")

    # If DEV_SAMPLERATE != sr then we have a problem and need to resample...
    if(DEV_SAMPLERATE != sr):
        wavdata = librosa.resample(wavdata, orig_sr=sr, target_sr=DEV_SAMPLERATE)

    # PLay file...
    print(f"Playing with SR: {sr} on device: {DEVICE}")
    sd.play(wavdata, blocking=False, device=DEVICE)
    sd.wait()
