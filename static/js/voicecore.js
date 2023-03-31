// Jobs of voicecore.js
// Handle getting user media for audio recording.
// Handle recording/stopping recording to files.
// Handle playback of files.
// Handle playback on a visualizer (if provided)
'use strict';
// More info on modules: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules

const VoiceCore = function(args) {
  // Class params -------------------------------------------
  const numInputChannels = (args.numInputChannels) ? args.numInputChannels : 2;
  const mediaConstraints = (args.mediaConstraints) ? args.mediaConstraints : { audio: { optional: [{ echoCancellation: false }] } };
  const visualizerSpecs = (args.visualizers) ? args.visualizers : [];
  const log = (args.logger) ? args.logger : console.log;
  const audioChannels = []; // active audio channels (WebAudio GainNodes)
  const audioRecorders = []; // opusrecorders for all audio channels
  const audioVisualizers = [];

  let audioCtx = undefined; // audio context
  let rawStream = undefined; // raw media stream from getUserMedia
  let streamSource = undefined; // active MediaStreamSource from raw stream



  // Class Functions ----------------------------------------
  const getMicrophoneAccess = (successFunc, errorFunc)=>{

    if (navigator.mediaDevices.getUserMedia) {
      log('getUserMedia supported');

      // Create callbacks for user media request...

      const onSuccess = function(stream) { // On successful access to microphone...
        rawStream = stream;
        if(!audioCtx) {
          audioCtx = new AudioContext();
        }
        streamSource = audioCtx.createMediaStreamSource(rawStream);

        let channelSplitter = audioCtx.createChannelSplitter(2);
        let signalLeft = new GainNode(audioCtx, {gain: 1.0, channelCount: 1});
        let signalRight = new GainNode(audioCtx, {gain: 1.0, channelCount: 1});
        streamSource.connect(channelSplitter);
        channelSplitter.connect(signalLeft, 0);
        channelSplitter.connect(signalRight, 1);

        audioChannels.push(signalLeft);

        // Create a recorder & visualizer for each audio channel.
        for(let i = 0; i < audioChannels.length; i++) {

          audioRecorders.push(
            new Recorder({
              monitorGain: 0.0,
              recordingGain: 1.0,
              numberOfChannels: 1,
              wavBitDepth: 16,
              encoderPath: "/js/opusrecorder/encoderWorker.min.js",
              sourceNode: audioChannels[i]
            }),
          );


          let visualizerSpec = visualizerSpecs[i];

          audioVisualizers.push(
            new AudioVisualizer({
              stream: rawStream,
              sourceNode: audioChannels[i],
              logger: log,
              audioCtx: audioCtx,
              fftSize: visualizerSpec.fftSize,
              targetCanvas: visualizerSpec.targetCanvas,
            })
          );

        }

        if(successFunc) {
          successFunc(audioRecorders, audioVisualizers);
        }
      } // end onSuccess

      let onError = function(err) { // Error while trying to access microphone...
        log('ERROR: The following error occured while trying to access microphone hardware: ', err);

        if(errorFunc) {
          errorFunc();
        }
      }

      // Ask user for access!
      navigator.mediaDevices.getUserMedia(mediaConstraints).then(onSuccess, onError);

    } else {
       log('ERROR: getUserMedia not supported on your browser!');
    }
  }


  return {
    // Parameters...
    log: log,
    audioCtx: audioCtx,
    rawStream: rawStream,
    streamSource: streamSource,
    audioChannels: audioChannels,
    audioRecorders: audioRecorders,
    audioVisualizers: audioVisualizers,

    // Functions...
    getMicrophoneAccess: getMicrophoneAccess,
  }
}

const AudioVisualizer = function(args) {
  // Class params -------------------------------------------
  const fftSize = (args.fftSize) ? args.fftSize : 2048;
  const sourceNode = (args.sourceNode) ? args.sourceNode : (()=>{throw "Error: No source node provided to AudioVisualizer!"})();
  const audioCtx = (args.audioCtx) ? args.audioCtx : (()=>{throw "Error: No AudioContext provided to AudioVisualizer!"})();
  const log = (args.logger) ? args.logger : console.log;

  const targetCanvas = (args.targetCanvas) ? args.targetCanvas : (()=>{throw "Error: No Canvas target provided to AudioVisualizer!"})();
  const width = targetCanvas.width
  const height = targetCanvas.height;
  const drawTarget = targetCanvas.getContext("2d");

  var analyser = undefined;

  // private params...
  const chunks = [];
  var dataArray;

  analyser = audioCtx.createAnalyser();
  analyser.fftSize = fftSize;
  const bufferLength = analyser.frequencyBinCount;
  dataArray = new Uint8Array(bufferLength);
  const sliceWidth = width * 1.0 / bufferLength;

  log("Frequency Bin Count on Analyser: " + analyser.frequencyBinCount);

  sourceNode.connect(analyser);

  const draw = ()=>{ // update visualizer canvas...
    //analyser.getByteTimeDomainData(dataArray[0]);
    analyser.getByteTimeDomainData(dataArray);

    //drawTarget.fillStyle = 'rgb(200, 200, 200)';
    drawTarget.clearRect(0, 0, width, height);
    drawTarget.lineWidth = 1.0;
    drawTarget.strokeStyle = 'rgb(0, 0, 0)';
    drawTarget.beginPath();

    let x = 0;
    for(let i = 0; i < bufferLength; i++) {
      let v = dataArray[i] / 128.0;
      let y = v * height/2;
      if(i === 0) {
        drawTarget.moveTo(x, y);
      } else {
        drawTarget.lineTo(x, y);
      }
      x += sliceWidth;
    }

    drawTarget.lineTo(width, height/2);
    drawTarget.stroke();
  };

  return {
    // Parameters...
    log: log,
    sourceNode: sourceNode,
    targetCanvas: targetCanvas,
    width: width,
    height: height,
    audioCtx: audioCtx,

    // Functions...
    draw: draw,
  }
}

export { VoiceCore, AudioVisualizer };
