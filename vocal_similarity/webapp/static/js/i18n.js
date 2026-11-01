const messages = {
  ko: {
    'app.subtitle': '미디어 URL의 음성을 분리·지문화하여 보컬 간 음색 유사도를 비교합니다',
    'language.label': '언어',
    'language.picker.aria': '표시 언어 선택',
    'artists.title': '아티스트 & URL',
    'artists.new': '+ 새 아티스트',
    'artist.name': '아티스트 이름',
    'artist.name.placeholder': '예: Artist A',
    'media.urls': '미디어 URL',
    'media.urls.hint': '(한 줄에 하나)',
    'media.urls.placeholder': 'https://media.example.com/item/1\nhttps://media.example.com/item/2',
    'button.cancel': '취소',
    'button.save': '저장',
    'artists.empty': '등록된 아티스트가 없습니다. ‘새 아티스트’로 시작하세요.',
    'job.title': '분석 실행',
    'job.status.waiting': '대기',
    'job.description': '체크한 아티스트만 분석합니다. 아무것도 선택하지 않으면 전체를 분석합니다. 이미 처리된 URL은 자동으로 건너뜁니다.',
    'job.start': '▶ 분석 시작',
    'job.cancel': '■ 취소',
    'job.target.all': '대상: 전체 아티스트',
    'job.target.selected': '대상: {names}',
    'job.copy.failures': '실패 로그 복사',
    'job.logs': '실행 로그',
    'job.stage.model': '모델 로드',
    'job.stage.download': '다운로드',
    'job.stage.convert': '오디오 변환',
    'job.stage.process': '보컬 분리·지문 추출',
    'job.stage.analyze': '유사도 분석',
    'job.status.queued': '대기열',
    'job.status.running': '실행 중',
    'job.status.succeeded': '완료',
    'job.status.failed': '실패',
    'job.status.cancelled': '취소됨',
    'job.toast.finished': '분석 {status}',
    'job.toast.already_running': '이미 실행 중인 작업이 있어 해당 작업을 표시합니다.',
    'job.toast.cancel_requested': '취소를 요청했습니다.',
    'job.toast.cancel_confirm': '작업을 취소할까요? 현재 처리 중인 URL이 끝난 뒤 중단됩니다.',
    'job.toast.failure_logs_empty': '복사할 실패 로그가 없습니다.',
    'job.toast.failure_logs_copied': '실패 로그 {count}줄을 복사했습니다.',
    'job.toast.failure_logs_copy_error': '실패 로그 복사 실패: {message}',
    'job.clipboard.unsupported': '이 브라우저에서 클립보드 복사를 지원하지 않습니다.',
    'artist.status.pending': '대기',
    'artist.status.downloaded': '다운로드됨',
    'artist.status.separated': '보컬 분리됨',
    'artist.status.done': '지문 완료',
    'artist.status.invalid': 'URL 오류',
    'artist.status.count': '지문 추출 완료 / 전체 URL',
    'artist.edit': '수정',
    'artist.delete': '삭제',
    'artist.url.count': 'URL {count}개',
    'artist.form.duplicate': '같은 이름의 아티스트가 이미 있습니다. 목록에서 ‘수정’을 사용하세요.',
    'artist.form.invalid': '잘못된 URL: {urls}',
    'artist.saved': '‘{name}’ 저장됨',
    'artist.delete.confirm': '‘{name}’ 아티스트를 목록에서 삭제할까요?',
    'artist.delete.data.confirm': '다운로드된 오디오와 추출된 지문(database 폴더)도 함께 삭제할까요?\n취소를 누르면 URL 목록만 삭제됩니다.',
    'artist.deleted': '‘{name}’ 삭제됨',
    'artist.list.error': '아티스트 목록을 불러오지 못했습니다: {message}',
    'results.title': '유사도 결과',
    'results.run.label': '분석 실행',
    'results.run.aria': '결과를 볼 분석 실행',
    'results.run.current': '현재 DB 프로필',
    'results.refresh': '새로고침',
    'results.csv': 'CSV 다운로드',
    'results.top.csv': '상위 10쌍 CSV',
    'results.empty': '지문이 추출된 아티스트가 2명 이상이면 유사도 행렬이 표시됩니다.',
    'results.matrix.aria': '유사도 행렬. 좌우로 스크롤할 수 있습니다.',
    'results.matrix.controls.aria': '행렬 보기 조작',
    'results.zoom.label': '확대/축소',
    'results.zoom.out': '유사도 표 축소',
    'results.zoom.in': '유사도 표 확대',
    'results.zoom.reset': '초기화',
    'results.highlight.clear': '강조 해제',
    'results.scroll.hint': '표가 화면보다 넓으면 표 영역에서 좌우로 스크롤해 전체 결과를 확인하세요.',
    'results.clustermap.alt': '보컬 유사도 클러스터맵',
    'results.clustermap.caption': '클러스터맵 (선택한 분석 실행)',
    'results.top.title': '상위 유사도 아티스트 쌍',
    'results.report.txt': '텍스트 보고서',
    'results.rank': '순위',
    'results.artist.a': '아티스트 A',
    'results.artist.b': '아티스트 B',
    'results.score': '코사인 유사도',
    'results.run.label.value': '분석 실행: {runId}',
    'results.profile.label': '현재 저장된 지문 기준',
    'results.toast.error': '결과를 불러오지 못했습니다: {message}',
    'results.heatmap.artist.aria': '아티스트 {artist} 행과 열 강조',
    'results.heatmap.cell.aria': '{artistA}와 {artistB}의 유사도 {score}. 클릭하여 행과 열 강조',
    'results.heatmap.cell.title': '{artistA} ↔ {artistB}: {score} (클릭하여 두 아티스트 강조)',
  },
  en: {
    'app.subtitle': 'Separate and fingerprint voices from media URLs to compare vocal similarity',
    'language.label': 'Language',
    'language.picker.aria': 'Choose display language',
    'artists.title': 'Artists & URLs',
    'artists.new': '+ Add artist',
    'artist.name': 'Artist name',
    'artist.name.placeholder': 'e.g. Artist A',
    'media.urls': 'Media URLs',
    'media.urls.hint': '(one per line)',
    'media.urls.placeholder': 'https://media.example.com/item/1\nhttps://media.example.com/item/2',
    'button.cancel': 'Cancel',
    'button.save': 'Save',
    'artists.empty': 'No artists yet. Start by adding an artist.',
    'job.title': 'Run analysis',
    'job.status.waiting': 'Idle',
    'job.description': 'Select artists to analyze, or leave all unchecked to analyze everyone. Already processed URLs are skipped.',
    'job.start': '▶ Start analysis',
    'job.cancel': '■ Cancel',
    'job.target.all': 'Target: all artists',
    'job.target.selected': 'Target: {names}',
    'job.copy.failures': 'Copy failure logs',
    'job.logs': 'Run log',
    'job.stage.model': 'Load model',
    'job.stage.download': 'Download',
    'job.stage.convert': 'Convert audio',
    'job.stage.process': 'Separate vocals & extract fingerprints',
    'job.stage.analyze': 'Analyze similarity',
    'job.status.queued': 'Queued',
    'job.status.running': 'Running',
    'job.status.succeeded': 'Completed',
    'job.status.failed': 'Failed',
    'job.status.cancelled': 'Cancelled',
    'job.toast.finished': 'Analysis {status}',
    'job.toast.already_running': 'An analysis is already running. Showing that job.',
    'job.toast.cancel_requested': 'Cancellation requested.',
    'job.toast.cancel_confirm': 'Cancel this job after the current URL finishes processing?',
    'job.toast.failure_logs_empty': 'There are no failure logs to copy.',
    'job.toast.failure_logs_copied': 'Copied {count} failure log lines.',
    'job.toast.failure_logs_copy_error': 'Could not copy failure logs: {message}',
    'job.clipboard.unsupported': 'Clipboard copy is not supported by this browser.',
    'artist.status.pending': 'Pending',
    'artist.status.downloaded': 'Downloaded',
    'artist.status.separated': 'Vocals separated',
    'artist.status.done': 'Fingerprint ready',
    'artist.status.invalid': 'Invalid URL',
    'artist.status.count': 'Fingerprints ready / total URLs',
    'artist.edit': 'Edit',
    'artist.delete': 'Delete',
    'artist.url.count': '{count} URLs',
    'artist.form.duplicate': 'An artist with this name already exists. Use Edit in the list.',
    'artist.form.invalid': 'Invalid URLs: {urls}',
    'artist.saved': 'Saved “{name}”',
    'artist.delete.confirm': 'Remove “{name}” from the artist list?',
    'artist.delete.data.confirm': 'Also delete downloaded audio and fingerprints (database folder)?\nChoose Cancel to remove only the URL list.',
    'artist.deleted': 'Deleted “{name}”',
    'artist.list.error': 'Could not load artist list: {message}',
    'results.title': 'Similarity results',
    'results.run.label': 'Analysis run',
    'results.run.aria': 'Select an analysis run',
    'results.run.current': 'Current database profiles',
    'results.refresh': 'Refresh',
    'results.csv': 'Download CSV',
    'results.top.csv': 'Top 10 pairs CSV',
    'results.empty': 'The similarity matrix appears when at least two artists have fingerprints.',
    'results.matrix.aria': 'Similarity matrix. Scroll horizontally to view more.',
    'results.matrix.controls.aria': 'Matrix view controls',
    'results.zoom.label': 'Zoom',
    'results.zoom.out': 'Zoom out similarity matrix',
    'results.zoom.in': 'Zoom in similarity matrix',
    'results.zoom.reset': 'Reset',
    'results.highlight.clear': 'Clear highlight',
    'results.scroll.hint': 'If the table is wider than your screen, scroll horizontally inside it.',
    'results.clustermap.alt': 'Vocal similarity clustermap',
    'results.clustermap.caption': 'Clustermap (selected analysis run)',
    'results.top.title': 'Top similar artist pairs',
    'results.report.txt': 'Text report',
    'results.rank': 'Rank',
    'results.artist.a': 'Artist A',
    'results.artist.b': 'Artist B',
    'results.score': 'Cosine similarity',
    'results.run.label.value': 'Analysis run: {runId}',
    'results.profile.label': 'Based on currently stored fingerprints',
    'results.toast.error': 'Could not load results: {message}',
    'results.heatmap.artist.aria': 'Highlight row and column for {artist}',
    'results.heatmap.cell.aria': 'Similarity between {artistA} and {artistB}: {score}. Select to highlight rows and columns',
    'results.heatmap.cell.title': '{artistA} ↔ {artistB}: {score} (select to highlight both artists)',
  },
};

let language = 'ko';

export function t(key, values = {}) {
  let text = messages[language][key] ?? messages.ko[key] ?? key;
  for (const [name, value] of Object.entries(values)) {
    text = text.replaceAll(`{${name}}`, String(value));
  }
  return text;
}

export function currentLanguage() {
  return language;
}

function applyLanguage() {
  document.documentElement.lang = language;
  document.querySelectorAll('[data-i18n]').forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach((node) => {
    node.setAttribute('placeholder', t(node.dataset.i18nPlaceholder));
  });
  document.querySelectorAll('[data-i18n-aria-label]').forEach((node) => {
    node.setAttribute('aria-label', t(node.dataset.i18nAriaLabel));
  });
  document.querySelectorAll('[data-i18n-title]').forEach((node) => {
    node.setAttribute('title', t(node.dataset.i18nTitle));
  });
  document.querySelectorAll('[data-i18n-alt]').forEach((node) => {
    node.setAttribute('alt', t(node.dataset.i18nAlt));
  });
  const selector = document.querySelector('#language-select');
  if (selector) selector.value = language;
  window.dispatchEvent(new CustomEvent('app-language-change', { detail: { language } }));
}

export function initLanguage() {
  const saved = localStorage.getItem('avs-language');
  language = saved === 'en' || saved === 'ko'
    ? saved
    : (navigator.language.toLowerCase().startsWith('en') ? 'en' : 'ko');
  const selector = document.querySelector('#language-select');
  selector.addEventListener('change', () => {
    language = selector.value === 'en' ? 'en' : 'ko';
    localStorage.setItem('avs-language', language);
    applyLanguage();
  });
  applyLanguage();
}
