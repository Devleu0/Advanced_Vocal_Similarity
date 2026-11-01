// 3. 유사도 결과 패널: 히트맵 표 + 클러스터맵 이미지
import { api } from './api.js';
import { $, el, toast } from './dom.js';

/** 0~1 값을 색으로 변환 (밝은 청록 → 진한 남색, 셀 글자색 대비 포함). */
function cellStyle(value) {
  const v = Math.min(Math.max(value, 0), 1);
  const lightness = 96 - v * 70; // 96% → 26%
  return {
    background: `hsl(${190 + v * 40}, 65%, ${lightness}%)`,
    color: lightness < 55 ? '#fff' : '#0f172a',
  };
}

function renderHeatmap({ artists, matrix }) {
  const table = $('#heatmap');
  const head = el('tr', {}, el('th', {}, ''), artists.map((a) => el('th', { scope: 'col', title: a }, a)));
  const rows = artists.map((rowName, i) => el('tr', {},
    el('th', { scope: 'row', title: rowName }, rowName),
    matrix[i].map((v, j) => {
      const td = el('td', { title: `${rowName} ↔ ${artists[j]}: ${v.toFixed(4)}` }, v.toFixed(2));
      Object.assign(td.style, cellStyle(v));
      if (i === j) td.classList.add('diag');
      return td;
    })));
  table.replaceChildren(el('thead', {}, head), el('tbody', {}, rows));
}

function loadClustermap() {
  const img = $('#clustermap-img');
  const url = api.clustermapUrl();
  img.onload = () => { $('#clustermap-figure').hidden = false; };
  img.onerror = () => { $('#clustermap-figure').hidden = true; };
  img.src = url;
  $('#clustermap-link').href = url;
}

export async function refreshResults() {
  let data;
  try {
    data = await api.similarity();
  } catch (e) {
    toast(`결과를 불러오지 못했습니다: ${e.message}`, 'error');
    return;
  }
  const hasMatrix = data.artists.length >= 2;
  $('#results-empty').hidden = hasMatrix;
  $('#heatmap-wrap').hidden = !hasMatrix;
  $('#results-csv-link').hidden = !hasMatrix;
  if (hasMatrix) renderHeatmap(data);
  if (data.clustermap_available) loadClustermap();
  else $('#clustermap-figure').hidden = true;
}

export function initResults() {
  $('#results-refresh-btn').addEventListener('click', refreshResults);
  return refreshResults();
}
