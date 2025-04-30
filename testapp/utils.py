import os
import subprocess
from pdf2image import convert_from_path
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

def convert_ppt_to_images(pptx_file, pdf_file, output_dir):
    """PPTX 파일을 PDF로 변환한 후 슬라이드별 이미지를 저장하는 함수"""

    # 출력 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    # 1. PPTX → PDF 변환 (LibreOffice CLI 사용)
    cmd = f'soffice --headless --invisible --convert-to pdf --outdir "{os.path.dirname(pdf_file)}" "{pptx_file}"'
    subprocess.run(cmd, shell=True)

    # 2. PDF → 이미지 변환
    images = convert_from_path(pdf_file)

    # 3. 이미지 저장
    image_paths = []
    for i, image in enumerate(images):
        img_path = os.path.join(output_dir, f'slide_{i+1:03d}.png')
        image.save(img_path, 'PNG')
        image_paths.append(img_path)

    return image_paths

def create_slide_clip(image_path, audio_path):
    """이미지 + 오디오 → 단일 비디오 클립"""
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    img_clip = ImageClip(image_path).with_duration(duration).with_audio(audio)
    return img_clip

def create_full_lecture_video(slide_dir, audio_dir, output_path):
    """여러 슬라이드 + 오디오 → 하나의 통합 영상"""
    # 파일 정렬
    slide_files = sorted([f for f in os.listdir(slide_dir) if f.lower().endswith((".png", ".jpg"))])
    audio_files = sorted([f for f in os.listdir(audio_dir) if f.lower().endswith((".mp3", ".wav", ".m4a"))])

    if len(slide_files) != len(audio_files):
        raise ValueError("슬라이드 이미지 수와 오디오 파일 수가 일치하지 않습니다.")

    clips = []
    for slide, audio in zip(slide_files, audio_files):
        slide_path = os.path.join(slide_dir, slide)
        audio_path = os.path.join(audio_dir, audio)
        print(f"📌 슬라이드와 오디오 연결 중: {slide} + {audio}")
        clip = create_slide_clip(slide_path, audio_path)
        clips.append(clip)

    final_video = concatenate_videoclips(clips, method="compose")

    final_video.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile="temp-audio.m4a",
        remove_temp=True,
    )

    print(f"\n✅ 최종 영상 저장 완료: {output_path}")
