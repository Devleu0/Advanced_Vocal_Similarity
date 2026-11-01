// 진입점: 패널 간 연결만 담당합니다. (각 패널의 로직은 개별 모듈에)
import { initArtists, refreshArtists, selectedArtists } from './artists.js';
import { initJobs, refreshJobTarget } from './jobs.js?v=3';
import { initResults, refreshResults } from './results.js?v=5';
import { initLanguage } from './i18n.js';

initLanguage();
await initArtists({ onSelectionChange: refreshJobTarget });
await initJobs({
  getSelection: selectedArtists,
  onTick: refreshArtists, // 실행 중 URL 별 처리 상태 갱신
  onFinished: () => Promise.all([refreshArtists(), refreshResults({ selectLatest: true })]),
});
await initResults();
