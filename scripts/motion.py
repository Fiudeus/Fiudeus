"""CSS-only, discrete terminal animations with complete static defaults."""
from .svg import number
from .terminal import Span, cells


def appear(canvas, name, delay):
    canvas.style(name, f'.{name}{{opacity:1;animation:{name} {delay+.1:.2f}s step-end 1}}'
                 f'@keyframes {name}{{0%,{delay/(delay+.1)*100:.3f}%{{opacity:0}}100%{{opacity:1}}}}')
    return name


def blink(canvas):
    canvas.style('cursor', '.cursor{opacity:1;animation:cursor 1.25s step-end infinite}'
                 '@keyframes cursor{0%,48%,100%{opacity:1}49%,99%{opacity:0}}')
    return 'cursor'


def type_command(grid, col, row, text, name, delay=0, duration=1.4, spans=None):
    c = grid.canvas
    w = cells(text) * grid.cell_width
    x, y = grid.x + col*grid.cell_width, grid.y + row*grid.line_height
    total = delay + duration
    pct = delay / total * 100
    c.style(name, f'.{name}{{width:{number(w)}px;animation:{name} {total}s steps({max(1,cells(text))},end) 1}}'
            f'@keyframes {name}{{0%,{pct:.3f}%{{width:0px}}100%{{width:{number(w)}px}}}}')
    c.define(name+'-clip', f'<clipPath id="{name}-clip"><rect class="{name}" x="{number(x)}" y="{number(y)}" '
             f'width="{number(w)}" height="{number(grid.line_height)}"/></clipPath>')
    c.add(f'<g clip-path="url(#{name}-clip)">{grid.fragment(col,row,*(spans or (Span(text),)))}</g>')
    grid.canvas.transcript.append((row,col,text))
    # A typing cursor is visible only during input; the final prompt owns the blink.
    c.style(name+'-caret', f'.{name}-caret{{opacity:0;animation:{name}-caret {total+.15}s step-end 1}}'
            f'@keyframes {name}-caret{{0%,{delay/(total+.15)*100:.3f}%{{opacity:0}}'
            f'{(delay+.01)/(total+.15)*100:.3f}%,{total/(total+.15)*100:.3f}%{{opacity:1}}100%{{opacity:0}}}}'
            f'.{name}-move{{transform:translateX({number(w)}px);animation:{name}-move {total}s steps({max(1,cells(text))},end) 1}}'
            f'@keyframes {name}-move{{0%,{pct:.3f}%{{transform:translateX(0)}}100%{{transform:translateX({number(w)}px)}}}}')
    c.add(f'<g class="{name}-caret"><g class="{name}-move">{grid.fragment(col,row,Span("▌","red"))}</g></g>')
