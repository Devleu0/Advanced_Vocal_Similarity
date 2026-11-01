// 1. 아티스트 & URL 관리 패널
import { api } from './api.js';
import { $, el, toast } from './dom.js';
import { t } from './i18n.js';

const STATUS_LABEL = {
  pending: 'artist.status.pending',
  downloaded: 'artist.status.downloaded',
  separated: 'artist.status.separated',
  done: 'artist.status.done',
  invalid: 'artist.status.invalid',
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
    toast(t('artist.list.error', { message: e.message }), 'error');
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
      el('span', { class: `count ${total && done === total ? 'complete' : ''}`, title: t('artist.status.count') },
        `${done}/${total}`),
      el('button', { class: 'btn ghost small', type: 'button', onclick: () => openForm(artist) }, t('artist.edit')),
      el('button', { class: 'btn ghost small danger-text', type: 'button', onclick: () => removeArtist(artist) }, t('artist.delete'))),
    el('details', { class: 'url-details' },
      el('summary', {}, t('artist.url.count', { count: total })),
      el('ul', { class: 'url-list' }, artist.urls.map((u) =>
        el('li', {},
          el('span', { class: `pill ${u.status}` }, t(STATUS_LABEL[u.status] || 'artist.status.pending')),
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
    $('#artist-form-error').textContent = t('artist.form.duplicate');
    return;
  }
  try {
    await api.saveArtist(name, urls);
  } catch (e) {
    const invalid = e.detail?.invalid_urls;
    $('#artist-form-error').textContent = invalid
      ? t('artist.form.invalid', { urls: invalid.join(', ') })
      : e.message;
    return;
  }
  toast(t('artist.saved', { name }), 'success');
  closeForm();
  await refreshArtists();
}

async function removeArtist(artist) {
  if (!confirm(t('artist.delete.confirm', { name: artist.name }))) return;
  const purge = artist.urls.some((u) => u.status !== 'pending' && u.status !== 'invalid')
    && confirm(t('artist.delete.data.confirm'));
  try {
    await api.deleteArtist(artist.name, purge);
  } catch (e) {
    toast(e.message, 'error');
    return;
  }
  selected.delete(artist.name);
  toast(t('artist.deleted', { name: artist.name }), 'success');
  await refreshArtists();
}

export function initArtists({ onSelectionChange } = {}) {
  onChange = onSelectionChange || onChange;
  $('#artist-new-btn').addEventListener('click', () => openForm());
  $('#artist-cancel-btn').addEventListener('click', closeForm);
  $('#artist-form').addEventListener('submit', submitForm);
  window.addEventListener('app-language-change', render);
  return refreshArtists();
}
