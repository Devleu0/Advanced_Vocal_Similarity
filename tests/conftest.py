"""공용 테스트 설정: demucs 가 설치되지 않은 환경(CI 의 --no-deps 등)에서도 processing 을 import 할 수 있게 스텁을 제공합니다."""
import sys
import types

try:
    import demucs.separate  # noqa: F401
except ImportError:
    _demucs = types.ModuleType("demucs")
    _separate = types.ModuleType("demucs.separate")
    _separate.main = lambda args=None: None
    _demucs.separate = _separate
    sys.modules["demucs"] = _demucs
    sys.modules["demucs.separate"] = _separate
