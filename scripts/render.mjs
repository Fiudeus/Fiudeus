// Optional development dependency: sharp. No Node dependency reaches README.
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const sharp=require(process.env.PROFILE_NODE_MODULES?path.join(process.env.PROFILE_NODE_MODULES,'sharp'):'sharp');
const args=process.argv.slice(2);
const root=path.resolve(args[args.indexOf('--root')+1]||'.');
await fs.mkdir(path.join(root,'previews'),{recursive:true});
for(const compact of [false,true])for(const theme of ['dark','light']){
  const width=compact?540:900;let top=16;const layers=[];
  for(const name of ['session','fastfetch','toolbox']){
    const source=await fs.readFile(path.join(root,'profile',`${name}${compact?'-compact':''}-${theme}.svg`));
    const img=sharp(source),meta=await img.metadata();
    layers.push({input:await img.png().toBuffer(),left:16,top});top+=meta.height+16;
  }
  const output=path.join(root,'previews',`profile${compact?'-compact':''}-${theme}.png`);
  await sharp({create:{width:width+32,height:top,channels:4,background:theme==='dark'?'#0d1117':'#fff'}})
    .composite(layers).png().toFile(output);
  console.log(path.relative(root,output));
}
for(const theme of ['dark','light'])for(const style of ['tree','badges','panels']){
  const source=await fs.readFile(path.join(root,'previews/toolbox',`${style}-${theme}.svg`));
  await sharp(source).png().toFile(path.join(root,'previews',`toolbox-${style}-${theme}.png`));
}
