import { chromium } from 'playwright';
const url = process.argv[2], out = process.argv[3];
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' }).catch(()=>chromium.launch());
const p = await b.newPage({ viewport: { width: 1080, height: 1920 }, locale: 'en-IN' });
await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
await p.waitForTimeout(5000);
for (const t of ['Allow all cookies','Accept','Allow all','Accept all']) { const btn = p.getByRole('button',{name:t}); if (await btn.count()) { await btn.first().click().catch(()=>{}); break; } }
const H = await p.evaluate(()=>document.body.scrollHeight);
for (let y=0,i=0; y<H && i<25; y+=1600,i++){ await p.evaluate(v=>scrollTo(0,v),y); await p.waitForTimeout(1200); await p.screenshot({path:`${out}/shot-${String(i).padStart(2,'0')}.png`}); }
const data = await p.evaluate(()=>({
  title: document.title,
  meta: [...document.querySelectorAll('meta[name=description],meta[property^="og:"]')].map(m=>(m.name||m.getAttribute('property'))+': '+m.content),
  text: document.body.innerText.slice(0,15000),
  imgs: [...new Set([...document.querySelectorAll('img')].map(i=>i.currentSrc||i.src).filter(s=>s.startsWith('http')))].slice(0,80),
  videos: [...new Set([...document.querySelectorAll('video, video source')].map(v=>v.currentSrc||v.src).filter(Boolean))],
  fonts: [...new Set([...document.querySelectorAll('h1,h2,p,button')].map(e=>getComputedStyle(e).fontFamily))],
  colors: [...new Set([...document.querySelectorAll('h1,h2,button,body')].map(e=>getComputedStyle(e).color+' / '+getComputedStyle(e).backgroundColor))].slice(0,15),
}));
console.log(JSON.stringify(data,null,1));
await b.close();
