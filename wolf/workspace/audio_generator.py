import uuid
import os
import threading
import time
from TTS.api import TTS
import whisper
import uuid
from pydub import AudioSegment
from pydub.playback import play
from jiwer import wer
import json
import sys
sys.path.append('/home/prakharrrr4/wolfy_ui/wolf/wolf')
import setting2 as settings
# from django.conf import settings

"""
AudioAudit :
- synthesize function :: It will create the audio data and it will keep the timing of the genrated audio file to later on correct

audio_audit_object.synthesize(text : str = None, speaker : str = None) -> compiles speaker wav output and internally prepare timings of the wav
                                            loads the audio and time mappings
    audio_audit_object.feedback(timings : list = []) -> Takes the timings of the faulty audios and refinds the incorrect audiofiles and regenerates along 
                                            with modified timings. 
                                            modifies the audio and time mappings
    audio_audit.save_file(result_path : str = None)    
"""

class AudioGenerator(object):

    def __init__(self):
        self.timings = dict()
        self.combined_audio = None
        self._id_ = uuid.uuid4().hex
        self.tts =  TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
        self.PATH = '/home/prakharrrr4/pegasus/data/tmp'


    def _sentence_splitter_(
                    self,
                    text,
                    ):
        from TTS.tts.layers.xtts.tokenizer import VoiceBpeTokenizer
        import torch
        import pysbd

        vocab_file = "/home/prakharrrr4/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2/vocab.json"
        tokenizer = VoiceBpeTokenizer(vocab_file)

        def get_token(sent):
            return torch.IntTensor(tokenizer.encode(sent, lang=language)).unsqueeze(0).to("cuda").shape[-1]
        
        limit = 300
        segmenter = pysbd.Segmenter(language="en", clean=False)
        sentences = segmenter.segment(text)
        result = [sentences[0]]
        for i in range(1,len(sentences)):
            sen = sentences[i]
            _trial_ = (" ").join([result[-1],sen])
            sen_tok = get_token(_trial_)
            if sen_tok <= limit:
                result[-1] = _trial_
            else:
                result.append(sen)
        return result



    def prepare_data_from_audio_files_and_texts(self, sentences, audio_files):
        from pydub import AudioSegment
        from pydub.playback import play

        time_mappings=  {}
        combined_audio = AudioSegment.empty()
        
        last_time = 0
        for i in range(len(audio_files)):
            file = audio_files[i]
            sen = sentences[i]
            current_audio0 = AudioSegment.from_file(file)
            current_audio = current_audio0 + AudioSegment.silent(duration=250)
            new_last_time = last_time +  len(current_audio)
            time_mappings[(last_time, new_last_time)] = (current_audio0, sen)
            combined_audio += current_audio
            last_time = new_last_time

        return time_mappings, combined_audio


    def synthesize(self, text = '', speaker = '', output = ''):

        self.speaker = speaker
        _folder_hash_ = uuid.uuid4().hex
        _hash_ = uuid.uuid4().hex + '.wav'

        sentences = self._sentence_splitter_(text)
        audio_files = []
        _folder_path_ = os.path.join(self.PATH, _folder_hash_)

        os.makedirs(_folder_path_, exist_ok = True)

        itr = 0

        for sen in sentences:
            
            path = os.path.join(_folder_path_,_folder_hash_ + '_{}.wav'.format(itr))
            self.tts.tts_to_file(text=sen,  
                            file_path= path,
                            speaker_wav=[speaker],
                            language="en",
                            split_sentences=False 
                            )
            audio_files.append(path)
            itr += 1

        self.timings, self.combined_audio = self.prepare_data_from_audio_files_and_texts(sentences, audio_files)


    def feedback(self, faulty_timings, is_seconds = False):
    
        if is_seconds:
            faulty_timings = [time*1000 for time in faulty_timings]

    
        faulty_timings.sort()      
        bad_keys = set()
        for f in faulty_timings:
            for (s,e), data in self.timings.items():
                if f>=s and f<=e:
                    bad_keys.add((s,e))
        
        _folder_hash_ = uuid.uuid4().hex
        _folder_path_ = os.path.join(self.PATH, _folder_hash_)
        os.makedirs(_folder_path_, exist_ok = True)
        itr = 0

        audio_files = []
        sentences = []

        for key, value in self.timings.items():
            cur_audio, sen = value
            path = os.path.join(_folder_path_,_folder_hash_ + '_{}.wav'.format(itr))
            if key in bad_keys:
                print(itr,'tts')
                self.tts.tts_to_file(text=sen,  
                                file_path= path,
                                speaker_wav=[self.speaker],
                                language="en",
                                split_sentences=False 
                                )
            else:
                print(itr,'audio')
                cur_audio.export(path, format="wav")
            audio_files.append(path)
            sentences.append(sen)
            itr += 1

        self.timings, self.combined_audio = self.prepare_data_from_audio_files_and_texts(sentences, audio_files)


    def save_file(self, result_path):
        self.combined_audio.export(result_path, format="wav")    



class WolfyTTSMiddleware(object):

    def __init__(self, workspace, _id_ : str = None):
        self.workspace = workspace
        self.PATH = os.path.join(settings.MEDIA_ROOT,'workspace')
        self._id_ = _id_ if _id_ else uuid.uuid4().hex
        os.makedirs(self.get_folder_path(),exist_ok = True)


    def _sentence_splitter_(
                    self,
                    text,
                    ):
        from TTS.tts.layers.xtts.tokenizer import VoiceBpeTokenizer
        import torch
        import pysbd

        vocab_file = "/home/prakharrrr4/.local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2/vocab.json"
        tokenizer = VoiceBpeTokenizer(vocab_file)

        def get_token(sent):
            return torch.IntTensor(tokenizer.encode(sent, lang="en")).unsqueeze(0).to("cuda").shape[-1]
        
        limit = 130
        segmenter = pysbd.Segmenter(language="en", clean=False)
        sentences = segmenter.segment(text)
        result = [sentences[0]]
        for i in range(1,len(sentences)):
            sen = sentences[i]
            _trial_ = (" ").join([result[-1],sen])
            sen_tok = get_token(_trial_)
            if sen_tok <= limit:
                result[-1] = _trial_
            else:
                result.append(sen)
        for sen in result:
            print(get_token(sen))
        return result


    def read_json(self, filename):
        j = open(filename, 'r')
        json_object =  json.loads(j.read())
        j.close()
        return json_object


    def save_json(self, request_body, filename):
        json_object = json.dumps(request_body, indent=4)    
        with open(filename, "w") as outfile:
            outfile.write(json_object)


    def save_with_silence(self, text="", file_path = "", speaker_wav = "", silence = 250):
        if text == "":
            current_audio = AudioSegment.silent(duration=silence)
        else:
            if not hasattr(self, 'tts'):
                self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)

            self.tts.tts_to_file(text=text,  
                                    file_path= file_path,
                                    speaker_wav= speaker_wav,
                                    language="en",
                                    split_sentences=False 
                                    )
            current_audio0 = AudioSegment.from_file(file_path)
            current_audio = current_audio0 + AudioSegment.silent(duration=silence)
        time = len(current_audio)
        current_audio.export(file_path, format="wav") 
        return time


    def save_audio_instance(
                            self,
                            text : str = None,
                            file_path : str = None,
                            speaker_wav : str = None,
                            silence : float = None,
                            rank : int = None,
                            chapter : int = None,
                            ):

            time = self.save_with_silence(text=text, file_path= file_path, speaker_wav=speaker_wav, silence = silence)
            asr_speech, wer, segment_timestamps = self.get_asr_and_wer(text, file_path)
            data = {
                'time' : time,
                'speaker' : speaker_wav,
                'rank' : rank,
                'chapter' : chapter,
                'speech' : text,
                'asr_speech' : asr_speech,
                'wer' : wer,
                'silence' : silence,
                'segment_timestamps' : segment_timestamps
            }
            data_path = file_path.replace("speech.wav","data.json")
            self.save_json(data, data_path)


    def get_asr_and_wer(self, text, audio_file):
        if text == "":
            return "" , 0.0, None
        if not hasattr(self, 'asr_model'):
            self.asr_model = whisper.load_model("base")
        result = self.asr_model.transcribe(audio_file)
        return result['text'], wer(text, result['text']), result


    def get_folder_path(self):
        return  os.path.join(self.PATH,
                os.path.join(self.workspace,
                os.path.join('audio',self._id_)))


    def synthesize(self, text = '', speaker = '', output = ''):

        speaker = self.get_speaker_path(speaker)
        _folder_path_ = self.get_folder_path()
        sentences = self._sentence_splitter_(text)
        audio_files = []

        os.makedirs(_folder_path_, exist_ok = True)

        for itr in range(len(sentences)):
            sen = sentences[itr]
            _hash_ = uuid.uuid4().hex
            audio_folder = os.path.join(_folder_path_, _hash_)
            os.mkdir(audio_folder)
            audio_file = os.path.join(audio_folder, 'speech.wav')
            self.save_audio_instance(text = sen,
                                     file_path = audio_file,
                                     speaker_wav = speaker,
                                     silence = 250,
                                     rank = itr + 1,
                                     chapter = 1,
                                     )


    def get_speaker_path(self, speaker_name):
        PATH = os.path.join(settings.MEDIA_ROOT,'data/audio_data')
        return PATH + '/' + speaker_name + '.wav' 


    def filesystem_to_media_url(self, absolute_file_path):
        media_root = os.path.normpath(settings.MEDIA_ROOT)
        absolute_file_path = os.path.normpath(absolute_file_path)
        
        if absolute_file_path.startswith(media_root):
            relative_path = absolute_file_path[len(media_root):].lstrip(os.path.sep)
            media_url = os.path.join(settings.MEDIA_URL, relative_path).replace('\\', '/')
            return media_url
        else:
            raise ValueError("The provided file path is not under MEDIA_ROOT.")


    def get_context(self, _ids_=None):
        folder_path = self.get_folder_path()
        audio_files = os.listdir(folder_path)
        
        context = dict()
        for audio_file in audio_files:
            if _ids_ and audio_file not in _ids_:
                continue
            audio_path = os.path.join(folder_path,audio_file)
            data = self.read_json(os.path.join(audio_path, 'data.json'))
            speech_wav = os.path.join(audio_path, 'speech.wav')
            key = '{}_{}_{}'.format(
                str(data['chapter']),
                str(data['rank']),
                str(audio_file)
            )
            context[key] = {
                                'time' : data['time']/1000,
                                'rank' : data['rank'],
                                'chapter' : data['chapter'],
                                'speaker' : data['speaker'].split('/')[-1].split('.')[0],
                                'speech' : data['speech'],
                                'asr_speech' : data['asr_speech'],
                                'wer' : data['wer'],
                                'audio_url' : self.filesystem_to_media_url(speech_wav),
                                'hash' : audio_file
                            }
            
        def sort_context(context):
            context_array = []
            for key, value in context.items():
                chapter, rank, _hash_ = key.split('_')
                chapter = int(chapter)
                rank = int(rank)
                context_array.append((chapter, rank, _hash_, key, value))
            context_array.sort()
            context = {}
            for (chapter, rank, _hash_, key, value) in context_array:
                context[key] = value
            return context
        context = sort_context(context)
            
        return context


    def save_file(self, nickname):
        older_folder_path = self.get_folder_path()
        self._id_ = nickname
        new_folder_path = self.get_folder_path()
        os.rename(older_folder_path, new_folder_path)


    def regenerate_by_ids(self, _ids_):
        if type(_ids_) != list:
            _ids_ = [_ids_]
        
        _folder_path_ = self.get_folder_path()

        _new_ids_ = []
        for _id_ in _ids_:
            _new_ids_.append(_id_.split('_')[-1])
        _ids_ = _new_ids_

        for _id_ in _ids_:
            
            audio_folder = os.path.join(_folder_path_, _id_)
            audio_data_path = os.path.join(audio_folder, 'data.json')
            audio_file = os.path.join(audio_folder, 'speech.wav')
            data = self.read_json(audio_data_path)
            self.save_audio_instance(text = data.get('speech'),
                            file_path = audio_file,
                            speaker_wav = data.get('speaker'),
                            silence = data.get('silence'),
                            rank = data.get('rank'),
                            chapter = data.get('chapter'),
                            )
        return self.get_context(set(_ids_))


    def get_internal_context(self):
        folder_path = self.get_folder_path()
        audio_files = os.listdir(folder_path)
        
        context = dict()
        for audio_file in audio_files:
            audio_path = os.path.join(folder_path,audio_file)
            data = self.read_json(os.path.join(audio_path, 'data.json'))
            speech_wav = os.path.join(audio_path, 'speech.wav')
            key = (data['chapter'], data['rank'], audio_file)
            context[key] = {
                                'rank' : data['rank'],
                                'chapter' : data['chapter'],
                                'data' : os.path.join(audio_path, 'data.json'),
                                'audio' : os.path.join(audio_path, 'speech.wav'),
                                'audio_path' : audio_path,
                                'hash' : audio_file,
                                'time' : data['time']
                            }
            
        def sort_context(context):
            context_array = []
            for key, value in context.items():
                (chapter, rank, _hash_) = key
                chapter = int(chapter)
                rank = int(rank)
                context_array.append((chapter, rank, _hash_, key, value))
            context_array.sort()
            context = {}
            for (chapter, rank, _hash_, key, value) in context_array:
                context[key] = value
            return context
        context = sort_context(context)
        return context


    def __iadd__(self, other):
        _a_ = self.get_internal_context()
        _b_ = other.get_internal_context()
        max_chapter = 0
        for (chapter,_,_) in _a_.keys():
            max_chapter = max(max_chapter, chapter)
        
        import shutil
        _a_folder = self.get_folder_path()
        _b_folder = other.get_folder_path()
        for (_,_,_),values in _b_.items():
            audio_path = values['audio_path']
            shutil.copytree(audio_path, _a_folder + '/{}'.format(values['hash']), dirs_exist_ok = True)
            new_path = os.path.join(_a_folder, values['hash'])
            data_path = os.path.join(new_path, 'data.json')
            speech_path = os.path.join(new_path, 'speech.wav')
            data = self.read_json(data_path)
            data['chapter'] += max_chapter
            self.save_json(data, data_path)
        return self


    def get_total_time(self):
        context = self.get_internal_context()
        time = 0
        for key,value in context.items():  
            time += value['time']
        return time


    def add_silence_audio(self, silence = 250):
        context = self.get_internal_context()
        max_c = 1
        max_r = 1
        for c,r,_ in context.keys():
            max_c = max(c,max_c)
        for c,r,_ in context.keys():
            if c == max_c:
                max_r = max(max_r, r) 

        max_r += 1
        file_path = os.path.join(self.get_folder_path(),uuid.uuid4().hex)
        os.mkdir(file_path)
        audio_path = os.path.join(file_path, 'speech.wav')
        self.save_audio_instance(
                            "",
                            audio_path,
                            "",
                            silence,
                            max_r,
                            max_c
                            )


    def get_subtitles(self):
        context = self.get_internal_context()
        subs = []
        timer = 0
        for key, value in context.items():
            data = self.read_json(value['data'])
            if 'segment_timestamps' in data.keys():
                for segment in data['segment_timestamps']['segments']:
                    subs.append({
                        'start' : timer + segment['start'] * 1000,
                        'end' : timer + segment['end'] * 1000,
                        'text' : segment['text']
                    })
            timer += value['time']

        return subs

# obj = WolfyTTSMiddleware('video_test')
# text ="""Let me tell. You are a champion. """
# speaker_name = "/home/prakharrrr4/wolfy_ui/wolf/media/data/audio_data/nick_ted.wav"
# obj.synthesize(text, speaker_name)
# con = obj.get_context()
# import pdb; pdb.set_trace()
# """
#     obj.synthesize(text, speaker_name) -> creates an audio space and return the id
#     obj.get_context() -> prepares the context to be loaded on the UI
#obj.export() -> combines the audio content and make the finale result.mp3 along with srt file
#     obj.combine_spaces() -> combines the two audio_spaces and deletes the other space from the workspace
# obj.improvise() -> refactors the audio files with the bad timings vector given
#     obj.regenerate_ny_ids([ids]) -> refactors the audio files and returns the corrected context of only those ids
#     obj.save_file(filename) -> renames the space to `filename` and mutates the _id_ attribute
#     obj.get_subtitles()
# """