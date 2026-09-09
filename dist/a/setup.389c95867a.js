(function(){
'use strict';
var REG={"keith-godding": {"slug": "keith-godding", "name": "Keith Godding", "title": "Realtor", "phone": "416-520-6687", "email": "keith@firstaccesshomes.com", "site": "firstaccesshomes.com", "headshot": "keith-godding.jpg", "tagline": "Toronto and the GTA"}};
function b64e(o){var s=JSON.stringify(o),b=new TextEncoder().encode(s),t='';
for(var i=0;i<b.length;i++)t+=String.fromCharCode(b[i]);
return btoa(t).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
function v(id){var e=document.getElementById(id);return e.type==='checkbox'?e.checked:e.value.trim();}
function build(){
  var pick=v('g-pick'), base=location.origin+'/', frag=[];
  if(pick && pick!=='__none__'){ base=location.origin+'/'+pick; }
  else if(pick===''){
    var a={};
    ['name','title','phone','email','site','tag','photo'].forEach(function(k){
      var val=v('g-'+k); if(val) a[k==='tag'?'tagline':k]=val;
    });
    if(Object.keys(a).length) frag.push('a='+b64e(a));
  }
  var s={};
  if(v('g-client'))  s.client=v('g-client');
  if(v('g-address')) s.address=v('g-address');
  if(v('g-closing')) s.closing=v('g-closing');
  if(v('g-condo'))   s.condo=1;
  if(v('g-buying'))  s.buying=1;
  if(v('g-rented'))  s.rented=1;
  if(Object.keys(s).length) frag.push('s='+b64e(s));
  var url=base+(frag.length?'#'+frag.join('&'):'');
  document.getElementById('out').textContent=url;
  document.getElementById('open').href=url;
  return url;
}
document.querySelectorAll('input,select').forEach(function(e){
  e.addEventListener('input',build); e.addEventListener('change',build);
});
document.getElementById('g-pick').addEventListener('change',function(){
  var r=REG[this.value];
  if(r){
    document.getElementById('g-name').value=r.name||'';
    document.getElementById('g-title').value=r.title||'';
    document.getElementById('g-phone').value=r.phone||'';
    document.getElementById('g-email').value=r.email||'';
    document.getElementById('g-site').value=r.site||'';
    document.getElementById('g-tag').value=r.tagline||'';
  }
  build();
});
document.getElementById('copy').addEventListener('click',function(){
  var url=build(), ok=document.getElementById('ok');
  function done(){ ok.textContent='Copied'; setTimeout(function(){ok.textContent='';},2200); }
  if(navigator.clipboard&&window.isSecureContext){
    navigator.clipboard.writeText(url).then(done,fallback);
  } else fallback();
  function fallback(){
    // clipboard API is blocked on plain http and in some embedded browsers;
    // the seller-facing page never needs this but a realtor on a locked-down
    // device does, and a copy button that silently does nothing is worse than
    // no button.
    var t=document.createElement('textarea');
    t.value=url; t.style.position='fixed'; t.style.opacity='0';
    document.body.appendChild(t); t.select();
    try{ document.execCommand('copy'); done(); }
    catch(e){ ok.textContent='Press and hold the link above to copy'; }
    t.remove();
  }
});
build();
})();