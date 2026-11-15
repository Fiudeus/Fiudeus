"""Three terminal windows with shared chrome and character-cell content."""
from datetime import date, datetime, timezone
import re

from . import art, motion
from .svg import Canvas
from .terminal import Grid, Span, cells
from .toolbox import layout as toolbox_layout


def mix(first, second, amount):
    a = [int(first[i:i+2],16) for i in (1,3,5)]
    b = [int(second[i:i+2],16) for i in (1,3,5)]
    return '#'+''.join(f'{round(x+(y-x)*amount):02x}' for x,y in zip(a,b))

def frame(config, theme, compact, name, rows, static=False):
    options, palette = config['terminal'], config['themes'][theme]
    width = 540 if compact else 900
    cols = options['compact_cols'] if compact else options['desktop_cols']
    size, pitch = options['font_size'], options['line_height']
    x = (width-cols*size*.6)/2
    margin, title_height, content_top = 8, 34, 60
    height = content_top + rows*pitch + 24
    c = Canvas(width, height, f'Fiudeus / {name}', f'{name}: a terminal scene from Fiudeus’s profile.',
               palette, static=static or not options['motion'])
    c.define('window-shadow', '<filter id="window-shadow" x="-3%" y="-5%" width="106%" height="115%">'
             f'<feDropShadow dx="0" dy="3" stdDeviation="3" flood-color="#080812" '
             f'flood-opacity="{.22 if theme=="dark" else .10}"/></filter>')
    c.add(f'<rect x="{margin}" y="{margin}" width="{width-2*margin}" height="{height-2*margin}" '
          f'rx="12" fill="{palette["base"]}" filter="url(#window-shadow)"/>')
    bottom = margin+title_height
    c.add(f'<path d="M20 {margin}H{width-20}Q{width-margin} {margin} {width-margin} 20V{bottom}'
          f'H{margin}V20Q{margin} {margin} 20 {margin}Z" fill="{palette["chrome"]}"/>')
    c.add(f'<path d="M{margin} {bottom}H{width-margin}" stroke="{palette["border"]}" stroke-opacity=".7"/>')
    c.add(f'<rect x="{margin+.5}" y="{margin+.5}" width="{width-2*margin-1}" height="{height-2*margin-1}" '
          f'rx="11.5" fill="none" stroke="{palette["border"]}"/>')
    with c.group('window-controls'):
        for i,color in enumerate(('red','yellow','green')):
            c.add(f'<circle cx="{margin+20+i*20}" cy="{margin+title_height/2}" r="5.5" fill="{palette[color]}"/>')
    title = config['windows'][name]
    caption_width = cells(title)*7.2
    if caption_width>width-192:
        raise ValueError(f'Window title is too long for its header: {title!r}')
    caption = Grid(c, cols=cells(title), rows=1, x=(width-caption_width)/2, y=margin+8,
                   size=12, line_height=18, record=False)
    with c.group('window-title'):
        caption.line(0, Span(title, 'muted'))
    return c, Grid(c, cols=cols, rows=rows, x=x, y=content_top, size=size, line_height=pitch)


def command_spans(command):
    """Foreground colors like shell syntax highlighting; preserve every cell."""
    parts = re.findall(r'''"[^"\n]*"|'[^'\n]*'|\s+|[^\s]+''',command)
    result = []
    for i,part in enumerate(parts):
        color = 'pale' if i==0 else ('red' if part.startswith(('"',"'")) else
                                    'lavender' if part.startswith('-') else
                                    'pink' if '/' in part else 'text')
        result.append(Span(part,color,i==0))
    return result


def colored_list(value, colors=('pale','pink','lavender','red')):
    """ANSI-style tokens separated by the same literal slash output."""
    output = []
    for i,part in enumerate(value.split(' / ')):
        if i:
            output.append(Span(' / ','dim'))
        output.append(Span(part,colors[i%len(colors)]))
    return output


def prompt(grid, config, row, command='', typed=None, delay=0):
    user = config['profile']['user']
    spans = (Span(user, 'lavender', True), Span('@github', 'pink',True), Span(' ~ ', 'red'), Span('$ ', 'pale'))
    prefix = sum(cells(s.text) for s in spans)
    grid.line(row, *spans)
    if typed:
        motion.type_command(grid, prefix, row, command, typed, delay=delay,spans=command_spans(command))
    else:
        grid.write(prefix, row, *command_spans(command))
    return prefix+cells(command)


def session(config, stats, theme, compact, static):
    word = config['profile']['banner']
    if not compact:
        word = (' '*config['terminal']['banner_spacing']).join(word)
    lettering = art.banner(word,config['profile']['banner_font'])
    rows = 8 + len(lettering)
    c, t = frame(config, theme, compact, 'home', rows, static)
    activity = stats.get('last_public_activity')
    stamp = (datetime.fromisoformat(activity.replace('Z','+00:00')).astimezone(timezone.utc)
             .strftime('%Y-%m-%d %H:%M UTC')) if activity else 'unavailable'
    t.line(0,Span(config['profile'].get('activity_label','Last public activity')+': '+stamp,'dim'))
    prompt(t, config, 2, config['commands']['welcome'], typed='welcome-input', delay=.15)
    reveal = motion.appear(c, 'welcome-output', 1.8)
    with c.group(reveal):
        banner_width = max(map(cells,lettering))
        offset = (t.cols-banner_width)//2
        shades = c.palette['banner']
        for row, line in enumerate(lettering):
            spans = []
            for i,ch in enumerate(line):
                color = shades[min(len(shades)-1,i*len(shades)//banner_width)]
                if ch not in ('█',' '):
                    # Dim the FIGlet shadow without introducing a gradient surface.
                    color = mix(color,c.palette['base'],.48)
                spans.append(Span(ch,color))
            t.write(offset,row+4,*spans)
        p = config['profile']
        greeting = p['hello']
        t.write((t.cols-cells(greeting))//2,len(lettering)+5,
                Span(greeting,'pink',True))
    row = rows-1
    with c.group(motion.appear(c, 'home-prompt', 2.1)):
        end = prompt(t, config, row)
        t.write(end, row, Span('▌', 'red'), css=motion.blink(c))
    return c


def number(value):
    return f'{value:,}' if value is not None else 'n/a'


def uptime(created, fetched):
    if not created:
        return 'n/a'
    started = date.fromisoformat(created[:10])
    ended = date.fromisoformat(fetched[:10])
    years = ended.year-started.year
    def anniversary_in(year):
        try:
            return started.replace(year=year)
        except ValueError:  # An account created on February 29.
            return started.replace(year=year,day=28)
    anniversary = anniversary_in(ended.year)
    if anniversary>ended:
        years-=1
        anniversary=anniversary_in(ended.year-1)
    days = (ended-anniversary).days
    return f'{years} years, {days} days' if years else f'{days} days'


def streaks(days):
    if not days:
        return None, None
    run = best = 0
    for day in days:
        run = run+1 if day['count'] else 0
        best = max(best,run)
    past = list(reversed(days))
    if not past[0]['count']:
        past = past[1:]
    current = 0
    for day in past:
        if not day['count']:
            break
        current += 1
    return current,best


def fastfetch(config, stats, theme, compact, static):
    rows = 22 if compact else 14
    c, t = frame(config, theme, compact, 'fastfetch', rows, static)
    prompt(t, config, 0, config['commands']['about'])
    col = 0
    p = config['profile']
    start = 2
    t.write(col, start, Span(p['github'], 'red', True), Span('@github', 'lavender', True))
    t.write(col, start+1, Span('─'*21, 'dim'))
    current, best = streaks(stats.get('days'))
    identity = [
        ('name', p['name']),
        ('role', p['role']),
        ('study', p['study']),
        ('campus', p['campus']),
        ('focus', p['focus']),
    ]
    metrics = [
        ('uptime', uptime(stats.get('created_at'),stats['fetched_at'])),
        ('repos', f'{number(stats.get("repos"))} public / {number(stats.get("stars"))} '+('star' if stats.get('stars')==1 else 'stars')),
        ('commits', f'{number(stats["commits"])} / last 12 months' if stats.get('commits') is not None else 'unavailable'),
        ('prs', f'{number(stats.get("prs"))} / issues {number(stats.get("issues"))} / 12mo'),
        ('followers', f'{number(stats.get("followers"))} / following {number(stats.get("following"))}'),
        ('streak', f'{number(current)} days / best {number(best)} in 12mo'),
        ('activity', f'{number(stats.get("contributions"))} contributions / 12mo'),
    ]
    def field(column, row, label, value, available):
        if cells(f'{label:<11}'+value)>available:
            raise ValueError(f'fastfetch {label} on row {row} exceeds its {available}-cell column')
        spans = [Span(f'{label:<11}', 'pink' if label in ('name','campus') else 'lavender',True)]
        if label in dict(identity):
            spans.extend(colored_list(value) if label=='focus' else (Span(value),))
        else:
            spans.extend(Span(part,'red' if part.isdigit() else 'muted',part.isdigit())
                         for part in re.split(r'(\d+)',value) if part)
        t.write(column,row,*spans)
    for i,(label,value) in enumerate(identity):
        field(0,4+i,label,value,t.cols if compact else 44)
    for i,(label,value) in enumerate(metrics):
        field(0 if compact else 49,(9 if compact else 4)+i,label,value,t.cols if compact else t.cols-49)
    row = 18 if compact else 12
    languages = stats.get('languages') or []
    total = sum(lang['bytes'] for lang in languages)
    if total:
        top = languages[:3]
        tones = ('lavender','red','pale','pink')
        slots = 31 if compact else 42
        t.write(col,row,Span('languages  ','lavender',True))
        repos=stats.get('language_repositories')
        scope=f'{len(repos)} public repos / bytes' if repos is not None else 'public code / bytes'
        t.write(11 if compact else 11+slots+2,row,Span(scope,'dim'))
        # Largest remainder allocation conserves exactly `slots` cells.
        values = [item['bytes'] for item in top] + ([total-sum(v['bytes'] for v in top)] if len(languages)>3 else [])
        raw = [value/total*slots for value in values]
        widths = [int(v) for v in raw]
        for i in sorted(range(len(raw)),key=lambda i:raw[i]-widths[i],reverse=True)[:slots-sum(widths)]:
            widths[i]+=1
        cursor = col+11
        bar_row = row+1 if compact else row
        for i,width in enumerate(widths):
            t.write(cursor,bar_row,Span('█'*width,tones[i]))
            cursor+=width
        legend_lines = [[]]
        legend_cells = 0
        legend_width = t.cols-11
        legend_items = top+([{'name':'other','bytes':values[-1]}] if len(languages)>3 else [])
        for i,item in enumerate(legend_items):
            percent=f'{item["bytes"]/total:.1%}'
            label = f'{item["name"]} {percent}'
            needed = cells(label)+2
            if legend_cells and legend_cells+needed+2>legend_width:
                legend_lines.append([])
                legend_cells=0
            if legend_cells:
                legend_lines[-1].append(Span('  '))
                legend_cells+=2
            legend_lines[-1].extend((Span('● ',tones[i]),Span(item['name']+' ','text'),Span(percent,tones[i])))
            legend_cells+=needed
        for i,line in enumerate(legend_lines):
            t.write(col+11,bar_row+1+i,*line)
    else:
        t.write(col,row,Span('languages  ','lavender',True),Span('n/a','muted'))
    return c


def toolbox(config, stats, theme, compact, static,style=None):
    cols = config['terminal']['compact_cols'] if compact else config['terminal']['desktop_cols']
    rows,entries=toolbox_layout(config,cols,compact,style)
    c,t = frame(config, theme, compact, 'toolbox', rows, static)
    prompt(t, config, 0, config['commands']['toolbox'])
    t.line(2,Span('~/toolbox/', 'red', True))
    for col,row,spans in entries:
        t.write(col,row,*spans)
    return c


def build_scenes(config, stats, compact=False, theme='dark', static=False):
    return {name:builder(config,stats,theme,compact,static) for name,builder in (
        ('session',session),('fastfetch',fastfetch),('toolbox',toolbox))}
