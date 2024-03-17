import utility, defaults
import sys
import os
import numpy as np

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from audio_generator import WolfyTTSMiddleware

from moviepy.editor import TextClip, AudioClip, VideoClip, AudioFileClip, VideoFileClip, CompositeAudioClip, ImageSequenceClip, ImageClip, CompositeVideoClip
from moviepy.editor import concatenate_audioclips, concatenate_videoclips
import moviepy.video.fx.all as vfx
import random



def create_video(audio_path, subtitle_path, video_path, font_path):

    audio_clip = AudioFileClip(audio_path)
    image_path = 'assets/images/joker.jpg'
    image_clip = ImageClip(image_path).set_duration(audio_clip.duration)

    clips = [image_clip]
    subtitles = utility.read_json(subtitle_path)
    for subtitle_data in subtitles:

        start_time = subtitle_data['start']/1000
        end_time = subtitle_data['end']/1000
        subtitle = subtitle_data['text']
        font_size = 60
        font_path = defaults.ttf_file
        txt_color = 'white'
        if len(subtitle) >50:
            txt_clip = (TextClip(subtitle, font=defaults.ttf_file, fontsize=60, color=txt_color)
                        .set_position(('center','center'))
                        .set_start(start_time)
                        .set_end(end_time)
                        .set_duration(end_time-start_time)
                        .crossfadein(0.5) 
                        .crossfadeout(0.5)) 
        elif len(subtitle) > 10:
            txt_clip = (TextClip(subtitle, font=defaults.ttf_file, fontsize=100, color=txt_color)
                    .set_position(('center','center'))
                    .set_start(start_time)
                    .set_end(end_time)
                    .set_duration(end_time-start_time)
                    .crossfadein(0.5) 
                    .crossfadeout(0.5))
        else:
            txt_clip = (TextClip(subtitle, font=defaults.ttf_file_2, fontsize=300, color=txt_color)
                    .set_position(('center','center'))
                    .set_start(start_time)
                    .set_end(end_time)
                    .set_duration(end_time-start_time)
                    .crossfadein(0.5) 
                    .crossfadeout(0.5))
        clips.append(txt_clip)

    # clips[0] = vfx.lum_contrast(clips[0], lum = 20, contrast = 0.4)
    # clips[0] = utility.warmth(clips[0])

    overlay_clip = utility.overlay(defaults.spot_overlay, clips[0].duration)
    clips.append(overlay_clip)
    final_video = CompositeVideoClip(clips).set_audio(audio_clip)
    # clips[0] = utility.shaky(clips[0])
    final_video.write_videofile(video_path, fps=24, codec="libx264")


def _make_(argument_map):
    workspace = argument_map.get('workspace')
    speech = argument_map.get('speech')
    wolfy_tts_middleware = WolfyTTSMiddleware(workspace, _id_ = speech)
    context = wolfy_tts_middleware.get_internal_context()

    audio_files = []
    data_files = []

    for key, values in context.items():
        audio_files.append(values['audio'])
        data_files.append(values['data'])
    
    c_audio = utility.get_hash() + '.wav'
    c_sub = utility.get_hash() + '.json'
    c_video = utility.get_hash() + '.mp4'

    utility.combine_audio(audio_files, c_audio)
    subtitles = wolfy_tts_middleware.get_subtitles()
    utility.save_json(subtitles, c_sub)
    utility.add_reverb(c_audio)

    create_video(c_audio, c_sub, c_video, data_files)



if __name__ == '__main__':

    _make_({
        'workspace' : 'video_1',
        'speech' : 'part_test2'
    })
