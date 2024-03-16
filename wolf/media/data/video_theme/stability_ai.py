"""
TODO : Add zoom affect by default
"""

import uuid
import os
import json
import shutil
from moviepy.editor import AudioClip, VideoClip, AudioFileClip, VideoFileClip, CompositeAudioClip, ImageSequenceClip, ImageClip
from moviepy.editor import concatenate_audioclips, concatenate_videoclips
from moviepy.video.fx import fadein, fadeout
import random
import os
import json
import traceback
import random

image_generator = 'stable-diffusion-xl-1024-v1-0'

def _sentence_splitter_(text):
    import pysbd
    segmenter = pysbd.Segmenter(language="en", clean=False)
    sentences = segmenter.segment(text)
    return sentences

def generate_clip_from_images(
                        chapter,
                        estimate,
                        generated_image_path,
                        number_of_images = 1,
                        fadein_time = 3,
                        fadeout_time = 3):
    if image_generator.startswith('stable'):
                image_type = 'photographic'
                number_of_images = 1
                import pdb; pdb.set_trace()
                prompt = chapter
                # negative_prompt = 'ugly, boring, bad anatomy, bad hands, blurry, pixelated, trees, green, obscure, unnatural colors, poor lighting, dullness, and unclear.'
                negative_prompt = None 
                image_files = generate_image_via_stability_api(
                                image_generator,
                                prompt,
                                negative_prompt,
                                generated_image_path,
                                image_type='photographic',
                                number_of_images= 1,
                                positive_weight = 0.5,
                                negative_weight = None,
                                clip_guidance_preset = None,
                                cfg_scale = 7)
    else:
        raise ValueError('image generator: {} is not implemented yet'.format(image_generator))
                
    per_image_time = estimate / number_of_images
    image_clips_for_this_iteration = []
    for image_file in image_files:
        image = ImageClip(image_file, duration = per_image_time).fadein(fadein_time).fadeout(fadeout_time)
        image_clips_for_this_iteration.append(image)

    video_clip_for_this_iteration = concatenate_videoclips(image_clips_for_this_iteration,
                                    method = 'compose')
    video_clip_for_this_iteration.set_duration(estimate)
    return video_clip_for_this_iteration


def generate_image_via_stability_api(
    image_generator,
    prompt,
    negative_prompt,
    result_path,
    image_type='photographic',
    number_of_images=1,
    positive_weight = 0.7,
    negative_weight = None,
    clip_guidance_preset = None,
    cfg_scale = 7
    ):
    import os
    import requests
    import base64

    api_host ='https://api.stability.ai'
    url = f"{api_host}/v1/engines/list"
    api_key = 'sk-RmjRShKlYdG3VArpSUYKmQCashOPQTaww3IqplKOiZ1razNV'

    text_prompts = [{'text' : prompt, 'weight' : positive_weight}]
    if negative_prompt: text_prompts.append({'text' : negative_prompt, 'weight' : negative_weight})

    response = requests.post(
        f"{api_host}/v1/generation/{image_generator}/text-to-image",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "text_prompts": text_prompts
            ,
            "height": 1024,
            "width": 1024,
            "samples": number_of_images,
            "steps": 30,
        },
        )

    data = response.json()

    turn_count = 0

    for filename in os.listdir(result_path):
        turn_count = max(turn_count, int(filename.split('_')[0]))
    
    turn_count += 1
    results = []
    for i, image in enumerate(data['artifacts']):
        curfile = os.path.join(result_path, "{}_{}.png".format(turn_count,i+1))
        file = open(curfile,'wb')
        file.write(base64.b64decode(image["base64"]))
        file.close()
        results.append(curfile)
    
    return results

def generate_video_content(chapters, input_audio_file, output_video_file):

    fadein_time = 3
    fadeout_time = 3
    audio_clip = AudioFileClip(input_audio_file)
    
    duration_of_video = audio_clip.duration
    estimate = float(duration_of_video) / len(chapters) # chapter's length

    final_video_clips = list()

    temp_storage = uuid.uuid4().hex
    generated_image_path = os.path.join(temp_storage)

    os.makedirs(generated_image_path, exist_ok = True)

    for chapter in chapters:
        image_file = os.path.join(generated_image_path, uuid.uuid4().hex)
        video_clip_for_this_iteration = generate_clip_from_images(chapter,
                                                        estimate,
                                                        image_file,
                                                        number_of_images = 1,
                                                        fadein_time = fadein_time,
                                                        fadeout_time = fadeout_time)                
        final_video_clips.append(video_clip_for_this_iteration)
        print('image: OK')

    final_video = concatenate_videoclips(final_video_clips,
                                            method = 'compose')
    final_video = final_video.set_duration(duration_of_video).set_audio(audio_clip)
    final_video.write_videofile(output_video_file, fps=24, codec="libx264")
    shutil.rmtree(temp_storage)

def generate_subtitles(input_audio_file):
    
    import whisper
    from moviepy.editor import VideoFileClip, CompositeVideoClip, TextClip
    model = whisper.load_model("base")
    results = model.transcribe(input_audio_file)
    subtitles = []

    for segment in results['segments']:
            print(f"Segment: {segment['text']}, Start: {segment['start']}, End: {segment['end']}")
            subtitles.append({'start' : segment['start'],
                            'end' : segment['end'],
                            'text' : segment['text']})
    return subtitles
    print(subtitles)


def generate_chunks_from_audio(input_audio_file):
    subtitles = generate_subtitles(input_audio_file)
    content = [s['text'] for s in subtitles]
    content = (' ').join(content)
    sentences = _sentence_splitter_(content)
    chunk_size = 5
    batches = []

    for i in range(0,len(sentences),chunk_size):
        batch = sentences[i:i+chunk_size]
        batches.append((' ').join(batch))
    return batches


def apply(
    input_audio_file : str = None,
    output_video_file : str = None,
    extra_settings : dict = None
):
    chunks = generate_chunks_from_audio(input_audio_file)
    generate_video_content(chunks, input_audio_file, output_video_file)
    import pdb; pdb.set_trace()


if __name__ == '__main__':
    audio = '/home/prakharrrr4/wolfy_ui/wolf/media/workspace/video_test/audio/inspire_robbins.wav'
    video = '/home/prakharrrr4/wolfy_ui/wolf/media/workspace/video_test/video/test_zig.mp4'
    apply(audio,video)