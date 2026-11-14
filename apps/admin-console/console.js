import {api, completeLogin, signIn, signOut} from './auth.js';

const content=document.getElementById('content'), status=document.getElementById('status');
const app=document.body.dataset.app;
const button=document.getElementById('signin');
let roles=[];
const has=(...requested)=>requested.some(role=>roles.includes(role));
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const details=x=>JSON.stringify(x,null,2);
const articleRole=()=>has('curator','editor','approver','publisher');
const activity=async(fn)=>{try{await fn();}catch(error){status.textContent=error.message;}};

function issueList(rows) {
  return `<section><h2>Issue PDFs</h2>${rows.map(row=>`<article><strong>${esc(row.title)}</strong><p>${esc(row.edition_date)} · ${esc(row.state)} · ${row.page_count} pages</p>
  <button class="secondary" data-action="pdf" data-id="${esc(row.id)}">Open PDF</button>
  ${app==='admin'&&((row.state==='draft'&&has('approver'))||(row.state==='approved'&&has('publisher')))?`<form data-action="${row.state==='draft'?'approve':'release'}" data-id="${esc(row.id)}"><label>Reviewed PDF checksum<input name="checksum" required pattern="[0-9a-f]{64}" placeholder="Copy the checksum shown below"></label><code>${esc(row.checksum)}</code><label>Decision note<input name="note" required minlength="12" maxlength="500"></label><button class="primary">${row.state==='draft'?'Approve reviewed PDF':'Release to tenant archive'}</button></form>`:''}</article>`).join('')||'<p>No issues for this account.</p>'}</section>`;
}

async function load() {
  if(app==='sutra'){content.innerHTML=issueList(await api('issues'));return;}
  if(app==='dashboard'){
    content.innerHTML=(!articleRole()?'':`<section><h2>Search reviewed research</h2><form data-action="search"><label>Search terms<input name="q" maxlength="120"></label><label>Topic<select name="topic"><option value="">All topics</option><option value="ai">AI</option><option value="data">Data engineering</option><option value="finance">Finance</option><option value="math">Mathematical modeling</option></select></label><label>Publication type<select name="kind"><option value="">All types</option><option value="brief">News brief</option><option value="peer-reviewed">Peer-reviewed</option><option value="preprint">Preprint</option></select></label><button class="primary">Search</button></form><div id="search-results"></div></section><section><h2>Collected evidence</h2><div id="evidence"></div></section>`)+issueList(await api('issues'));
    if (articleRole()) {const evidence=await api('evidence');document.getElementById('evidence').innerHTML=evidence.map(a=>`<article><strong>${esc(a.title)}</strong><p>${a.fixture?'Fixture':'Collected feed'} · ${esc(a.publisher)}</p>${has('curator')?`<button class="secondary" data-action="suggest" data-id="${esc(a.urn)}">Request AI suggestion</button><p aria-live="polite"></p>`:''}</article>`).join('')||'<p>No evidence has been collected.</p>';}
    return;
  }
  const rows=articleRole()?await api('articles'):[];
  content.innerHTML=`${has('curator')?'<section><h2>Submit or revise a brief</h2><form data-action="submit"><label>Article JSON<textarea name="brief" required></textarea></label><label>Current revision for edits<input name="revision" type="number" min="1"></label><button class="primary">Save draft</button></form></section>':''}
  ${articleRole()?`<section><h2>Briefs and review</h2>${rows.map(a=>`<article><strong>${esc(a.title)}</strong><p>ID <code>${esc(a.id)}</code> · Revision ${a.revision} · ${esc(a.state)}</p><details><summary>Read article and source</summary><pre>${esc(details(a))}</pre><a class="plain-link" href="${esc(a.source.url)}" rel="noopener noreferrer" target="_blank">Open primary source</a></details><button class="secondary" data-action="language" data-id="${esc(a.id)}">Check language</button><pre aria-live="polite"></pre>
  ${has('editor')&&a.state==='draft'?`<form data-action="review" data-id="${esc(a.id)}"><label><span><input type="checkbox" required> I checked the original source and the publication type</span></label><label><span><input type="checkbox" required> I reviewed grammar and spelling</span></label><label>Review rationale<input name="rationale" required minlength="12"></label><button class="primary">Review brief</button></form>`:''}</article>`).join('')||'<p>There are no submitted briefs.</p>'}</section>`:''}
  ${has('editor')?'<section><h2>Create draft issue</h2><form data-action="create"><label>Issue title<input name="title" required minlength="4"></label><label>Edition date<input type="date" name="date" required></label><label>Reviewed article IDs separated by commas<input name="ids" required></label><button class="primary">Generate draft PDF</button></form></section>':''}
  ${issueList(await api('issues'))}
  ${has('auditor')?`<section><h2>Platform and IAM</h2><pre>${esc(details(await api('platform')))}</pre></section><section><h2>Audit events</h2><pre>${esc(details(await api('audit')))}</pre></section>`:''}`;
}

content.addEventListener('submit',event=>{event.preventDefault();const form=event.target;const data=Object.fromEntries(new FormData(form)); activity(async()=>{
  const action=form.dataset.action,id=form.dataset.id;
  if(action==='search'){
    const query=new URLSearchParams(Object.entries(data).filter(([,v])=>v));
    const rows=await api('search?'+query);
    document.getElementById('search-results').innerHTML=rows.map(row=>`<article><strong>${esc(row.title)}</strong><p>${esc(row.kind)} · ${esc(row.summary)}</p></article>`).join('')||'<p>No reviewed matches.</p>';
    return;
  }
  for(const control of form.querySelectorAll('button')) control.disabled=true;
  try{
    if(action==='submit'){const item=JSON.parse(data.brief);await api(data.revision?`articles/${encodeURIComponent(item.id)}?revision=${encodeURIComponent(data.revision)}`:'articles',data.revision?'PUT':'POST',item);}
    if(action==='review') await api('articles/'+id+'/review','POST',{source_checked:true,grammar_reviewed:true,rationale:data.rationale});
    if(action==='create') await api('issues','POST',{title:data.title,date:data.date,article_ids:data.ids.split(',').map(x=>x.trim())});
    if(action==='approve'||action==='release') await api('issues/'+id+'/'+action,'POST',data);
    status.textContent='Saved'; await load();
  }finally{for(const control of form.querySelectorAll('button')) control.disabled=false;}
});});
content.addEventListener('click', event=>{
 const control=event.target.closest('button[data-action]');if(!control)return;
 activity(async()=>{
   const {id,action}=control.dataset;
   if(action==='pdf'){
     const blob=await api('issues/'+id+'/pdf','GET',null,true);
     const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download='sutra-'+id+'.pdf';link.click();setTimeout(()=>URL.revokeObjectURL(url),30000);
   }else if(action==='language'){control.nextElementSibling.textContent=details(await api('articles/'+id+'/language','POST'));}
   else if(action==='suggest'){control.nextElementSibling.textContent=(await api('evidence/'+id+'/suggest','POST')).suggestion;}
 });
});
button.addEventListener('click',()=>activity(signIn));
activity(async()=>{
 if(!await completeLogin())return;
 const session=await api('session');roles=session.roles;
 button.replaceWith(Object.assign(document.createElement('button'),{textContent:'Sign out',className:'secondary',onclick:signOut}));
 status.textContent=`Signed in · Tenant ${session.tenant}`;
 await load();
});
