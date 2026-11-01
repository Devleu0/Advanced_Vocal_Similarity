# ROADMAP — 해야 할 일

상태: `TODO` · `DOING` · `DONE` · `BLOCKED`. 작업을 시작/완료할 때 이 파일을 갱신하세요.

## 지금 필요한 것 (검증)
| 상태 | 작업 | 비고 |
|---|---|---|
| TODO | PR #1~#5 의 CI(pytest/ruff, Python 3.9~3.11) 결과 확인 및 실패 수정 | 작성 환경에서 pytest 미실행 |
| TODO | 실제 데이터로 `evaluate.py` 측정: ecapa vs wavlm-sv vs resnet | 결과는 docs/EXPERIMENTS.md 에 기록 |
| TODO | 옵션별 효과 측정: 센터링, 다중화자 필터, VAD(rms/relative/silero), Demucs shifts | 한 번에 하나씩 바꿔 비교 |
| TODO | 측정 결과로 기본 모델/프리셋(`accurate`) 구성 결정 | 근거 없이 기본값 변경 금지 |
| TODO | 유튜브가 아닌 사이트 URL 로 실제 다운로드/처리 확인 | yt-dlp·사이트 의존 |

## 개선 후보 (정확도)
| 상태 | 작업 | 메모 |
|---|---|---|
| TODO | 화자 분리(diarization) 도입 검토 | 다중화자 필터(군집 휴리스틱)보다 정확하지만 무거움 → 선택 옵션으로 |
| TODO | 노래 음성에 맞는 임베딩 모델 탐색/파인튜닝 | 현재 모델은 모두 말소리 기반 |
| TODO | 평가 확장: 아티스트 단위 후처리(video_topk, s-norm, 앙상블)도 평가 지표에 반영 | 현재 `evaluate.py` 는 영상 단위 지문만 평가 |
| TODO | 보컬 분리 모델 비교 (mdx_extra / htdemucs / htdemucs_ft) | 분리 품질이 지문에 미치는 영향 측정 |

## 개선 후보 (운영/유지보수)
| 상태 | 작업 | 메모 |
|---|---|---|
| TODO | `run.bat` 에 `--preset`/`--model` 전달 지원 | 현재 인자 없이 실행 |
| TODO | 로그 파일 위치 정리 (`VOCAL_BASE_DIR` 기준) | `logger.py` 는 `config.BASE_DIR` 사용 — 확인 필요 |
| TODO | Demucs 단계 병렬/배치 처리 검토 | 가장 느린 단계 |
| TODO | 비유튜브 URL 의 동일 영상 중복 감지 (URL 해시 대신 yt-dlp 의 extractor/id 사용) | 현재는 다른 URL = 다른 영상 |
| TODO | 결과 비교 도구: `database/results/*` 간 행렬 차이 요약 | 설정별 결과가 쌓이므로 필요 |

## 완료
| 작업 | PR |
|---|---|
| 모듈화 리팩터링, CUDA 캐시 정리 버그 수정 | #1 |
| 꼬리 청크 크래시 수정, 정규화/센터링, 평가 도구 | #2 |
| 임베딩 모델 선택 | #3 |
| 캐시/메타, 선택 옵션, 프리셋, CLI | #4 |
| 입력 소스 일반화 | #5 |

## 작업 규칙
- 새 기능은 **기본 OFF** 로 추가하고, 오래 걸리는 것은 config 주석에 `[느림]` 표시
- PR 마다 `CHANGELOG.md`(변경/호환성)와 `docs/EXPERIMENTS.md`(기대 효과·검증 상태)를 갱신
- 검증하지 못한 것은 "미검증"이라고 명시
