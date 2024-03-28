

def extract_audio_from_chat_gpt(text, file_path, speaker_wav = 'echo'):
    from pathlib import Path
    from openai import OpenAI
    client = OpenAI(api_key = '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')

    response = client.audio.speech.create(
    input=text,
    model="tts-1-hd",
    voice="echo",
    )
    response.stream_to_file(file_path)

extract_audio_from_chat_gpt("Have Faith in God", 'duff.mp3')