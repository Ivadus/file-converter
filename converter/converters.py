import os
from PIL import Image
import pillow_heif
import ffmpeg
import rawpy
import imageio

def convert_image(file_path, output_dir, output_format):
    pillow_heif.register_heif_opener()
    image = Image.open(file_path)
    filename, _ = os.path.splitext(os.path.basename(file_path))
    output_path = os.path.join(output_dir, filename + output_format)
    image.save(output_path)
    return output_path

def convert_video(file_path, output_dir):
    filename, _ = os.path.splitext(os.path.basename(file_path))
    output_path = os.path.join(output_dir, filename + '.mp4')
    ffmpeg.input(file_path).output(output_path, vcodec='libx264').run(overwrite_output=True, quiet=True)
    return output_path

def convert_raw(file_path, output_dir, output_format):
    with rawpy.imread(file_path) as raw:
        rgb = raw.postprocess(gamma=(2.222, 4.5), output_bps=8)
    filename, _ = os.path.splitext(os.path.basename(file_path))
    output_path = os.path.join(output_dir, filename + output_format)
    imageio.imsave(output_path, rgb)
    return output_path

CONVERSION_FUNCTIONS = {
    '.heic': convert_image,
    '.tiff': convert_image,
    '.bmp': convert_image,
    '.webp': convert_image,
    '.mov': convert_video,
    '.avi': convert_video,
    '.mkv': convert_video,
    '.cr2': convert_raw,
    '.nef': convert_raw,
    '.arw': convert_raw,
}