// 2. 분석 실행 패널: 작업 시작/취소, 진행률·로그 폴링
import { api } from './api.js';
import { $, el, toast } from './dom.js';
import { t } from './i18n.js';

// 서버의 pipeline.STAGES (+ runner 의 model 단계) 와 순서를 맞춥니다.
const STAGES = [
  ['model', 'job.stage.model'],
  ['download', 'job.stage.download'],
  ['convert', 'job.stage.convert'],
  ['process', 'job.stage.process'],
  ['analyze', 'job.stage.analyze'],
];
const STATUS_LABEL = {
  queued: 'job.status.queued',
  running: 'job.status.running',
  succeeded: 'job.status.succeeded',
  failed: 'job.status.failed',
  cancelled: 'job.status.cancelled',
};
const POLL_MS = 1000;
const MAX_LOG_CHARS = 200_000;

let job = null;
let logOffset = 0;
let pollTimer = null;
let pollCount = 0;
let hooks = { getSelection: () => [], onTick: () => {}, onFinished: () => {} };

const isActive = (j) => j && (j.status === 'queued' || j.status === 'running');

function overallPercent(j) {
  if (!j) return 0;
  if (j.status === 'succeeded') return 100;
  const idx = STAGES.findIndex(([key]) => key === j.stage);
  if (idx < 0) return 0;
  const within = j.total ? j.current / j.total : 0;
  return Math.round(((idx + within) / STAGES.length) * 100);
}

function render() {
  const active = isActive(job);
  const badge = $('#job-status-badge');
  badge.textContent = job
    ? t(STATUS_LABEL[job.status] || 'job.status.waiting')
    : t('job.status.waiting');
  badge.className = `badge ${job?.status || ''}`;
  $('#job-start-btn').disabled = active;
  $('#job-cancel-btn').hidden = !active;
  $('#job-progress').style.width = `${overallPercent(job)}%`;
  $('#job-progress').classList.toggle('animated', active);
  $('#job-error').textContent = job?.error || '';
  $('#job-copy-failures-btn').disabled = !job?.failure_logs?.length;

  const currentIdx = STAGES.findIndex(([key]) => key === job?.stage);
  $('#job-stages').replaceChildren(...STAGES.map(([key, label], i) => {
    let state = '';
    if (job && (i < currentIdx || job.status === 'succeeded')) state = 'done';
    else if (job && i === currentIdx) state = active ? 'current' : job.status;
    const detail = state === 'current' && key !== 'model' && job.total ? ` ${job.current}/${job.total}` : '';
    return el('li', { class: state }, t(label) + detail);
  }));
  renderTarget();
}

function renderTarget() {
  const names = isActive(job) ? job.artists : hooks.getSelection();
  $('#job-target').textContent = names?.length
    ? t('job.target.selected', { names: names.join(', ') })
    : t('job.target.all');
}

function appendLogs(lines) {
  if (!lines?.length) return;
  const pre = $('#job-log');
  const stick = pre.scrollTop + pre.clientHeight >= pre.scrollHeight - 8;
  let text = pre.textContent + lines.join('\n') + '\n';
  if (text.length > MAX_LOG_CHARS) text = text.slice(-MAX_LOG_CHARS);
  pre.textContent = text;
  if (stick) pre.scrollTop = pre.scrollHeight;
}

function copyText(text) {
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.setAttribute('readonly', '');
  textarea.style.position = 'fixed';
  textarea.style.opacity = '0';
  document.body.append(textarea);
  let copied;
  try {
    textarea.select();
    copied = document.execCommand('copy');
  } finally {
    textarea.remove();
  }
  if (!copied) throw new Error(t('job.clipboard.unsupported'));
}

async function copyFailureLogs() {
  const lines = job?.failure_logs || [];
  if (!lines.length) {
    toast(t('job.toast.failure_logs_empty'), 'info');
    return;
  }
  const text = lines.join('\n');
  try {
    if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(text);
    else copyText(text);
    toast(t('job.toast.failure_logs_copied', { count: lines.length }), 'success');
  } catch (e) {
    toast(t('job.toast.failure_logs_copy_error', { message: e.message }), 'error');
  }
}

async function poll() {
  if (!job) return;
  try {
    const next = await api.getJob(job.id, logOffset);
    appendLogs(next.logs);
    logOffset = next.next_log_offset;
    const wasActive = isActive(job);
    job = next;
    render();
    pollCount += 1;
    if (isActive(job)) {
      if (pollCount % 5 === 0) hooks.onTick();
      pollTimer = setTimeout(poll, POLL_MS);
    } else if (wasActive) {
      const kind = job.status === 'succeeded' ? 'success' : job.status === 'failed' ? 'error' : 'info';
      toast(t('job.toast.finished', { status: t(STATUS_LABEL[job.status]) }), kind);
      hooks.onFinished(job);
    }
  } catch (e) {
    pollTimer = setTimeout(poll, POLL_MS * 3); // 일시적인 네트워크 오류는 재시도
  }
}

function track(newJob) {
  clearTimeout(pollTimer);
  job = newJob;
  logOffset = 0;
  pollCount = 0;
  $('#job-log').textContent = '';
  render();
  poll();
}

async function start() {
  try {
    const created = await api.startJob(hooks.getSelection());
    $('#job-log-box').open = true;
    track(created);
  } catch (e) {
    if (e.status === 409 && e.detail?.active_job_id) {
      toast(t('job.toast.already_running'), 'info');
      track(await api.getJob(e.detail.active_job_id));
    } else {
      toast(e.message, 'error');
    }
  }
}

async function cancel() {
  if (!job || !confirm(t('job.toast.cancel_confirm'))) return;
  try {
    job = await api.cancelJob(job.id);
    toast(t('job.toast.cancel_requested'), 'info');
  } catch (e) {
    toast(e.message, 'error');
  }
}

export const refreshJobTarget = () => renderTarget();

export async function initJobs(options) {
  hooks = { ...hooks, ...options };
  $('#job-start-btn').addEventListener('click', start);
  $('#job-cancel-btn').addEventListener('click', cancel);
  $('#job-copy-failures-btn').addEventListener('click', copyFailureLogs);
  window.addEventListener('app-language-change', render);
  render();
  // 새로고침해도 진행 중이거나 가장 최근 작업을 이어서 보여줍니다.
  try {
    const [latest] = await api.listJobs();
    if (latest) track(latest);
  } catch {
    /* 서버 미기동 등은 무시 */
  }
}
