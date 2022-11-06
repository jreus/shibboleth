#!/usr/bin/env python3
import os, sys, time
import random
from pathlib import Path
import logging
import librosa
import soundfile
from logging import Logger
from typing import List, Union, Any, Dict

import torch
import torchaudio
import numpy as np
from TTS.tts.utils.synthesis import synthesis, trim_silence
from TTS.utils.synthesizer import Synthesizer

torch.set_grad_enabled(False) # we're only doing inference

class VoiceSynth:

    def __init__(self, audio_write_path: str, use_cuda: bool, logger: Logger) -> None:
        self.audio_write_path = Path(audio_write_path)
        self.use_cuda = use_cuda
        self.log = logger

        # Create audio write dir if does not exist...
        if self.audio_write_path.suffix != '':
            self.audio_write_path = self.audio_write_path.parent
            self.log.warning(f"Got audio scratch path as a file, using: {self.audio_write_path}")

        if not self.audio_write_path.exists():
            self.log.warning(f"Audio scratch path does not exist, creating: {self.audio_write_path}")
            os.makedirs(self.audio_write_path)


    def load_models(self, model_specs: dict) -> None:
        """
        Instantiate models from a model specs dict.
            model_specs     A dict of model specs, see example code below for format
        """
        # PARSE COQUI TTS MODELS

        if 'tts' in model_specs:
            tts_model_specs = model_specs['tts']
            tts_model_root = model_specs['tts_model_root_path']
        else:
            tts_model_specs = dict()
            tts_model_root = None

        self.tts = dict()
        for modelname, spec in tts_model_specs.items():
            model_path = os.path.join(tts_model_root, spec[0])
            model_config_path = os.path.join(tts_model_root, spec[1])
            speakers_file_path = spec[2]
            language_ids_file_path = spec[3]
            vocoder_model_path = spec[4]
            vocoder_config_path = spec[5]
            encoder_model_path = spec[6]
            encoder_config_path = spec[7]

            self.log.info(f"LOADING MODEL at {spec}")

            if speakers_file_path is not None:
                speakers_file_path = os.path.join(tts_model_root, speakers_file_path)
            if language_ids_file_path is not None:
                language_ids_file_path = os.path.join(tts_model_root, language_ids_file_path)
            if vocoder_model_path is not None:
                vocoder_model_path = os.path.join(tts_model_root, vocoder_model_path)
            if vocoder_config_path is not None:
                vocoder_config_path = os.path.join(tts_model_root, vocoder_config_path)
            if encoder_model_path is not None:
                encoder_model_path = os.path.join(tts_model_root, encoder_model_path)
            if encoder_config_path is not None:
                encoder_config_path = os.path.join(tts_model_root, encoder_config_path)

            # Load model
            self.tts[modelname] = dict()
            self.tts[modelname]["tts"] = Synthesizer(
                model_path,
                model_config_path,
                speakers_file_path,
                language_ids_file_path,
                vocoder_model_path,
                vocoder_config_path,
                encoder_model_path,
                encoder_config_path,
                self.use_cuda,
            )

            self.tts[modelname]["model"] = self.tts[modelname]['tts'].tts_model
            #self.tts[modelname]["ap"] = self.tts[modelname]["tts"].ap # TTS 0.5.0
            self.tts[modelname]["ap"] = self.tts[modelname]["tts"].tts_model.ap # TTS > 0.6.0
            self.tts[modelname]["config"] = self.tts[modelname]['tts'].tts_config
            self.tts[modelname]["sr"] = self.tts[modelname]["ap"].sample_rate
            self.tts[modelname]["arch"] = self.tts[modelname]["config"].model


    def synthesize(self, text: str, filename: str, model_id: str,
        speaker_name: str = None, language_name: str = None,
        clean_text: bool = True, rewrite_words: Dict[str, str] = None):
        """
        Synthesize an utterance & save to tmp directory
        Uses pr_synthesize as a helper function.
        """
        if clean_text:
            text = cleanup_text_for_tts(text)

        if rewrite_words is not None:
            for key in rewrite_words:
                text = text.replace(key, rewrite_words[key])

        self.log.info(f"Synthesizing Text >{text}<")

        wav = self.pr_synthesize(self.tts[model_id]["tts"], text, speaker_name, language_name, None, None)

        # Save temp wav file.
        wav = np.array(wav)
        savepath = os.path.abspath(os.path.join(self.audio_write_path, filename))
        sr = self.tts[model_id]["sr"]
        self.tts[model_id]["ap"].save_wav(wav, savepath, sr)
        self.log.debug(f"Wrote file: {savepath}")
        return wav, sr, savepath


    def pr_synthesize(self,
        synth: Synthesizer,
        text: str,
        speaker_name: str = "",
        language_name: str = "",
        speaker_wav: Union[str, List[str]] = None,
        style_wav: Union[str, List[str]] = None,
        reference_wav=None,
        reference_speaker_name=None,
    ) -> List[int]:
        """TTS magic. Run all the models and generate speech.

        NOTE!: This method is based on TTS.synthesizer.Synthesizer.tts
        and should be checked for functional equivalence on a regular
        basis with the latest and greatest in the TTS library.

        LAST UPDATE MAY 8 2022 -- TTS 0.6.2

        Args:
            synth (Synthesizer): synthesizer to use for synthesis.
            text (str): input text.
            speaker_name (str, optional): spekaer id for multi-speaker models. Defaults to "".
            language_name (str, optional): language id for multi-language models. Defaults to "".
            speaker_wav (Union[str, List[str]], optional): path to the speaker wav. Defaults to None.
            style_wav ([type], optional): style waveform for GST. Defaults to None.
            reference_wav ([type], optional): reference waveform for voice conversion. Defaults to None.
            reference_speaker_name ([type], optional): spekaer id of reference waveform. Defaults to None.
        Returns:
            List[int]: [description]


        """
        start_time = time.time()
        wavs = []

        if not text and not reference_wav:
            self.log.error("You need to define either `text` (for sythesis) or a `reference_wav` (for voice conversion) to use the Coqui TTS API.")
            raise ValueError(
                "You need to define either `text` (for sythesis) or a `reference_wav` (for voice conversion) to use the Coqui TTS API."
            )

        if text:
            sens = synth.split_into_sentences(text)
            self.log.info(f"Text splitted to sentences: {sens}")

        # handle multi-speaker
        speaker_embedding = None
        speaker_id = None
        if synth.tts_speakers_file or hasattr(synth.tts_model.speaker_manager, "ids"):
            if speaker_name and isinstance(speaker_name, str):
                if synth.tts_config.use_d_vector_file:
                    # get the average speaker embedding from the saved d_vectors.
                    speaker_embedding = synth.tts_model.speaker_manager.get_mean_embedding(
                        speaker_name, num_samples=None, randomize=False
                    )
                    speaker_embedding = np.array(speaker_embedding)[None, :]  # [1 x embedding_dim]
                else:
                    # get speaker idx from the speaker name
                    speaker_id = self.tts_model.speaker_manager.ids[speaker_name]

            elif not speaker_name and not speaker_wav:
                self.log.error("[!] Look like you use a multi-speaker model. You need to define either a `speaker_name` or a `style_wav` to use a multi-speaker model.")
                raise ValueError(
                    "[!] Look like you use a multi-speaker model. You need to define either a `speaker_name` or a `style_wav` to use a multi-speaker model."
                )
            else:
                speaker_embedding = None

        else:
            if speaker_name:
                raise ValueError(
                    f" [!] Missing speakers.json file path for selecting speaker {speaker_name}."
                    "Define path for speaker.json if it is a multi-speaker model or remove defined speaker idx. "
                )

        # handle multi-lingaul
        language_id = None
        if synth.tts_languages_file or (
            hasattr(synth.tts_model, "language_manager") and synth.tts_model.language_manager is not None
        ):
            if language_name and isinstance(language_name, str):
                language_id = synth.tts_model.language_manager.ids[language_name]

            elif not language_name:
                raise ValueError(
                    " [!] Look like you use a multi-lingual model. "
                    "You need to define either a `language_name` or a `style_wav` to use a multi-lingual model."
                )

            else:
                raise ValueError(
                    f" [!] Missing language_ids.json file path for selecting language {language_name}."
                    "Define path for language_ids.json if it is a multi-lingual model or remove defined language idx. "
                )

        # compute a new d_vector from the given clip.
        if speaker_wav is not None:
            speaker_embedding = synth.tts_model.speaker_manager.compute_embedding_from_clip(speaker_wav)

        use_gl = synth.vocoder_model is None

        if not reference_wav:
            for sen in sens:
                # synthesize voice
                outputs = synthesis(
                    model=synth.tts_model,
                    text=sen,
                    CONFIG=synth.tts_config,
                    use_cuda=synth.use_cuda,
                    speaker_id=speaker_id,
                    language_id=language_id,
                    style_wav=style_wav,
                    use_griffin_lim=use_gl,
                    d_vector=speaker_embedding,
                    do_trim_silence=False,
                )
                waveform = outputs["wav"]
                mel_postnet_spec = outputs["outputs"]["model_outputs"][0].detach().cpu().numpy()
                if not use_gl:
                    # denormalize tts output based on tts audio config
                    mel_postnet_spec = synth.tts_model.ap.denormalize(mel_postnet_spec.T).T
                    device_type = "cuda" if synth.use_cuda else "cpu"
                    # renormalize spectrogram based on vocoder config
                    vocoder_input = synth.vocoder_ap.normalize(mel_postnet_spec.T)
                    # compute scale factor for possible sample rate mismatch
                    scale_factor = [
                        1,
                        synth.vocoder_config["audio"]["sample_rate"] / synth.tts_model.ap.sample_rate,
                    ]
                    if scale_factor[1] != 1:
                        self.log.info("Interpolating tts model output.")
                        vocoder_input = interpolate_vocoder_input(scale_factor, vocoder_input)
                    else:
                        vocoder_input = torch.tensor(vocoder_input).unsqueeze(0)  # pylint: disable=not-callable
                    # run vocoder model
                    # [1, T, C]
                    waveform = synth.vocoder_model.inference(vocoder_input.to(device_type))
                if synth.use_cuda and not use_gl:
                    waveform = waveform.cpu()
                if not use_gl:
                    waveform = waveform.numpy()
                waveform = waveform.squeeze()

                # trim silence
                try:
                    if synth.tts_config["do_trim_silence"] is True:
                        waveform = trim_silence(waveform, synth.tts_model.ap)
                except KeyError:
                    pass

                wavs += list(waveform)
                wavs += [0] * 10000

        else: # VOICE CONVERSION
            # get the speaker embedding or speaker id for the reference wav file
            reference_speaker_embedding = None
            reference_speaker_id = None
            if synth.tts_speakers_file or hasattr(synth.tts_model.speaker_manager, "speaker_ids"):
                if reference_speaker_name and isinstance(reference_speaker_name, str):
                    if synth.tts_config.use_d_vector_file:
                        # get the speaker embedding from the saved d_vectors.
                        reference_speaker_embedding = synth.tts_model.speaker_manager.get_embeddings_by_name(
                            reference_speaker_name
                        )[0]
                        reference_speaker_embedding = np.array(reference_speaker_embedding)[
                            None, :
                        ]  # [1 x embedding_dim]
                    else:
                        # get speaker idx from the speaker name
                        reference_speaker_id = synth.tts_model.speaker_manager.ids[reference_speaker_name]
                else:
                    reference_speaker_embedding = synth.tts_model.speaker_manager.compute_embedding_from_clip(
                        reference_wav
                    )

            outputs = transfer_voice(
                model=synth.tts_model,
                CONFIG=synth.tts_config,
                use_cuda=synth.use_cuda,
                reference_wav=reference_wav,
                speaker_id=speaker_id,
                d_vector=speaker_embedding,
                use_griffin_lim=use_gl,
                reference_speaker_id=reference_speaker_id,
                reference_d_vector=reference_speaker_embedding,
            )
            waveform = outputs
            if not use_gl:
                mel_postnet_spec = outputs[0].detach().cpu().numpy()
                # denormalize tts output based on tts audio config
                mel_postnet_spec = synth.tts_model.ap.denormalize(mel_postnet_spec.T).T
                device_type = "cuda" if synth.use_cuda else "cpu"
                # renormalize spectrogram based on vocoder config
                vocoder_input = synth.vocoder_ap.normalize(mel_postnet_spec.T)
                # compute scale factor for possible sample rate mismatch
                scale_factor = [
                    1,
                    synth.vocoder_config["audio"]["sample_rate"] / synth.tts_model.ap.sample_rate,
                ]
                if scale_factor[1] != 1:
                    self.log.info(" > interpolating tts model output.")
                    vocoder_input = interpolate_vocoder_input(scale_factor, vocoder_input)
                else:
                    vocoder_input = torch.tensor(vocoder_input).unsqueeze(0)  # pylint: disable=not-callable
                # run vocoder model
                # [1, T, C]
                waveform = synth.vocoder_model.inference(vocoder_input.to(device_type))
            if synth.use_cuda:
                waveform = waveform.cpu()
            if not use_gl:
                waveform = waveform.numpy()
            wavs = waveform.squeeze()


        # compute stats
        process_time = time.time() - start_time
        audio_time = len(wavs) / synth.tts_config.audio["sample_rate"]
        self.log.info(f" > Processing time: {process_time}")
        self.log.info(f" > Real-time factor: {process_time / audio_time}")
        return wavs


if __name__ == '__main__':
    # python voicesynth.py --text "Hello World" --model-path ../../../outputs/checkpoints/hifi54_390k/
    # Make sure the model dir contains a model_file.pth and config.json
    import argparse
    from argparse import RawTextHelpFormatter

    import sounddevice as sd

    parser = argparse.ArgumentParser(
        description="""Voice Synthesizer\n\n""",
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument("--text", type=str, default=None, required=True, help="Text to generate speech.")

    parser.add_argument(
        "--model-path",
        type=Path,
        default=None,
        required=True,
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
        "--output", "-o",
        type=Path,
        default="tmp/wav",
        help="Audio write / output directory.",
    )

    parser.add_argument("--use-cuda", type=bool, help="Run model on CUDA.", default=False)

    args = parser.parse_args()

    TEXT = args.text
    AUDIO_WRITE_PATH = args.output.resolve() # audio renders go here
    MODEL_TYPE = args.model_type
    MODEL_PATH = args.model_path.resolve() # path to root directory of model
    USE_CUDA = args.use_cuda

    # Build a Model Spec depending on type.
    modelroot = str(MODEL_PATH.parent)
    modelsubdir = MODEL_PATH.name
    model_spec = { 'tts_model_root_path': modelroot, 'tts': None }
    if MODEL_TYPE == "vits":
        model_spec['tts'] = {
            "vits": [
                os.path.join(modelsubdir, "model_file.pth"),
                os.path.join(modelsubdir, "config.json"),
                None, None, None, None, None, None
            ]
        }
    elif MODEL_TYPE == "capacitron":
        raise Error("Capacitron support is not yet implemented")
    else:
        raise Error(f"Unknown model type '{MODEL_TYPE}'")

    voicesynth = VoiceSynth(AUDIO_WRITE_PATH, USE_CUDA, logging.getLogger("VoiceSynthesizer"))
    voicesynth.load_models(model_spec)

    # Just synthesize one line of text and play the result.
    print(f"Generating: >>{TEXT}<<")
    filename = f"{MODEL_TYPE}_testoutput.wav"

    wav, sr, outfile = voicesynth.synthesize(
        TEXT, filename, "vits",
        speaker_name=None,
        language_name=None,
        clean_text=False,
        rewrite_words=None
    )

    print(outfile)

    sd.play(wav, sr)
    sd.wait()

    ### END ### SYNTHESIS LOOP
    print("...DONE...")
