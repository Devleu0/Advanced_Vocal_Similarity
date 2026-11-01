import csv
import glob
import os
import shutil

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import torch

import config
from embedding_store import list_embedding_files
from logger import log
from models import EMBEDDING_MODELS
from similarity import (
    artist_similarity, ensemble_matrices, score_normalize, video_similarity_matrix,
)


def run_tag(models, scoring, score_norm, centered):
    """결과 폴더 이름: 어떤 설정으로 만든 결과인지 한눈에 구분합니다."""
    parts = ["+".join(models), scoring]
    if score_norm:
        parts.append(score_norm)
    if centered:
        parts.append("centered")
    return "_".join(parts)


def _load_embeddings(model):
    """{아티스트: [임베딩]}, [(아티스트/파일, 임베딩)] 을 반환합니다. 로드 실패한 아티스트는 건너뜁니다."""
    artist_embs, labeled = {}, []
    artist_dirs = sorted(d for d in glob.glob(os.path.join(config.DB_DIR, "*")) if os.path.isdir(d))
    for adir in artist_dirs:
        name = os.path.basename(adir)
        files = list_embedding_files(adir, model, EMBEDDING_MODELS)
        if not files:
            continue
        try:
            embs = [torch.load(f, weights_only=True) for f in files]
        except Exception as e:
            log.error(f"  [오류] '{name}'의 임베딩 로드 중 에러 발생: {e}", exc_info=True)
            continue
        artist_embs[name] = embs
        labeled += [(f"{name}/{os.path.basename(f)}", e) for f, e in zip(files, embs)]
    return artist_embs, labeled


def generate_and_visualize_similarity(models=None):
    """
    아티스트 간 유사도 행렬을 계산해 클러스터맵/텍스트로 저장합니다.

    models 가 여럿이면(앙상블) 모델별 행렬을 공통 아티스트 기준으로 평균합니다.
    결과는 database/results/<태그>/ 에 저장되고, 최신 결과는 database/ 바로 아래에도 복사됩니다.
    """
    models = list(models or config.ENSEMBLE_MODELS or [config.EMBEDDING_MODEL])
    log.info("\n" + "=" * 50)
    log.info(f"[*] [Step 5] 유사도 계산 및 시각화 시작 (models={models}, scoring={config.ARTIST_SCORING})")
    log.info("=" * 50)

    results, labeled_first = [], None
    for model in models:
        artist_embs, labeled = _load_embeddings(model)
        if not artist_embs:
            log.warning(f"[!] '{model}' 모델의 임베딩이 없습니다.")
            continue
        names, matrix = artist_similarity(
            artist_embs, config.ARTIST_SCORING, config.USE_CENTERING,
            config.CENTERING_MIN_ARTISTS, config.VIDEO_TOPK,
        )
        if config.SCORE_NORM == "snorm":
            matrix = score_normalize(matrix)
        results.append((names, matrix))
        labeled_first = labeled_first or labeled

    if not results:
        log.warning("[!] 비교할 임베딩이 없습니다.")
        return
    artists, matrix = ensemble_matrices(results)
    if len(artists) < 2:
        log.warning("[!] 비교할 가수가 2명 이상이어야 시각화가 가능합니다.")
        return

    tag = run_tag(models, config.ARTIST_SCORING, config.SCORE_NORM, config.USE_CENTERING)
    out_dir = os.path.join(config.DB_DIR, "results", tag)
    os.makedirs(out_dir, exist_ok=True)

    df = pd.DataFrame(matrix.numpy(), index=artists, columns=artists)
    txt_path = os.path.join(out_dir, "vocal_similarities.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"=== Vocal Similarity Matrix ({tag}) ===\n")
        f.write(df.to_string())
    log.info(f"  -> 텍스트 결과물 저장: {txt_path}")

    fig_size = max(8, len(artists))
    g = sns.clustermap(
        df,
        annot=True,
        fmt=".2f",
        cmap="mako",
        vmin=min(0.0, float(matrix.min())),
        vmax=max(1.0, float(matrix.max())),
        figsize=(fig_size, fig_size),
    )
    g.fig.suptitle(f"Vocal Similarity Clustermap ({tag})", y=1.05)
    png_path = os.path.join(out_dir, "vocal_clustermap.png")
    g.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close("all")
    log.info(f"  -> 시각화 결과물 저장: {png_path}")

    if config.SAVE_VIDEO_MATRIX and labeled_first:
        labels, vmat = video_similarity_matrix(labeled_first, config.USE_CENTERING)
        csv_path = os.path.join(out_dir, "vocal_video_similarities.csv")
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([""] + labels)
            for label, row in zip(labels, vmat.tolist()):
                writer.writerow([label] + [f"{v:.4f}" for v in row])
        log.info(f"  -> 영상 단위 유사도 저장: {csv_path}")

    # 최신 결과를 기존 위치에도 복사 (하위 호환)
    for name in ("vocal_similarities.txt", "vocal_clustermap.png"):
        src = os.path.join(out_dir, name)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(config.DB_DIR, name))
