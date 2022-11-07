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
conda install flask
conda install -c conda-forge python-sounddevice
conda install -c conda-forge librosa
conda update scipy
pip install TTS
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
