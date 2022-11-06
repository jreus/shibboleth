#!/usr/bin/env python3
import argparse
import json
import random
import wave
import queue
import sys
import os
import time
import threading
import logging
from pathlib import Path
from typing import Callable

from tkinter import Tk, Button, Text, INSERT, END
import tkinter.ttk as ttk

from voicesynth import VoiceSynth

from vosk import Model, KaldiRecognizer, SetLogLevel

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

class GuiWrapper:
    """
    Configure and build the gui.
    Also includes a function called by a worker thread to read
    incoming commands from worker threads in the command queue
    """
    def __init__(self, window: Tk, command_queue: queue, button_callback: Callable):
        self.queue = command_queue
        # See: https://tkdocs.com/tutorial/text.html
        # See: https://www.tutorialspoint.com/python/tk_text.htm
        # width is in characters, not pixels!
        self.text = Text(window, width=50, height=80)
        self.text.pack()
        self.text.configure(font = ("Helvetica", 20, "bold"))

        # Set up the GUI
        self.quitbut = Button(window, text='QUIT', command=button_callback)
        self.quitbut.pack()
        # Add more GUI stuff here depending on your specific needs

    def updateFromQueue(self):
        """Handle all messages currently in the queue, if any."""
        while self.queue.qsize(  ):
            try:
                msg = self.queue.get(0)
                # Check contents of message and do whatever is needed. As a
                # simple test, print it (in real life, you would
                # suitably update the GUI's display in a richer fashion).
                self.text.insert(INSERT, msg)
            except queue.Empty:
                # just on general principles, although we don't
                # expect this branch to be taken in this case
                pass

class App:
    """
    The main application logic.
    * Builds the gui from the Tkinter root window
    * Sets up any worker threads to run background tasks
    * Runs a periodic call to the GuiWrapper to update the gui from whatever
        results the background tasks are producing
    """
    def __init__(self, window: Tk, kaldi_recognizer, voice_synth, tts_model_spec, args):
        """
        Build the GUI
        Start all the background threads
        Start a periodic update function in the main thread (which will also be used by Tkinter)
        """
        self.window = window

        self.kaldi_recognizer = kaldi_recognizer
        self.voice_synth = voice_synth
        self.tts_model_spec = tts_model_spec

        self.args = args

        self.filenum = 0
        self.audio_queue = queue.Queue() # used by audio thread to transmit incoming mic frames
        self.message_queue = queue.Queue() # used to pass transcribed text messages to Tkinter thread

        # Build the gui
        self.gui = GuiWrapper(self.window, self.message_queue, self.endApplicationFunc)

        # Used by worker threads and main thread
        self.running = True

        # Set up the worker threads
        # Here we just set up one to do the text generation
        # More threads can also be created and used, if necessary
        self.textgen_thread = threading.Thread(target=self.textgenThread)
        self.textgen_thread.start(  )

        # Start periodic updates on the GUI
        self.update_every = 200 # update the gui every 200ms
        self.periodicUpdateGUI()

    def periodicUpdateGUI(self):
        """
        Loops until self.running == False
        Update the gui every self.update_every ms
        """
        self.gui.updateFromQueue()

        # Tkinter's after method allows you to schedule callbacks on the event loop.
        if self.running:
            self.window.after(self.update_every, self.periodicUpdateGUI)
        else:
            # This is a brutal stop of the system. You may want to do
            # some cleanup before actually shutting it down.
            sys.exit(1)

    def textgenThread(self):
        """
        This function runs inside a thread.
        Generates text lines and places them in the queue to be read by the GUI.
        One important thing to remember is that this thread has
        to yield control pretty regularly, by select or otherwise.
        """

        self.voice_synth.load_models(self.tts_model_spec)

        try:
            # Open the input audio stream from the microphone and let's go!
            print("Opening input audio stream...")
            with sd.RawInputStream(
                samplerate=self.args.samplerate,
                blocksize=self.args.blocksize,
                device=self.args.input_device["name"],
                dtype="int16",
                channels=1,
                callback=self.processMicrophoneInput):

                print("#" * 80)
                print("Press Ctrl+C to stop the recording")
                print("#" * 80)

                while self.running:
                    data = self.audio_queue.get()
                    if self.kaldi_recognizer.AcceptWaveform(data):
                        txt = json.loads(self.kaldi_recognizer.Result())
                        txt = txt['text']
                        if len(txt) > 0:
                            wav, sr, outfile = self.synthesize(txt)
                            self.message_queue.put(txt + '\n')
                            sd.play(wav, sr)
                    else:
                        j = json.loads(self.kaldi_recognizer.PartialResult())
                        # print(j['partial'])
                        # Don't do anything with partial results for now!

        except KeyboardInterrupt:
            print("\nDone")

    def synthesize(self, text: str):
        print(f"Generating: >>{text}<<")
        filename = f"testoutput{self.filenum}.wav"
        self.filenum += 1
        # TODO: Do I even need a temp directory?
        #   Maybe writing tmp file is not needed...
        wav, sr, outfile = self.voice_synth.synthesize(
            text, filename, "vits",
            speaker_name=None,
            language_name=None,
            clean_text=False,
            rewrite_words=None
        )

        return wav, sr, outfile


    def processMicrophoneInput(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)

        self.audio_queue.put(bytes(indata))


    def endApplicationFunc(self):
        self.running = 0

if __name__ == "__main__":
    # python test_vosk_coqui_communication.py --model-path ../../../outputs/checkpoints/hifi54_390k/
    # python test_vosk_coqui_communication

    # Parse list-devices
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument(
        "-l", "--list-devices",
        action="store_true",
        help="Show list of audio devices and exit"
    )

    parser.add_argument("--input_only", action="store_true", help="If present, no synthesis is done - only text input to the texteditor GUI.")

    namespace, remaining_args = parser.parse_known_args()

    if namespace.list_devices:
        import sounddevice as sd
        print(sd.query_devices())
        parser.exit(0)

    INPUT_ONLY = namespace.input_only

    parser.add_argument(
        "--input-device", type=int_or_str,
        help="Input audio device (numeric ID or substring)")

    # TODO: Is it even possible to specify different input/output devices?
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
        required=(not INPUT_ONLY),
        help='Path to root directory of TTS model. Files expected in this dir: model_file.pth, config.json, and more depending on model type'
    )

    parser.add_argument(
        "--model-type",
        type=str,
        default="vits",
        required=False,
        help='Model type: vits, capacitron'
    )

    parser.add_argument(
        "--output-path",
        type=Path,
        default="tmp/wav",
        help="Audio write / temp file output directory.",
    )

    parser.add_argument("--use-cuda", type=bool, help="Run model on CUDA.", default=False)

    args = parser.parse_args(remaining_args)

    # Log Level of VOSK
    # You can set log level to -1 to disable debug messages from vosk
    SetLogLevel(0)

    print("Initializing VOSK model...")
    
    # VOSK Speech Recognition Model
    vosk_model = Model(lang="en-us")
    # You can also init model by name or with a folder path
    # model = Model(model_name="vosk-model-en-us-0.21")
    # model = Model("models/en")

    # NOTE: There is a very strange incompatibility between the VOSK model loading and sounddevice!
    #       sounddevice must be imported after the model is initialized
    import sounddevice as sd

    if args.input_device is None:
        device_list = sd.query_devices()
        # for dev in device_list:
        #     print(dev)
        args.input_device = sd.query_devices(device=None, kind="input")
        print(f"No device specified, using {args.input_device['name']}")
    else:
        args.input_device = sd.query_devices(device=args.input_device)

    print(f"Using audio input: {args.input_device}")

    if args.samplerate is None:
        args.samplerate = int(args.input_device["default_samplerate"])
        print(f"No samplerate specified, using {args.samplerate}")

    if args.blocksize is None:
        args.blocksize = int(args.samplerate / 4); # 1/4 second
        print(f"No blocksize specified, using {args.blocksize}")

    AUDIO_WRITE_PATH = args.output_path.resolve() # audio renders go here
    TTS_MODEL_TYPE = args.model_type
    TTS_MODEL_PATH = args.model_path.resolve() # path to root directory of model
    USE_CUDA = args.use_cuda

    # TODO: Break this out into a json model config file.
    # Build a Model Spec depending on type.
    modelroot = str(TTS_MODEL_PATH.parent)
    modelsubdir = TTS_MODEL_PATH.name
    tts_model_spec = { 'tts_model_root_path': modelroot, 'tts': None }
    if TTS_MODEL_TYPE == "vits":
        tts_model_spec['tts'] = {
            "vits": [
                os.path.join(modelsubdir, "model_file.pth"),
                os.path.join(modelsubdir, "config.json"),
                None, None, None, None, None, None
            ]
        }
    elif TTS_MODEL_TYPE == "capacitron":
        raise Error("Capacitron support is not yet implemented")
    else:
        raise Error(f"Unknown model type '{TTS_MODEL_TYPE}'")

    print("Initializing Kaldi recognizer...")
    # Create the Kaldi Recognizer
    kaldi_recognizer = KaldiRecognizer(vosk_model, args.samplerate)
    kaldi_recognizer.SetWords(True)
    kaldi_recognizer.SetPartialWords(True)

    voice_synth = VoiceSynth(AUDIO_WRITE_PATH, USE_CUDA, logging.getLogger("VoiceSynthesizer"))

    window = Tk()
    window.title("Shibboleth")

    try:
        app = App(
            window=window,
            kaldi_recognizer=kaldi_recognizer,
            voice_synth=voice_synth,
            tts_model_spec=tts_model_spec,
            args=args
        )
        window.mainloop() # run the Tk event loop
    except KeyboardInterrupt as e:
        print("Exit by KeyboardInterrupt")
    finally:
        app.running = 0
