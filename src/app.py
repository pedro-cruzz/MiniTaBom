import csv
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
from core import read_table, numeric_column
from project import load_document, save_document
from workspace_model import new_document, new_sheet, active_sheet, sync_sheet, is_stale, validate_document
from excel_import import read_excel_workbook
from analysis_service import execute_t, rerun_analysis
from regression_service import execute_regression, archived_model, model_for_prediction
from regression_contract import REGRESSION_METHOD
from prediction_service import execute_prediction
from anova_service import execute_anova
from anova_contract import ANOVA_METHOD
from diagnostic_service import execute_normality,execute_study
from diagnostic_contract import NORMALITY_METHOD
from two_poisson_service import execute_two_poisson
from two_poisson_dialog import TwoPoissonDialog
from two_poisson import TITLE as TWO_POISSON_TITLE
from core import DESCRIPTIVE_STATISTICS, descriptive_report
from worksheet import Worksheet
from history import WorksheetHistory
from graphs import GraphWindow, GroupGraphWindow
from inference_dialog import InferenceDialog, TITLES
from basic_inference import analyze_basic, z_mean, one_proportion, format_basic
from basic_inference_dialog import BasicInferenceDialog, BASIC_TITLES
from extended_inference import analyze_extended, two_proportions, one_variance, two_variances, format_extended, EXTENDED_TITLES
from extended_inference_dialog import ExtendedInferenceDialog
from poisson_inference import one_poisson, analyze_poisson, format_poisson, TITLE as POISSON_TITLE
from poisson_dialog import PoissonDialog
from contingency import categorical_table, matrix_table, format_contingency
from contingency_dialog import ContingencyDialog
from normality import analyze_normality, format_normality
from normality_dialog import NormalityDialog
from anova import prepare_groups, one_way, format_anova_report
from group_dialog import AnovaDialog, GroupPlotDialog
from descriptive_dialog import DescriptiveDialog
from linear_models import correlations, linear_regression, format_correlation, format_regression
from linear_dialog import LinearDialog
from regression_graph import RegressionGraph
from prediction import parse_cases, predict_linear, predict_columns, format_predictions
from prediction_dialog import PredictionDialog
from distributions import distribution_calculation, format_distribution
from distribution_dialog import DistributionDialog
from icons import create_icons
from xy_graphs import prepare_xy, XYGraphWindow
from xy_graph_dialog import XYGraphDialog
from data_operations import sort_rows, stack_columns, unstack_column, format_operation
from data_operation_dialog import DataOperationDialog, DATA_TITLES
from ui_geometry import centered_position, monitor_work_area
from update_dialog import UpdateDialog
from app_resources import resource_path
from study_tests import analyze_study, format_study
from study_test_dialog import StudyTestDialog
from probability_graph import ProbabilityGraph
from column_calculator import calculate_column, append_generated, regression_columns
from study_tests import paired_values
from calculator_dialog import CalculatorDialog
from study_descriptives import frequency_table,format_frequency,sample_percentiles
from frequency_dialog import FrequencyDialog
from frequency_graph import FrequencyGraph
from percentile_dialog import PercentileDialog
from excel_dialog import ExcelDialog
from bivariate_normality import bivariate_normality,format_bivariate

class MiniTaBom(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('MiniTaBom')
        self.geometry('1180x790')
        self.minsize(900, 650)
        self.project_path = None
        self.dirty = False
        self.last_regression = None
        self.last_regression_id = None
        self.headers = ['Coluna 1', 'Coluna 2', 'Coluna 3']
        self.rows = []
        self.history = WorksheetHistory(self.headers, self.rows)
        self.document = new_document(self.headers, self.rows)
        self.sheet_histories = {self.document['active_worksheet_id']: self.history}
        self.status = tk.StringVar(value='Pronto')
        self.dimensions = tk.StringVar()
        self.cell_name = tk.StringVar(value='C1 · linha 1')
        self.cell_value = tk.StringVar()
        self.configure_style()
        self.icons = create_icons(self)
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.create_menus()
        self.create_toolbar()
        self.create_workspace()
        footer = ttk.Frame(self, style='Status.TFrame', padding=(8, 3))
        footer.pack(fill='x', side='bottom')
        ttk.Label(footer, textvariable=self.status, style='Status.TLabel').pack(side='left')
        ttk.Label(footer, textvariable=self.dimensions, style='Status.TLabel').pack(side='right')
        self.refresh()
        self.output.edit_modified(False)
        self.output.bind('<<Modified>>', self.output_changed)
        self.update_title()
        for key, command in [('<Control-o>', self.open_project), ('<Control-s>', self.save_project),
                             ('<Control-n>', self.new_project), ('<F1>', self.show_help),
                             ('<Control-m>', lambda: self.focus_pane('session')),
                             ('<Control-d>', lambda: self.focus_pane('worksheet'))]:
            self.bind(key, lambda event, command=command: self.shortcut(command))

    def configure_style(self):
        style = ttk.Style(self)
        style.theme_use('vista' if 'vista' in style.theme_names() else 'clam')
        self.configure(background='#d6dce4')
        style.configure('.', font=('Segoe UI', 9), background='#f0f1f3', foreground='#202832')
        style.configure('TButton', padding=(7, 3))
        style.configure('Tool.TButton', padding=(6, 2))
        style.configure('TLabel', background='#f0f1f3')
        style.configure('Panel.TFrame', background='white')
        style.configure('Panel.TLabel', background='white', foreground='#536477')
        style.configure('Title.TLabel', background='#dbe4ee', foreground='#273d56', padding=(8, 4), font=('Segoe UI', 9, 'bold'))
        style.configure('Accent.TButton', padding=(10, 4))
        style.configure('TNotebook', tabmargins=(0, 2, 0, 0))
        style.configure('TNotebook.Tab', padding=(12, 4))
        style.configure('Status.TFrame', background='#edf0f4')
        style.configure('Status.TLabel', background='#edf0f4', foreground='#475260', font=('Segoe UI', 9))
        style.configure('Nav.Treeview', rowheight=25, background='white', fieldbackground='white', borderwidth=0)

    def create_menus(self):
        menu = tk.Menu(self)
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label='Novo projeto', accelerator='Ctrl+N', command=self.new_project)
        file_menu.add_command(label='Abrir projeto…', accelerator='Ctrl+O', command=self.open_project)
        file_menu.add_command(label='Salvar projeto', accelerator='Ctrl+S', command=self.save_project)
        file_menu.add_command(label='Salvar projeto como…', command=lambda: self.save_project(save_as=True))
        file_menu.add_separator()
        file_menu.add_command(label='Abrir CSV…', command=self.open_csv)
        file_menu.add_command(label='Abrir Excel…',command=self.open_excel)
        file_menu.add_command(label='Exportar CSV…', command=self.save_csv)
        file_menu.add_command(label='Exportar sessão…', command=self.export)
        file_menu.add_separator()
        file_menu.add_command(label='Sair', command=self.close)
        menu.add_cascade(label='Arquivo', menu=file_menu)
        edit_menu = tk.Menu(menu, tearoff=False)
        edit_menu.add_command(label='Desfazer na planilha', accelerator='Ctrl+Z', command=self.undo_data)
        edit_menu.add_command(label='Refazer na planilha', accelerator='Ctrl+Y', command=self.redo_data)
        edit_menu.add_separator()
        for label, method in [('Copiar da planilha', 'copy'), ('Colar na planilha', 'paste'),
                              ('Limpar células selecionadas', 'clear_selection'), ('Selecionar toda a planilha', 'select_all')]:
            edit_menu.add_command(label=label, command=lambda method=method: self.worksheet_action(method))
        menu.add_cascade(label='Editar', menu=edit_menu)
        data_menu = tk.Menu(menu, tearoff=False)
        data_menu.add_command(label='Nova planilha…', command=self.add_worksheet)
        data_menu.add_command(label='Usar primeira linha como nomes das colunas',command=self.promote_first_row)
        data_menu.add_command(label='Adicionar linha', command=self.add_row)
        data_menu.add_command(label='Adicionar coluna…', command=self.add_column)
        data_menu.add_command(label='Renomear coluna atual…', command=lambda: self.rename_column(self.worksheet.active[1]))
        data_menu.add_separator()
        for operation, title in DATA_TITLES.items():
            data_menu.add_command(label=title + '…', command=lambda operation=operation: self.data_operation_dialog(operation))
        menu.add_cascade(label='Dados', menu=data_menu)
        calc_menu = tk.Menu(menu, tearoff=False)
        calc_menu.add_command(label='Calculadora…', command=self.calculator_dialog)
        calc_menu.add_command(label='Distribuições de probabilidade…', command=self.distribution_dialog)
        menu.add_cascade(label='Calc', menu=calc_menu)
        stat_menu = tk.Menu(menu, tearoff=False)
        basic_menu = tk.Menu(stat_menu, tearoff=False)
        basic_menu.add_command(label='Exibir estatísticas descritivas…', command=self.summary_dialog)
        basic_menu.add_command(label='Percentis e decis…', command=self.percentile_dialog)
        basic_menu.add_separator()
        basic_menu.add_command(label=BASIC_TITLES['z'] + '…', command=lambda: self.basic_test_dialog('z'))
        for mode, title in TITLES.items():
            basic_menu.add_command(label=title + '…', command=lambda mode=mode: self.ttest_dialog(mode))
        basic_menu.add_separator()
        basic_menu.add_command(label=BASIC_TITLES['proportion'] + '…', command=lambda: self.basic_test_dialog('proportion'))
        for mode, title in EXTENDED_TITLES.items():
            basic_menu.add_command(label=title + '…', command=lambda mode=mode: self.extended_test_dialog(mode))
        basic_menu.add_command(label=POISSON_TITLE + '…', command=self.poisson_dialog)
        basic_menu.add_command(label=TWO_POISSON_TITLE+'…',command=self.two_poisson_dialog)
        basic_menu.add_command(label='Correlação…', command=lambda: self.linear_dialog('correlation'))
        basic_menu.add_command(label='Teste de normalidade…', command=self.normality_dialog)
        basic_menu.add_command(label='Igualdade de variâncias…', command=lambda: self.study_dialog('variances'))
        stat_menu.add_cascade(label='Estatísticas básicas', menu=basic_menu)
        rank_menu = tk.Menu(stat_menu, tearoff=False)
        for key, label in [('mannwhitney','Mann–Whitney…'),('wilcoxon','Wilcoxon pareado…'),('kruskal','Kruskal–Wallis…')]:
            rank_menu.add_command(label=label, command=lambda mode=key: self.study_dialog(mode))
        stat_menu.add_cascade(label='Não paramétricos', menu=rank_menu)
        anova_menu = tk.Menu(stat_menu, tearoff=False)
        anova_menu.add_command(label='Um fator…', command=self.anova_dialog)
        stat_menu.add_cascade(label='ANOVA', menu=anova_menu)
        regression_menu = self.regression_menu = tk.Menu(stat_menu, tearoff=False)
        regression_menu.add_command(label='Ajustar modelo linear…', command=lambda: self.linear_dialog('regression'))
        regression_menu.add_command(label='Prever novos casos…', command=self.prediction_dialog, state='disabled')
        stat_menu.add_cascade(label='Regressão', menu=regression_menu)
        tables_menu = tk.Menu(stat_menu, tearoff=False)
        tables_menu.add_command(label='Tabela de frequências…',command=self.frequency_dialog)
        tables_menu.add_command(label='Qui-quadrado de associação…', command=self.contingency_dialog)
        stat_menu.add_cascade(label='Tabelas', menu=tables_menu)
        menu.add_cascade(label='Estat', menu=stat_menu)
        graph_menu = tk.Menu(menu, tearoff=False)
        graph_menu.add_command(label='Gráfico de dispersão…', command=lambda: self.xy_graph_dialog('scatter'))
        graph_menu.add_command(label='Gráfico de séries temporais…', command=lambda: self.xy_graph_dialog('time'))
        graph_menu.add_separator()
        graph_menu.add_command(label='Histograma', command=lambda:self.frequency_dialog('histogram'))
        for key,label in [('bar','Gráfico de barras…'),('pareto','Diagrama de Pareto…'),('pie','Gráfico de setores…')]:
            graph_menu.add_command(label=label,command=lambda kind=key:self.frequency_dialog(kind))
        graph_menu.add_command(label='Boxplot', command=lambda: self.plot('Boxplot'))
        graph_menu.add_command(label='Boxplots comparativos…', command=self.group_plot_dialog)
        menu.add_cascade(label='Gráfico', menu=graph_menu)
        window_menu = tk.Menu(menu, tearoff=False)
        window_menu.add_command(label='Sessão', accelerator='Ctrl+M', command=lambda: self.focus_pane('session'))
        window_menu.add_command(label='Planilha', accelerator='Ctrl+D', command=lambda: self.focus_pane('worksheet'))
        window_menu.add_command(label='Histórico de análises…', command=self.analysis_history_dialog)
        self.show_project = tk.BooleanVar(value=False)
        window_menu.add_checkbutton(label='Gerenciador de projeto', variable=self.show_project, command=self.toggle_project)
        menu.add_cascade(label='Janela', menu=window_menu)
        help_menu = tk.Menu(menu, tearoff=False)
        help_menu.add_command(label='Como usar', accelerator='F1', command=self.show_help)
        help_menu.add_command(label='Cobertura do projeto…', command=self.coverage_dialog)
        help_menu.add_command(label='Verificar atualizações…', command=self.update_dialog)
        help_menu.add_command(label='Sobre o MiniTaBom', command=lambda: messagebox.showinfo('MiniTaBom',
            'Projeto independente para fins educativos e estudo de estatística.\n'
            'Sem vínculo, patrocínio ou endosso da Minitab.\n'
            'Referência pretendida: Minitab 16.\nCompatibilidade ainda não validada.', parent=self))
        menu.add_cascade(label='Ajuda', menu=help_menu)
        self.config(menu=menu)
        self.decorate_menus(menu, top=True)

    def decorate_menus(self, menu, top=False):
        mapping = {
            'Novo projeto': 'new', 'Abrir projeto…': 'open', 'Salvar projeto': 'save',
            'Salvar projeto como…': 'save', 'Abrir CSV…': 'table', 'Exportar CSV…': 'table',
            'Exportar sessão…': 'session', 'Desfazer na planilha': 'undo', 'Refazer na planilha': 'redo',
            'Copiar da planilha': 'copy', 'Colar na planilha': 'paste', 'Limpar células selecionadas': 'clear',
            'Selecionar toda a planilha': 'table', 'Adicionar linha': 'table', 'Adicionar coluna…': 'table',
            'Renomear coluna atual…': 'options', 'Distribuições de probabilidade…': 'distribution',
            'Exibir estatísticas descritivas…': 'summary', 'Correlação…': 'correlation',
            'Estatísticas básicas': 'summary', 'ANOVA': 'anova', 'Um fator…': 'anova',
            'Regressão': 'regression', 'Ajustar modelo linear…': 'regression', 'Prever novos casos…': 'predict',
            'Histograma': 'histogram', 'Boxplot': 'boxplot', 'Boxplots comparativos…': 'groups',
            'Gráfico de dispersão…': 'scatter', 'Gráfico de séries temporais…': 'predict',
            'Tabelas': 'table', 'Qui-quadrado de associação…': 'table',
            'Teste de normalidade…': 'distribution',
            POISSON_TITLE + '…': 'distribution',
            TWO_POISSON_TITLE+'…':'distribution', 'Abrir Excel…':'table',
            'Sessão': 'session', 'Planilha': 'table', 'Gerenciador de projeto': 'project',
            'Como usar': 'help', 'Cobertura do projeto…': 'project', 'Sobre o MiniTaBom': 'help',
            'Verificar atualizações…': 'help', 'Calculadora…':'summary', 'Percentis e decis…':'summary', 'Tabela de frequências…':'table', 'Não paramétricos':'distribution', 'Mann–Whitney…':'distribution', 'Wilcoxon pareado…':'distribution', 'Kruskal–Wallis…':'anova', 'Igualdade de variâncias…':'groups', 'Gráfico de barras…':'histogram', 'Diagrama de Pareto…':'histogram', 'Gráfico de setores…':'histogram',
        }
        mapping.update({title + '…': 'distribution' for title in TITLES.values()})
        mapping.update({title + '…': 'distribution' for title in BASIC_TITLES.values()})
        mapping.update({title + '…': 'distribution' for title in EXTENDED_TITLES.values()})
        mapping.update({title + '…': 'table' for title in DATA_TITLES.values()})
        for index in range((menu.index('end') or 0) + 1):
            kind = menu.type(index)
            if kind not in ('command', 'checkbutton', 'radiobutton', 'cascade'):
                continue
            label = menu.entrycget(index, 'label')
            if not top and label in mapping:
                menu.entryconfigure(index, image=self.icons[mapping[label]], compound='left')
            if kind == 'cascade':
                child = self.nametowidget(menu.entrycget(index, 'menu'))
                self.decorate_menus(child)

    def create_toolbar(self):
        bar = ttk.Frame(self, padding=(5, 3))
        bar.pack(fill='x')
        for label, command, icon in [('Novo', self.new_project, 'new'), ('Abrir…', self.open_project, 'open'), ('Salvar', self.save_project, 'save')]:
            ttk.Button(bar, text=label, image=self.icons[icon], compound='left', style='Tool.TButton', command=command).pack(side='left', padx=1)
        ttk.Separator(bar, orient='vertical').pack(side='left', fill='y', padx=6)
        for label, command, icon in [('Desfazer', self.undo_data, 'undo'), ('Refazer', self.redo_data, 'redo'),
                               ('Descritivas…', self.summary_dialog, 'summary'), ('Histograma', lambda:self.frequency_dialog('histogram'), 'histogram')]:
            ttk.Button(bar, text=label, image=self.icons[icon], compound='left', style='Tool.TButton', command=command).pack(side='left', padx=1)
        ttk.Separator(bar, orient='vertical').pack(side='left', fill='y', padx=6)
        ttk.Label(bar, text='Variável:').pack(side='left', padx=(4, 5))
        self.column = ttk.Combobox(bar, state='readonly', width=14)
        self.column.pack(side='left')
        self.column.bind('<<ComboboxSelected>>', self.choose_column)
        ttk.Checkbutton(bar, text='Projeto', variable=self.show_project, command=self.toggle_project).pack(side='right', padx=6)

    def create_workspace(self):
        workspace = self.workspace = ttk.Panedwindow(self, orient='horizontal')
        workspace.pack(fill='both', expand=True, padx=4, pady=(0, 3))
        sidebar = ttk.Frame(workspace, style='Panel.TFrame', width=185)
        self.sidebar = sidebar
        ttk.Label(sidebar, text='Gerenciador de projeto', style='Title.TLabel').pack(fill='x')
        self.navigator = ttk.Treeview(sidebar, show='tree', selectmode='browse', style='Nav.Treeview', height=7)
        self.navigator.pack(fill='both', expand=True, padx=3, pady=3)
        self.navigator.insert('', 'end', iid='project', text='Sem título', open=True)
        self.navigator.insert('project', 'end', iid='session', text='Sessão')
        self.navigator.insert('project', 'end', iid='worksheet', text='Worksheet 1')
        self.navigator.insert('project', 'end', iid='results', text='Análises', open=True)
        self.result_positions = {}
        self.navigator.bind('<<TreeviewSelect>>', self.navigate)
        self.panes = ttk.Panedwindow(workspace, orient='vertical')
        workspace.add(self.panes, weight=1)
        session = self.session_pane = ttk.Frame(self.panes, style='Panel.TFrame', relief='sunken', borderwidth=1)
        grid = self.grid_pane = ttk.Frame(self.panes, style='Panel.TFrame', relief='sunken', borderwidth=1)
        self.panes.add(session, weight=2)
        self.panes.add(grid, weight=3)
        self.session_title = tk.Label(session, text='Sessão', anchor='w', padx=7, pady=3,
                                      background='#dbe4ee', foreground='#30455c', font=('Segoe UI', 9, 'bold'))
        self.session_title.pack(fill='x')
        text_frame = ttk.Frame(session, style='Panel.TFrame', padding=0)
        text_frame.pack(fill='both', expand=True)
        self.output = tk.Text(text_frame, height=10, wrap='none', font=('Courier New', 10),
                              background='white', foreground='#202020', borderwidth=0,
                              padx=8, pady=5, undo=True)
        self.output.tag_configure('report-title', foreground='#23598a', font=('Courier New', 10, 'bold'), spacing1=8, spacing3=5)
        sy = ttk.Scrollbar(text_frame, orient='vertical', command=self.output.yview)
        sx = ttk.Scrollbar(text_frame, orient='horizontal', command=self.output.xview)
        self.output.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.output.grid(row=0, column=0, sticky='nsew')
        sy.grid(row=0, column=1, sticky='ns')
        sx.grid(row=1, column=0, sticky='ew')
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)
        self.grid_title = tk.Label(grid, text='Worksheet 1', anchor='w', padx=7, pady=3,
                                   background='#2d6495', foreground='white', font=('Segoe UI', 9, 'bold'))
        self.grid_title.pack(fill='x')
        editbar = ttk.Frame(grid, padding=(4, 2))
        editbar.pack(fill='x')
        ttk.Label(editbar, textvariable=self.cell_name, width=17, relief='sunken', padding=(4, 2)).pack(side='left', padx=(0, 6))
        self.sheet_picker = ttk.Combobox(editbar, state='readonly', width=18)
        self.sheet_picker.pack(side='left', padx=(0, 6))
        self.sheet_picker.bind('<<ComboboxSelected>>', self.choose_worksheet)
        ttk.Label(editbar, textvariable=self.cell_value, anchor='w').pack(side='left', fill='x', expand=True)
        ttk.Button(editbar, text='+ Linha', style='Tool.TButton', command=self.add_row).pack(side='left', padx=1)
        ttk.Button(editbar, text='+ Coluna', style='Tool.TButton', command=self.add_column).pack(side='left', padx=1)
        self.worksheet = Worksheet(grid, self.data_changed, self.cell_selected, self.rename_column)
        self.worksheet.pack(fill='both', expand=True)
        self.table = self.worksheet.table
        self.bind('<FocusIn>', self.highlight_pane)

    def toggle_project(self):
        if self.show_project.get():
            self.workspace.insert(0, self.sidebar, weight=0)
            self.workspace.sashpos(0, 205)
        else:
            self.workspace.forget(self.sidebar)

    def highlight_pane(self, event):
        widget = str(event.widget)
        if widget == str(self.session_pane) or widget.startswith(str(self.session_pane) + '.'):
            active = 'session'
        elif widget == str(self.grid_pane) or widget.startswith(str(self.grid_pane) + '.'):
            active = 'worksheet'
        else:
            return
        for name, title in [('session', self.session_title), ('worksheet', self.grid_title)]:
            title.configure(background='#2d6495' if name == active else '#dbe4ee',
                            foreground='white' if name == active else '#30455c')

    def shortcut(self, command):
        # Atalhos da janela principal não devem atuar dentro de diálogos.
        if self.grab_current() is None:
            command()
        return 'break'

    def cell_selected(self, row, column):
        self.cell_name.set(f'C{column + 1} · linha {row + 1}')
        value = self.rows[row][column] if row < len(self.rows) else ''
        self.cell_value.set(value if value else '(célula vazia)')
        self.column.current(column)

    def choose_column(self, event=None):
        selected = self.column.current()
        self.worksheet.commit_edit()
        self.worksheet.select(self.worksheet.active[0], selected)

    def worksheet_action(self, method):
        self.table.focus_set()
        getattr(self.worksheet, method)()

    def data_changed(self):
        self.sync_document()
        self.restore_regression()
        self.history.record(self.headers, self.rows, columns=active_sheet(self.document)['columns'])
        self.mark_dirty()
        self.dimensions.set(f'{len(self.rows)} linhas  |  {len(self.headers)} colunas')
        self.status.set('Dados alterados · execute novamente as análises para atualizar a sessão')

    def undo_data(self):
        self.restore_history('undo')

    def redo_data(self):
        self.restore_history('redo')

    def restore_history(self, direction):
        self.worksheet.commit_edit()
        active = self.worksheet.active
        state = getattr(self.history, direction)()
        if state is None:
            self.status.set('Nenhuma alteração para ' + ('desfazer' if direction == 'undo' else 'refazer'))
            return 'break'
        self.headers, self.rows = state
        columns = self.history.current_columns()
        if columns is not None:
            active_sheet(self.document)['columns'] = columns
        self.refresh()
        self.worksheet.select(*active)
        self.mark_dirty()
        self.status.set('Planilha restaurada · execute novamente as análises para atualizar a sessão')
        return 'break'

    def navigate(self, event=None):
        selected = self.navigator.selection()
        if selected and selected[0] in ('session', 'worksheet'):
            self.focus_pane(selected[0])
        elif selected and selected[0] in self.result_positions:
            self.output.see(self.result_positions[selected[0]])
            self.output.focus_set()

    def index_results(self):
        children = self.navigator.get_children('results')
        if children:
            self.navigator.delete(*children)
        self.result_positions = {}
        self.output.tag_remove('report-title', '1.0', 'end')
        starts = ('DUAS TAXAS DE POISSON', 'TAXA DE POISSON DE UMA AMOSTRA', 'MANN–WHITNEY', 'WILCOXON PAREADO', 'KRUSKAL–WALLIS', 'IGUALDADE DE VARIÂNCIAS', 'TABELA DE FREQUÊNCIAS', 'PERCENTIS DA AMOSTRA', 'CALCULADORA DE COLUNAS', 'Estatísticas descritivas:', 'T DE UMA AMOSTRA', 'T PAREADO', 'T DE WELCH', 'T DE DUAS AMOSTRAS', 'Z DE UMA AMOSTRA', 'TESTE DE UMA PROPORÇÃO', 'TESTE DE DUAS PROPORÇÕES', 'TESTE DE UMA VARIÂNCIA', 'TESTE DE DUAS VARIÂNCIAS', 'QUI-QUADRADO DE ASSOCIAÇÃO', 'TESTE DE NORMALIDADE', 'ANOVA DE UM FATOR', 'CORRELAÇÃO DE', 'REGRESSÃO LINEAR', 'PREVISÃO LINEAR', 'DISTRIBUIÇÃO —', 'OPERAÇÃO DE DADOS —')
        for line, text in enumerate(self.output.get('1.0', 'end-1c').splitlines(), 1):
            if text.startswith(starts):
                key = f'result:{line}'
                self.result_positions[key] = f'{line}.0'
                self.navigator.insert('results', 'end', iid=key, text=text[:55])
                self.output.tag_add('report-title', f'{line}.0', f'{line}.end')

    def focus_pane(self, name):
        self.worksheet.commit_edit()
        if name == 'session':
            self.output.focus_set()
        else:
            self.table.focus_set()

    def update_dialog(self):
        existing = getattr(self, '_updates_window', None)
        if existing is not None and existing.winfo_exists():
            existing.lift()
            return existing
        self._updates_window = UpdateDialog(self)
        return self._updates_window

    def show_help(self):
        messagebox.showinfo('Como usar o MiniTaBom',
            '1. Abra um projeto ou importe um CSV pelo menu Arquivo.\n'
            '2. Edite as células com duplo clique, F2 ou digitando.\n'
            '3. Use Enter e Tab para confirmar e avançar; Esc cancela.\n'
            '4. Cole blocos tabulados com Ctrl+V na planilha.\n'
            '   Arraste ou use Shift+setas para selecionar um intervalo; Ctrl+C copia o bloco.\n'
            '   Delete limpa a seleção; Ctrl+Z desfaz. Ctrl+A seleciona os dados.\n'
            '5. Abra Estat > Estatísticas básicas para analisar os dados.\n'
            '6. Salve o projeto com Ctrl+S para guardar dados e sessão.\n\n'
            'Duplo clique no cabeçalho renomeia uma coluna.\n'
            'Arraste a borda do cabeçalho para ajustar a largura; duplo clique na borda ajusta ao conteúdo.\n'
            'Descritivas: escolha as medidas e, se desejar, colunas em Por variáveis para resumir por grupo.\n'
            'As linhas vazias exibidas no final são espaço para digitação.\n'
            'Editar > Desfazer/Refazer restaura alterações da planilha.\n'
            'Ctrl+Z/Ctrl+Y na planilha acessam o histórico das últimas 50 alterações.\n'
            'A sessão tem seu próprio desfazer de texto.\n'
            'Gráfico > Boxplot mostra quartis, mediana e valores extremos.', parent=self)

    def coverage_dialog(self):
        try:
            registry = json.loads(resource_path('CAPACIDADES.json').read_text(encoding='utf-8'))
            areas = {}
            for requirement in registry['requirements']:
                areas.setdefault(requirement['area'], []).append(requirement)
            inventory = dict(alvo=registry['target'], areas=[dict(id=name, requirements=items) for name, items in areas.items()])
        except (OSError, ValueError) as error:
            messagebox.showerror('Cobertura indisponível', str(error), parent=self)
            return
        dialog = tk.Toplevel(self)
        dialog.title('Cobertura do projeto')
        dialog.transient(self)
        dialog.geometry('860x560')
        dialog.minsize(650, 400)
        ttk.Label(dialog, text='Referência: ' + inventory['alvo'], style='Title.TLabel').pack(fill='x')
        ttk.Label(dialog, text='Registro de capacidades · implementação e validação no 16 são estados distintos.', padding=10).pack(fill='x')
        panes = ttk.Panedwindow(dialog, orient='horizontal')
        panes.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        listing = ttk.Frame(panes)
        panes.add(listing, weight=1)
        tree = ttk.Treeview(listing, columns=('status',), show='tree headings', selectmode='browse')
        tree.heading('#0', text='Área')
        tree.heading('status', text='Estado')
        tree.column('#0', width=230)
        tree.column('status', width=85, stretch=False)
        sy = ttk.Scrollbar(listing, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=sy.set)
        sy.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True)
        detail_frame = ttk.Frame(panes)
        panes.add(detail_frame, weight=1)
        detail = tk.Text(detail_frame, wrap='word', font=('Segoe UI', 10), width=40, borderwidth=0, padx=12, pady=10)
        detail_scroll = ttk.Scrollbar(detail_frame, orient='vertical', command=detail.yview)
        detail.configure(yscrollcommand=detail_scroll.set)
        detail_scroll.pack(side='right', fill='y')
        detail.pack(fill='both', expand=True)
        for index, area in enumerate(inventory['areas']):
            name = area['id'].replace('_', ' ').capitalize()
            tree.insert('', 'end', iid=str(index), text=name,
                        values=('Parcial / pendente',))
        def show_area(event=None):
            if not tree.selection():
                return
            area = inventory['areas'][int(tree.selection()[0])]
            sections = [area['id']]
            for r in area['requirements']:
                state = r['states']
                sections += ['\n' + r['id'] + ' — ' + r['name'],
                             'Implementação: ' + state['implementation'] + '; interface: ' + state['ui'],
                             'Validação16: ' + state['validation16'] + '; persistência: ' + state['persistence']]
                sections += ['• ' + note for note in r['limitations']]
            detail.configure(state='normal')
            detail.delete('1.0', 'end')
            detail.insert('1.0', '\n'.join(sections))
            detail.configure(state='disabled')
        tree.bind('<<TreeviewSelect>>', show_area)
        tree.selection_set('0')
        show_area()
        ttk.Button(dialog, text='Fechar', command=dialog.destroy).pack(anchor='e', padx=10, pady=(0, 10))
        dialog.bind('<Escape>', lambda event: dialog.destroy())
        self.center_dialog(dialog)

    def new_project(self):
        self.worksheet.commit_edit()
        if not self.confirm_replace():
            return
        self.headers, self.rows = ['Coluna 1', 'Coluna 2', 'Coluna 3'], []
        self.document = new_document(self.headers, self.rows)
        self.history = WorksheetHistory(self.headers, self.rows)
        self.sheet_histories = {self.document['active_worksheet_id']: self.history}
        self.project_path = None
        self.output.delete('1.0', 'end')
        self.output.edit_reset()
        self.output.edit_modified(False)
        self.dirty = False
        self.refresh()
        self.update_title()
        self.status.set('Novo projeto · digite na planilha ou importe um CSV')
        self.table.focus_set()

    def mark_dirty(self):
        self.dirty = True
        self.update_title()

    def update_title(self):
        name = Path(self.project_path).name if self.project_path else 'Sem título'
        self.title(f'MiniTaBom — {name}' + (' *' if self.dirty else ''))
        self.navigator.item('project', text=name + (' *' if self.dirty else ''))

    def output_changed(self, event=None):
        if self.output.edit_modified():
            self.mark_dirty()
            self.output.edit_modified(False)
            self.index_results()

    def confirm_replace(self):
        if not self.dirty:
            return True
        answer = messagebox.askyesnocancel('Alterações não salvas',
            'Salvar o projeto antes de continuar?')
        if answer is None:
            return False
        return self.save_project() if answer else True

    def close(self):
        self.worksheet.commit_edit()
        if self.confirm_replace():
            self.destroy()

    def save_project(self, save_as=False):
        self.worksheet.commit_edit()
        path = None if save_as else self.project_path
        if not path:
            path = filedialog.asksaveasfilename(defaultextension='.statlab',
                filetypes=[('Projeto MiniTaBom', '*.statlab')])
        if not path:
            return False
        try:
            self.sync_document()
            save_document(path, self.document)
        except (OSError, ValueError) as error:
            messagebox.showerror('Falha ao salvar projeto', str(error))
            return False
        self.project_path, self.dirty = path, False
        self.output.edit_modified(False)
        self.update_title()
        self.status.set('Projeto salvo · ' + Path(path).name)
        return True

    def open_project(self):
        self.worksheet.commit_edit()
        path = filedialog.askopenfilename(filetypes=[('Projeto MiniTaBom', '*.statlab')])
        if not path:
            return
        try:
            document = load_document(path)
        except (OSError, ValueError) as error:
            messagebox.showerror('Falha ao abrir projeto', str(error))
            return
        if not self.confirm_replace():
            return
        self.document = document
        sheet = active_sheet(document)
        self.headers, self.rows = [c['name'] for c in sheet['columns']], sheet['rows']
        self.history = WorksheetHistory(self.headers, self.rows)
        self.sheet_histories = {sheet['id']: self.history}
        self.output.delete('1.0', 'end')
        self.output.insert('1.0', document['output'])
        self.output.edit_reset()
        self.output.edit_modified(False)
        self.project_path, self.dirty = path, False
        self.refresh()
        self.update_title()
        self.status.set('Projeto aberto · ' + Path(path).name)

    def refresh(self):
        self.sync_document()
        self.restore_regression()
        self.column['values'] = self.headers
        self.worksheet.set_data(self.headers, self.rows)
        self.dimensions.set(f'{len(self.rows)} linhas  |  {len(self.headers)} colunas')
        self.index_results()

    def sync_document(self):
        sheet = active_sheet(self.document)
        sync_sheet(sheet, self.headers, self.rows)
        self.history.attach_columns(self.headers, self.rows, sheet['columns'])
        self.document['output'] = self.output.get('1.0', 'end-1c')
        if hasattr(self, 'sheet_picker'):
            sheets = self.document['worksheets']
            self.sheet_picker['values'] = [s['name'] for s in sheets]
            self.sheet_picker.current(next(i for i, s in enumerate(sheets) if s['id'] == sheet['id']))
            self.grid_title.configure(text=sheet['name'])

    def reset_document(self):
        self.document = new_document(self.headers, self.rows)
        self.sheet_histories = {self.document['active_worksheet_id']: self.history}

    def add_worksheet(self, name=None):
        self.worksheet.commit_edit()
        if name is None:
            name = simpledialog.askstring('Nova planilha', 'Nome da planilha:',
                                          initialvalue=f'Worksheet {len(self.document["worksheets"]) + 1}', parent=self)
        if name is None:
            return False
        name = name.strip()
        if not name or name in [s['name'] for s in self.document['worksheets']] or len(self.document['worksheets']) >= 100:
            messagebox.showerror('Planilha inválida', 'Use nome único e não vazio; limite de 100 planilhas.', parent=self)
            return False
        self.sync_document()
        sheet = new_sheet(name)
        self.document['worksheets'].append(sheet)
        self.switch_worksheet(sheet['id'])
        self.mark_dirty()
        return True

    def choose_worksheet(self, event=None):
        index = self.sheet_picker.current()
        if index >= 0:
            self.switch_worksheet(self.document['worksheets'][index]['id'])

    def switch_worksheet(self, worksheet_id):
        self.worksheet.commit_edit()
        target = next((s for s in self.document['worksheets'] if s['id'] == worksheet_id), None)
        if target is None:
            raise ValueError('Planilha não encontrada.')
        self.sync_document()
        old_id = self.document['active_worksheet_id']
        self.sheet_histories[old_id] = self.history
        self.document['active_worksheet_id'] = worksheet_id
        self.headers, self.rows = [c['name'] for c in target['columns']], target['rows']
        self.history = self.sheet_histories.setdefault(worksheet_id, WorksheetHistory(self.headers, self.rows, columns=target['columns']))
        self.refresh()
        self.worksheet.select(0, 0)
        if old_id != worksheet_id:
            self.mark_dirty()
        self.status.set('Planilha ativa · ' + target['name'])

    def analysis_history_dialog(self):
        from analysis_history_dialog import AnalysisHistoryDialog
        self.worksheet.commit_edit()
        self.sync_document()
        return AnalysisHistoryDialog(self)

    def rerun_saved_analysis(self, analysis_id):
        self.worksheet.commit_edit()
        self.sync_document()
        try:
            if len(self.document['analyses']) >= 10000:
                raise ValueError('Limite de 10000 análises estruturadas por projeto atingido.')
            result = rerun_analysis(self.document, analysis_id)
            storage = self.prepare_analysis_storage(result)
        except (ValueError, ArithmeticError) as error:
            messagebox.showerror('Não foi possível reexecutar', str(error), parent=self.grab_current() or self)
            return False
        self.apply_analysis_storage(result, storage)
        self.document['analyses'].append(result)
        self.append_analysis(result['report'], 'Análise reexecutada · resultado anterior preservado')
        if result['method_id']==REGRESSION_METHOD:
            self.finish_regression(result)
        elif result['method_id']==ANOVA_METHOD and result['parameters']['show_graph']:
            self.show_saved_anova_graph(result['analysis_id'])
        elif result['method_id']==NORMALITY_METHOD and result['parameters']['show_graph']:
            self.show_saved_normality_graph(result['analysis_id'])
        return True

    def prepare_analysis_storage(self, result):
        if result['method_id']==REGRESSION_METHOD:
            if not result['parameters']['store']:return None
            sheet=next(s for s in self.document['worksheets'] if s['id']==result['source']['worksheet_id'])
            return sheet['id'],regression_columns([c['name'] for c in sheet['columns']],sheet['rows'],archived_model(result))
        if not result['parameters'].get('store_differences', False):
            return None
        sheet = next(s for s in self.document['worksheets'] if s['id'] == result['source']['worksheet_id'])
        headers = [c['name'] for c in sheet['columns']]
        indices = [next(i for i, c in enumerate(sheet['columns']) if c['id'] == key)
                   for key in result['source']['column_ids']]
        _, differences, _ = paired_values(headers, sheet['rows'], *indices)
        return sheet['id'], append_generated(headers, sheet['rows'], ['Diferenças'], [differences])

    def apply_analysis_storage(self, result, storage):
        if storage is None:
            return
        sheet_id, generated = storage
        if sheet_id == self.document['active_worksheet_id']:
            self.install_generated(*generated)
        else:
            sheet = next(s for s in self.document['worksheets'] if s['id'] == sheet_id)
            history = self.sheet_histories.setdefault(sheet_id, WorksheetHistory([c['name'] for c in sheet['columns']], sheet['rows'], columns=sheet['columns']))
            sync_sheet(sheet, generated[0], generated[1])
            history.record(generated[0], generated[1], columns=sheet['columns'])
        sheet = next(s for s in self.document['worksheets'] if s['id'] == sheet_id)
        result['storage'] = dict(policy='append_new_column_per_execution', worksheet_id=sheet_id,
                                 column_ids=[c['id'] for c in sheet['columns'] if c['name'] in generated[2]],
                                 names=generated[2])
        result['report'] += ('\nColunas armazenadas: ' if result['method_id']==REGRESSION_METHOD else '\nDiferenças armazenadas em: ') + ', '.join(generated[2]) + '\n'

    def open_csv(self):
        self.worksheet.commit_edit()
        path = filedialog.askopenfilename(filetypes=[('CSV', '*.csv'), ('Todos', '*.*')])
        if path:
            try:
                headers, rows = read_table(Path(path).read_text(encoding='utf-8-sig'))
                if not self.confirm_replace():
                    return
                self.headers, self.rows = headers, rows
                self.history = WorksheetHistory(self.headers, self.rows)
                self.reset_document()
                self.project_path = None
                self.output.delete('1.0', 'end')
                self.output.edit_reset()
                self.refresh()
                self.mark_dirty()
                self.status.set('CSV importado · salve um projeto para preservar dados e sessão')
            except (ValueError, OSError, UnicodeError) as error:
                messagebox.showerror('Falha ao importar', str(error))

    def open_excel(self):
        self.worksheet.commit_edit()
        path=filedialog.askopenfilename(filetypes=[('Excel (.xlsx)','*.xlsx')])
        if not path:return None
        try:return self.import_excel_workbook(read_excel_workbook(path),path)
        except (ValueError,OSError) as error:
            messagebox.showerror('Falha ao abrir Excel',str(error),parent=self);return None

    def import_excel_workbook(self,workbook,path):
        document=new_document()
        document['worksheets']=[new_sheet(item['name'],item['headers'],item['rows']) for item in workbook['worksheets']]
        for sheet,item in zip(document['worksheets'],workbook['worksheets']):sheet['metadata']['excel_import']=item['metadata']
        document['active_worksheet_id']=next(s['id'] for s in document['worksheets'] if s['name']==workbook['active_name'])
        document['metadata']['excel_source']=Path(path).name
        lines=['EXCEL ABERTO — '+Path(path).name,
               f"{len(document['worksheets'])} aba(s). Troque de aba pelo seletor acima da planilha.",
               'Todas as linhas foram mantidas, com colunas A, B, C...; nenhum intervalo precisa ser informado.']
        for item in workbook['worksheets']:
            if item['metadata']['uncached_formulas']:lines.append(item['name']+': '+item['metadata']['note'])
        if any(item['metadata']['excel_state']!='visible' for item in workbook['worksheets']):
            lines.append('Abas ocultas do arquivo também foram incluídas no seletor.')
        document['output']='\n'.join(lines)+'\n'
        validate_document(document)
        if not self.confirm_replace():return False
        self.document=document;sheet=active_sheet(document)
        self.headers,self.rows=[c['name'] for c in sheet['columns']],sheet['rows']
        self.history=WorksheetHistory(self.headers,self.rows,columns=sheet['columns']);self.sheet_histories={sheet['id']:self.history}
        self.output.delete('1.0','end');self.output.insert('1.0',document['output']);self.output.edit_reset();self.output.edit_modified(False)
        self.project_path=None;self.dirty=True;self.refresh();self.update_title()
        self.status.set('Excel aberto · '+Path(path).name+' · todas as abas disponíveis')
        return True

    def promote_first_row(self):
        self.worksheet.commit_edit()
        if not self.rows:return False
        headers=[value.strip() for value in self.rows[0]]
        if any(not name for name in headers) or len(set(headers))!=len(headers):
            messagebox.showerror('Nomes inválidos','A primeira linha deve conter um nome único e não vazio para cada coluna.',parent=self);return False
        self.sync_document();sheet=active_sheet(self.document)
        sheet['columns']=[dict(column,name=name) for column,name in zip(sheet['columns'],headers)]
        self.headers,self.rows=headers,self.rows[1:]
        self.data_changed();self.refresh();self.worksheet.select(0,0)
        self.status.set('Primeira linha usada como nomes · Ctrl+Z desfaz')
        return True

    def import_excel_data(self,headers,rows,meta,path):
        if not self.confirm_replace():return False
        self.headers,self.rows=headers,rows
        self.history=WorksheetHistory(self.headers,self.rows)
        self.reset_document()
        self.project_path=None
        self.output.delete('1.0','end');self.output.edit_reset()
        self.output.insert('end',f"IMPORTAÇÃO EXCEL\n{Path(path).name}; aba {meta['sheet']}; intervalo {meta['range']}.\n"+meta['note']+'\n')
        self.refresh();self.mark_dirty()
        self.status.set('Excel importado · salve um projeto para preservar os dados');return True

    def save_csv(self):
        self.worksheet.commit_edit()
        path = filedialog.asksaveasfilename(defaultextension='.csv')
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8-sig') as stream:
                    writer = csv.writer(stream, delimiter=';')
                    writer.writerow(self.headers)
                    writer.writerows(self.rows)
            except OSError as error:
                messagebox.showerror('Falha ao salvar', str(error))

    def add_row(self):
        self.worksheet.commit_edit()
        self.rows.append(['']*len(self.headers))
        self.data_changed()
        self.worksheet.render()
        self.worksheet.select(len(self.rows) - 1, self.worksheet.active[1])
        self.table.focus_set()

    def add_column(self):
        self.worksheet.commit_edit()
        name = simpledialog.askstring('Coluna', 'Nome da nova coluna:', parent=self)
        if name is None:
            return
        name = name.strip()
        if not name or name in self.headers:
            messagebox.showerror('Coluna inválida', 'Use um nome único e não vazio.')
            return
        self.headers.append(name)
        for row in self.rows:
            row.append('')
        self.refresh()
        self.data_changed()
        self.worksheet.select(0, len(self.headers) - 1)

    def rename_column(self, index):
        self.worksheet.commit_edit()
        name = simpledialog.askstring('Renomear coluna', f'Nome de C{index + 1}:',
                                      initialvalue=self.headers[index], parent=self)
        if name is None:
            return
        name = name.strip()
        if not name or any(i != index and h == name for i, h in enumerate(self.headers)):
            messagebox.showerror('Coluna inválida', 'Use um nome único e não vazio.', parent=self)
            return
        if name != self.headers[index]:
            active = self.worksheet.active
            self.headers[index] = name
            self.refresh()
            self.worksheet.select(*active)
            self.data_changed()

    def data(self):
        self.worksheet.commit_edit()
        return numeric_column(self.rows, self.headers.index(self.column.get()))

    def summary(self):
        self.run_summary([self.headers.index(self.column.get())], DESCRIPTIVE_STATISTICS)

    def run_summary(self, columns, selected, **options):
        self.worksheet.commit_edit()
        try:
            report = descriptive_report(self.headers, self.rows, columns, selected, **options)
            self.output.insert('end', '\n' + report)
            self.index_results()
            self.mark_dirty()
            self.output.see('end')
            self.status.set('Estatísticas descritivas adicionadas à sessão')
            return True
        except ValueError as error:
            messagebox.showerror('Dados inválidos', str(error), parent=self.grab_current() or self)
            return False

    def ttest_dialog(self, mode):
        self.worksheet.commit_edit()
        return InferenceDialog(self, mode)

    def basic_test_dialog(self, mode):
        self.worksheet.commit_edit()
        return BasicInferenceDialog(self, mode)

    def extended_test_dialog(self, mode):
        self.worksheet.commit_edit()
        return ExtendedInferenceDialog(self, mode)

    def poisson_dialog(self):
        self.worksheet.commit_edit()
        return PoissonDialog(self)

    def two_poisson_dialog(self):
        self.worksheet.commit_edit();return TwoPoissonDialog(self)

    def run_two_poisson(self,input_kind='columns',columns=None,**options):
        self.worksheet.commit_edit();self.sync_document()
        try:
            if len(self.document['analyses'])>=10000:raise ValueError('Limite de 10000 análises por projeto atingido.')
            indices=[] if input_kind=='summary' else columns
            if not isinstance(indices,(list,tuple)) or any(type(i) is not int or not 0<=i<len(self.headers) for i in indices):
                raise ValueError('Selecione as colunas de contagens e/ou grupo.')
            sheet=active_sheet(self.document)
            result=execute_two_poisson(sheet,[sheet['columns'][i]['id'] for i in indices],input_kind=input_kind,**options)
        except (ValueError,ArithmeticError) as error:
            messagebox.showerror('Não foi possível comparar as taxas',str(error),parent=self.grab_current() or self);return False
        self.document['analyses'].append(result);self.append_analysis(result['report'],'Duas taxas Poisson adicionadas ao histórico');return True

    def run_poisson(self, source, perform_test=True, **options):
        self.worksheet.commit_edit()
        try:
            if source == 'summary':
                result = one_poisson(**options)
            elif source == 'column':
                result = analyze_poisson(self.headers, self.rows, **options)
            else:
                raise ValueError('Formato de dados inválido.')
            report = format_poisson(result, perform_test)
        except (ValueError, ArithmeticError) as error:
            messagebox.showerror('Não foi possível calcular', str(error), parent=self.grab_current() or self)
            return False
        self.append_analysis(report, POISSON_TITLE + ' adicionada à sessão')
        return True

    def contingency_dialog(self):
        self.worksheet.commit_edit()
        return ContingencyDialog(self)

    def study_dialog(self, mode):
        self.worksheet.commit_edit()
        return StudyTestDialog(self, mode)

    def run_study(self, mode, **options):
        self.worksheet.commit_edit()
        try:
            self.sync_document()
            if len(self.document['analyses'])>=10000:raise ValueError('Limite de 10000 análises por projeto atingido.')
            columns=options.pop('columns',None);response=options.pop('response',None);factor=options.pop('factor',None)
            indices=columns if columns is not None else [response,factor]
            if not isinstance(indices,(list,tuple)) or any(type(i) is not int or not 0<=i<len(self.headers) for i in indices):
                raise ValueError('Selecione as colunas do teste.')
            sheet=active_sheet(self.document)
            result=execute_study(sheet,[sheet['columns'][i]['id'] for i in indices],mode,
                                 input_kind='columns' if columns is not None else 'stacked',**options)
        except (ValueError, ArithmeticError) as error:
            messagebox.showerror('Não foi possível calcular', str(error), parent=self.grab_current() or self)
            return False
        self.document['analyses'].append(result)
        self.append_analysis(result['report'],result['values']['title']+' concluído')
        return True

    def normality_dialog(self):
        self.worksheet.commit_edit()
        return NormalityDialog(self)

    def run_normality(self, column, method='ad', show_graph=False):
        self.worksheet.commit_edit()
        try:
            self.sync_document()
            if len(self.document['analyses'])>=10000:raise ValueError('Limite de 10000 análises por projeto atingido.')
            if type(column) is not int or not 0<=column<len(self.headers):raise ValueError('Selecione uma coluna válida.')
            sheet=active_sheet(self.document)
            result=execute_normality(sheet,[sheet['columns'][column]['id']],method=method,show_graph=show_graph)
        except ValueError as error:
            messagebox.showerror('Não foi possível testar a normalidade', str(error), parent=self.grab_current() or self)
            return False
        self.document['analyses'].append(result)
        self.append_analysis(result['report'], 'Teste de normalidade adicionado à sessão e ao histórico')
        if show_graph:
            self.show_saved_normality_graph(result['analysis_id'])
        return True

    def show_saved_normality_graph(self,analysis_id):
        try:
            result=next((r for r in self.document['analyses'] if r['analysis_id']==analysis_id),None)
            if result is None or result['method_id']!=NORMALITY_METHOD:raise ValueError('Selecione um teste de normalidade no histórico.')
            graph=ProbabilityGraph(self,result['scenes'][0]['sample'],result['values'])
        except ValueError as error:
            messagebox.showerror('Gráfico indisponível',str(error),parent=self.grab_current() or self);return None
        graph.title('Normalidade — resultado salvo em '+result['created_at'])
        self.center_dialog(graph);return graph

    def run_contingency(self, source, show_expected=True, show_residuals=False,
                        show_contributions=False, show_percentages=False, **options):
        self.worksheet.commit_edit()
        try:
            if source not in ('categorical', 'matrix'):
                raise ValueError('Formato de tabela inválido.')
            result = (categorical_table if source == 'categorical' else matrix_table)(self.headers, self.rows, **options)
            report = format_contingency(result, show_expected, show_residuals, show_contributions, show_percentages)
        except ValueError as error:
            messagebox.showerror('Não foi possível analisar a tabela', str(error), parent=self.grab_current() or self)
            return False
        self.append_analysis(report, 'Qui-quadrado de associação adicionado à sessão')
        return True

    def run_extended_test(self, mode, source, perform_test=True, **options):
        self.worksheet.commit_edit()
        functions = {'two_proportions': two_proportions, 'one_variance': one_variance, 'two_variances': two_variances}
        try:
            if mode not in functions:
                raise ValueError('Análise inválida.')
            if source == 'summary':
                result = functions[mode](**options)
            else:
                result = analyze_extended(self.headers, self.rows, mode, source=source, **options)
            report = format_extended(result, perform_test)
        except ValueError as error:
            messagebox.showerror('Não foi possível calcular', str(error), parent=self.grab_current() or self)
            return False
        self.append_analysis(report, EXTENDED_TITLES[mode] + ' adicionado à sessão')
        return True

    def data_operation_dialog(self, operation):
        self.worksheet.commit_edit()
        return DataOperationDialog(self, operation)

    def run_data_operation(self, operation, **options):
        self.worksheet.commit_edit()
        functions = {'sort': sort_rows, 'stack': stack_columns, 'unstack': unstack_column}
        try:
            if operation not in functions:
                raise ValueError('Operação de dados inválida.')
            headers, rows, meta = functions[operation](self.headers, self.rows, **options)
            report = format_operation(meta)
        except ValueError as error:
            messagebox.showerror('Não foi possível transformar os dados', str(error), parent=self.grab_current() or self)
            return False
        if not meta['changed']:
            self.status.set('Os dados já estão na ordem solicitada')
            return True
        active = self.worksheet.active
        old_width = len(self.headers)
        self.headers, self.rows = headers, rows
        self.data_changed()
        self.refresh()
        self.worksheet.select(active[0], active[1] if operation == 'sort' else old_width)
        self.append_analysis(report, DATA_TITLES[operation] + ' concluído · Ctrl+Z desfaz a alteração na planilha')
        return True

    def run_basic_test(self, mode, source, column=None, event=None, perform_test=True, **options):
        self.worksheet.commit_edit()
        try:
            if source == 'column':
                result = analyze_basic(self.headers, self.rows, mode, column, event=event, **options)
            elif source == 'summary' and mode in ('z', 'proportion'):
                result = (z_mean if mode == 'z' else one_proportion)(**options)
            else:
                raise ValueError('Tipo de análise ou entrada inválido.')
            report = format_basic(result, perform_test)
        except ValueError as error:
            messagebox.showerror('Não foi possível calcular', str(error), parent=self.grab_current() or self)
            return False
        self.append_analysis(report, BASIC_TITLES[mode] + ' adicionado à sessão')
        return True

    def linear_dialog(self, mode):
        self.worksheet.commit_edit()
        return LinearDialog(self, mode)

    def append_analysis(self, report, status):
        start = self.output.index('end-1c')
        self.output.insert('end', '\n' + report)
        self.index_results()
        self.mark_dirty()
        self.output.yview(start + '+1line')
        self.status.set(status)

    def run_correlation(self, columns, check_bivariate=False, **options):
        self.worksheet.commit_edit()
        try:
            result = correlations(self.headers, self.rows, columns, **options)
            report = format_correlation(result)
            if check_bivariate:
                report += '\n' + format_bivariate(bivariate_normality(self.headers,self.rows,columns))
        except (ValueError,ArithmeticError) as error:
            messagebox.showerror('Não foi possível calcular a correlação', str(error), parent=self.grab_current() or self)
            return False
        self.append_analysis(report, 'Correlação adicionada à sessão')
        return True

    def run_regression(self, response, predictors, show_graph=True, observations=False, store=False, **options):
        self.worksheet.commit_edit()
        self.configure(cursor='watch')
        self.update_idletasks()
        try:
            self.sync_document()
            if len(self.document['analyses'])>=10000:raise ValueError('Limite de 10000 análises por projeto atingido.')
            sheet=active_sheet(self.document)
            indices=[response,*predictors]
            if any(type(i) is not int or not 0<=i<len(sheet['columns']) for i in indices):
                raise ValueError('Selecione resposta e preditores válidos.')
            result=execute_regression(sheet,[sheet['columns'][i]['id'] for i in indices],
                                      show_graph=show_graph,observations=observations,store=store,**options)
            storage=self.prepare_analysis_storage(result)
        except ValueError as error:
            messagebox.showerror('Não foi possível ajustar a regressão', str(error), parent=self.grab_current() or self)
            return False
        finally:
            self.configure(cursor='')
        self.apply_analysis_storage(result,storage)
        self.document['analyses'].append(result)
        self.append_analysis(result['report'], 'Regressão linear adicionada à sessão')
        self.finish_regression(result)
        return True

    def finish_regression(self,result):
        self.document['metadata'].setdefault('active_regression_by_sheet',{})[result['source']['worksheet_id']]=result['analysis_id']
        self.restore_regression()
        if result['parameters']['show_graph']:
            self.show_saved_regression_graph(result['analysis_id'])

    def restore_regression(self):
        self.clear_regression()
        sheet=active_sheet(self.document)
        selection=self.document['metadata'].get('active_regression_by_sheet',{}).get(sheet['id'])
        candidates=[r for r in self.document['analyses'] if r['method_id']==REGRESSION_METHOD and r['source']['worksheet_id']==sheet['id']]
        result=next((r for r in candidates if r['analysis_id']==selection),None) if selection else (candidates[-1] if candidates else None)
        if result is None:return
        try:model=model_for_prediction(result,sheet)
        except ValueError:return
        self.last_regression,self.last_regression_id=model,result['analysis_id']
        self.regression_menu.entryconfigure(1,state='normal')

    def use_saved_regression(self,analysis_id):
        self.worksheet.commit_edit();self.sync_document()
        try:
            result=next((r for r in self.document['analyses'] if r['analysis_id']==analysis_id),None)
            if result is None:raise ValueError('Modelo não encontrado.')
            sheet=next(s for s in self.document['worksheets'] if s['id']==result['source']['worksheet_id'])
            model_for_prediction(result,sheet)
        except ValueError as error:
            messagebox.showerror('Modelo indisponível',str(error),parent=self.grab_current() or self);return False
        self.switch_worksheet(sheet['id'])
        self.document['metadata'].setdefault('active_regression_by_sheet',{})[sheet['id']]=analysis_id
        self.restore_regression();self.mark_dirty()
        self.status.set('Modelo selecionado · use Estat > Regressão > Prever novos casos')
        return True

    def show_saved_regression_graph(self,analysis_id):
        try:
            result=next((r for r in self.document['analyses'] if r['analysis_id']==analysis_id),None)
            if result is None:raise ValueError('Modelo não encontrado.')
            graph=RegressionGraph(self,archived_model(result))
        except ValueError as error:
            messagebox.showerror('Gráfico indisponível',str(error),parent=self.grab_current() or self);return None
        graph.title('Regressão — resultado salvo em '+result['created_at'])
        self.center_dialog(graph)
        return graph

    def show_saved_anova_graph(self,analysis_id):
        try:
            result=next((r for r in self.document['analyses'] if r['analysis_id']==analysis_id),None)
            if result is None or result['method_id']!=ANOVA_METHOD:raise ValueError('Selecione uma ANOVA no histórico.')
            scene=result['scenes'][0]
            graph=GroupGraphWindow(self,scene['groups'],scene['response_label'])
        except ValueError as error:
            messagebox.showerror('Gráfico indisponível',str(error),parent=self.grab_current() or self);return None
        graph.title('ANOVA — resultado salvo em '+result['created_at'])
        self.center_dialog(graph);return graph

    def clear_regression(self):
        self.last_regression = None
        self.last_regression_id = None
        self.regression_menu.entryconfigure(1, state='disabled')

    def distribution_dialog(self):
        self.worksheet.commit_edit()
        return DistributionDialog(self)

    def run_distribution(self, name, parameters, operation, value, upper=None):
        self.worksheet.commit_edit()
        try:
            result = distribution_calculation(name, parameters, operation, value, upper)
            report = format_distribution(result)
        except ValueError as error:
            messagebox.showerror('Não foi possível calcular', str(error), parent=self.grab_current() or self)
            return False
        self.append_analysis(report, 'Cálculo de distribuição adicionado à sessão')
        return True

    def prediction_dialog(self):
        self.worksheet.commit_edit()
        self.sync_document();self.restore_regression()
        if self.last_regression is None:
            messagebox.showinfo('Modelo necessário', 'Ajuste uma regressão com os dados atuais antes de prever.', parent=self)
            return None
        return PredictionDialog(self, self.last_regression)

    def run_prediction(self, text=None, columns=None, omit_missing=True, **options):
        self.worksheet.commit_edit()
        self.sync_document();self.restore_regression()
        try:
            if self.last_regression is None:
                raise ValueError('Ajuste uma regressão com os dados atuais antes de prever.')
            if len(self.document['analyses'])>=10000:raise ValueError('Limite de 10000 análises por projeto atingido.')
            sheet=active_sheet(self.document)
            if columns is not None:
                if any(type(i) is not int or not 0<=i<len(sheet['columns']) for i in columns):
                    raise ValueError('Selecione colunas válidas para prever.')
                result=execute_prediction(self.document,self.last_regression_id,sheet['id'],input_kind='columns',
                                          input_column_ids=[sheet['columns'][i]['id'] for i in columns],omit_missing=omit_missing,**options)
            else:
                cases, numbers = parse_cases(text or '', len(self.last_regression['predictors']))
                result=execute_prediction(self.document,self.last_regression_id,sheet['id'],cases=cases,case_numbers=numbers,**options)
        except ValueError as error:
            messagebox.showerror('Não foi possível prever', str(error), parent=self.grab_current() or self)
            return False
        self.document['analyses'].append(result)
        self.append_analysis(result['report'], 'Previsão adicionada à sessão e ao histórico')
        return True

    def anova_dialog(self):
        self.worksheet.commit_edit()
        return AnovaDialog(self)

    def group_plot_dialog(self):
        self.worksheet.commit_edit()
        return GroupPlotDialog(self)

    def xy_graph_dialog(self, kind):
        self.worksheet.commit_edit()
        return XYGraphDialog(self, kind)

    def run_xy_graph(self, kind, y, x=None, **options):
        self.worksheet.commit_edit()
        try:
            model = prepare_xy(self.headers, self.rows, y, x, kind=kind, **options)
        except ValueError as error:
            messagebox.showerror('Não foi possível criar o gráfico', str(error), parent=self.grab_current() or self)
            return None
        graph = XYGraphWindow(self, model)
        self.center_dialog(graph)
        self.status.set(f"Gráfico criado: {model['n']} pontos, {model['missing']} linhas omitidas")
        return graph

    def plot_groups(self, **selection):
        self.worksheet.commit_edit()
        try:
            groups, _ = prepare_groups(self.headers, self.rows, **selection)
            response = self.headers[selection['response']] if 'response' in selection else 'Valores'
            window = GroupGraphWindow(self, groups, response)
        except ValueError as error:
            messagebox.showerror('Não foi possível criar o gráfico', str(error), parent=self.grab_current() or self)
            return False
        self.center_dialog(window)
        return True

    def run_anova(self, equal_var=True, confidence=95, comparisons=False, show_graph=False, comparison_method='tukey', **selection):
        self.worksheet.commit_edit()
        self.status.set('Calculando ANOVA…')
        self.configure(cursor='watch')
        self.update_idletasks()
        graph = None
        try:
            self.sync_document()
            if len(self.document['analyses'])>=10000:raise ValueError('Limite de 10000 análises por projeto atingido.')
            indices=selection['columns'] if selection.get('columns') is not None else [selection.get('response'),selection.get('factor')]
            if not isinstance(indices,(list,tuple)) or any(type(i) is not int or not 0<=i<len(self.headers) for i in indices):
                raise ValueError('Selecione os grupos ou resposta/fator da ANOVA.')
            sheet=active_sheet(self.document)
            result=execute_anova(sheet,[sheet['columns'][i]['id'] for i in indices],
                                 input_kind='columns' if selection.get('columns') is not None else 'stacked',
                                 equal_var=equal_var,confidence=confidence,comparisons=comparisons,comparison_method=comparison_method,show_graph=show_graph)
        except ValueError as error:
            self.status.set('ANOVA não concluída · confira os dados e as opções')
            messagebox.showerror('Não foi possível calcular', str(error), parent=self.grab_current() or self)
            return False
        finally:
            self.configure(cursor='')
        self.document['analyses'].append(result)
        self.output.insert('end', '\n' + result['report'])
        self.index_results()
        self.mark_dirty()
        self.output.see('end')
        self.status.set('ANOVA de um fator adicionada à sessão')
        if show_graph:self.show_saved_anova_graph(result['analysis_id'])
        return True

    def run_ttest(self, mode, first=None, second=None, perform_test=True, store=False, **options):
        self.worksheet.commit_edit()
        self.status.set('Calculando teste t…')
        self.configure(cursor='watch')
        self.update_idletasks()
        try:
            self.sync_document()
            if len(self.document['analyses']) >= 10000:
                raise ValueError('Limite de 10000 análises estruturadas por projeto atingido.')
            sheet = active_sheet(self.document)
            indices = [] if options.get('source') == 'summary' else [first] if mode == 'one' else [first, second]
            if any(type(i) is not int or not 0 <= i < len(sheet['columns']) for i in indices):
                raise ValueError('Selecione as colunas das amostras.')
            structured = execute_t(sheet, mode, [sheet['columns'][i]['id'] for i in indices],
                                   perform_test=perform_test, store_differences=store, **options)
            storage = self.prepare_analysis_storage(structured)
        except ValueError as error:
            self.status.set('Cálculo não concluído · confira os dados e as opções')
            messagebox.showerror('Não foi possível calcular', str(error), parent=self.grab_current() or self)
            return False
        finally:
            self.configure(cursor='')
        self.apply_analysis_storage(structured, storage)
        self.document['analyses'].append(structured)
        self.output.insert('end', '\n' + structured['report'])
        self.index_results()
        self.mark_dirty()
        self.output.see('end')
        self.status.set(TITLES[mode] + ' adicionado à sessão')
        return True

    def install_generated(self, headers, rows, names):
        start=len(self.headers)
        self.headers,self.rows=headers,rows
        self.data_changed();self.refresh();self.worksheet.select(0,start)

    def calculator_dialog(self):
        self.worksheet.commit_edit()
        return CalculatorDialog(self)

    def run_calculator(self,expression,name):
        self.worksheet.commit_edit()
        try:generated=calculate_column(self.headers,self.rows,expression,name)
        except ValueError as error:
            messagebox.showerror('Cálculo não concluído',str(error),parent=self.grab_current() or self)
            return False
        self.install_generated(*generated)
        self.append_analysis('CALCULADORA DE COLUNAS\n'+generated[2][0]+' = '+expression+'\n','Coluna calculada · Ctrl+Z desfaz')
        return True

    def frequency_dialog(self,kind='table'):
        self.worksheet.commit_edit()
        return FrequencyDialog(self,kind)

    def run_frequency(self,column,kind='table',**options):
        self.worksheet.commit_edit()
        try:
            result=frequency_table(self.headers,self.rows,column,**options)
            report=format_frequency(result)
            graph=FrequencyGraph(self,result,kind) if kind!='table' else None
        except (ValueError,ArithmeticError) as error:
            messagebox.showerror('Frequências não calculadas',str(error),parent=self.grab_current() or self);return False
        self.append_analysis(report,'Tabela de frequências adicionada à sessão')
        if graph:self.center_dialog(graph)
        return True

    def percentile_dialog(self):
        self.worksheet.commit_edit()
        return PercentileDialog(self)

    def run_percentiles(self,column,percentages,method):
        self.worksheet.commit_edit()
        try:
            values,missing=numeric_column(self.rows,column)
            result=sample_percentiles(values,percentages,method)
            lines=['PERCENTIS DA AMOSTRA — '+self.headers[column],f'N={len(values)}; ausentes={missing}; método={method}']
            for r in result:
                lines.append(f"P{r['percentile']:g}: "+(f"{r['value']:.10g}" if r['value'] is not None else 'indefinido: posição fora da amostra'))
        except (ValueError,ArithmeticError,IndexError) as error:
            messagebox.showerror('Percentis não calculados',str(error),parent=self.grab_current() or self);return False
        self.append_analysis('\n'.join(lines)+'\n','Percentis adicionados à sessão');return True

    def summary_dialog(self):
        self.worksheet.commit_edit()
        return DescriptiveDialog(self)

    def center_dialog(self, dialog):
        pending = getattr(dialog, '_center_after_id', None)
        if pending:
            dialog.after_cancel(pending)

        def place():
            dialog._center_after_id = None
            if not dialog.winfo_exists():
                return
            dialog.update_idletasks()
            x, y = centered_position(
                (self.winfo_rootx(), self.winfo_rooty(), self.winfo_width(), self.winfo_height()),
                getattr(dialog, 'initial_size', (dialog.winfo_width(), dialog.winfo_height())), monitor_work_area(self))
            # '+-100' preserva coordenada absoluta negativa no Tk.
            dialog.geometry(f'+{x}+{y}')

        place()
        # O primeiro posicionamento de uma janela transitória pode ser
        # substituído pelo Windows ao fechar o diálogo que a abriu.
        dialog._center_after_id = dialog.after(80, place)
        if not getattr(dialog, '_center_cancel_bound', False):
            def cancel(event):
                if event.widget is dialog and getattr(dialog, '_center_after_id', None):
                    dialog.after_cancel(dialog._center_after_id)
                    dialog._center_after_id = None
            dialog.bind('<Destroy>', cancel, add='+')
            dialog._center_cancel_bound = True

    def plot(self, kind='Histograma'):
        try:
            values, _ = self.data()
            window = GraphWindow(self, kind, self.column.get(), values)
        except ValueError as error:
            messagebox.showerror('Dados inválidos', str(error), parent=self)
            return
        self.center_dialog(window)

    def export(self):
        self.worksheet.commit_edit()
        path = filedialog.asksaveasfilename(defaultextension='.txt')
        if path:
            try:
                Path(path).write_text(self.output.get('1.0','end'), encoding='utf-8')
            except OSError as error:
                messagebox.showerror('Falha ao exportar', str(error))

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == '--smoke-test':
        from release_smoke import run
        raise SystemExit(run(MiniTaBom, sys.argv[2]))
    MiniTaBom().mainloop()
