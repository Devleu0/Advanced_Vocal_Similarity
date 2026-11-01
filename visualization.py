import os
import glob
import torch
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import config
from logger import log
from similarity import build_master_profiles, compute_similarity_matrix

def generate_and_visualize_similarity():
    """
    아티스트별 마스터 프로필을 생성하고, 유사도 행렬을 계산하여
    클러스터맵과 텍스트 파일로 저장합니다.
    """
    log.info("\n" + "="*50)
    log.info("[*] [Step 5] 전체 마스터 프로필 생성 및 시각화 시작")
    log.info("="*50)
    
    artist_dirs = [d for d in glob.glob(os.path.join(config.DB_DIR, "*")) if os.path.isdir(d)]
    artist_embs = {}

    for adir in artist_dirs:
        artist_name = os.path.basename(adir)
        emb_files = glob.glob(os.path.join(adir, "emb_*.pt"))
        if not emb_files:
            continue

        try:
            artist_embs[artist_name] = [torch.load(f, weights_only=True) for f in emb_files]
        except Exception as e:
            log.error(f"  [오류] '{artist_name}'의 임베딩 로드 중 에러 발생: {e}", exc_info=True)
            continue

    master_profiles = build_master_profiles(
        artist_embs, center=config.USE_CENTERING, min_artists=config.CENTERING_MIN_ARTISTS
    )

    if len(master_profiles) < 2:
        log.warning("[!] 비교할 가수가 2명 이상이어야 시각화가 가능합니다.")
        return

    artists, matrix = compute_similarity_matrix(master_profiles)

    df = pd.DataFrame(matrix.numpy(), index=artists, columns=artists)
    
    txt_path = os.path.join(config.DB_DIR, "vocal_similarities.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=== Vocal Similarity Matrix ===\n")
        f.write(df.to_string())
    log.info(f"  -> 텍스트 결과물 저장: {txt_path}")

    fig_size = max(8, len(artists))
    g = sns.clustermap(
        df, 
        annot=True, 
        fmt=".2f", 
        cmap="mako", 
        vmin=min(0.0, float(matrix.min())),
        vmax=1.0,
        figsize=(fig_size, fig_size)
    )
    g.fig.suptitle("Vocal Similarity Clustermap", y=1.05)
    
    png_path = os.path.join(config.DB_DIR, "vocal_clustermap.png")
    g.savefig(png_path, dpi=300, bbox_inches='tight') 
    plt.close('all') 
    log.info(f"  -> 시각화 결과물 저장: {png_path}")
