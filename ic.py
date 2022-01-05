import subprocess
import re
from tempfile import NamedTemporaryFile
from sys import exit

TYPE_RE = r"(\w+|(struct\s\w+))\s??\*?"
FUNCTION_RE = fr"{TYPE_RE}\s\w+\("
TYPEDEF_RE = r'typedef\s'
STRUCT_RE = r'struct\s\w+\s\{'

macros = ['#include <stdio.h>']
fns = []
stmts = []
eval_stmt = ''

last_added_to = None

matching_chars = '([{}])'

type_to_format = {
    'int': '%i',
    'float': '%f',
    'double': '%f',    # I think?
    'str': '%s',
    'other': 'Unprintable type'
}

var_tab = {}

def command_handler(cmd):
    if cmd == 'q':
        exit(0)

def get_line():
    txt = input('> ')
    if not txt:
        return get_line()
    if txt[0] == ':':
        command_handler(txt[1:])
        return get_line()
    while True:
        if sum(map(txt.count, matching_chars[:3])) == sum(map(txt.count, matching_chars[3:])) and (txt[0] == '#' or txt[-1] in ['}', ';']):
            break
        txt += '\n' + input('  ')
    return txt

def infer_type(stmt):
    global var_tab
    default = '?'
    if m := re.match(fr'(?P<type>{TYPE_RE})\s(?P<name>\w+)\s=', stmt):
        var_tab[m.group('name')] = t if (t := m.group('type')) in type_to_format else 'other'
        default = 'none'
    else:
        try:
            default = var_tab[next(iter(sorted(filter(stmt.startswith, var_tab.keys()), key=len)))]
        except StopIteration:
            default = 'none'
    return input(f'Type [{default}]: ') or default

def classify(txt):
    global last_added_to
    global eval_stmt
    txt = txt.strip()
    if txt[0] == '#':
        macros.append(txt)
        last_added_to = macros
    elif any(re.match(x, txt) for x in [FUNCTION_RE, TYPEDEF_RE, STRUCT_RE]):
        fns.append(txt)
        last_added_to = fns
    else:
        stmts.append(txt)
        last_added_to = stmts
        eval_stmt = mk_print_fn(txt, infer_type(txt))

def mk_print_fn(stmt, typeof):
    if typeof not in type_to_format:
        return stmt
    else:
        if stmt[-1] == ';': stmt = stmt[:-1]
        return f'printf("{type_to_format[typeof]}\\n", {stmt});'

def mk_file_and_run():
    global last_added_to
    global eval_stmt
    with NamedTemporaryFile('r+') as f:
        f.write('\n'.join(macros) + '\n')
        f.write('\n\n'.join(fns) + '\n')
        f.write('int main() {\n' + '\n'.join(stmts[:-1]) + '\n' + eval_stmt + '\n}')
        f.seek(0)
        # print('---DEBUG---')
        # print(f'{macros=}')
        # print(f'{fns=}')
        # print(f'{stmts=}')
        # print('---PROG---')
        # print(f.read())
        # print('---RUN---')
        if (error_code := subprocess.run(['tcc', '-run', f.name]).returncode) == 1:
            last_added_to.pop()
        eval_stmt = ''

while True:
    classify(get_line())
    mk_file_and_run()

print(macros, fns, stmts)
