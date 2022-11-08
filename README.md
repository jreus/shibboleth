# Shibboleth Performance Interface

Some useful software:
[homebrew](https://brew.sh/)
[vscode](https://code.visualstudio.com/download)
[miniconda](https://docs.conda.io/en/latest/miniconda.html)


## OSX

On OSX Catalina and later you may need to set up miniconda to zsh shell.
Or, easier, download the 3.9 package (make sure you use python 3.9!)
and install as usual

Run:

```
miniconda/lib/activate
conda init zsh
```

And then restart your terminal window before proceeding with setting up your environments.

After that you should update conda.
```
conda update conda
conda update pip
```


## Setting up the Environment

Before running Shibboleth you'll need to have an anaconda/conda environment
set up with a few key dependencies.


Most importantly, these dependencies:

* [sounddevice](https://python-sounddevice.readthedocs.io/en/0.4.5/)
* [VOSK](https://alphacephei.com/vosk/)
* [COQUI TTS](https://github.com/coqui-ai/TTS)

If you're lucky, this is just a matter of creating a conda environment and installing sounddevice, VOSK and TTS using pip.

```
conda create -n shibboleth python=3.9
conda activate shibboleth
conda install -c conda-forge python-sounddevice
conda install -c conda-forge librosa
conda update scipy
(at this point test that importing librosa works!)

You might need to set up some simlinks to fix librosa errors...
ln -s libvorbis.0.dylib libvorbis.0.4.9.dylib
ln -s libvorbisenc.2.dylib libvorbisenc.2.0.12.dylib

conda install -c conda-forge websockets
pip install TTS
```

For the flask server and VOSK STT you'll also need..
```
conda install flask
pip install vosk
```

## Preparing your TTS Model Checkpoints

Your TTS model checkpoints must use the following directory structure and file
naming conventions, it should contain one `pth` and one `json` file:

- MODEL_ROOT_DIRECTORY
  - model_file.pth
  - config.json

Where `MODEL_ROOT_DIRECTORY` is the directory for a single checkpoint, ideally named
in a way that makes it clear what checkpoint is within the directory.

`model_file.pth`  is the checkpoint itself
`config.json`     is the coqui model configuration file


## Running the program

Once all the above is in order, you can run shibboleth from within the `shibboleth`
repository directory. You will actually need to run two programs: `shibboleth.py` and also a local web server to host the text editor. 

### 1. Start shibboleth

Open up a new terminal window and navigate to the shibboleth project folder.
Make sure your conda environment is activated, and then run shibboleth using `python shibboleth.py`

```
conda activate shibboleth
python shibboleth.py
```

### 2. Run the web server / text editor

Open up a new terminal window and navigate to the shibboleth project folder. 
Make sure your conda environment is activated, and then run the webserver using `python -m http.server`

```
conda activate shibboleth
python -m http.server
```

Now, open up your web browser and navigate to [localhost:8000](http://localhost:8000) to launch the text editor that will feed into shibboleth.


## Selecting different voice models

The basic `python shibboleth.py` command will run the program with the default model (Effi + Amir hybrid). You can also choose a specific voice, or point to a model path, using the options `--voice` and `--model-path`

The input to `--voice` can be either "effi" "amir" or "effiamir"
The input to `--model-path` must be a model directory containing a .pth file and a .json config file.

```
python shibboleth.py --model-path path/to/MODEL_ROOT_DIRECTORY
python shibboleth.py --voice effi
```

## Getting help and selected audio output device

Get help using the flag `-h`
```
python shibboleth.py -h
```

You may also want to check the audio device you are using. This can be done using the `-l` flag.
```
python shibboleth.py -l
```

You can choose which audio device to use by passing the audio device index in with the `--output-device` flag.
```
python shibboleth.py --output-device 3
```
