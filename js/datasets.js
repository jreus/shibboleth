// Handle file loading.
// Dataset management.
// Managing utterances & audio files...
'use strict';

const DatasetManager = function(args) {
  let fileCount = 0;

  const func = ()=>{};

  // The clip name should be generated based on enumeration in the existing dataset + label information...
  const generateAudioFileName = ()=>{
    fileCount++;
    return "mydatasetrecording" + fileCount;
  };


  return {
    count: fileCount,
    func: func,
    generateAudioFileName: generateAudioFileName,
  };
}

export { DatasetManager };
