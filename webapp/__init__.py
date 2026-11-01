"""Advanced Vocal Similarity 웹 UI 패키지.

구성 (계층별 책임):
- routers/   HTTP 엔드포인트 (요청 검증·응답 변환만 담당)
- services/  도메인 로직 (입력 관리, 작업 실행, 결과 조회)
- static/    프런트엔드 (빌드 단계 없는 HTML/CSS/ES 모듈)
"""
import os

# 웹 서버는 GUI 가 없는 백그라운드 스레드에서 matplotlib 을 사용하므로 Agg 백엔드를 강제합니다.
os.environ.setdefault("MPLBACKEND", "Agg")
