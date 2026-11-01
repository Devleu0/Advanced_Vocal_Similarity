// 3. 유사도 결과 패널: 히트맵 표 + 클러스터맵 이미지
import { api } from './api.js';
import { $, el, toast } from './dom.js';
import { t } from './i18n.js';

const MIN_ZOOM = 0.7;
const MAX_ZOOM = 1.6;
const ZOOM_STEP = 0.1;
let heatmapZoom = 1;
let highlightedArtists = new Set();
let currentArtists = [];
let currentData = null;

/** 0~1 값을 색으로 변환 (밝은 청록 → 진한 남색, 셀 글자색 대비 포함). */
function cellStyle(value) {
  const v = Math.min(Math.max(value, 0), 1);
  const lightness = 96 - v * 70; // 96% → 26%
  return {
    background: `hsl(${190 + v * 40}, 65%, ${lightness}%)`,
    color: lightness < 55 ? '#fff' : '#0f172a',
  };
}

function updateHeatmapControls() {
  const table = $('#heatmap');
  table.style.setProperty('--heatmap-zoom', heatmapZoom.toFixed(1));
  $('#heatmap-zoom-label').textContent = `${Math.round(heatmapZoom * 100)}%`;
  $('#heatmap-zoom-out').disabled = heatmapZoom <= MIN_ZOOM;
  $('#heatmap-zoom-in').disabled = heatmapZoom >= MAX_ZOOM;
  $('#heatmap-highlight-clear').disabled = highlightedArtists.size === 0;
}

function highlightArtists(indices) {
  highlightedArtists = new Set(
    indices.map((index) => currentArtists[index]).filter(Boolean),
  );
  const table = $('#heatmap');
  table.querySelectorAll('[data-artist-index]').forEach((node) => {
    const index = Number(node.dataset.artistIndex);
    const selected = highlightedArtists.has(currentArtists[index]);
    node.classList.toggle('highlighted', selected);
    if (node.matches('button')) {
      node.setAttribute('aria-pressed', String(selected));
    }
  });
  table.querySelectorAll('[data-row-index][data-column-index]').forEach((cell) => {
    const rowIndex = Number(cell.dataset.rowIndex);
    const columnIndex = Number(cell.dataset.columnIndex);
    const rowSelected = highlightedArtists.has(currentArtists[rowIndex]);
    const columnSelected = highlightedArtists.has(currentArtists[columnIndex]);
    cell.classList.toggle(
      'highlighted',
      rowSelected || columnSelected,
    );
    cell.classList.toggle('highlighted-intersection', rowSelected && columnSelected);
  });
  updateHeatmapControls();
}

function renderHeatmap({ artists, matrix }) {
  const table = $('#heatmap');
  currentArtists = artists;
  const head = el('tr', {},
    el('th', {}, ''),
    artists.map((artist, index) => {
      const button = el('button', {
        class: 'heatmap-artist',
        type: 'button',
        title: t('results.heatmap.artist.aria', { artist }),
        'aria-label': t('results.heatmap.artist.aria', { artist }),
        'aria-pressed': highlightedArtists.has(artist),
        'data-artist-index': index,
      }, artist);
      button.addEventListener('click', () => highlightArtists([index]));
      return el('th', { scope: 'col', title: artist }, button);
    }));
  const rows = artists.map((rowName, i) => el('tr', {},
    el('th', { scope: 'row', title: rowName },
      el('button', {
        class: 'heatmap-artist',
        type: 'button',
        title: t('results.heatmap.artist.aria', { artist: rowName }),
        'aria-label': t('results.heatmap.artist.aria', { artist: rowName }),
        'aria-pressed': highlightedArtists.has(rowName),
        'data-artist-index': i,
      }, rowName)),
    matrix[i].map((v, j) => {
      const td = el('td', {
        title: t('results.heatmap.cell.title', {
          artistA: rowName,
          artistB: artists[j],
          score: v.toFixed(4),
        }),
        'data-row-index': i,
        'data-column-index': j,
        tabindex: 0,
        role: 'button',
        'aria-label': t('results.heatmap.cell.aria', {
          artistA: rowName,
          artistB: artists[j],
          score: v.toFixed(4),
        }),
      }, v.toFixed(2));
      Object.assign(td.style, cellStyle(v));
      if (i === j) td.classList.add('diag');
      td.addEventListener('click', () => highlightArtists([i, j]));
      td.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          highlightArtists([i, j]);
        }
      });
      return td;
    })));
  table.replaceChildren(el('thead', {}, head), el('tbody', {}, rows));
  highlightArtists(
    [...highlightedArtists]
      .map((artist) => artists.indexOf(artist))
      .filter((index) => index >= 0),
  );
  updateHeatmapControls();
}

function loadClustermap(runId) {
  const img = $('#clustermap-img');
  const url = api.clustermapUrl(runId);
  img.onload = () => { $('#clustermap-figure').hidden = false; };
  img.onerror = () => { $('#clustermap-figure').hidden = true; };
  img.src = url;
  $('#clustermap-link').href = url;
}

function renderTopPairs(pairs) {
  const section = $('#top-pairs-section');
  section.hidden = !pairs.length;
  $('#top-pairs-body').replaceChildren(...pairs.map((pair, index) => el('tr', {},
    el('td', {}, String(index + 1)),
    el('td', {}, pair.artist_a),
    el('td', {}, pair.artist_b),
    el('td', {}, pair.similarity.toFixed(4)))));
}

function formatRunLabel(runId) {
  return `${runId.slice(0, 4)}-${runId.slice(4, 6)}-${runId.slice(6, 8)} `
    + `${runId.slice(9, 11)}:${runId.slice(11, 13)}:${runId.slice(13, 15)}`
    + `.${runId.slice(16)}`;
}

async function loadRuns(selectLatest) {
  const select = $('#results-run-select');
  const current = select.value;
  const runs = await api.listResultRuns();
  const options = [el('option', { value: '' }, t('results.run.current'))];
  for (const run of runs) {
    options.push(el('option', { value: run.id }, formatRunLabel(run.id)));
  }
  select.replaceChildren(...options);
  if (selectLatest && runs.length) select.value = runs[0].id;
  else if (runs.some((run) => run.id === current)) select.value = current;
  return select.value || null;
}

export async function refreshResults({ selectLatest = false } = {}) {
  let data;
  let runId;
  try {
    runId = await loadRuns(selectLatest);
    data = await api.similarity(runId);
  } catch (e) {
    toast(t('results.toast.error', { message: e.message }), 'error');
    return;
  }
  currentData = data;
  const selectedLabel = data.run_id
    ? t('results.run.label.value', { runId: formatRunLabel(data.run_id) })
    : t('results.profile.label');
  $('#results-run-label').textContent = selectedLabel;
  const hasMatrix = data.artists.length >= 2;
  $('#results-empty').hidden = hasMatrix;
  $('#heatmap-wrap').hidden = !hasMatrix;
  $('#heatmap-scroll-hint').hidden = !hasMatrix;
  $('#results-csv-link').hidden = !hasMatrix;
  $('#results-csv-link').href = api.similarityCsvUrl(runId);
  $('#results-report-link').href = api.topPairsCsvUrl(runId);
  $('#results-report-link').hidden = !data.top_pairs.length;
  $('#results-report-txt-link').href = api.topPairsTxtUrl(runId);
  if (hasMatrix) renderHeatmap(data);
  renderTopPairs(data.top_pairs);
  if (data.clustermap_available) loadClustermap(runId);
  else $('#clustermap-figure').hidden = true;
}

window.addEventListener('app-language-change', () => {
  const currentProfileOption = $('#results-run-select').querySelector('option[value=""]');
  if (currentProfileOption) currentProfileOption.textContent = t('results.run.current');
  if (!currentData) return;
  $('#results-run-label').textContent = currentData.run_id
    ? t('results.run.label.value', { runId: formatRunLabel(currentData.run_id) })
    : t('results.profile.label');
  if (currentData.artists.length >= 2) renderHeatmap(currentData);
});

export function initResults() {
  $('#results-refresh-btn').addEventListener('click', () => refreshResults({ selectLatest: true }));
  $('#results-run-select').addEventListener('change', () => refreshResults());
  $('#heatmap-zoom-out').addEventListener('click', () => {
    heatmapZoom = Math.max(MIN_ZOOM, Math.round((heatmapZoom - ZOOM_STEP) * 10) / 10);
    updateHeatmapControls();
  });
  $('#heatmap-zoom-in').addEventListener('click', () => {
    heatmapZoom = Math.min(MAX_ZOOM, Math.round((heatmapZoom + ZOOM_STEP) * 10) / 10);
    updateHeatmapControls();
  });
  $('#heatmap-zoom-reset').addEventListener('click', () => {
    heatmapZoom = 1;
    updateHeatmapControls();
  });
  $('#heatmap-highlight-clear').addEventListener('click', () => highlightArtists([]));
  updateHeatmapControls();
  return refreshResults({ selectLatest: true });
}
