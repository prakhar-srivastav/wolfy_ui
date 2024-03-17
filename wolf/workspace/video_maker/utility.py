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
from moviepy.editor import AudioClip, VideoClip, AudioFileClip, VideoFileClip, CompositeAudioClip, CompositeVideoClip, ImageSequenceClip, ImageClip
from moviepy.editor import concatenate_audioclips, concatenate_videoclips
import moviepy.video.fx.all as vfx 
import random


def get_hash():
    return 'temp/' +  uuid.uuid4().hex


"""
A U D I O
A F F E C T S
"""

def resample_audio(input_path, output_path, target_sr):
    audio, sr = librosa.load(input_path, sr=None)
    audio_resampled = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
    sf.write(output_path, audio_resampled, target_sr)


def apply_exponential_decay(ir, decay_rate=0.0001):
    """
    Applies an exponential decay to the impulse response.
    decay_rate controls the rate of the decay.
    """
    n = np.arange(len(ir))
    decay_curve = np.exp(-decay_rate * n)
    return ir * decay_curve


def add_reverb(audio_path):
    resample_audio(audio_path, audio_path, 24000)
    audio, sr_audio = librosa.load(audio_path, sr=None, mono=True)
    ir, sr_ir = librosa.load(defaults.ir_path, sr=None, mono=True)
    ir = apply_exponential_decay(ir)
    reverberated_audio = fftconvolve(audio, ir, mode='full')
    reverberated_audio /= np.max(np.abs(reverberated_audio))
    sf.write(audio_path, reverberated_audio, sr_audio)


def make_silence(duration):
    return AudioClip(lambda t: 0, duration = duration)


def combine_audio(audio_files, ret_path):
    audio_clips = []
    for audio_file in audio_files:
        audio_clip = AudioFileClip(audio_file)
        audio_clips.append(audio_clip)
    final_clip = concatenate_audioclips(audio_clips)    
    final_clip.write_audiofile(ret_path)



"""
V I D E O 
A F F E C T S
"""


def warmth(clip, strength=0.8):
    def process_frame(get_frame, t):
        frame = get_frame(t)
        frame[:, :, 0] = frame[:, :, 0] * strength
        return frame

    return clip.fl(process_frame)


def shaky(clip, amplitude=0.2):
    def fl(gf, t):
        dx = float(np.random.randint(-amplitude*1000, amplitude*1000)) / 1000
        dy = float(np.random.randint(-amplitude*1000, amplitude*1000)) / 1000
        return gf(t).clip(dx, dy)
    
    return clip.fl(fl)


def overlay(video_file, duration, opacity = 0.2, fadeout_duration = 3):
    composite_list = []
    rem = duration
    start = 0

    while rem > 0:
        clip = VideoFileClip(video_file)        
        duration_a = rem
        duration_b = clip.duration

        if clip.duration < rem:
            clip = vfx.fadeout(clip.set_start(start), fadeout_duration)
            composite_list.append(clip)
            rem -= clip.duration
            start += clip.duration
        else:
            clip = vfx.fadeout(clip.set_duration(rem).set_start(start), fadeout_duration)
            composite_list.append(clip)
            start += rem
            rem = 0

    result = CompositeVideoClip(composite_list).set_opacity(opacity)
    return result



"""
F I L E
P A R S I N G
"""

def save_json(request_body, filename):
    json_object = json.dumps(request_body, indent=4)    
    with open(filename, "w") as outfile:
        outfile.write(json_object)


def read_json(filename):
    j = open(filename, 'r')
    json_object =  json.loads(j.read())
    j.close()
    return json_object


