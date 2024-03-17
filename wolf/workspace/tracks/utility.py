from pydub import AudioSegment
import numpy as np
import librosa
import numpy as np
from scipy.signal import fftconvolve
import soundfile as sf
import librosa, os
import uuid
import defaults
import json
import shutil
from moviepy.editor import AudioClip, VideoClip, AudioFileClip, VideoFileClip, CompositeAudioClip, ImageSequenceClip, ImageClip
from moviepy.editor import concatenate_audioclips, concatenate_videoclips
from moviepy.video.fx import fadein, fadeout
import random


def get_hash():
    return 'temp/' +  uuid.uuid4().hex


def resample_audio(input_path, output_path, target_sr):
    audio, sr = librosa.load(input_path, sr=None)
    audio_resampled = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
    sf.write(output_path, audio_resampled, target_sr)


def apply_exponential_decay(ir, decay_rate=0.0001):
    """
    Applies an exponential decay to the impulse response.
    decay_rate controls the rate of the decay.
    """
    # return ir
    n = np.arange(len(ir))
    decay_curve = np.exp(-decay_rate * n)
    return ir * decay_curve


def add_reverb(audio_path):
    resample_audio(audio_path, audio_path, 24000)
    audio, sr_audio = librosa.load(audio_path, sr=None, mono=True)
    ir, sr_ir = librosa.load(defaults.ir_path, sr=None, mono=True)
    # decay_rate = 0.04
    # envelope = np.exp(-decay_rate * np.arange(len(ir)))
    # envelope *=-1
    # ir *= envelope
    # ir = ir[:int(sr_ir * 0.15)]
    ir = apply_exponential_decay(ir)
    reverberated_audio = fftconvolve(audio, ir, mode='full')
    reverberated_audio /= np.max(np.abs(reverberated_audio))
    sf.write(audio_path, reverberated_audio, sr_audio)


def make_silence(duration):
    return AudioClip(lambda t: 0, duration = duration)


def combine_audio(audio_files, ret_path, intro_silence = 0):
    audio_clips = [make_silence(intro_silence)]
    for audio_file in audio_files:
        audio_clip = AudioFileClip(audio_file)
        audio_clips.append(audio_clip)
    final_clip = concatenate_audioclips(audio_clips)    
    final_clip.write_audiofile(ret_path)

