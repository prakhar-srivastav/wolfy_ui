from moviepy.editor import VideoFileClip
import moviepy.video.fx.all  as vfx
import os
from PIL import Image, ImageFile
from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
import time
import psutil
from transformers import CLIPProcessor, CLIPModel
import signal
import sys
import json

def read_json(filename):
    j = open(filename, 'r')
    json_object =  json.loads(j.read())
    j.close()
    return json_object


def save_json(request_body, filename):
    json_object = json.dumps(request_body, indent=4)    
    with open(filename, "w") as outfile:
        outfile.write(json_object)

def _sentence_splitter_(
                    text,
                    ):
    import pysbd
    segmenter = pysbd.Segmenter(language="en", clean=False)
    sentences = segmenter.segment(text)
    return sentences


def generate_clip_scores(hash, st, et, result_path):

    arg = read_json(hash)

    full_text = arg.get('full_text')
    folder_path = arg.get('folder_path')
    image_path_list = arg.get('image_path_list')

    text = _sentence_splitter_(full_text)
    image_path_list = os.listdir(folder_path)[st:en]

    image0 = [folder_path + '/' + x for x in image_path_list]
    images = [Image.open(x) for x in image0]

    print(len(images))

    text = _sentence_splitter_(full_text)
    text_map = {}
    for te in text:
        text_map[te] = []

    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to("cuda")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    inputs = processor(text=text, images=images, return_tensors="pt", padding=True)
    outputs = model(**inputs.to("cuda"))
    logits_per_image = outputs.logits_per_image
    ma = 0
    _id_ = image0
    for te in text:
        for j in range(len(_id_)):
            yo = int(_id_[j].split('/')[-1].split('.')[0])
            text_map[te].append((yo, float(logits_per_image[j][ma])))
        ma += 1

    save_json(text_map, result_path)

if __name__ == '__main__':
    hash = sys.argv[1]
    st = int(sys.argv[2])
    en = int(sys.argv[3])
    result_path = sys.argv[4]

    generate_clip_scores(hash, st, en ,result_path)