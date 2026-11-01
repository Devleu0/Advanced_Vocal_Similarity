from typing import List

from fastapi import APIRouter, Depends, HTTPException, Response, status

from input_store import InvalidArtistName
from webapp.dependencies import get_artist_service, get_job_manager
from webapp.schemas import ArtistIn, ArtistOut
from webapp.services.artists import ArtistService, InvalidUrls
from webapp.services.jobs import JobManager

router = APIRouter(prefix="/api/artists", tags=["artists"])

# Starlette 버전별로 상수 이름이 다르므로(UNPROCESSABLE_ENTITY/CONTENT) 숫자를 직접 사용합니다.
HTTP_422 = 422


@router.get("", response_model=List[ArtistOut])
def list_artists(service: ArtistService = Depends(get_artist_service)):
    return [ArtistOut.from_domain(a) for a in service.list()]


@router.put("/{name}", response_model=ArtistOut)
def save_artist(name: str, body: ArtistIn, service: ArtistService = Depends(get_artist_service)):
    """아티스트를 생성하거나 URL 목록을 덮어씁니다."""
    try:
        return ArtistOut.from_domain(service.save(name, body.urls))
    except InvalidArtistName as e:
        raise HTTPException(HTTP_422, str(e))
    except InvalidUrls as e:
        raise HTTPException(HTTP_422, {"message": str(e), "invalid_urls": e.urls})


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_artist(name: str, purge: bool = False,
                  service: ArtistService = Depends(get_artist_service),
                  jobs: JobManager = Depends(get_job_manager)):
    """입력 파일을 삭제합니다. purge=true 면 database/ 의 처리 산출물도 함께 삭제합니다."""
    if purge and jobs.active():
        raise HTTPException(status.HTTP_409_CONFLICT, "작업 실행 중에는 처리 데이터를 삭제할 수 없습니다.")
    try:
        removed = service.delete(name, purge_data=purge)
    except InvalidArtistName as e:
        raise HTTPException(HTTP_422, str(e))
    if not removed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"아티스트를 찾을 수 없습니다: {name}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
