// 1. 아티스트 & URL 관리 패널
import { api } from './api.js';
import { $, el, toast } from './dom.js';

const STATUS_LABEL = {
  pending: '대기',
  downloaded: '다운로드됨',
  separated: '보컬 분리됨',
  done: '지문 완료',
  invalid: 'URL 오류',
};

const selected = new Set();
let artists = [];
let editing = null; // 수정 중인 아티스트 이름 (새로 만들 때는 null)
let onChange = () => {};

export function selectedArtists() {
  return artists.map((a) => a.name).filter((n) => selected.has(n));
}

export async function refreshArtists() {
  try {
    artists = await api.listArtists();
  } catch (e) {
    toast(`아티스트 목록을 불러오지 못했습니다: ${e.message}`, 'error');
    return;
  }
  for (const name of [...selected]) if (!artists.some((a) => a.name === name)) selected.delete(name);
  render();
}

function render() {
  const list = $('#artist-list');
  list.replaceChildren(...artists.map(renderArtist));
  $('#artist-empty').hidden = artists.length > 0;
  onChange();
}

function renderArtist(artist) {
  const total = artist.urls.length;
  const done = artist.embeddings;
  return el('li', { class: 'artist' },
    el('div', { class: 'artist-row' },
      el('label', { class: 'check' },
        el('input', {
          type: 'checkbox',
          checked: selected.has(artist.name),
          onchange: (ev) => {
            if (ev.target.checked) selected.add(artist.name); else selected.delete(artist.name);
            onChange();
          },
        }),
        el('span', { class: 'artist-name' }, artist.name)),
      el('span', { class: `count ${total && done === total ? 'complete' : ''}`, title: '지문 추출 완료 / 전체 URL' },
        `${done}/${total}`),
      el('button', { class: 'btn ghost small', type: 'button', onclick: () => openForm(artist) }, '수정'),
      el('button', { class: 'btn ghost small danger-text', type: 'button', onclick: () => removeArtist(artist) }, '삭제')),
    el('details', { class: 'url-details' },
      el('summary', {}, `URL ${total}개`),
      el('ul', { class: 'url-list' }, artist.urls.map((u) =>
        el('li', {},
          el('span', { class: `pill ${u.status}` }, STATUS_LABEL[u.status] || u.status),
          el('a', { href: u.url, target: '_blank', rel: 'noopener', class: 'url' }, u.url))))));
}

function openForm(artist = null) {
  editing = artist?.name ?? null;
  const form = $('#artist-form');
  form.hidden = false;
  $('#artist-name').value = artist?.name ?? '';
  $('#artist-name').readOnly = Boolean(artist);
  $('#artist-urls').value = artist ? artist.urls.map((u) => u.url).join('\n') : '';
  $('#artist-form-error').textContent = '';
  (artist ? $('#artist-urls') : $('#artist-name')).focus();
}

function closeForm() {
  $('#artist-form').hidden = true;
  editing = null;
}

async function submitForm(ev) {
  ev.preventDefault();
  const name = editing ?? $('#artist-name').value.trim();
  const urls = $('#artist-urls').value.split('\n').map((s) => s.trim()).filter(Boolean);
  if (!editing && artists.some((a) => a.name === name)) {
    $('#artist-form-error').textContent = '같은 이름의 아티스트가 이미 있습니다. 목록에서 ‘수정’을 사용하세요.';
    return;
  }
  try {
    await api.saveArtist(name, urls);
  } catch (e) {
    const invalid = e.detail?.invalid_urls;
    $('#artist-form-error').textContent = invalid ? `잘못된 URL: ${invalid.join(', ')}` : e.message;
    return;
  }
  toast(`‘${name}’ 저장됨`, 'success');
  closeForm();
  await refreshArtists();
}

async function removeArtist(artist) {
  if (!confirm(`‘${artist.name}’ 아티스트를 목록에서 삭제할까요?`)) return;
  const purge = artist.urls.some((u) => u.status !== 'pending' && u.status !== 'invalid')
    && confirm('다운로드된 오디오와 추출된 지문(database 폴더)도 함께 삭제할까요?\n취소를 누르면 URL 목록만 삭제됩니다.');
  try {
    await api.deleteArtist(artist.name, purge);
  } catch (e) {
    toast(e.message, 'error');
    return;
  }
  selected.delete(artist.name);
  toast(`‘${artist.name}’ 삭제됨`, 'success');
  await refreshArtists();
}

export function initArtists({ onSelectionChange } = {}) {
  onChange = onSelectionChange || onChange;
  $('#artist-new-btn').addEventListener('click', () => openForm());
  $('#artist-cancel-btn').addEventListener('click', closeForm);
  $('#artist-form').addEventListener('submit', submitForm);
  return refreshArtists();
}
