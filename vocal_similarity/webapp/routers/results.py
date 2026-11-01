from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, Response

from ..dependencies import get_result_service
from ..schemas import SimilarityOut
from ..services.results import ResultService

router = APIRouter(prefix="/api/results", tags=["results"])


@router.get("/similarity", response_model=SimilarityOut)
def similarity(service: ResultService = Depends(get_result_service)):
    """저장된 지문으로 아티스트 간 코사인 유사도 행렬을 계산합니다."""
    result = service.similarity()
    return SimilarityOut(artists=result.artists, matrix=result.matrix,
                         clustermap_available=service.clustermap_path() is not None)


@router.get("/similarity.csv")
def similarity_csv(service: ResultService = Depends(get_result_service)):
    return Response(
        content=service.similarity_csv().encode("utf-8-sig"),  # 엑셀에서 한글이 깨지지 않도록 BOM 포함
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="vocal_similarity.csv"'},
    )


@router.get("/clustermap.png")
def clustermap(service: ResultService = Depends(get_result_service)):
    path = service.clustermap_path()
    if not path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "클러스터맵이 아직 생성되지 않았습니다.")
    return FileResponse(path, media_type="image/png", headers={"Cache-Control": "no-store"})
