"""Analysis result and archived-run lookup service."""
from __future__ import annotations

import csv
import io
import json
import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SimilarityResult:
    artists: List[str]
    matrix: List[List[float]]
    top_pairs: List[Dict[str, object]]
    run_id: Optional[str] = None


class RunNotFoundError(Exception):
    """요청한 실행 ID가 유효하지 않거나 보관 결과가 없음."""


class ResultService:
    RUN_ID_RE = re.compile(r"^\d{8}_\d{6}_\d{6}$")

    def _runs_dir(self) -> str:
        from ... import config

        return os.path.join(config.DB_DIR, "runs")

    def runs(self) -> List[Dict[str, str]]:
        runs_dir = self._runs_dir()
        if not os.path.isdir(runs_dir):
            return []
        from ...visualization import SIMILARITY_JSON_NAME

        run_ids = [
            name for name in os.listdir(runs_dir)
            if self.RUN_ID_RE.fullmatch(name)
            and os.path.isfile(os.path.join(runs_dir, name, SIMILARITY_JSON_NAME))
        ]
        return [{"id": run_id, "created_at": run_id} for run_id in sorted(run_ids, reverse=True)]

    def _run_directory(self, run_id: str) -> str:
        if not self.RUN_ID_RE.fullmatch(run_id):
            raise RunNotFoundError("유효하지 않은 실행 ID 입니다.")
        run_dir = os.path.join(self._runs_dir(), run_id)
        from ...visualization import SIMILARITY_JSON_NAME

        if not os.path.isfile(os.path.join(run_dir, SIMILARITY_JSON_NAME)):
            raise RunNotFoundError("해당 실행 결과를 찾을 수 없습니다.")
        return run_dir

    def _latest_run_id(self) -> Optional[str]:
        run_list = self.runs()
        return run_list[0]["id"] if run_list else None

    def similarity(self, run_id: Optional[str] = None) -> SimilarityResult:
        selected_run = run_id or self._latest_run_id()
        if selected_run:
            from ...visualization import SIMILARITY_JSON_NAME

            path = os.path.join(self._run_directory(selected_run), SIMILARITY_JSON_NAME)
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return SimilarityResult(
                artists=data["artists"],
                matrix=data["matrix"],
                top_pairs=data["top_pairs"],
                run_id=data["run_id"],
            )

        # Heavy modules are loaded only when results are requested.
        from ...visualization import (
            build_similarity_dataframe,
            load_master_profiles,
            top_similar_pairs,
        )

        profiles = load_master_profiles()
        if not profiles:
            return SimilarityResult([], [], [])
        df = build_similarity_dataframe(profiles)
        matrix = [[round(float(v), 4) for v in row] for row in df.values.tolist()]
        return SimilarityResult(list(df.index), matrix, top_similar_pairs(df))

    def similarity_csv(self, run_id: Optional[str] = None) -> str:
        result = self.similarity(run_id)
        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerow(["artist", *result.artists])
        for name, row in zip(result.artists, result.matrix):
            writer.writerow([name, *(f"{v:.4f}" for v in row)])
        return buf.getvalue()

    def top_pairs_csv(self, run_id: Optional[str] = None) -> str:
        result = self.similarity(run_id)
        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerow(["rank", "artist_a", "artist_b", "similarity"])
        for rank, pair in enumerate(result.top_pairs, start=1):
            writer.writerow(
                [rank, pair["artist_a"], pair["artist_b"], f"{pair['similarity']:.4f}"]
            )
        return buf.getvalue()

    def top_pairs_text(self, run_id: Optional[str] = None) -> str:
        result = self.similarity(run_id)
        lines = [
            "=== Top 10 Vocal Similarity Pairs ===",
            "순위 | 아티스트 A | 아티스트 B | 코사인 유사도",
        ]
        lines.extend(
            f"{rank:>2} | {pair['artist_a']} | {pair['artist_b']} | "
            f"{pair['similarity']:.4f}"
            for rank, pair in enumerate(result.top_pairs, start=1)
        )
        return "\n".join(lines) + "\n"

    def clustermap_path(self, run_id: Optional[str] = None) -> Optional[str]:
        from ...visualization import CLUSTERMAP_PNG_NAME, clustermap_path

        selected_run = run_id or self._latest_run_id()
        path = (
            os.path.join(self._run_directory(selected_run), CLUSTERMAP_PNG_NAME)
            if selected_run
            else clustermap_path()
        )
        return path if os.path.exists(path) else None
