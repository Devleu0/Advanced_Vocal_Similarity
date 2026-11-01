# CHANGELOG

PR 단위로 변경 내용과 **호환성 영향**을 기록합니다. 새 PR 을 올릴 때 이 파일도 함께 갱신하세요.
기대 효과의 검증 상태는 [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md), 남은 작업은 [docs/ROADMAP.md](docs/ROADMAP.md) 에 있습니다.

> PR 은 #1 → #2 → #3 → #4 → #5 순서로 쌓여 있습니다 (앞 PR 머지 후 base 를 main 으로 변경).
> 아래 모든 항목은 작성 시점에 `pytest` 를 **실행하지 못했습니다** (작업 환경에 torch 설치 불가). CI 결과로 확인 필요.

## #5 입력을 yt-dlp 지원 사이트 전반으로 일반화
- README/로그의 '유튜브' 한정 표현을 일반 표현으로 변경
- `utils.get_media_id`: 유튜브는 기존 11자 ID, 그 외 http(s) URL 은 `u`+URL 해시 10자리, 영상 URL 로 보기 어려운 입력은 None
- 유튜브만 표준 watch URL 로 정규화, 그 외는 원본 URL 을 yt-dlp 에 전달
- 기존 `extract_video_id` 정규식이 아무 사이트의 11자 경로를 ID 로 오인하던 문제를 호스트 검사로 해결
- **호환성**: 유튜브 산출물 파일명 변경 없음

## #4 선택형 파이프라인 옵션
- 산출물(보컬/청크 임베딩/지문)에 생성 설정 시그니처(`*.meta.json`) 기록 → 설정이 같으면 건너뛰고 바뀌면 해당 단계부터 재생성
- 청크 임베딩 캐시(`chunks_{model}_{vid}.pt`): 집계 옵션만 바꿀 때 모델 추론 생략
- 선택 기능(기본 OFF): 다중화자 필터, Silero VAD, Demucs shifts, 오디오 길이 제한, 영상 단위 점수(video_max/topk), s-norm, 모델 앙상블, 영상 단위 CSV
- CLI: `--preset fast|balanced|accurate`, `--ensemble`, `--input-dir`, `--db-dir`, `--device`, `--set KEY=VALUE`
- 결과를 `database/results/<태그>/` 에 설정별 저장 (최신본은 기존 위치에도 복사)
- `processing.py` 를 단계 함수로 분리, `main.py` 를 `configure()`/`collect_tasks()` 로 분리
- **호환성**: 메타 없는 기존 보컬은 재사용, 메타 없는 기존 지문은 1회 재생성(보컬이 남아 있으면 임베딩 단계만)

## #3 임베딩 모델 선택
- 모델 레지스트리(`models.py`): `ecapa`(기본) / `wavlm-sv`(추천 표시) / `resnet`, `--model`, `--list-models`, 환경변수 `VOCAL_EMBEDDING_MODEL`
- `HFXVectorEncoder`: WavLM-SV 를 기존 `encode_batch(wavs, wav_lens)` 인터페이스로 래핑
- 모델별 임베딩 파일 분리(`embedding_store.py`)
- **호환성**: `ecapa` 는 기존 `emb_{vid}.pt` 이름 유지. `transformers` 는 wavlm-sv 사용 시에만 필요

## #2 임베딩 품질 개선 + 평가 도구
- **버그 수정**: 영상 끝 꼬리 청크(1~5초)로 길이가 달라 `torch.stack` 이 실패하던 문제 → 패딩 + `wav_lens`
- 청크 임베딩을 L2 정규화 후 집계, 최종 지문도 정규화
- 아티스트 공통 성분 제거(센터링, 5명 이상일 때만), 히트맵 `vmin` 이 음수 유사도를 자르던 문제 수정
- 선택 옵션: 상대 RMS VAD, 겹치는 청크, 배치 크기, 병렬 다운로드(기본 4)
- `evaluation.py`/`evaluate.py`: EER, top-1 검색 정확도, 클래스 내/간 점수 차이
- **호환성**: 기존 `emb_*.pt` 사용 가능(비교 단계에서 재정규화). 꼬리 청크 때문에 실패했던 영상은 재실행 시 처리됨

## #1 모듈화 리팩터링
- 순수 로직 분리: `fingerprint.py`(청킹/VAD/집계), `similarity.py`(프로필/유사도), I/O 계층(`processing.py`, `visualization.py`)은 호출만
- **버그 수정**: `config.DEVICE == "cuda"` 는 `"cuda:0"` 과 비교되어 항상 False 였음 → `startswith("cuda")`
- 존재하지 않는 `process_url` 을 대상으로 한 낡은 테스트 삭제/재작성, 커밋돼 있던 `.pyc` 제거
- `ARCHITECTURE.md` 추가, README 배지/URL 수정
