// Optional development dependencies: Playwright with Chromium and sharp.
// A local-only server is started and closed by this command.
import fs from 'node:fs/promises';
import path from 'node:path';
import http from 'node:http';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {chromium}=require(process.env.PROFILE_NODE_MODULES?path.join(process.env.PROFILE_NODE_MODULES,'playwright'):'playwright');
const sharp=require(process.env.PROFILE_NODE_MODULES?path.join(process.env.PROFILE_NODE_MODULES,'sharp'):'sharp');
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

function assertRasterFrames(data,info,geometry,scale,label){
  const paper=geometry.paper.match(/[0-9a-f]{2}/gi).map(value=>parseInt(value,16));
  const ink=(x,y)=>{
    const i=(y*info.width+x)*info.channels;
    return Math.max(...paper.map((channel,k)=>Math.abs(data[i+k]-channel)))>20;
  };
  for(const frame of geometry.frames){
    const x1=Math.ceil((frame.left+9)*scale),x2=Math.floor((frame.right-9)*scale);
    const cy=Math.floor(frame.bottom*scale);
    let bottom=0;
    for(let y=Math.max(0,cy-2);y<=Math.min(info.height-1,cy+2);y++){
      let hits=0;for(let x=x1;x<x2;x++)if(ink(x,y))hits++;
      bottom=Math.max(bottom,hits/(x2-x1));
    }
    assert.ok(bottom>.95,`${label}: bottom border on terminal row ${frame.row} disappeared (${bottom})`);
    const y1=Math.ceil((frame.top+4)*scale),y2=Math.floor((frame.bottom-4)*scale);
    for(const [side,x] of [['left',frame.left],['right',frame.right]]){
      const cx=Math.floor(x*scale);let coverage=0;
      for(let px=Math.max(0,cx-2);px<=Math.min(info.width-1,cx+2);px++){
        let hits=0;for(let y=y1;y<y2;y++)if(ink(px,y))hits++;
        coverage=Math.max(coverage,hits/(y2-y1));
      }
      assert.ok(coverage>.95,`${label}: ${side} border on terminal row ${frame.row} disappeared (${coverage})`);
    }
  }
}
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
  let rasterCases=0;
  for(const compact of [false,true])for(const theme of ['dark','light'])for(const scene of ['session','fastfetch','toolbox','tree','badges','panels']){
    const prefix=['tree','badges','panels'].includes(scene)?'previews/toolbox':'profile';
    await rp.goto(`${base}/${prefix}/${scene}${compact?'-compact':''}-${theme}.svg`);
    const result=await rp.evaluate(()=>{
      const svg=document.documentElement,w=svg.viewBox.baseVal.width,h=svg.viewBox.baseVal.height;
      const bad=[...document.querySelectorAll('[data-row]')].filter(el=>{const b=el.getBBox();return b.x<-.6||b.y<-.6||b.x+b.width>w+.6||b.y+b.height>h+.6;}).map(el=>el.dataset.text);
      const rows=[...document.querySelectorAll('[data-row]')];
      const frames=rows.filter(el=>/^└─+┘$/u.test(el.dataset.text)).map(el=>{
        const b=el.getBBox();
        const header=rows.filter(row=>row.dataset.col===el.dataset.col&&+row.dataset.row<+el.dataset.row&&row.dataset.text.startsWith('┌'))
          .sort((a,b)=>+b.dataset.row-+a.dataset.row)[0];
        return {left:b.x,right:b.x+b.width,bottom:b.y+b.height,top:header.querySelector('path').getBBox().y,row:el.dataset.row};
      });
      const paper=svg.querySelector(':scope > rect[fill]:not([fill="none"])').getAttribute('fill');
      return{width:w,frames,paper,animations:document.getAnimations().length,bad,output:document.querySelector('.welcome-output')?getComputedStyle(document.querySelector('.welcome-output')).opacity:null};
    });
    assert.equal(result.animations,0,`${scene}: reduced motion`);assert.deepEqual(result.bad,[],`${scene}: glyph bounds`);
    if(scene==='session')assert.equal(result.output,'1','Static output stays visible');
    if(scene==='panels'){
      assert.equal(result.frames.length,7,'Every toolbox panel must have a closed frame');
      const source=await fs.readFile(path.join(root,prefix,`${scene}${compact?'-compact':''}-${theme}.svg`));
      for(const width of compact?[540,400,375,343]:[900,840,828,818,768,720]){
        const scale=width/result.width;
        const {data,info}=await sharp(source,{density:72*scale}).ensureAlpha().raw().toBuffer({resolveWithObject:true});
        assertRasterFrames(data,info,result,scale,`${theme}/${compact?'compact':'desktop'}/${width}px`);
        rasterCases++;
      }
    }
  }
  for(const compact of [false,true])for(const theme of ['dark','light']){
    await rp.goto(`${base}/profile/session${compact?'-compact':''}-still-${theme}.svg`);
    assert.equal(await rp.evaluate(()=>document.getAnimations().length),0);
    assert.equal(await rp.locator('.welcome-output').evaluate(el=>getComputedStyle(el).opacity),'1');
  }
  await reduced.close();report.checks.push('All 28 SVGs: zero animations with reduced motion; complete output; scene glyph ink stays in bounds');
  report.checks.push(`Raster regression: all seven panel bottoms and sides stay visible across ${rasterCases} theme/layout/scale cases`);
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
