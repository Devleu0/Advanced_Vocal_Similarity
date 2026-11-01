from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, Response

from ..dependencies import get_result_service
from ..schemas import AnalysisRunOut, SimilarityOut
from ..services.results import ResultService, RunNotFoundError

router = APIRouter(prefix="/api/results", tags=["results"])


@router.get("/runs", response_model=List[AnalysisRunOut])
def runs(service: ResultService = Depends(get_result_service)):
    """보관된 분석 실행 목록을 최신순으로 반환합니다."""
    return service.runs()


@router.get("/similarity", response_model=SimilarityOut)
def similarity(
    run_id: Optional[str] = Query(default=None),
    service: ResultService = Depends(get_result_service),
):
    """저장된 지문으로 아티스트 간 코사인 유사도 행렬을 계산합니다."""
    try:
        result = service.similarity(run_id)
        return SimilarityOut(
            artists=result.artists,
            matrix=result.matrix,
            top_pairs=result.top_pairs,
            run_id=result.run_id,
            clustermap_available=service.clustermap_path(run_id) is not None,
        )
    except RunNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e)) from e


@router.get("/similarity.csv")
def similarity_csv(
    run_id: Optional[str] = Query(default=None),
    service: ResultService = Depends(get_result_service),
):
    try:
        return Response(
            content=service.similarity_csv(run_id).encode("utf-8-sig"),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="vocal_similarity.csv"'},
        )
    except RunNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e)) from e


@router.get("/clustermap.png")
def clustermap(
    run_id: Optional[str] = Query(default=None),
    service: ResultService = Depends(get_result_service),
):
    try:
        path = service.clustermap_path(run_id)
        if not path:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "클러스터맵이 아직 생성되지 않았습니다.")
        return FileResponse(path, media_type="image/png", headers={"Cache-Control": "no-store"})
    except RunNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e)) from e


@router.get("/top-pairs.csv")
def top_pairs_csv(
    run_id: Optional[str] = Query(default=None),
    service: ResultService = Depends(get_result_service),
):
    try:
        return Response(
            content=service.top_pairs_csv(run_id).encode("utf-8-sig"),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="top_similar_pairs.csv"'},
        )
    except RunNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e)) from e


@router.get("/top-pairs.txt")
def top_pairs_report(
    run_id: Optional[str] = Query(default=None),
    service: ResultService = Depends(get_result_service),
):
    try:
        return Response(
            content=service.top_pairs_text(run_id),
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="top_similar_pairs.txt"'},
        )
    except RunNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e)) from e
