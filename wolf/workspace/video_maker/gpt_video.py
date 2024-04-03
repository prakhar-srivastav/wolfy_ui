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
import uuid
import shutil
import json
import subprocess


"""
I am using CLIP to identify obvious bad targets and remove them
"""

def kill_child_processes(parent_pid = os.getpid(), sig=signal.SIGTERM):
    import pdb; pdb.set_trace()
    try:
        parent = psutil.Process(parent_pid)
    except psutil.NoSuchProcess:
        return
    children = parent.children(recursive=True)  # Get all child processes
    for process in children:
        print(f"Killing child process {process.pid}")
        process.send_signal(sig)


def _sentence_splitter_(
                    text,
                    ):
    import pysbd
    segmenter = pysbd.Segmenter(language="en", clean=False)
    sentences = segmenter.segment(text)
    return sentences


def save_frame(args):
    video_path, i_s, output_dir = args
    clip = VideoFileClip(video_path)
    for i in i_s:
        frame_path = os.path.join(output_dir, f"{i}.png")
        clip.save_frame(frame_path, t=i)


def divide_chunks(lst, n):
    chunk_size = len(lst) // n
    chunks = [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
    remainder = len(lst) % n
    if remainder:
        for i in range(1, remainder + 1):
            chunks[-i].append(lst[-i])
    
    return chunks


def make_image_out_of_movies(video_path):
    output_dir = 'image_of_movies'
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok = True)
    
    duration = int(VideoFileClip(video_path).duration)
    num_workers = 16
    inps = [i for i in range(0, duration, 1)]
    inps = divide_chunks(inps, num_workers)
    inps = [(video_path, x, output_dir) for x in inps]
    with ProcessPoolExecutor() as executor:
        list(executor.map(save_frame, inps))


def read_json(filename):
    j = open(filename, 'r')
    json_object =  json.loads(j.read())
    j.close()
    return json_object


def save_json(request_body, filename):
    json_object = json.dumps(request_body, indent=4)    
    with open(filename, "w") as outfile:
        outfile.write(json_object)


def generate_clip_scores(folder_path, full_text) -> dict:

    image_path_list = os.listdir(folder_path)
    image_path_list = [folder_path + '/' + x for x in image_path_list]

    try:
        shutil.rmtree('clip_data')
    except:
        pass
    os.makedirs('clip_data',exist_ok = True)

    hash = uuid.uuid4().hex + '.json'
    save_json({
        'full_text' : full_text,
        'folder_path' : folder_path,
        'image_path_list' : image_path_list,
    },
    hash)

    arg = read_json(hash)

    full_text = arg.get('full_text')
    folder_path = arg.get('folder_path')
    image_path_list = arg.get('image_path_list')

    text = _sentence_splitter_(full_text)
    text_map = {}
    for te in text:
        text_map[te] = []

    CHUNK = 50
    for i in tqdm(range(0,len(image_path_list),CHUNK)):

        ma = 0
        hash2 = uuid.uuid4().hex + '.json'
        result_path = os.path.join('clip_data', hash2)
        command = ["python3", "generate_clip_score_worker.py", hash, str(i), str(i + CHUNK), result_path]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            cur_data = read_json(result_path)
            for te in text:
                text_map[te].extend(cur_data[te])
            ma += 1
        else:
            raise


    for key, value in text_map.items():
        text_map[key].sort()
    return text_map


if __name__ == '__main__':

    full_text = """Peter, this engineer, has these super intense nightmares where it feels like he and all his loved ones are caught up in this wild, alien invasion scenario, fighting off some mysterious enemy. 
    It's gotten so bad that it's putting a real strain on things with his wife, Alice, and his daughters, Hanna and Lucy. Despite not being super into the idea, he ends up dragging himself to a clinic to get some psychiatric help. But here's where it gets even crazier: he bumps into another patient who's having the exact same nightmares. And this guy tells him that the doctors are just going to try to dull these visions, making Peter think that maybe, just maybe, these aren't just nightmares but actual premonitions of some alien invasion that's about to happen.

    Peter's worst fears weren't just bad dreams—they were eerily accurate premonitions. That very night, the sky lights up as invading spaceships start laying waste to the city. Amidst the chaos, Peter and Alice quickly turn their apartment into a makeshift bunker, trying to shut out the terrifying sounds of battle raging outside. In a heart-stopping moment, an alien soldier clad in armor smashes through their defenses, only to stumble upon Lucy cowering under a table. The soldier hesitates, seemingly intrigued by the sight of the little girl, giving Peter and Alice just the window they need to take the invader down. Now armed with the soldier's weapon, Peter steels himself, ready to lead his family to safety, navigating through the ruins of their once peaceful life.
    Though we later found out that this weapon has a tracking system using which its owner can detect the location of weapon

    Taking a cue from his all-too-real visions, Peter and his crew decide it's time to make a move to the one place they figure they'll be safe—the factory where Peter clocks in every day. In a moment of pure movie-hero stuff, Peter somehow gets past the fancy security on the alien rifle and takes out the guards at their building's exit. They sneak their way to a tunnel that's supposed to be their secret path to the factory. But just as they're making progress, a bomb goes off, leaving Alice injured. Just when they're trying to catch their breath, guess who shows up? The alien soldier from their apartment, hot on their trail because of some tracking device on the rifle Peter nabbed. But here's the twist—when the soldier whips off his helmet, the guy looks...human. With the tables turned, Peter makes him carry Alice all the way to the factory. And it's there they find out from Peter's boss, David, that this whole invasion scenario? They've been bracing for it for years.

    A medic checks out Alice but hits Peter with the gut punch that she's beyond saving. As if things couldn't get any more intense, the captured soldier, now bound for what looks like a grim end courtesy of David's crew, throws a lifeline—shouting over that he's the key to saving Alice. Peter's at a crossroads but decides to stick with the soldier, if there's even a sliver of hope for Alice. Meanwhile, David steps up, arranging for their kids to be whisked away to a subway station, where a train's ready to shuttle them to some kind of safe haven, a base far from the chaos unfolding around them.

    In an unexpected twist, the soldier drops a bombshell on Peter: Alice isn't just your everyday person; she's a synthetic being, an AI. The only way to pull her back from the brink is for her to tap into an alternative power source, and that source is none other than Peter himself. Guided by the soldier, Peter, in a move that's as shocking as it is brave, slices open his own chest with a pocket knife. And there it is—the undeniable proof that Peter, too, is a synthetic.
    The soldier hooks up a cable between Peter and Alice, linking them in a way that's straight out of a sci-fi novel. As Peter's consciousness fades, he's plunged into what he once believed were premonitions of a future conflict. But the truth is far more complex and haunting. These aren't warnings of what's to come; they're vivid, detailed recollections of a past war, experiences engraved in his synthetic memory, playing back in full force as he drifts into unconsciousness.

    Driven by a deep-seated fear that android workers—referred to as "synthetics"—might revolt against their creators, the military launched a preemptive strike against these unarmed beings. But the synthetics, pushed to their limits, fought back with unexpected ferocity, eventually succeeding in banishing humans from the planet entirely. Amid this backdrop of war and mistrust, Peter and Alice found each other, two synthetics caught in the crossfire of a battle they never wished for.
    Their paths crossed with Hanna and Lucy during the chaos, two more synthetics who, like them, were fighting for survival in a world that had turned against them. As the dust settled and they emerged victorious, the weight of what they had done—and the fear of a potential human counterattack—loomed heavily over them. To escape this burden and the constant dread of retribution, most synthetics, Peter and his family included, chose to erase their memories, effectively rebooting their lives in blissful ignorance of their true identities and the history they had shaped.
    Peter rubs the sleep from his eyes, and there's Miles, looking all soldier-like, filling him in on a whopper: humans have been calling Mars home for half a century now. Peter, well, he was bracing himself to come face to face with what he thought would be monstrosities—instead, he finds families. Kids running around, even. And Lucy, hiding shyly under the table, seals the deal for him: no way he can bring himself to harm a soul. So, Peter and Alice, they make their farewells with Miles on a good note, all while the humans are making quite the entrance, busting through the factory roof. As they're catching the train out of there, David tells Peter that he and a few other synthetic  hold onto their memories, for when humans would show up again. And Peter, ever the optimist, throws out that maybe, just maybe, there's a shot at peace between the humans and the synths one day.
    """


    video_path = '/home/prakharrrr4/wolfy_ui/wolf/workspace/video_maker/extinction.mp4'
    folder_path = '/home/prakharrrr4/wolfy_ui/wolf/workspace/video_maker/image_of_movies'

    st = time.time()
    text_map = generate_clip_scores(folder_path, full_text)
    et = time.time()
    print("TIME : ", et - st)
    import pdb; pdb.set_trace()


