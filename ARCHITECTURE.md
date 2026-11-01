# Architecture

파이프라인은 **I/O 계층**과 **순수 로직 계층**으로 분리되어 있습니다.

```
main.py            오케스트레이션 (단계 실행 순서)
├─ processing.py   I/O: yt-dlp 다운로드, ffmpeg 변환, demucs 보컬 분리, 임베딩 저장
│   └─ fingerprint.py   순수 로직: 리샘플/모노/정규화, 청킹, VAD, 임베딩 집계(이상치 제거)
└─ visualization.py I/O: 임베딩 로드, txt/clustermap 저장
    └─ similarity.py    순수 로직: 마스터 프로필, 코사인 유사도 행렬
```

- `fingerprint.py`, `similarity.py` 는 `config`/파일시스템에 의존하지 않고 인자만 받으므로 `tests/` 에서 합성 텐서로 단위 테스트합니다.
- 알고리즘(VAD, 이상치 제거, 유사도 계산)을 바꿀 때는 위 두 모듈과 해당 테스트만 수정하면 됩니다.
- 새 단계를 추가할 때는 순수 로직은 별도 모듈로 두고, `processing.py` 는 호출만 하도록 유지하세요.
