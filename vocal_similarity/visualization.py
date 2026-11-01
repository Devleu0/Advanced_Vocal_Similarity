import glob
import json
import os
import shutil
from typing import Dict, Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import torch

from . import config
from .logger import log
from .similarity import build_master_profile, compute_similarity_matrix

SIMILARITY_TXT_NAME = "vocal_similarities.txt"
CLUSTERMAP_PNG_NAME = "vocal_clustermap.png"
TOP_PAIRS_TXT_NAME = "top_similar_pairs.txt"
TOP_PAIRS_CSV_NAME = "top_similar_pairs.csv"
SIMILARITY_JSON_NAME = "similarity.json"


def similarity_txt_path(db_dir: Optional[str] = None) -> str:
    return os.path.join(db_dir or config.DB_DIR, SIMILARITY_TXT_NAME)


def clustermap_path(db_dir: Optional[str] = None) -> str:
    return os.path.join(db_dir or config.DB_DIR, CLUSTERMAP_PNG_NAME)


def top_pairs_path(db_dir: Optional[str] = None, extension: str = "txt") -> str:
    name = TOP_PAIRS_CSV_NAME if extension == "csv" else TOP_PAIRS_TXT_NAME
    return os.path.join(db_dir or config.DB_DIR, name)


def similarity_json_path(db_dir: str) -> str:
    return os.path.join(db_dir, SIMILARITY_JSON_NAME)


def load_master_profiles(db_dir: Optional[str] = None) -> Dict[str, torch.Tensor]:
    """DB 폴더의 아티스트별 `emb_*.pt` 를 읽어 {아티스트: 마스터 프로필} 을 반환합니다.

    읽을 수 없는 임베딩이 있는 아티스트는 오류를 기록하고 건너뜁니다.
    """
    db_dir = db_dir or config.DB_DIR
    artist_dirs = sorted(d for d in glob.glob(os.path.join(db_dir, "*")) if os.path.isdir(d))
    master_profiles = {}

    for adir in artist_dirs:
        artist_name = os.path.basename(adir)
        emb_files = sorted(glob.glob(os.path.join(adir, "emb_*.pt")))
        if not emb_files:
            continue

        try:
            embs = [torch.load(f, weights_only=True) for f in emb_files]
            master_profiles[artist_name] = build_master_profile(embs)
        except Exception as e:
            log.error(f"  [오류] '{artist_name}'의 프로필 생성 중 에러 발생: {e}", exc_info=True)
            continue
    return master_profiles


def build_similarity_dataframe(master_profiles: Dict[str, torch.Tensor]) -> pd.DataFrame:
    """마스터 프로필 → 아티스트×아티스트 코사인 유사도 DataFrame."""
    artists, matrix = compute_similarity_matrix(master_profiles)
    return pd.DataFrame(matrix.numpy(), index=artists, columns=artists)


def save_similarity_text(df: pd.DataFrame, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("=== Vocal Similarity Matrix ===\n")
        f.write(df.to_string())
    log.info(f"  -> 텍스트 결과물 저장: {path}")


def save_clustermap(df: pd.DataFrame, path: str) -> None:
    fig_size = max(8, len(df.index))
    g = sns.clustermap(
        df,
        annot=True,
        fmt=".2f",
        cmap="mako",
        vmin=0.0,
        vmax=1.0,
        figsize=(fig_size, fig_size)
    )
    g.fig.suptitle("Vocal Similarity Clustermap", y=1.05)
    g.savefig(path, dpi=300, bbox_inches='tight')
    plt.close('all')
    log.info(f"  -> 시각화 결과물 저장: {path}")


def top_similar_pairs(df: pd.DataFrame, limit: int = 10) -> list:
    """유사도 행렬의 대각선을 제외한 상위 아티스트 쌍을 반환합니다."""
    pairs = [
        {
            "artist_a": str(df.index[i]),
            "artist_b": str(df.index[j]),
            "similarity": round(float(df.iat[i, j]), 4),
        }
        for i in range(len(df.index))
        for j in range(i + 1, len(df.columns))
    ]
    pairs.sort(
        key=lambda pair: (-pair["similarity"], pair["artist_a"], pair["artist_b"])
    )
    return pairs[:limit]


def save_top_pairs(pairs: list, txt_path: str, csv_path: str) -> None:
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=== Top 10 Vocal Similarity Pairs ===\n")
        f.write("순위 | 아티스트 A | 아티스트 B | 코사인 유사도\n")
        for rank, pair in enumerate(pairs, start=1):
            f.write(
                f"{rank:>2} | {pair['artist_a']} | {pair['artist_b']} "
                f"| {pair['similarity']:.4f}\n"
            )

    pd.DataFrame(
        [
            {
                "rank": rank,
                "artist_a": pair["artist_a"],
                "artist_b": pair["artist_b"],
                "similarity": pair["similarity"],
            }
            for rank, pair in enumerate(pairs, start=1)
        ],
        columns=["rank", "artist_a", "artist_b", "similarity"],
    ).to_csv(csv_path, index=False, encoding="utf-8-sig")
    log.info(f"  -> 상위 유사도 쌍 보고서 저장: {txt_path}")


def generate_and_visualize_similarity(
    output_dir: Optional[str] = None,
) -> Optional[pd.DataFrame]:
    """
    아티스트별 마스터 프로필을 생성하고, 유사도 행렬을 계산하여
    클러스터맵과 텍스트 파일로 저장합니다. 비교 대상이 2명 미만이면 None.
    """
    log.info("\n" + "="*50)
    log.info("[*] [Step 5] 전체 마스터 프로필 생성 및 시각화 시작")
    log.info("="*50)

    master_profiles = load_master_profiles()
    if len(master_profiles) < 2:
        log.warning("[!] 비교할 가수가 2명 이상이어야 시각화가 가능합니다.")
        return None

    df = build_similarity_dataframe(master_profiles)
    output_dir = output_dir or config.DB_DIR
    os.makedirs(output_dir, exist_ok=True)
    pairs = top_similar_pairs(df)
    matrix = [[round(float(value), 4) for value in row] for row in df.values.tolist()]
    run_id = (
        os.path.basename(output_dir)
        if os.path.basename(os.path.dirname(output_dir)) == "runs"
        else None
    )
    payload = {
        "run_id": run_id,
        "created_at": run_id,
        "artists": list(df.index),
        "matrix": matrix,
        "top_pairs": pairs,
    }

    save_similarity_text(df, os.path.join(output_dir, SIMILARITY_TXT_NAME))
    save_clustermap(df, os.path.join(output_dir, CLUSTERMAP_PNG_NAME))
    save_top_pairs(
        pairs,
        os.path.join(output_dir, TOP_PAIRS_TXT_NAME),
        os.path.join(output_dir, TOP_PAIRS_CSV_NAME),
    )
    if run_id:
        with open(similarity_json_path(output_dir), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    if os.path.abspath(output_dir) != os.path.abspath(config.DB_DIR):
        for name in (
            SIMILARITY_TXT_NAME,
            CLUSTERMAP_PNG_NAME,
            TOP_PAIRS_TXT_NAME,
            TOP_PAIRS_CSV_NAME,
        ):
            shutil.copy2(os.path.join(output_dir, name), os.path.join(config.DB_DIR, name))
        log.info(f"  -> 최신 결과 복사: {config.DB_DIR}")
    return df
