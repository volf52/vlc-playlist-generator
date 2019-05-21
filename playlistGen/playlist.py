import argparse
import os
import subprocess
import lxml.etree as ET
from typing import List, Tuple
import sys
from urllib.request import pathname2url, url2pathname
from moviepy.video.io.VideoFileClip import VideoFileClip


def generate():
    args = get_args()
    root_dir = args.root_dir
    if root_dir is None:
        root_dir = os.getcwd()
    file_paths, encoded_paths = get_files(root_dir)
    fname = os.path.basename(root_dir)
    if args.fname is not None:
        fname = args.fname

    xml_txt = get_xml(fname, file_paths, encoded_paths)
    # print(xml_txt)
    with open(f"{fname}.xspf", "wb") as f:
        f.write(xml_txt)


def get_args():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "-d",
        "--directory",
        action="store",
        dest="root_dir",
        help="The directory with files (Default = current dir)",
    )
    parser.add_argument(
        "-f",
        "--file",
        action="store",
        dest="fname",
        help="The filename for playlist (Default = dir name)",
    )
    return parser.parse_args()


def get_files(root_dir: str) -> Tuple[List[str], List[str]]:
    ret_list = [
        os.path.join(root, f) for root, dirs, files in os.walk(root_dir) for f in files
    ]
    encoded_list = [f"file:{pathname2url(x)}" for x in ret_list]
    return ret_list, encoded_list


def get_xml(dirname: str, file_list: list, encoded_list: list) -> bytes:
    NSMAP = {
        None: "http://xspf.org/ns/0/",
        "vlc": "http://www.videolan.org/vlc/playlist/ns/0/",
    }
    playlist = ET.Element("playlist", version="1", nsmap=NSMAP)
    ET.SubElement(playlist, "title").text = dirname
    tracklist = ET.SubElement(playlist, "trackList")

    for i, (normal_name, encoded_name) in enumerate(zip(file_list, encoded_list)):
        track = ET.SubElement(tracklist, "track")
        ET.SubElement(track, "location").text = encoded_name
        ET.SubElement(track, "duration").text = str(get_duration(normal_name))
        ext = ET.SubElement(
            track, "extension", application="http://www.videolan.org/vlc/playlist/0"
        )
        ET.SubElement(ext, "{%s}id" % NSMAP["vlc"]).text = str(i)

    extension_outer = ET.SubElement(
        playlist, "extension", application="http://www.videolan.org/vlc/playlist/0"
    )
    for i, path in enumerate(file_list):
        ET.SubElement(extension_outer, "{%s}item" % NSMAP["vlc"], tid=str(i))
    tree = ET.ElementTree(playlist)
    return ET.tostring(
        tree, xml_declaration=True, encoding="UTF-8", method="xml", pretty_print=True
    )


def get_duration(file_path: str) -> int:
    result = subprocess.Popen(
        ["ffprobe", file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    lines = result.stdout.readlines()
    clip = VideoFileClip(file_path)
    dur = int(clip.duration * 1000)
    clip.reader.close()
    clip.audio.reader.close_proc()
    return dur


if __name__ == "__main__":
    generate()
