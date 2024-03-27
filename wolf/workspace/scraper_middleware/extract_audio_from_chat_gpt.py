import shutil


def extract_audio_from_chat_gpt(text, file_path, speaker):
    # output = speaker.split('_')[-1]
    output = "/home/prakharrrr4/pegasus/spider/dan_clipped.wav"
    shutil.copyfile(output, file_path)

