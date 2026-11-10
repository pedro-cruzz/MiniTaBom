"""Benchmark declarado de sincronização e snapshots; usa só dados sintéticos."""
import argparse
import json
from pathlib import Path
import platform
import sys
import time
import tracemalloc

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from workspace_model import new_document,active_sheet,sync_sheet
from history import WorksheetHistory


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    headers=[f'C{i+1}' for i in range(10)]
    rows=[[str((i*13+j)%1001) for j in range(10)] for i in range(20000)]
    tracemalloc.start();started=time.perf_counter()
    document=new_document(headers,rows);sheet=active_sheet(document)
    history=WorksheetHistory(headers,rows,columns=sheet['columns'])
    initial_seconds=time.perf_counter()-started
    timings=[]
    for value in ('1111','2222','3333','4444','5555'):
        rows[100][0]=value;started=time.perf_counter()
        sync_sheet(sheet,headers,rows);history.record(headers,rows,columns=sheet['columns'])
        timings.append(time.perf_counter()-started)
    current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    report=dict(python=platform.python_version(),rows=20000,columns=10,cells=200000,
                snapshots=len(history.states),initial_seconds=initial_seconds,
                edit_and_snapshot_seconds=timings,traced_bytes=current,peak_traced_bytes=peak,
                limitations=['Tempo inclui overhead de tracemalloc.',
                             'Mede modelo/snapshots, sem renderização da grade ou cálculos estatísticos.',
                             'Não extrapolar para todos os formatos, máquinas ou 50 snapshots.'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
