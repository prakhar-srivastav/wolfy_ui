import utility
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from audio_generator import WolfyTTSMiddleware


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
    c_sub = utility.get_hash() + '.sub'
    c_video = utility.get_hash() + 'mp4'

    utility.combine_audio(audio_files, c_audio, intro_silence = 1)
    # utility.make_subtitles(c_audio, c_sub)
    utility.add_reverb(c_audio)

    create_video(c_audio, c_sub, c_video, data_files)



if __name__ == '__main__':

    _make_({
        'workspace' : 'video_1',
        'speech' : 'part_test2'
    })
