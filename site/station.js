'use strict';
const $ = s => document.querySelector(s);
const canvas = $('#sky'), ctx = canvas.getContext('2d');
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
let paused = reduced.matches, frame = 0, nodes = [], data, width = 0, height = 0, warp = 0;
function setPause(value) { paused = value; $('#motion').textContent = paused ? '启动轨道' : '暂停轨道'; $('#motion').setAttribute('aria-pressed', String(paused)); document.body.classList.toggle('paused', paused); }
setPause(paused);
reduced.addEventListener('change', e => setPause(e.matches));
$('#motion').onclick = () => setPause(!paused);
$('#theme').onclick = () => { const light = document.body.classList.toggle('light'); $('#theme').textContent = light ? '夜间模式' : '日间模式'; };
document.body.classList.toggle('light', matchMedia('(prefers-color-scheme: light)').matches);
$('#theme').textContent = document.body.classList.contains('light') ? '夜间模式' : '日间模式';
function resize() { const rect = canvas.getBoundingClientRect(); width = rect.width; height = rect.height; const dpr = Math.min(devicePixelRatio || 1, 2); canvas.width = width * dpr; canvas.height = height * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0); }
new ResizeObserver(resize).observe(canvas);
function draw() {
  ctx.clearRect(0, 0, width, height);
  const styles = getComputedStyle(document.body), cyan = styles.getPropertyValue('--cyan').trim(), amber = styles.getPropertyValue('--amber').trim();
  const cx = width * .5, cy = height * .47, radius = Math.min(width * .45, height * .44);
  const glow = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.max(1, radius)); glow.addColorStop(0, document.body.classList.contains('light') ? '#98cbd433' : '#39778638'); glow.addColorStop(1, '#39778600'); ctx.fillStyle = glow; ctx.fillRect(0, 0, width, height);
  ctx.strokeStyle = styles.getPropertyValue('--line').trim(); ctx.lineWidth = .7;
  for (const r of [.35, .65, 1]) { ctx.beginPath(); ctx.ellipse(cx, cy, radius * r, radius * r * .7, 0, 0, Math.PI * 2); ctx.stroke(); }
  nodes = [];
  (data?.days || []).forEach((day, i, days) => {
    const a = i * 2.39996323 + frame * .001, r = 20 + Math.sqrt(i / Math.max(1, days.length - 1)) * (radius - 20);
    const x = cx + Math.cos(a) * r, y = cy + Math.sin(a) * r * .7;
    const size = day.contributionCount ? Math.min(5, 1.6 + Math.log2(day.contributionCount + 1) * .55) : 1;
    ctx.fillStyle = day.contributionCount > 8 ? amber : day.contributionCount ? cyan : styles.getPropertyValue('--line').trim();
    ctx.beginPath(); ctx.arc(x, y, size, 0, Math.PI * 2); ctx.fill(); nodes.push({ x, y, day });
  });
  ctx.fillStyle = cyan; ctx.beginPath(); ctx.arc(cx, cy, 5, 0, Math.PI * 2); ctx.fill();
  const a = frame * .008; ctx.fillStyle = amber; ctx.beginPath(); ctx.arc(cx + Math.cos(a) * radius, cy + Math.sin(a) * radius * .7, 4, 0, Math.PI * 2); ctx.fill();
  if (!paused && !document.hidden) { frame += warp > 0 ? 18 : 1; if (warp > 0) warp--; }
  requestAnimationFrame(draw);
}
requestAnimationFrame(draw);
canvas.addEventListener('pointermove', e => {
  const box = canvas.getBoundingClientRect(), x = e.clientX - box.left, y = e.clientY - box.top;
  let closest, distance = 14;
  nodes.forEach(n => { const d = Math.hypot(x - n.x, y - n.y); if (d < distance) { closest = n; distance = d; } });
  $('#star-info').textContent = closest ? `${closest.day.date} / ${closest.day.contributionCount} 次贡献` : '移动到星星上，查看当天贡献';
});
let catIndex = 0;
const messages = ['喵。轨道正常，咖啡储量未知。', '你知道吗？这里每颗星，都是一天真实的贡献记录。', '我的工作是巡逻，最擅长的技能是休眠。', '试试在终端输入 warp。准备好跃迁了吗？', '收到新任务：去给喜欢的开源项目一颗星。'];
$('#cat').onclick = () => { $('#cat-message').textContent = messages[catIndex++ % messages.length]; };
function log(text) { const p = document.createElement('p'); p.textContent = text; $('#log').append(p); while ($('#log').children.length > 25) $('#log').firstElementChild.remove(); $('#log').scrollTop = $('#log').scrollHeight; }
$('#terminal').addEventListener('submit', e => {
  e.preventDefault(); const command = $('#command').value.trim().toLowerCase(); if (!command) return; log('$ ' + command); $('#command').value = '';
  switch (command) {
    case 'help': log('help / projects / stars / warp / meow / clear'); break;
    case 'projects': $('#projects').scrollIntoView({ behavior: reduced.matches ? 'instant' : 'smooth' }); log('项目舱已就绪。选择项目名称打开仓库。'); break;
    case 'stars': log(data ? `星图记录了 ${data.days.length} 天，共 ${data.total} 次贡献。` : '贡献信号暂未接通。稍后刷新重试。'); break;
    case 'warp': if (paused) log('轨道已暂停。点击“启动轨道”后再试。'); else { warp = 100; log('跃迁引擎启动。下一站：未知的好点子。'); } break;
    case 'meow': $('#cat').click(); log($('#cat-message').textContent); break;
    case 'clear': $('#log').replaceChildren(); break;
    default: log('未知指令。输入 help 查看可用指令。');
  }
});
fetch('data.json').then(r => { if (!r.ok) throw Error(r.status); return r.json(); }).then(payload => {
  data = payload; $('#total').textContent = `${data.total.toLocaleString()} 次贡献 / ${data.days.length} 天观测`; $('#updated').textContent = '最近同步 ' + data.updated;
  const list = $('#project-list'); list.replaceChildren();
  data.projects.forEach((project, index) => {
    const article = document.createElement('article'); article.className = 'project';
    const number = document.createElement('span'); number.className = 'index'; number.textContent = String(index + 1).padStart(2, '0');
    const body = document.createElement('div'), title = document.createElement('h3'), link = document.createElement('a');
    link.href = project.url; link.textContent = project.name + ' ↗'; title.append(link);
    const desc = document.createElement('p'); desc.textContent = project.description || '打开仓库，探索项目。'; body.append(title, desc);
    const meta = document.createElement('div'); meta.className = 'meta'; meta.textContent = `${project.primaryLanguage?.name || '开源项目'} / ★ ${project.stargazerCount}`;
    article.append(number, body, meta); list.append(article);
  });
}).catch(() => { $('#total').textContent = '贡献数据暂时不可用'; $('#updated').textContent = '请刷新重试，或通过项目舱访问 GitHub'; log('星图同步失败。项目舱中的 GitHub 链接仍可使用。'); });
