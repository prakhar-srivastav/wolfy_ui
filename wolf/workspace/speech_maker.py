from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django import forms
from django.http import JsonResponse
from django.templatetags.static import static
from django.conf import settings

import sys
import os
import json
import uuid
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
from .audio_generator import WolfyTTSMiddleware

def get_speaker_path(speaker_name):
    PATH = os.path.join(settings.MEDIA_ROOT,'data/audio_data')
    return PATH + '/' + speaker_name + '.wav'

@csrf_exempt
def speech_maker(request):
    data = request.GET
    youtube_link = data.get('youtube_link',"").strip()
    theme = data.get("theme","").strip()
    transcript = data.get("transcript","").strip()
    speaker_name = data.get("speaker_name","").strip()
    workspace = data.get("workspace","").strip()
    instance_name = data.get('instance_name', "").strip()
    # if theme is not None and theme != '':
        # text = ThemeFactory(theme).apply_theme(text)

    global wolfy_tts_middleware
    if instance_name == "":
        text = ''
        if youtube_link is None or youtube_link == '':
            text = transcript
        else:
            text = get_youtube_captions(youtube_link)

        wolfy_tts_middleware = WolfyTTSMiddleware(workspace)
        wolfy_tts_middleware.synthesize(text, speaker_name)
    else:
        wolfy_tts_middleware = WolfyTTSMiddleware(workspace, _id_ = instance_name)
    content_context = wolfy_tts_middleware.get_context()
    
    return render(request,
                'speech_maker/main.html',
                context = {
                    'workspace' : workspace,
                    'content_context' : content_context,
                    'instance_name' : instance_name
                })    
    
@csrf_exempt
def save_instance(request):
    data = json.loads(request.body.decode('utf-8'))['data']
    filename = data['filename']
    wolfy_tts_middleware.save_file(filename)
    return HttpResponse('true')


@csrf_exempt
def combine_audio_instance(request):
    data = json.loads(request.body.decode('utf-8'))['data']
    audio_list = data['audio_list']
    workspace = data['workspace']
    a = WolfyTTSMiddleware(workspace, _id_ = audio_list[0])

    for i in range(1,len(audio_list)):
        if audio_list[i].startswith('s_'):
            silence = int(audio_list[i].split('_')[-1])
            a.add_silence_audio(silence)
        else:
            a += WolfyTTSMiddleware(workspace, audio_list[i])
    return HttpResponse('true')


@csrf_exempt
def regenerate(request):
    data = json.loads(request.body.decode('utf-8'))['data']
    _ids_ = data['_ids_']
    context = wolfy_tts_middleware.regenerate_by_ids(_ids_)
    return JsonResponse(context)
