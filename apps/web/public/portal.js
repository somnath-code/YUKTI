const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const topics = {all:'All topics', ai:'AI', data:'Data engineering', finance:'Finance', math:'Mathematical modeling', research:'Research papers'};
const kinds = {brief:'News brief', 'peer-reviewed':'Peer-reviewed', preprint:'Preprint'};
const dates = new Intl.DateTimeFormat('en-GB', {dateStyle:'medium', timeZone:'UTC'});
const showDate = value => value.length === 10 ? dates.format(new Date(value+'T00:00:00Z')) : value;
const state = {view:'issues', issue:null, topic:'all'};
let catalog, lookup, opener;

function sync() {
  const [requested, id] = location.hash.slice(1).split('/');
  state.view = ['issues','library','preview'].includes(requested) ? requested : 'issues';
  state.issue = catalog.issues.find(x=>x.id===id && x.status==='archive') || catalog.issues.find(x=>x.status==='archive');
  state.topic='all'; $('search').value=''; $('kind').value='';
  render();
}

function render() {
  const draft=catalog.issues.find(x=>x.status==='draft');
  const issue=state.view==='preview'?draft:state.issue;
  for (const link of document.querySelectorAll('nav [data-view]')) {
    if(link.dataset.view===state.view) link.setAttribute('aria-current','page'); else link.removeAttribute('aria-current');
  }
  $('hero').innerHTML=`<div class="hero-copy"><div class="eyebrow">The weekly research magazine</div><h1 id="hero-title">SUTRA</h1><div class="hero-title">Ideas, evidence and impact</div><p>Explore research papers and concise briefs with direct links to the original sources.</p><div class="hero-actions"><a class="primary" href="#issues">Read latest issue <span aria-hidden="true">→</span></a><a class="secondary" href="#preview">Preview next issue</a></div></div><div class="art"><figure><img src="assets/sutra-cover.webp" alt="SUTRA concept cover with a gold spiral and open book on a navy background"></figure></div>`;
  $('aside').innerHTML=`<h2 class="aside-title">Issue archive</h2><div class="issues">${catalog.issues.filter(x=>x.status==='archive').map(x=>`<a class="issue" href="#issues/${x.id}" ${state.view==='issues'&&issue.id===x.id?'aria-current="page"':''}><strong>Issue ${x.number}</strong><span aria-hidden="true">→</span><small>${showDate(x.date)}</small></a>`).join('')}</div><div class="aside-note"><p>Sample editions use dated, historical sources.</p><p><b>Peer-reviewed</b> identifies a journal or conference publication. <b>Preprint</b> identifies the repository version cited.</p></div>`;
  const label=state.view==='library'?'Research library':`Issue ${issue.number} · ${showDate(issue.date)}`;
  const title=state.view==='library'?'Browse research and briefs':issue.title;
  const subtitle=state.view==='library'?'Search across the sample archive by topic or publication type.':issue.subtitle;
  $('intro').innerHTML=`<div class="eyebrow">${esc(label)}</div><h2 id="feed-title">${esc(title)}</h2><p>${esc(subtitle)}</p>${state.view==='preview'?'<div class="preview-notice"><span><strong>Awaiting manual approval</strong><br>Private editorial preview of the sample issue.</span><a class="plain-link" href="assets/sutra-draft.pdf" target="_blank" rel="noopener">Open draft PDF ↗</a></div>':''}`;
  renderResults();
}

function renderResults() {
  $('topics').innerHTML=Object.entries(topics).map(([key,label])=>`<button type="button" data-topic="${key}" aria-pressed="${state.topic===key}">${label}</button>`).join('');
  const draft=catalog.issues.find(x=>x.status==='draft');
  const issue=state.view==='preview'?draft:state.issue;
  const ids=state.view==='library'?[...new Set(catalog.issues.filter(x=>x.status==='archive').flatMap(x=>x.article_ids))]:issue.article_ids;
  const query=$('search').value.trim().toLowerCase();
  const kind=$('kind').value;
  const visible=ids.map(id=>lookup.get(id)).filter(x=>
    (state.topic==='all'||(state.topic==='research'?x.kind!=='brief':x.topic===state.topic)) &&
    (!kind||x.kind===kind) &&
    (!query||[x.title,x.summary,x.source.authors,x.source.venue,x.source.title].some(v=>v.toLowerCase().includes(query))));
  $('result-meta').textContent=`${visible.length} ${visible.length===1?'item':'items'}`;
  $('results').innerHTML=visible.length?`<div class="cards">${visible.map(x=>`<article class="card"><div class="tags"><span class="badge">${topics[x.topic]}</span><span class="badge ${x.kind}">${kinds[x.kind]}</span></div><h3>${esc(x.title)}</h3><p>${esc(x.summary)}</p><button type="button" data-brief="${x.id}">Read brief <span aria-hidden="true">→</span></button></article>`).join('')}</div>`:'<p class="empty">No items match those filters. <button class="plain-link" id="clear" type="button">Clear filters</button></p>';
}

function readBrief(article) {
  const url=new URL(article.source.url);
  $('brief-inner').innerHTML=`<section class="detail" aria-labelledby="detail-title"><div class="dialog-top"><div class="tags"><span class="badge">${topics[article.topic]}</span><span class="badge ${article.kind}">${kinds[article.kind]}</span></div><button type="button" id="close" aria-label="Close brief">×</button></div><h2 id="detail-title">${esc(article.title)}</h2><p>${esc(article.summary)}</p><h3>What · When · Why</h3><dl><dt>What</dt><dd>${esc(article.what)}</dd><dt>When</dt><dd>${esc(showDate(article.when))}</dd><dt>Why</dt><dd>${esc(article.why)}</dd></dl><h3>Context · Action · Result</h3><dl><dt>Context</dt><dd>${esc(article.context)}</dd><dt>Action</dt><dd>${esc(article.action)}</dd><dt>Result</dt><dd>${esc(article.result)}</dd></dl>${article.formula?`<p class="formula">${esc(article.formula)}</p>`:''}<div class="reference"><h3>Primary source</h3><p>${esc(article.source.authors)}. “${esc(article.source.title)}.” ${esc(article.source.venue)} (${esc(article.when.slice(0,4))}).</p>${url.protocol==='https:'?`<a class="plain-link" href="${esc(url.href)}" target="_blank" rel="noopener noreferrer">Open original source ↗</a>`:''}</div></section>`;
  $('brief').showModal();
  $('close').focus();
}

$('brief').addEventListener('close',()=>opener?.focus());
document.addEventListener('click', event=>{
  const button=event.target.closest('button');
  if (!button) return;
  if(button.dataset.topic){state.topic=button.dataset.topic;renderResults();$('topics').querySelector(`[data-topic="${state.topic}"]`).focus();}
  if(button.dataset.brief){opener=button;readBrief(lookup.get(button.dataset.brief));}
  if(button.id==='close') $('brief').close();
  if(button.id==='clear'){state.topic='all';$('search').value='';$('kind').value='';renderResults();$('search').focus();}
});
$('search').addEventListener('input',renderResults);
$('kind').addEventListener('change',renderResults);
window.addEventListener('hashchange',sync);
fetch('./catalog.json').then(response=>{
  if(!response.ok) throw new Error('Catalog unavailable');
  return response.json();
}).then(data=>{catalog=data;lookup=new Map(data.articles.map(x=>[x.id,x]));sync();}).catch(()=>{
  $('intro').innerHTML='<h2 id="feed-title">The SUTRA catalog could not load</h2><p>Reload the page to try again.</p>';
  $('filters').hidden=true;
});
