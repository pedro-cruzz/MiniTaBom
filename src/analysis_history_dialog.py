import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from workspace_model import is_stale
from t_analysis_contract import T_METHODS
from regression_contract import REGRESSION_METHOD
from prediction_contract import PREDICTION_METHOD
from anova_contract import ANOVA_METHOD
from diagnostic_contract import NORMALITY_METHOD,STUDY_METHODS
from two_poisson_contract import TWO_POISSON_METHOD
from random_contract import RANDOM_METHOD


class AnalysisHistoryDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title('Histórico de análises')
        self.transient(parent)
        self.geometry('900x590')
        body = ttk.Frame(self, padding=14)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text='Histórico: testes t, diagnósticos, postos, variâncias, ANOVA, regressão, previsões e dados aleatórios.\n'
                  'As demais análises continuam disponíveis no texto da sessão.', wraplength=840).pack(anchor='w', pady=(0, 10))
        self.tree = ttk.Treeview(body, columns=('sheet', 'revision', 'status'), show='tree headings', height=7)
        for key, label in [('#0','Análise'), ('sheet','Planilha'), ('revision','Revisão'), ('status','Origem')]:
            self.tree.heading(key, text=label)
            self.tree.column(key, width=170 if key != 'revision' else 65)
        self.tree.pack(fill='x')
        self.details = tk.Text(body, wrap='none', font=('Courier New', 10), height=12)
        self.details.pack(fill='both', expand=True, pady=10)
        self.tree.bind('<<TreeviewSelect>>', self.show)
        actions = ttk.Frame(body)
        actions.pack(fill='x')
        self.rerun_button=ttk.Button(actions, text='Reexecutar com dados atuais', command=self.rerun)
        self.rerun_button.pack(side='left')
        ttk.Button(actions, text='Exportar resultado JSON…', command=self.export).pack(side='left', padx=8)
        self.use_model=ttk.Button(actions,text='Usar modelo',command=self.activate_model,state='disabled')
        self.use_model.pack(side='left')
        self.graph=ttk.Button(actions,text='Ver gráficos',command=self.view_graph,state='disabled')
        self.graph.pack(side='left',padx=8)
        ttk.Button(actions, text='Fechar', command=self.destroy).pack(side='right')
        self.refresh()
        self.bind('<Escape>', lambda event: self.destroy())
        parent.center_dialog(self)
        self.grab_set()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        sheets = {s['id']: s for s in self.parent.document['worksheets']}
        for result in self.parent.document['analyses']:
            sheet = sheets[result['source']['worksheet_id']]
            mode,source=T_METHODS.get(result['method_id'],(None,None))
            title=({'one':'t de uma amostra','paired':'t pareado','two':'t de duas amostras'}.get(mode,result['method_id'])
                   + (' · '+{'columns':'colunas','summary':'resumo','stacked':'empilhadas'}[source] if source else ''))
            if result['method_id']==REGRESSION_METHOD:title='Regressão linear · '+result['values']['response']
            if result['method_id']==PREDICTION_METHOD:title='Previsão · '+result['values']['response']
            if result['method_id']==ANOVA_METHOD:title='ANOVA · '+('variâncias iguais' if result['parameters']['equal_var'] else 'Welch')
            if result['method_id']==NORMALITY_METHOD:title='Normalidade · '+result['values']['method']
            if result['method_id'] in STUDY_METHODS:title=result['values']['title']
            if result['method_id']==TWO_POISSON_METHOD:title='Duas taxas de Poisson'
            if result['method_id']==RANDOM_METHOD:title='Dados aleatórios · '+result['parameters']['distribution']
            self.tree.insert('', 'end', iid=result['analysis_id'], text=title,
                             values=(sheet['name'], result['source']['revision'],
                                     'Modelo/casos fixos' if result['source'].get('kind')=='fixed_prediction' else
                                     'Valores salvos' if result['source'].get('kind')=='fixed_generation' else
                                     'Resumo informado' if result['source'].get('kind') == 'summary' else
                                     'Dados alterados' if is_stale(result, sheet) else 'Entrada atual'))
        keys = self.tree.get_children()
        if keys:
            self.tree.selection_set(keys[-1]); self.show()

    def selected(self):
        selection = self.tree.selection()
        return next((r for r in self.parent.document['analyses'] if selection and r['analysis_id'] == selection[0]), None)

    def show(self, event=None):
        result = self.selected()
        label='Reexecutar com dados atuais'
        if result and result['method_id']==RANDOM_METHOD:
            label='Reproduzir valores salvos'
        if result and result['method_id']==PREDICTION_METHOD:
            label='Recalcular casos salvos' if result['parameters']['input_kind']=='cases' else 'Recalcular colunas atuais'
        self.rerun_button.configure(text=label)
        state='normal' if result and result['method_id']==REGRESSION_METHOD else 'disabled'
        self.use_model.configure(state=state)
        self.graph.configure(state='normal' if result and result['method_id'] in (REGRESSION_METHOD,ANOVA_METHOD,NORMALITY_METHOD) else 'disabled')
        self.details.configure(state='normal'); self.details.delete('1.0', 'end')
        if result:
            text=result['report']+'\nExecutado em: '+result['created_at']+'\nVersão do MiniTaBom: '+result['versions'].get('application','?')
            if result.get('parent_analysis_id'):
                text+='\nReexecução: o resultado anterior foi preservado.'
            text+='\n\n'+'\n'.join(result['warnings'])
            self.details.insert('1.0', text)
        self.details.configure(state='disabled')

    def activate_model(self):
        result=self.selected()
        if result and self.parent.use_saved_regression(result['analysis_id']):self.destroy()

    def view_graph(self):
        result=self.selected()
        if result:
            functions={ANOVA_METHOD:self.parent.show_saved_anova_graph,NORMALITY_METHOD:self.parent.show_saved_normality_graph,
                       REGRESSION_METHOD:self.parent.show_saved_regression_graph}
            graph=functions[result['method_id']](result['analysis_id']) if result['method_id'] in functions else None
            if graph is not None:self.grab_release()

    def rerun(self):
        result = self.selected()
        if result and self.parent.rerun_saved_analysis(result['analysis_id']):
            self.refresh()
            if result['parameters'].get('show_graph',False):self.grab_release()

    def export(self):
        result = self.selected()
        if result is None:
            return
        path = filedialog.asksaveasfilename(parent=self, defaultextension='.json', filetypes=[('Resultado JSON', '*.json')])
        if path:
            try:
                Path(path).write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
            except OSError as error:
                messagebox.showerror('Falha ao exportar', str(error), parent=self)
