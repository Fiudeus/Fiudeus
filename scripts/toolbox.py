"""Three character-cell presentations of the same complete, unchanged stack."""
from functools import lru_cache

from .terminal import Span,cells
from .icons import manifest

STYLES=('tree','badges','panels')
TONES=('pale','pink','lavender','red')


@lru_cache(maxsize=1)
def icon_map():
    return manifest()


def icon(name):
    return icon_map().get(name,{}).get('char') or '  '


def packed(items,width,gap=' / '):
    lines=[[]]
    for item in items:
        if cells(item)>width:
            raise ValueError(f'Toolbox item exceeds {width} cells: {item!r}')
        if lines[-1] and cells(gap.join([*lines[-1],item]))>width:
            lines.append([])
        lines[-1].append(item)
    return lines


def text_tokens(items):
    spans=[]
    for i,item in enumerate(items):
        if i:
            spans.append(Span(' / ','dim'))
        spans.append(Span(item,TONES[i%len(TONES)]))
    return tuple(spans)


def layout(config,cols,compact,style=None):
    options=config['toolbox']
    style=style or options['style']
    if style not in STYLES:
        raise ValueError(f'Unknown toolbox style: {style!r}')
    entries=[]
    def put(col,row,*spans):
        entries.append((col,row,spans))
    categories=options['categories']
    row=3
    if style=='tree':
        label_width=max(cells(label) for label,_ in categories)+2
        for i,(label,value) in enumerate(categories):
            last=i==len(categories)-1
            branch='└── ' if last else '├── '
            tone=TONES[i%4]
            items=value.split(' / ')
            if compact:
                put(0,row,Span(branch,'dim'),Span(label,tone,True));row+=1
                for line in packed(items,cols-4):
                    put(0,row,Span('    ' if last else '│   ','dim'),*text_tokens(line));row+=1
            else:
                put(0,row,Span(branch,'dim'),Span(label.ljust(label_width),tone,True),*text_tokens(items));row+=1
    elif style=='badges':
        for i,(label,value) in enumerate(categories):
            put(0,row,Span(label,TONES[i%4],True));row+=1
            col=0
            for j,name in enumerate(value.split(' / ')):
                width=cells(' '+icon(name)+' '+name+' ')
                if col and col+width>cols:
                    row+=1;col=0
                tone=TONES[j%4]
                background='badge_red' if tone in ('red','pink') else 'badge_lavender'
                put(col,row,Span(' '+icon(name)+' ',tone,background=background),
                    Span(name+' ','text',background=background))
                col+=width+2
            row+=2
    else:
        # Actual Unicode box-drawing, like Rich panels. No CSS cards or images.
        panel_width=cols if compact else (cols-4)//2
        pair_row=row
        pair_height=0
        for i,(label,value) in enumerate(categories):
            if not compact and i%2==0 and i:
                pair_row+=pair_height+1;pair_height=0
            px=0 if compact or i%2==0 else panel_width+4
            py=row if compact else pair_row
            inner=panel_width-4
            names=value.split(' / ')
            slot=inner//2
            columns=1 if compact or any(cells(name)+3>slot for name in names) else 2
            body_rows=(len(names)+columns-1)//columns
            height=body_rows+2
            tone=TONES[i%4]
            put(px,py,Span('┌─ ','dim'),Span(label,tone,True),Span(' '+'─'*(panel_width-cells(label)-5)+'┐','dim'))
            for k in range(body_rows):
                put(px,py+k+1,Span('│','dim'));put(px+panel_width-1,py+k+1,Span('│','dim'))
            for k,name in enumerate(names):
                cx=px+2+(k%columns)*(inner//columns)
                put(cx,py+1+k//columns,Span(icon(name)+' ',TONES[k%4]),Span(name))
            put(px,py+height-1,Span('└'+'─'*(panel_width-2)+'┘','dim'))
            if compact:
                row+=height+1
            else:
                pair_height=max(pair_height,height)
        if not compact:
            row=pair_row+pair_height+1
    if style=='tree':
        row+=1
    put(0,row,Span(options['learning_title'],'red',True));row+=1
    for line in packed(options['learning'],cols-2):
        put(2,row,*text_tokens(line));row+=1
    return row,entries
