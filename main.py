import os
import glob
import config
from utils import setup_korean_font
from models import load_speech_brain_model, load_audio_separator_model
from processing import process_url
from visualization import generate_and_visualize_similarity

def main():
    """
    전체 보컬 유사도 분석 파이프라인을 실행합니다.
    """
    # 1. 초기 설정
    print("="*50)
    print(" End-to-End Vocal Similarity Pipeline Started")
    print("="*50)
    print(f"[*] 사용할 디바이스: {config.DEVICE}")
    setup_korean_font()

    # 2. 모델 로드
    classifier = load_speech_brain_model()
    separator = load_audio_separator_model()

    # 3. 입력 파일 처리
    txt_files = glob.glob(os.path.join(config.INPUT_DIR, "*.txt"))
    if not txt_files:
        print("
[!] 'inputs' 폴더에 처리할 .txt 파일이 없습니다.")
        return

    for txt_file in txt_files:
        artist_name = os.path.splitext(os.path.basename(txt_file))[0]
        print(f"
>> 처리 중인 아티스트: [{artist_name}]")
        
        with open(txt_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        for idx, url in enumerate(urls, 1):
            print(f"  [{idx}/{len(urls)}] Processing: {url}")
            process_url(url, artist_name, separator, classifier)
    
    # 4. 최종 분석 및 시각화
    generate_and_visualize_similarity()
    
    print("
[*] 모든 파이프라인 처리가 완료되었습니다!")

if __name__ == "__main__":
    main()
