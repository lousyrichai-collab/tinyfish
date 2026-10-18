import { chromium } from 'playwright';
import { pathToFileURL } from 'url';
const [,, mode, outDir, ...times] = process.argv;
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
await p.goto(pathToFileURL(process.cwd() + '/reel.html').href);
await p.evaluate(async () => {
  await Promise.all([
    document.fonts.load('800 100px "Baloo 2"', 'दोस्तों ABC'), document.fonts.load('500 100px "Baloo 2"', 'दोस्तों'),
    document.fonts.load('800 100px "Mukta"', 'फोटो ABC'), document.fonts.load('600 100px "Mukta"', 'फोटो ABC'),
  ]);
  await document.fonts.ready;
});
const shot = async (t, path) => { await p.evaluate(t => window.render(t), t); await p.screenshot({ path, type: 'jpeg', quality: 92 }); };
if (mode === 'stills') for (const t of times) await shot(+t, `${outDir}/still-${(+t).toFixed(2)}.jpg`);
else { const fps = 30, n = Math.round(21 * fps); for (let i = 0; i < n; i++) await shot(i / fps, `${outDir}/f${String(i).padStart(4, '0')}.jpg`); }
console.log(await p.evaluate(() => [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.weight).join(', ')));
await b.close();
