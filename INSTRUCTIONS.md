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

The shibboleth server will then run in this terminal window until you quit.
To quit the shibboleth server type `CTRL+C` in the terminal window.

Remember that if you stop and start the shibboleth server, you will need to also reload the webpage in your browser! This is because the webpage in the browser needs to make a new connection to the shibboleth server each time the server is restarted.

## 2. Start the Local Webserver

1. Open another terminal window and again navigate to the `shibboleth` directory with `cd ~/shibboleth`
2. Activate the local webserver with `python -m http.server`

```
cd ~/shibboleth
python -m http.server
```

The webserver will then run in this terminal window until you quit.
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


# (ADVANCED) Selecting a Port for the Shibboleth Websockets Server

By default the shibboleth server binds to port 8765 for its websockets connection
to the browser app. But you may want to run it on a different port.
For example, port 8654 might be used by another application. Or you might want to run
multiple shibboleth servers with different voices on multiple ports.

You can choose the port using the  `--port` option. So, for example, to run the
server on port 10000 you launch it with the command: `python shibboleth.py --port 10000`

_IMPORTANT!_ If you change the websockets port here you must also change the URL
you use to access the text editor web page. For the websockets port 10000
you need to use the website `http://localhost:8000/?port=10000`


Multiple options can also be combined by listing them one after another.
For example, to run the server using the effi voice on port 11111 would write:
```
python shibboleth.py --voice effi --port 11111
```

For the websockets port 11111 you need to use the website `http://localhost:8000/?port=11111`






# Choosing an Audio Output Device

You may need to choose an audio output device for the voice synthesis to play back.

You can see a list of the available devices with the command: `python shibboleth.py --list-devices`

This will give you a list of audio devices, each beginning with a number. To select an output device, use that number together with the `--output-device` option. For example, if you wanted to use device `1`, you would run the shibboleth server using the command:
`python shibboleth.py --output-device 1`


# Playing the Test Introduction Sentence

You can start the shibboleth server with a test sentence using the `--test` option.

With the command: `python shibboleth.py --test`

# To Update the Software When Changes Have Been Made

You may sometimes need to update the software when changes have been made.

1. Open a terminal window and navigate to the shibboleth directory with: `cd ~/shibboleth`
2. "Pull" the latest updates with the command: `git pull`

```
cd ~/shibboleth
git pull
```
