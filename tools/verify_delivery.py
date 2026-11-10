"""Registra regressão e ambiente com saídas originais, sem acessar dados pessoais."""
import json
from pathlib import Path
import platform
import subprocess
import sys
import argparse

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    target=args.output if args.output.is_absolute() else ROOT/args.output
    target.mkdir(parents=True,exist_ok=True)
    records=[]
    for name,arguments in [('unittest',['-B','-m','unittest','-q']),
                           ('examples',['-B','tools/check_study_examples.py'])]:
        result=subprocess.run([sys.executable,'-X','utf8',*arguments],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
        (target/(name+'.log')).write_text('STDOUT\n'+result.stdout+'\nSTDERR\n'+result.stderr,encoding='utf-8')
        records.append(dict(command=[sys.executable,'-X','utf8',*arguments],returncode=result.returncode,log=name+'.log'))
        print(name,result.returncode,result.stdout.strip(),result.stderr.strip(),flush=True)
    from inference import scientific_stats
    scientific_stats()
    import scipy,numpy
    report=dict(python=platform.python_version(),scipy=scipy.__version__,numpy=numpy.__version__,checks=records,
                native16_fixtures_added=0,native16_validation='pending: reference executable absent here')
    (target/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return int(any(r['returncode'] for r in records))


if __name__=='__main__':raise SystemExit(main())
