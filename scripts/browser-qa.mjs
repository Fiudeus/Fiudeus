// Optional development dependency: Playwright with Chromium (or PROFILE_BROWSER).
// A local-only server is started and closed by this command.
import fs from 'node:fs/promises';
import path from 'node:path';
import http from 'node:http';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.PROFILE_NODE_MODULES?path.join(process.env.PROFILE_NODE_MODULES,'playwright'):'playwright');
const root=process.cwd(),out=path.join(root,'previews/qa');
await fs.mkdir(out,{recursive:true});
const mime={'.svg':'image/svg+xml','.html':'text/html','.png':'image/png','.md':'text/plain'};
const server=http.createServer(async(req,res)=>{
  try{
    const filename=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));
    if(!filename.startsWith(root+path.sep)){res.writeHead(403).end();return;}
    const data=await fs.readFile(filename);res.writeHead(200,{'content-type':mime[path.extname(filename)]||'text/plain'}).end(data);
  }catch{res.writeHead(404).end();}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const base=`http://127.0.0.1:${server.address().port}`;
let browser;
const report={checks:[],browser:null};
try{
  browser=await chromium.launch({headless:true,...(process.env.PROFILE_BROWSER?{executablePath:process.env.PROFILE_BROWSER}:{})});
  report.browser=browser.version();
  const readme=await fs.readFile(path.join(root,'README.md'),'utf8');
  const pictures=readme.match(/<picture>[\s\S]*?<\/picture>/g).join('\n');
  for(const motion of ['reduce','no-preference'])for(const theme of ['dark','light'])for(const width of [900,375]){
    const context=await browser.newContext({viewport:{width,height:800},colorScheme:theme,reducedMotion:motion,deviceScaleFactor:1});
    const page=await context.newPage();
    await page.setContent(`<!doctype html><base href="${base}/"><style>body{margin:0;padding:16px;background:${theme==='dark'?'#0d1117':'white'}}main{max-width:840px;margin:auto}img{display:block;width:100%;height:auto;margin-bottom:16px}</style><main>${pictures}</main>`);
    await page.waitForFunction(()=>[...document.images].every(img=>img.complete&&img.naturalWidth>0));
    const sources=await page.locator('img').evaluateAll(nodes=>nodes.map(img=>img.currentSrc));
    for(const [index,source] of sources.entries())assert.ok(source.endsWith(`${width<600?'-compact':''}${index===0&&motion==='reduce'?'-still':''}-${theme}.svg`),source);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),width,'No horizontal overflow');
    assert.equal(await page.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches),motion==='reduce');
    // Exercise the real <img> embedding too: browser media emulation can behave
    // differently in SVG image documents than in directly opened SVG pages.
    if(motion==='reduce'){
      const home=page.locator('img').first();
      const before=await home.screenshot({animations:'allow'});
      await page.waitForTimeout(900);
      const after=await home.screenshot({animations:'allow'});
      assert.equal(Buffer.compare(before,after),0,'README image must remain still with reduced motion');
    }
    await page.screenshot({path:path.join(out,`readme-${theme}-${width}${motion==='reduce'?'':'-animated'}.png`),fullPage:true});
    report.checks.push(`README picture sources / ${theme} / ${width}px / motion ${motion} / no horizontal overflow${motion==='reduce'?' / pixel-identical still frames':''}`);
    await context.close();
  }
  const motionContext=await browser.newContext({viewport:{width:1000,height:900},reducedMotion:'no-preference'});
  const page=await motionContext.newPage();
  await page.goto(base+'/profile/session-dark.svg');
  await page.evaluate(()=>{window.qaAnimations=document.getAnimations();for(const a of window.qaAnimations)a.pause();});
  const widths=[];
  for(const ms of [0,900,2500]){
    await page.evaluate(ms=>{for(const a of window.qaAnimations)a.currentTime=ms;},ms);
    widths.push(await page.locator('rect.welcome-input').evaluate(el=>parseFloat(getComputedStyle(el).width)));
    await page.screenshot({path:path.join(out,`typing-${ms}.png`)});
  }
  assert.equal(widths[0],0);assert.ok(widths[1]>0&&widths[1]<widths[2]);
  assert.equal(await page.locator('.welcome-output').evaluate(el=>getComputedStyle(el).opacity),'1');
  report.checks.push('Command reveal has distinct 0 / 900 / 2500ms frames; complete final output');
  for(const compact of [false,true])for(const theme of ['dark','light']){
    await page.goto(`${base}/profile/session${compact?'-compact':''}-still-${theme}.svg`);
    assert.equal(await page.evaluate(()=>document.getAnimations().length),0,'Still assets must be still even without a media preference');
    assert.equal(await page.locator('.welcome-output').evaluate(el=>getComputedStyle(el).opacity),'1');
  }
  report.checks.push('All four still home variants show complete output without any animation, even with no reduced-motion preference');
  await motionContext.close();
  const reduced=await browser.newContext({reducedMotion:'reduce'}),rp=await reduced.newPage();
  for(const compact of [false,true])for(const theme of ['dark','light'])for(const scene of ['session','fastfetch','toolbox','tree','badges','panels']){
    const prefix=['tree','badges','panels'].includes(scene)?'previews/toolbox':'profile';
    await rp.goto(`${base}/${prefix}/${scene}${compact?'-compact':''}-${theme}.svg`);
    const result=await rp.evaluate(()=>{
      const svg=document.documentElement,w=svg.viewBox.baseVal.width,h=svg.viewBox.baseVal.height;
      const bad=[...document.querySelectorAll('[data-row]')].filter(el=>{const b=el.getBBox();return b.x<-.6||b.y<-.6||b.x+b.width>w+.6||b.y+b.height>h+.6;}).map(el=>el.dataset.text);
      return{animations:document.getAnimations().length,bad,output:document.querySelector('.welcome-output')?getComputedStyle(document.querySelector('.welcome-output')).opacity:null};
    });
    assert.equal(result.animations,0,`${scene}: reduced motion`);assert.deepEqual(result.bad,[],`${scene}: glyph bounds`);
    if(scene==='session')assert.equal(result.output,'1','Static output stays visible');
  }
  for(const compact of [false,true])for(const theme of ['dark','light']){
    await rp.goto(`${base}/profile/session${compact?'-compact':''}-still-${theme}.svg`);
    assert.equal(await rp.evaluate(()=>document.getAnimations().length),0);
    assert.equal(await rp.locator('.welcome-output').evaluate(el=>getComputedStyle(el).opacity),'1');
  }
  await reduced.close();report.checks.push('All 28 SVGs: zero animations with reduced motion; complete output; scene glyph ink stays in bounds');
  const previewContext=await browser.newContext({viewport:{width:900,height:800},reducedMotion:'reduce'});
  const previewPage=await previewContext.newPage();
  await previewPage.goto(base+'/previews/index.html');
  for(const style of ['tree','badges','panels']){
    await previewPage.locator('#toolbox').selectOption(style);
    await previewPage.waitForFunction(()=>[...document.images].every(img=>img.complete&&img.naturalWidth>0));
    assert.ok((await previewPage.locator('img[data-scene=toolbox]').getAttribute('src')).endsWith(`/`+style+'-dark.svg'));
  }
  await previewPage.goto(base+'/previews/toolbox-variants.html?theme=light&layout=compact');
  await previewPage.waitForFunction(()=>[...document.images].every(img=>img.complete&&img.naturalWidth>0));
  const choices=await previewPage.locator('img').evaluateAll(nodes=>nodes.map(img=>img.currentSrc));
  assert.equal(choices.length,3);assert.ok(choices.every(src=>src.endsWith('-compact-light.svg')));
  await previewContext.close();report.checks.push('Live preview switches all toolbox styles; comparison page loads all three compact/light choices');
  report.status='passed';
  await fs.writeFile(path.join(out,'report.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report,null,2));
}finally{if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));}
