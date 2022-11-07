// Handle UI elements and gluing everything together

// Using dynamic module loading outside of a module (in this case within a script file)
// see: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/import

import { VoiceCore } from './voicecore.js';
import { DatasetManager } from './datasets.js';

// UI Elements from DOM
const loadDatasetButton = document.querySelector('#loadDatasetButton');
const log = document.querySelector('#log');
const prompt = document.querySelector('#prompt');
const soundClips = document.querySelector('#soundClips');
const visualizerCanvas = document.querySelector('#audioVisualizer');
const visualizerContext = visualizerCanvas.getContext("2d");

// User logging function.
function userlog(text, data) {
  let p = document.createElement('p');
  let t = document.createElement('span');
  let d = document.createElement('span');
  t.innerHTML = text;
  d.innerHTML = (data || '');
  t.classList.add('log-text');
  d.classList.add('log-data');
  p.appendChild(t);
  p.appendChild(d);
  log.appendChild(p);
}

// 1. Create a VoiceCore (manage audio recorders & files)
const voicecore = new VoiceCore({
  logger: userlog,
  numInputChannels: 1, // use only the first input channel...
  mediaConstraints: { audio: { optional: [{ echoCancellation: false }] } },
  visualizers: [ {fftSize: 2048, logger: userlog, targetCanvas: visualizerCanvas} ],
});

// 2. Create a DatasetManager (dataset manager)
const datasetmanager = new DatasetManager();

// 3. Set up UI elements & plug them into Voice & Dataset callbacks...
const recStopButton = document.querySelector('#recordStopButton');

var audiorecorder;

// Request Microphone Access...
voicecore.getMicrophoneAccess((audioRecorders, visualizers)=>{
  // Set up voice recorder controls and callbacks...
  audiorecorder = audioRecorders[0];
  // Setup audio recorder status callbacks...
  audiorecorder.onstart = function() {
    //recStopButton.setIconToRecording();
    recStopButton.style.background = "red";
    userlog("Recorder started");
  };

  audiorecorder.onstop = function() {
    recStopButton.style.background = "";
    recStopButton.style.color = "";
    userlog("Recorder stopped");
  };

  audiorecorder.onstreamerror = function(e) {
    userlog('Error encountered: ', e.message );
  };

  audiorecorder.ondataavailable = (typedArray) => { // Recording complete, now what to do with the buffered audio data?
    console.log("Recorder stopped, new audio data available");

    // The clip name should be generated based on enumeration in the existing dataset + label information...
    let clipName = datasetmanager.generateAudioFileName();

    if(clipName == '') {
      //clipName = new Date().toISOString() + ".wav";
      clipName = "MyRecording"
      clipName = prompt('Enter a memorable name for your voiceprint', clipName);
      nameInput.value = clipName;
    }
    clipName = clipName + '.wav';

    const dataBlob = new Blob( [typedArray], { type: 'audio/wav' });
    const audioURL = window.URL.createObjectURL( dataBlob );

    // CREATE THE AUDIO PLAYBACK OBJECT...
    const audio = document.createElement('audio');
    audio.setAttribute('controls', '');
    audio.src = audioURL;
    audio.audioBlob = dataBlob;

    // Create DOM elements for audioclip preview & add to soundClips
    const clipContainer = document.createElement('article');
    const clipLabel = document.createElement('p');
    const deleteButton = document.createElement('button');
    const link = document.createElement('a'); // link to...
    clipLabel.textContent = clipName;
    clipContainer.classList.add('clip');
    deleteButton.textContent = 'Delete';
    deleteButton.className = 'delete';
    audio.clipName = clipName; // stash the clip name on the audio element...
    link.href = audioURL;
    link.download = clipName;
    link.innerHTML = link.download;

    deleteButton.onclick = function(e) {
      let evtTgt = e.target;
      evtTgt.parentNode.parentNode.removeChild(evtTgt.parentNode);
    }

    clipLabel.onclick = function() {
      const existingName = clipLabel.textContent;
      const newClipName = prompt('Enter a new name for your sound clip?');
      if(newClipName === null) {
        clipLabel.textContent = existingName;
      } else {
        clipLabel.textContent = newClipName;
      }

      audio.clipName = clipLabel.textContent;
    }

    clipContainer.appendChild(audio);
    clipContainer.appendChild(clipLabel);
    clipContainer.appendChild(deleteButton);
    soundClips.appendChild(clipContainer);

    // TODO: How to add it to the post request?
  }; // end recorder.ondataavailable

});



// Rec/Stop button click event listener...
recStopButton.addEventListener('click', ()=>{
  if(audiorecorder.state === "recording") { // Stop...
    audiorecorder.stop();
  } else { // Start...
    audiorecorder.start().catch((e)=>{
      console.log('Error encountered:', e.message);
      userlog('Error encountered:', e.message );
    });
  }
});

// Set up recorded audio submission/upload...
const submitButton = document.querySelector('#submitButton');
const submitAudioForm = document.querySelector('#metadataForm');

submitAudioForm.addEventListener('submit', (e)=>{
  e.preventDefault();   // On form submission, prevent default
  // Fetch the audio objects (if some recordings have been made)
  const clipElements = soundClips.querySelectorAll('.clip');

  for(let i=0; i < clipElements.length; i++) {

    const audioElement = clipElement.querySelector('audio');

    if(!audioElement) {
       userlog("Error: You need to make at least one recording before you can submit!")
       console.log("Error: No audio recordings in soundClips", audioRecordings);
       return;
    } else {
      // Construct a FormData object in which to store the audio data
      const formData = new FormData(submitAudioForm);
      const audioFileName = audioElement.clipName;
      const request = new XMLHttpRequest();

      console.log("Append audio data audioBlob and clipName from", audioElement);

      // Append the file data & submit the form via xhr
      formData.append('file', audioElement.audioBlob, audioFileName);

      // More detailed information about the xhr process
      // request.addEventListener('readystatechange', ()=>{ // Call a function when the state changes.
      //     console.log("Ready State Change", request);
      //     if (request.readyState === XMLHttpRequest.DONE && request.status === 200) {
      //         // Request finished. Do processing here.
      //         console.log("Request sent successfully, received response?", request)
      //     }
      // });

      request.addEventListener('load', ()=>{
        const response = request.response;
        console.log("XHR response", request.response);
        if(response == 'Success') {
          // Delete uploaded clip...
          soundClips.removeChild(clipElement);
          userlog("Uploaded ", audioFileName);

        } else { // Print error...
          userlog("Error uploading recording '"+audioFileName+"': ", response);
        }
      });

      request.open("POST", "/");
      request.send(formData);

    }

  }

});


////// TODO: Integrate this bit of code into the above... we need to add all the audio files to the form
///////////  when it gets submitted....

form.addEventListener('submit', (e)=>{
  // On form submission, prevent default
  e.preventDefault();


  // Fetch the audio object (if a recording has been made)
  let clipElement = soundClips.querySelector('.clip');
  let audioElement = clipElement.querySelector('audio');

  if(audioElement) {
    // Construct a FormData object
    let formData = new FormData(form);
    let fileName = audioElement.clipName;
    console.log("Append audio data audioBlob and clipName from", audioElement);

    // Append the file data...
    formData.append('file', audioElement.audioBlob, fileName);

    // Submit the form via xhr
    let request = new XMLHttpRequest();

    // More detailed information about the xhr process
    // request.addEventListener('readystatechange', ()=>{ // Call a function when the state changes.
    //     console.log("Ready State Change", request);
    //     if (request.readyState === XMLHttpRequest.DONE && request.status === 200) {
    //         // Request finished. Do processing here.
    //         console.log("Request sent successfully, received response?", request)
    //     }
    // });

    request.addEventListener('load', ()=>{
      let response = request.response;
      console.log("XHR response", request.response);
      if(response == 'Success') {
        // Delete uploaded clip...
        soundClips.removeChild(clipElement);
        screenLogger("Uploaded ", fileName);

      } else {
        // Print error...
        screenLogger("Error uploading recording '"+fileName+"': ", response);
      }
    });

    request.open("POST", "/");
    request.send(formData);


  } else {
    // Throw an error or something? Cannot do anything...
    screenLogger("You need to make a recording before you can save it to the list of voiceprints!")
    console.log("No audio recordings", audioRecordings);
    return;
  }

});



////// TODO



// Set up dataset / prompt controls...

const skipButton = document.querySelector('#skipButton');
const nextButton = document.querySelector('#nextButton');



// FINAL STEPS -----------

// Set up user interaction callbacks... / window.onresize

window.onresize = function() {
  // Resize the audio visualizer
  //visualizerCanvas.width = (mainSection.offsetWidth - 20) / 2;
}

window.onresize();

// Start audio visualizers...
const startVisualizers = ()=>{
  draw()

  function draw() {
    requestAnimationFrame(draw);

    // Go through all the visualizers and call their draw() function...
    for(let i=0; i<voicecore.audioVisualizers.length;i++) {
      voicecore.audioVisualizers[i].draw();
    }
  }
}

startVisualizers();
//export { startVisualizers };
