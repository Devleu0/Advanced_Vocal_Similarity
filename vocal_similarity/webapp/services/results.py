"""분석 결과 조회 서비스.

유사도는 저장된 임베딩(`emb_*.pt`)으로부터 요청 시 계산하므로 파이프라인 실행 후
별도 동기화 없이 항상 최신 상태를 보여줍니다. 계산 로직은 `visualization.py` 를 재사용합니다.
"""
from __future__ import annotations

import csv
import io
import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SimilarityResult:
    artists: List[str]
    matrix: List[List[float]]


class ResultService:
    def similarity(self) -> SimilarityResult:
        # 무거운 모듈(torch/seaborn)은 실제로 결과를 요청할 때만 import 합니다.
        from ...visualization import build_similarity_dataframe, load_master_profiles

        profiles = load_master_profiles()
        if not profiles:
            return SimilarityResult([], [])
        df = build_similarity_dataframe(profiles)
        matrix = [[round(float(v), 4) for v in row] for row in df.values.tolist()]
        return SimilarityResult(list(df.index), matrix)

    def similarity_csv(self) -> str:
        result = self.similarity()
        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerow(["artist", *result.artists])
        for name, row in zip(result.artists, result.matrix):
            writer.writerow([name, *(f"{v:.4f}" for v in row)])
        return buf.getvalue()

    def clustermap_path(self) -> Optional[str]:
        from ...visualization import clustermap_path

        path = clustermap_path()
        return path if os.path.exists(path) else None
