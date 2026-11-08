# -*- coding: utf-8 -*-
"""Nosrati ++ v2 - Persian-to-C++ compiler prototype"""
import argparse, re, subprocess, sys
from pathlib import Path

# نمایش درست پیام‌های فارسی در CMD ویندوز
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, OSError):
    pass
D = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩','01234567890123456789')
ID = r"[آ-یءۀ‌_][آ-یءۀ‌_0-9۰-۹٠-٩]*"
T = {'عدد':'long long','اعشاری':'double','رشته':'string','درست‌نما':'bool','منطقی':'bool'}
def cn(s): return '_n_' + '_'.join(f'{ord(c):x}' for c in s)
def ex(s):
    s=s.translate(D).replace('×','*').replace('÷','/').replace('≠','!=').replace('≤','<=').replace('≥','>=')
    s=re.sub(r'\bو\b','&&',s); s=re.sub(r'\bیا\b','||',s); s=re.sub(r'\bنه\b','!',s)
    s=re.sub(r'\bدرست\b','true',s); s=re.sub(r'\bنادرست\b','false',s)
    p=re.split(r'("(?:\\.|[^"\\])*")',s)
    for i in range(0,len(p),2): p[i]=re.sub(ID,lambda m:cn(m.group()),p[i])
    return ''.join(p)
def params(raw,n):
    out=[]
    if not raw.strip(): return ''
    for part in raw.split('،'):
        m=re.fullmatch(r'\s*(عدد|اعشاری|رشته|درست‌نما|منطقی)\s+('+ID+r')\s*',part)
        if not m: raise ValueError(f'خط {n}: پارامتر را مانند «عدد مقدار» بنویسید.')
        out.append(T[m.group(1)]+' '+cn(m.group(2)))
    return ', '.join(out)
def translate(src):
    pre=['#include <iostream>','#include <string>','#include <vector>','using namespace std;','']
    funcs=[]; classes=[]; main=[]; out=main; depth=1; stack=[]; mode='main'
    declared = {'main': set()}
    def emit(s): out.append('    '*depth+s)
    for n,raw in enumerate(src.splitlines(),1):
        s=raw.strip()
        if not s or s.startswith('#') or s.startswith('//'): continue
        s=s.translate(D)
        m=re.fullmatch(r'تابع\s+('+ID+r')\s*\((.*)\)\s*(?:->\s*(عدد|اعشاری|رشته|درست‌نما))?\s*آنگاه',s)
        if m:
            if mode!='main': raise ValueError(f'خط {n}: تعریف تابع تو در تو مجاز نیست.')
            name,ps,rt=m.groups(); funcs.append(f'{T.get(rt,"long long")} {cn(name)}({params(ps,n)}) {{')
            declared['function'] = set(re.findall(r'(?:عدد|اعشاری|رشته|درست‌نما|منطقی)\\s+(' + ID + r')', ps))
            out=funcs; depth=1; stack.append(('function',out)); mode='function'; continue
        m=re.fullmatch(r'کلاس\s+('+ID+r')\s*آنگاه',s)
        if m:
            if mode!='main': raise ValueError(f'خط {n}: کلاس تو در تو مجاز نیست.')
            classes.append(f'struct {cn(m.group(1))} {{'); out=classes; depth=1; stack.append(('class',out)); mode='class'; continue
        if s=='پایان':
            if not stack: raise ValueError(f'خط {n}: پایان بدون بلوک باز.')
            kind,_=stack.pop(); depth-=1; out.append('    '*depth+('};' if kind=='class' else '}'))
            if kind in ('class','function'):
                mode='main'; out=main
                if kind == 'function': declared.pop('function', None)
            continue
        if s=='وگرنه':
            if not stack or stack[-1][0]!='if': raise ValueError(f'خط {n}: وگرنه بدون اگر.')
            depth-=1; emit('} else {'); depth+=1; stack[-1]=('else',out); continue
        m=re.fullmatch(r'اگر\s+(.+?)\s+آنگاه',s)
        if m: emit(f'if ({ex(m.group(1))}) {{'); stack.append(('if',out)); depth+=1; continue
        m=re.fullmatch(r'تاوقتی\s+(.+?)\s+آنگاه',s)
        if m: emit(f'while ({ex(m.group(1))}) {{'); stack.append(('while',out)); depth+=1; continue
        m=re.fullmatch(r'برای\s+('+ID+r')\s+از\s+(.+?)\s+تا\s+(.+?)\s+آنگاه',s)
        if m:
            v,a,b=m.groups(); emit(f'for (long long {cn(v)}={ex(a)}; {cn(v)}<={ex(b)}; ++{cn(v)}) {{'); stack.append(('for',out)); depth+=1; continue
        m=re.fullmatch(r'آرایه\s*<\s*(عدد|اعشاری|رشته|درست‌نما)\s*>\s*('+ID+r')\s*=\s*\[(.*)\]',s)
        if m:
            typ,name,vals=m.groups()
            vals=', '.join(ex(x.strip()) for x in vals.split('،') if x.strip())
            scope = declared.setdefault(mode, set())
            if name in scope:
                emit(f'{cn(name)} = vector<{T[typ]}>{{{vals}}};')
            else:
                emit(f'vector<{T[typ]}> {cn(name)} = {{{vals}}};')
                scope.add(name)
            continue
        m=re.fullmatch(r'(عدد|اعشاری|رشته|درست‌نما|منطقی)\s+('+ID+r')\s*=\s*(.+)',s)
        if m:
            typ,name,val=m.groups()
            scope = declared.setdefault(mode, set())
            if name in scope:
                # تعریف تکراری در همان بدنه به‌عنوان انتساب مجدد تفسیر می‌شود.
                emit(f'{cn(name)} = {ex(val)};')
            else:
                emit(f'{T[typ]} {cn(name)} = {ex(val)};')
                scope.add(name)
            continue
        m=re.fullmatch(r'چاپ\s*\((.*)\)',s)
        if m: emit(f'cout << {ex(m.group(1))} << endl;'); continue
        m=re.fullmatch(r'ورودی\s*\(\s*('+ID+r')\s*\)',s)
        if m: emit(f'cin >> {cn(m.group(1))};'); continue
        m=re.fullmatch(r'بازگردان\s+(.+)',s)
        if m: emit(f'return {ex(m.group(1))};'); continue
        m=re.fullmatch(r'('+ID+r')\s*=\s*(.+)',s)
        if m: emit(f'{cn(m.group(1))} = {ex(m.group(2))};'); continue
        m=re.fullmatch(r'('+ID+r')\s*\((.*)\)',s)
        if m:
            name,args=m.groups(); emit(f'{cn(name)}('+', '.join(ex(a.strip()) for a in args.split('،') if a.strip())+');'); continue
        raise ValueError(f'خط {n}: دستور ناشناخته: {raw.strip()}')
    if stack: raise ValueError('خطا: یک یا چند بلوک با «پایان» بسته نشده‌اند.')
    return '\n'.join(pre+classes+funcs+['int main() {']+main+['    return 0;','}',''])
def main():
    p=argparse.ArgumentParser(description='کامپایلر Nosrati ++'); p.add_argument('source'); p.add_argument('-o','--output'); p.add_argument('--keep-cpp',action='store_true'); a=p.parse_args()
    src=Path(a.source)
    if not src.exists(): print('فایل پیدا نشد:',src); return 2
    cpp=src.with_suffix('.generated.cpp'); exe=Path(a.output) if a.output else src.with_suffix('.exe')
    try: cpp.write_text(translate(src.read_text(encoding='utf-8-sig')),encoding='utf-8')
    except Exception as e:
        print(f'خطای زبان در فایل {src.name}: {e}')
        return 1
    try: r=subprocess.run(['g++','-std=c++17',str(cpp),'-o',str(exe)],capture_output=True,text=True)
    except FileNotFoundError: print('g++ پیدا نشد؛ MinGW-w64 یا MSYS2 را نصب و به PATH اضافه کنید.'); return 2
    if r.returncode: print(r.stderr); return r.returncode
    if not a.keep_cpp: cpp.unlink(missing_ok=True)
    print('کامپایل موفق:',exe); return 0
if __name__=='__main__': raise SystemExit(main())
