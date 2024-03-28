import utility, defaults
import sys
import os
import numpy as np

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from audio_generator import ThemeFactory

from moviepy.editor import TextClip, AudioClip, VideoClip, AudioFileClip, VideoFileClip, CompositeAudioClip, ImageSequenceClip, ImageClip, CompositeVideoClip
from moviepy.editor import concatenate_audioclips, concatenate_videoclips
import moviepy.video.fx.all as vfx
import random




def create_image_clips(subtitle_path):
    data = utility.read_json(subtitle_path)
    chapters = []
    for _data_ in data:
            cur_text = _data_['text']
            cur_start_time = _data_['start']
            cur_end_time = _data_['end']
            cur_chapter = _data_['chapter']
            if len(chapters) == 0 or chapters[-1][3] != cur_chapter:
                chapters.append([
                    cur_text,
                    cur_start_time,
                    cur_end_time,
                    cur_chapter
                ])
            else:
                last_e = chapters[-1]
                chapters[-1][0] += ' {}'.format(cur_text)
                chapters[-1][2] = cur_end_time

    image_clips = []        
    for chapter in chapters:
        prob = random.randint(0,2)
        if prob != 1:
            continue
        prompt = chapter[0]
        system = """You are a extremely wise stoic scene describer. Provide a vivid, highly detailed, photographic description of the following text
            Provide the final output in the following python dict. It should have a fields. Keep it within 200 words
            { "image_prompt" : ""
            }"""
        keys = set(['image_prompt'])
        prompt = utility.generate_dict_1(system, prompt, keys).get('image_prompt')
        negative_prompt = 'ugly'
        start_time = chapter[1]/1000
        end_time = chapter[2]/1000
        c_image = utility.get_hash() + '.jpeg'
        utility.generate_image_s(prompt, '', c_image)
        image_clip = (ImageClip(c_image)
                        .set_start(start_time)
                        .set_end(end_time)
                        .set_duration(end_time-start_time)
                        .crossfadein(0.5)
                        .crossfadeout(0.5)
                        .set_opacity(0.4))
        image_clips.append(image_clip)

    return image_clips 


def create_video(audio_path, subtitle_path, video_path, data_path):

    audio_clip = AudioFileClip(audio_path)
    image_path = 'assets/images/standard.jpg'
    image_clip = ImageClip(image_path).set_duration(audio_clip.duration)

    clips = [image_clip]
    subtitles = utility.read_json(subtitle_path)
    for subtitle_data in subtitles:

        start_time = subtitle_data['start']/1000
        end_time = subtitle_data['end']/1000
        subtitle = subtitle_data['text']
        font_size = 60
        txt_color = 'white'
        if len(subtitle) >100:
            txt_clip = (TextClip(subtitle, font=defaults.ttf_file, fontsize=40, color=txt_color)
                        .set_position(('center','center'))
                        .set_start(start_time)
                        .set_end(end_time)
                        .set_duration(end_time-start_time)
                        .crossfadein(0.5) 
                        .crossfadeout(0.5)) 
        elif len(subtitle) >50:
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

    overlay_clip = utility.overlay(defaults.flames_overlay, clips[0].duration)
    clips.append(overlay_clip)

    # image_clips = create_image_clips(subtitle_path)
    # clips.extend(image_clips)

    final_video = CompositeVideoClip(clips).set_audio(audio_clip)
    final_video.write_videofile(video_path,
                        fps = 24,
                        codec="libx264",
                        ffmpeg_params = [ "-preset", "fast"])

def _make_(argument_map):
    workspace = argument_map.get('workspace')
    speech = argument_map.get('speech')
    wolfy_tts_middleware = ThemeFactory().get_middleware(workspace, _id_ = speech)
    context = wolfy_tts_middleware.get_internal_context()

    audio_files = []
    data_files = []

    for key, values in context.items():
        audio_files.append(values['audio'])
        data_files.append(values['data'])
    
    c_audio = utility.get_hash() + '.wav'
    c_audio_bg = utility.get_hash() + '.mp3'
    c_sub = utility.get_hash() + '.json'
    c_credit = utility.get_hash() + '.json'
    c_video = utility.get_hash() + '.mp4'

    utility.combine_audio(audio_files, c_audio)
    subtitles = wolfy_tts_middleware.get_subtitles()
    utility.save_json(subtitles, c_sub)
    utility.add_reverb(c_audio)
    utility.add_background_music(c_audio, c_audio_bg, credit_file = c_credit)
    create_video(c_audio_bg, c_sub, c_video, data_files)



if __name__ == '__main__':

    _make_({
        'workspace' : 'a',
        'speech' : 'a_a_milne'
    })
