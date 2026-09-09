(function(){
'use strict';
var REG={"keith-godding": {"slug": "keith-godding", "name": "Keith Godding", "title": "Realtor", "phone": "416-520-6687", "email": "keith@firstaccesshomes.com", "site": "firstaccesshomes.com", "headshot": "keith-godding.webp", "tagline": "Toronto and the GTA"}};
function b64e(o){var s=JSON.stringify(o),b=new TextEncoder().encode(s),t='';
for(var i=0;i<b.length;i++)t+=String.fromCharCode(b[i]);
return btoa(t).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
function v(id){var e=document.getElementById(id);return e.type==='checkbox'?e.checked:e.value.trim();}

// ---------------------------------------------------------------------------
// The photograph. A realtor who has one online pastes its address and the link
// stays short. A realtor who only has it on their phone uploads it, and it is
// downscaled and encoded HERE, in their browser, then carried inside the link
// itself. Nothing is uploaded to any server, because there is no server to
// upload to: this whole tool is static files.
//
// 192px WebP at 0.88, which is exactly what the registry ships, so an uploaded
// photograph is not a lesser one. The close draws the photo at 62px in a
// circle, and a 3x phone therefore asks for 186 real pixels: under that the
// device is upscaling, and upscaling is what soft looks like. Measured against
// the untouched source crop, root-mean-square error per channel: 128 WebP q72
// read 5.19, 176 JPEG q86 (what the registry shipped before) 2.94, 192 WebP
// q88 2.28, and 192 WebP q94 only 1.76 for half again the bytes. So 192 at
// 0.88 is the knee, and it is both sharper and smaller than the JPEG.
// ---------------------------------------------------------------------------
var PHOTO = null;
var PHOTO_PX = 192;
var PHOTO_Q = 0.88;

function note(msg){ document.getElementById('g-note').textContent = msg; }

function showPhoto(dataUri){
  PHOTO = dataUri;
  var prev = document.getElementById('g-prev');
  var clear = document.getElementById('g-clear');
  if(dataUri){ prev.src = dataUri; prev.hidden = false; clear.hidden = false; }
  else { prev.removeAttribute('src'); prev.hidden = true; clear.hidden = true; }
  build();
}

// A pasted address is the other half of this, and it used to fail in silence.
// The content policy allows an image from 'self', from https, or from a data:
// URI, and nothing else, so an http:// address or a share page that is not
// actually an image simply never appears, with no error a realtor could see.
// Check it here, in front of them, and show what will actually render.
var URLCHECK = null;
function checkPhotoUrl(u){
  u = (u || '').trim();
  if(URLCHECK){ URLCHECK.onload = URLCHECK.onerror = null; URLCHECK = null; }
  if(!u){
    if(!PHOTO) showPhoto(null);
    note('Or paste the address of one already online, below. Leave both empty '
         + 'and the close simply has no photograph.');
    return;
  }
  if(!/^https:\/\//i.test(u)){
    showPhoto(null);
    note('That address has to start with https:// or the browser will refuse '
         + 'to show it.');
    return;
  }
  note('Checking that address ...');
  var probe = new Image();
  URLCHECK = probe;
  probe.onload = function(){
    if(URLCHECK !== probe) return;
    var p = document.getElementById('g-prev');
    p.src = u; p.hidden = false;
    document.getElementById('g-clear').hidden = false;
    note(probe.naturalWidth < 186
      ? 'That photograph loads, but it is only ' + probe.naturalWidth + 'px '
        + 'wide and it will look soft on a phone. Uploading one is sharper.'
      : 'That photograph loads, ' + probe.naturalWidth + 'px wide. The link '
        + 'stays short because only the address travels in it.');
  };
  probe.onerror = function(){
    if(URLCHECK !== probe) return;
    showPhoto(null);
    note('Nothing loaded from that address. Open it in a browser tab: if it '
         + 'does not show a photograph on its own there, it will not show here. '
         + 'A share page from Drive or Dropbox is a page, not a picture.');
  };
  probe.src = u;
}

function loadPhotoFile(file){
  if(!file) return;
  if(!/^image\//.test(file.type)){ note('That file is not an image.'); return; }
  // FileReader, not URL.createObjectURL: the content policy allows data: images
  // but not blob:, so an object URL would be blocked before it ever decoded.
  var fr = new FileReader();
  fr.onerror = function(){ note('That file could not be read.'); };
  fr.onload = function(){
    var img = new Image();
    img.onload = function(){
      var s = Math.min(img.width, img.height);
      var sx = (img.width - s) / 2;
      // Bias the crop UPWARD, because a centred square on a portrait cuts the
      // top of the head off and leaves a chest. Same rule the registry uses.
      var sy = Math.min(Math.max(0, (img.height - s) / 4), img.height - s);
      var c = document.createElement('canvas');
      c.width = c.height = PHOTO_PX;
      var g = c.getContext('2d');
      g.imageSmoothingEnabled = true;
      g.imageSmoothingQuality = 'high';
      g.drawImage(img, sx, sy, s, s, 0, 0, PHOTO_PX, PHOTO_PX);
      var d = c.toDataURL('image/webp', PHOTO_Q);
      // Safari before 14 cannot encode WebP from a canvas and silently hands
      // back a PNG, which is far larger. Check what actually came out, and drop
      // to JPEG rather than carry a 40KB PNG inside the link.
      if(d.slice(0, 15) !== 'data:image/webp') d = c.toDataURL('image/jpeg', PHOTO_Q);
      document.getElementById('g-photo').value = '';
      note('Cropped to a square and shrunk to ' + PHOTO_PX + 'px, in this browser. '
           + 'It travels inside the link.');
      showPhoto(d);
    };
    img.onerror = function(){
      note('That image could not be opened. An iPhone HEIC photo often cannot be; '
           + 'open it and export a JPEG, then try again.');
    };
    img.src = fr.result;
  };
  fr.readAsDataURL(file);
}
function build(){
  var pick=v('g-pick'), base=location.origin+'/', frag=[];
  if(pick && pick!=='__none__'){ base=location.origin+'/'+pick; }
  else if(pick===''){
    var a={};
    ['name','title','phone','email','site','tag'].forEach(function(k){
      var val=v('g-'+k); if(val) a[k==='tag'?'tagline':k]=val;
    });
    var photo = PHOTO || v('g-photo');
    if(photo) a.photo = photo;
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
  reportLength(url);
  return url;
}
function reportLength(url){
  var el = document.getElementById('len'), n = url.length;
  if(n < 400){
    el.className = 'len';
    el.innerHTML = '<b>' + n + '</b> characters. Short enough to put anywhere.';
  } else if(PHOTO){
    el.className = 'len';
    el.innerHTML = '<b>' + n.toLocaleString() + '</b> characters, because the '
      + 'photograph is inside the link. That sends fine by email, text or '
      + 'WhatsApp, but it looks unwieldy written out. The photograph itself is '
      + 'the same either way. For a short link, ask to be added permanently and '
      + 'you get an address like /your-name instead.';
  } else {
    el.className = 'len';
    el.innerHTML = '<b>' + n.toLocaleString() + '</b> characters.';
  }
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
document.getElementById('g-file').addEventListener('change',function(){
  loadPhotoFile(this.files && this.files[0]);
  this.value='';   // so re-picking the SAME file fires change again
});
document.getElementById('g-clear').addEventListener('click',function(){
  document.getElementById('g-photo').value = '';
  if(URLCHECK){ URLCHECK.onload = URLCHECK.onerror = null; URLCHECK = null; }
  note('Or paste the address of one already online, below. Leave both empty and '
       + 'the close simply has no photograph.');
  showPhoto(null);
});
document.getElementById('g-photo').addEventListener('input',function(){
  if(this.value.trim() && PHOTO) showPhoto(null);   // a pasted address wins
  checkPhotoUrl(this.value);
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