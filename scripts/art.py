"""Standard FIGlet lettering through pyfiglet."""
import pyfiglet

def banner(word, font='ansi_shadow'):
    rows = pyfiglet.figlet_format(word, font=font, width=1000).splitlines()
    while rows and not rows[-1].strip():
        rows.pop()
    return [row.rstrip() for row in rows]
