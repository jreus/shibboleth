# To Start

## 1. Start the Shibboleth Server

1. Open a terminal window and navigate to the `shibboleth` directory with `cd ~/shibboleth`
2. Activate the shibboleth python environment with `conda activate shibboleth`
3. Run the shibboleth server with `python shibboleth.py`

Here are what all the commands look like one after another:
```
cd ~/shibboleth
conda activate shibboleth
python shibboleth.py
```

To quit the shibboleth server type `CTRL+C` in the terminal window.


## 2. Start the Local Webserver

1. Open another terminal window and again navigate to the `shibboleth` directory with `cd ~/shibboleth`
2. Activate the local webserver with `python -m http.server`

To quit the web server type `CTRL+C` in the terminal window.



## 3. Go to the Local Text Editor Website
1. Open a web browser and enter the url `localhost:8000`
2. Type or dictate text into the text editor, it will be sent to the shibboleth server for synthesis into voice.
3. If you restart the shibboleth server, you will also need to reload the website.


# Selecting a Voice

When you start the shibboleth server, there are a few options you can add to the command.
You can view them all with the help command `python shibboleth.py -h`

By default the shibboleth server uses the combined `effiamir` voice. You can also
select the `effi` voice or the `amir` voice using the `--voice` option.

To use the `effi` voice run the command: `python shibboleth.py --voice effi`
For the `amir` voice run the command: `python shibboleth.py --voice amir`


# Choosing an Audio Output Device

You may need to choose an audio output device for the voice synthesis to play back.
You can see a list of the available devices with the command: `python shibboleth.py --list-devices`
