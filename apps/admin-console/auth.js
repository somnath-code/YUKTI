const config = await fetch('/ui-config').then(response => response.json());
const root = config.issuer + '/protocol/openid-connect';
const redirect = location.origin + location.pathname;
const encoder = new TextEncoder();
const b64 = data => btoa(String.fromCharCode(...data)).replace(/=/g,'').replace(/\+/g,'-').replace(/\//g,'_');
const random = () => b64(crypto.getRandomValues(new Uint8Array(32)));
let token = sessionStorage.getItem('yukti-token');

export async function signIn() {
  const verifier=random(), state=random();
  sessionStorage.setItem('yukti-pkce', JSON.stringify({verifier,state,redirect}));
  const challenge=b64(new Uint8Array(await crypto.subtle.digest('SHA-256',encoder.encode(verifier))));
  const params=new URLSearchParams({client_id:config.client_id, redirect_uri:redirect, response_type:'code', scope:'openid',
                                    state, code_challenge:challenge, code_challenge_method:'S256'});
  location.assign(root+'/auth?'+params);
}
export function signOut() {
  sessionStorage.removeItem('yukti-token');
  location.assign(root+'/logout');
}
export async function completeLogin() {
  const params=new URLSearchParams(location.search);
  const code=params.get('code');
  if (!code && !params.has('error')) return Boolean(token);
  history.replaceState({},'',location.pathname);
  const flow=JSON.parse(sessionStorage.getItem('yukti-pkce')||'null');
  sessionStorage.removeItem('yukti-pkce');
  if(!code || !flow || flow.state!==params.get('state') || flow.redirect!==redirect) throw Error('Sign-in could not be verified. Start again.');
  const response=await fetch(root+'/token',{method:'POST',body:new URLSearchParams({grant_type:'authorization_code',
    client_id:config.client_id,code,redirect_uri:redirect,code_verifier:flow.verifier})});
  if(!response.ok) throw Error('Keycloak could not complete sign-in.');
  token=(await response.json()).access_token;
  sessionStorage.setItem('yukti-token',token);
  return true;
}
export async function api(path, method='GET', data, binary=false) {
  const headers={Authorization:'Bearer '+token};
  if (data) headers['Content-Type']='application/json';
  const response=await fetch('/api/'+path,{method,headers,body:data?JSON.stringify(data):undefined,cache:'no-store'});
  if(response.status===401){sessionStorage.removeItem('yukti-token');throw Error('Your session expired. Reload and sign in again.');}
  if(!response.ok){const detail=(await response.json()).detail;throw Error(typeof detail==='string'?detail:JSON.stringify(detail,null,2));}
  return binary?response.blob():response.json();
}
