# Shibboleth Performance Interface

## Setting up the Environment

Before running Shibboleth you'll need to have an anaconda/conda environment
set up with a few key dependencies.

Most importantly:

* [sounddevice](https://python-sounddevice.readthedocs.io/en/0.4.5/)
* [VOSK](https://alphacephei.com/vosk/)
* [COQUI TTS](https://github.com/coqui-ai/TTS)

If you're lucky, this is just a matter of creating a conda environment and
installing sounddevice, VOSK and TTS using pip.

```
conda env create -n shibboleth
conda activate shibboleth
conda install -c conda-forge python-sounddevice
pip install TTS
pip install vosk
```

## Preparing your TTS Model Checkpoints

Your TTS model checkpoints must use the following directory structure and file
naming conventions:

- MODEL_ROOT_DIRECTORY
  - model_file.pth
  - config.json

Where `MODEL_ROOT_DIRECTORY` is the directory for a single checkpoint, ideally named
in a way that makes it clear what checkpoint is within the directory.

`model_file.pth`  is the checkpoint itself
`config.json`     is the coqui model configuration file


## Running the program

Once all the above is in order, you can run shibboleth from within the `Performance`
directory like so:

```
python shibboleth.py --model-path path/to/MODEL_ROOT_DIRECTORY
```

Get help using `-h`
```
python shibboleth.py -h
```

You may also want to check the audio device you are using. This can be done using the `-l` flag.
```
python shibboleth.py -l
```

You can choose which audio device to use by passing the audio device index in with the `--input-device` flag.
```
python shibboleth.py --input-device 3 --model-path path/to/MODEL_ROOT_DIRECTORY
```
