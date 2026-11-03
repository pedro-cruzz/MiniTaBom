import csv
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
from core import read_table, numeric_column
from project import load_project, save_project
from core import DESCRIPTIVE_STATISTICS, descriptive_report
from worksheet import Worksheet
from history import WorksheetHistory
from graphs import GraphWindow, GroupGraphWindow
from inference import analyze_t_inputs, format_t_report
from inference_dialog import InferenceDialog, TITLES
from basic_inference import analyze_basic, z_mean, one_proportion, format_basic
from basic_inference_dialog import BasicInferenceDialog, BASIC_TITLES
from extended_inference import analyze_extended, two_proportions, one_variance, two_variances, format_extended, EXTENDED_TITLES
from extended_inference_dialog import ExtendedInferenceDialog
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

class MiniTaBom(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('MiniTaBom')
        self.geometry('1180x790')
        self.minsize(900, 650)
        self.project_path = None
        self.dirty = False
        self.last_regression = None
        self.headers = ['Medição', 'Grupo']
        self.rows = [[str(x), 'A'] for x in [10,12,11,14,13,15,12,16,14,13]]
        self.history = WorksheetHistory(self.headers, self.rows)
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
        self.output.insert('end', 'MiniTaBom — sessão de estudos\n\nDados de exemplo fictícios carregados.\nSelecione uma coluna e use Estat > Estatísticas básicas.\n')
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
        data_menu.add_command(label='Adicionar linha', command=self.add_row)
        data_menu.add_command(label='Adicionar coluna…', command=self.add_column)
        data_menu.add_command(label='Renomear coluna atual…', command=lambda: self.rename_column(self.worksheet.active[1]))
        data_menu.add_separator()
        for operation, title in DATA_TITLES.items():
            data_menu.add_command(label=title + '…', command=lambda operation=operation: self.data_operation_dialog(operation))
        menu.add_cascade(label='Dados', menu=data_menu)
        calc_menu = tk.Menu(menu, tearoff=False)
        calc_menu.add_command(label='Distribuições de probabilidade…', command=self.distribution_dialog)
        menu.add_cascade(label='Calc', menu=calc_menu)
        stat_menu = tk.Menu(menu, tearoff=False)
        basic_menu = tk.Menu(stat_menu, tearoff=False)
        basic_menu.add_command(label='Exibir estatísticas descritivas…', command=self.summary_dialog)
        basic_menu.add_separator()
        basic_menu.add_command(label=BASIC_TITLES['z'] + '…', command=lambda: self.basic_test_dialog('z'))
        for mode, title in TITLES.items():
            basic_menu.add_command(label=title + '…', command=lambda mode=mode: self.ttest_dialog(mode))
        basic_menu.add_separator()
        basic_menu.add_command(label=BASIC_TITLES['proportion'] + '…', command=lambda: self.basic_test_dialog('proportion'))
        for mode, title in EXTENDED_TITLES.items():
            basic_menu.add_command(label=title + '…', command=lambda mode=mode: self.extended_test_dialog(mode))
        basic_menu.add_command(label='Correlação…', command=lambda: self.linear_dialog('correlation'))
        basic_menu.add_command(label='Teste de normalidade…', command=self.normality_dialog)
        stat_menu.add_cascade(label='Estatísticas básicas', menu=basic_menu)
        anova_menu = tk.Menu(stat_menu, tearoff=False)
        anova_menu.add_command(label='Um fator…', command=self.anova_dialog)
        stat_menu.add_cascade(label='ANOVA', menu=anova_menu)
        regression_menu = self.regression_menu = tk.Menu(stat_menu, tearoff=False)
        regression_menu.add_command(label='Ajustar modelo linear…', command=lambda: self.linear_dialog('regression'))
        regression_menu.add_command(label='Prever novos casos…', command=self.prediction_dialog, state='disabled')
        stat_menu.add_cascade(label='Regressão', menu=regression_menu)
        tables_menu = tk.Menu(stat_menu, tearoff=False)
        tables_menu.add_command(label='Qui-quadrado de associação…', command=self.contingency_dialog)
        stat_menu.add_cascade(label='Tabelas', menu=tables_menu)
        menu.add_cascade(label='Estat', menu=stat_menu)
        graph_menu = tk.Menu(menu, tearoff=False)
        graph_menu.add_command(label='Gráfico de dispersão…', command=lambda: self.xy_graph_dialog('scatter'))
        graph_menu.add_command(label='Gráfico de séries temporais…', command=lambda: self.xy_graph_dialog('time'))
        graph_menu.add_separator()
        graph_menu.add_command(label='Histograma', command=self.plot)
        graph_menu.add_command(label='Boxplot', command=lambda: self.plot('Boxplot'))
        graph_menu.add_command(label='Boxplots comparativos…', command=self.group_plot_dialog)
        menu.add_cascade(label='Gráfico', menu=graph_menu)
        window_menu = tk.Menu(menu, tearoff=False)
        window_menu.add_command(label='Sessão', accelerator='Ctrl+M', command=lambda: self.focus_pane('session'))
        window_menu.add_command(label='Planilha', accelerator='Ctrl+D', command=lambda: self.focus_pane('worksheet'))
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
            'Sessão': 'session', 'Planilha': 'table', 'Gerenciador de projeto': 'project',
            'Como usar': 'help', 'Cobertura do projeto…': 'project', 'Sobre o MiniTaBom': 'help',
            'Verificar atualizações…': 'help',
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
                               ('Descritivas…', self.summary_dialog, 'summary'), ('Histograma', self.plot, 'histogram')]:
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
        self.clear_regression()
        self.history.record(self.headers, self.rows)
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
        starts = ('Estatísticas descritivas:', 'T DE UMA AMOSTRA', 'T PAREADO', 'T DE WELCH', 'T DE DUAS AMOSTRAS', 'Z DE UMA AMOSTRA', 'TESTE DE UMA PROPORÇÃO', 'TESTE DE DUAS PROPORÇÕES', 'TESTE DE UMA VARIÂNCIA', 'TESTE DE DUAS VARIÂNCIAS', 'QUI-QUADRADO DE ASSOCIAÇÃO', 'TESTE DE NORMALIDADE', 'ANOVA DE UM FATOR', 'CORRELAÇÃO DE', 'REGRESSÃO LINEAR', 'PREVISÃO LINEAR', 'DISTRIBUIÇÃO —', 'OPERAÇÃO DE DADOS —')
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
            inventory = json.loads(resource_path('INVENTARIO_FUNCIONAL.json').read_text(encoding='utf-8'))
        except (OSError, ValueError) as error:
            messagebox.showerror('Cobertura indisponível', str(error), parent=self)
            return
        dialog = tk.Toplevel(self)
        dialog.title('Cobertura do projeto')
        dialog.transient(self)
        dialog.geometry('860x560')
        dialog.minsize(650, 400)
        ttk.Label(dialog, text='Referência: ' + inventory['alvo'], style='Title.TLabel').pack(fill='x')
        ttk.Label(dialog, text='Mapa inicial por áreas · a verificação integral das funções ainda está pendente.', padding=10).pack(fill='x')
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
                        values=('Pendente' if area['estado'] == 'pendente' else 'Parcial',))
        def show_area(event=None):
            if not tree.selection():
                return
            area = inventory['areas'][int(tree.selection()[0])]
            sections = [area['id'].replace('_', ' ').capitalize(), '\nDISPONÍVEL']
            sections += ['• ' + value for value in area['existente']] or ['Nenhuma implementação nesta área.']
            sections += ['\nPENDENTE'] + ['• ' + value for value in area['pendente']]
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
        self.history = WorksheetHistory(self.headers, self.rows)
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
            save_project(path, self.headers, self.rows, self.output.get('1.0', 'end-1c'))
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
            headers, rows, output = load_project(path)
        except (OSError, ValueError) as error:
            messagebox.showerror('Falha ao abrir projeto', str(error))
            return
        if not self.confirm_replace():
            return
        self.headers, self.rows = headers, rows
        self.history = WorksheetHistory(self.headers, self.rows)
        self.output.delete('1.0', 'end')
        self.output.insert('1.0', output)
        self.output.edit_reset()
        self.output.edit_modified(False)
        self.project_path, self.dirty = path, False
        self.refresh()
        self.update_title()
        self.status.set('Projeto aberto · ' + Path(path).name)

    def refresh(self):
        self.clear_regression()
        self.column['values'] = self.headers
        self.worksheet.set_data(self.headers, self.rows)
        self.dimensions.set(f'{len(self.rows)} linhas  |  {len(self.headers)} colunas')
        self.index_results()

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
                self.project_path = None
                self.output.delete('1.0', 'end')
                self.output.edit_reset()
                self.refresh()
                self.mark_dirty()
                self.status.set('CSV importado · salve um projeto para preservar dados e sessão')
            except (ValueError, OSError, UnicodeError) as error:
                messagebox.showerror('Falha ao importar', str(error))

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

    def contingency_dialog(self):
        self.worksheet.commit_edit()
        return ContingencyDialog(self)

    def normality_dialog(self):
        self.worksheet.commit_edit()
        return NormalityDialog(self)

    def run_normality(self, column):
        self.worksheet.commit_edit()
        try:
            result = analyze_normality(self.headers, self.rows, column)
            report = format_normality(result)
        except ValueError as error:
            messagebox.showerror('Não foi possível testar a normalidade', str(error), parent=self.grab_current() or self)
            return False
        self.append_analysis(report, 'Teste de normalidade adicionado à sessão')
        return True

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

    def run_correlation(self, columns, **options):
        self.worksheet.commit_edit()
        try:
            result = correlations(self.headers, self.rows, columns, **options)
            report = format_correlation(result)
        except ValueError as error:
            messagebox.showerror('Não foi possível calcular a correlação', str(error), parent=self.grab_current() or self)
            return False
        self.append_analysis(report, 'Correlação adicionada à sessão')
        return True

    def run_regression(self, response, predictors, show_graph=True, observations=False, **options):
        self.worksheet.commit_edit()
        self.configure(cursor='watch')
        self.update_idletasks()
        try:
            result = linear_regression(self.headers, self.rows, response, predictors, **options)
            report = format_regression(result, observations)
        except ValueError as error:
            messagebox.showerror('Não foi possível ajustar a regressão', str(error), parent=self.grab_current() or self)
            return False
        finally:
            self.configure(cursor='')
        self.append_analysis(report, 'Regressão linear adicionada à sessão')
        self.last_regression = result
        self.regression_menu.entryconfigure(1, state='normal')
        if show_graph:
            self.center_dialog(RegressionGraph(self, result))
        return True

    def clear_regression(self):
        self.last_regression = None
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
        if self.last_regression is None:
            messagebox.showinfo('Modelo necessário', 'Ajuste uma regressão com os dados atuais antes de prever.', parent=self)
            return None
        return PredictionDialog(self, self.last_regression)

    def run_prediction(self, text=None, columns=None, omit_missing=True, **options):
        self.worksheet.commit_edit()
        try:
            if self.last_regression is None:
                raise ValueError('Ajuste uma regressão com os dados atuais antes de prever.')
            if columns is not None:
                result = predict_columns(self.last_regression, self.headers, self.rows, columns,
                                         omit_missing=omit_missing, **options)
            else:
                cases, numbers = parse_cases(text or '', len(self.last_regression['predictors']))
                result = predict_linear(self.last_regression, cases, case_numbers=numbers, **options)
            report = format_predictions(result)
        except ValueError as error:
            messagebox.showerror('Não foi possível prever', str(error), parent=self.grab_current() or self)
            return False
        self.append_analysis(report, 'Previsões adicionadas à sessão')
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

    def run_anova(self, equal_var=True, confidence=95, comparisons=False, show_graph=False, **selection):
        self.worksheet.commit_edit()
        self.status.set('Calculando ANOVA…')
        self.configure(cursor='watch')
        self.update_idletasks()
        graph = None
        try:
            groups, excluded = prepare_groups(self.headers, self.rows, **selection)
            result = one_way(groups, equal_var=equal_var, confidence=confidence, comparisons=comparisons)
            report = format_anova_report(result, excluded)
            if show_graph:
                response = self.headers[selection['response']] if 'response' in selection else 'Valores'
                graph = GroupGraphWindow(self, groups, response)
        except ValueError as error:
            self.status.set('ANOVA não concluída · confira os dados e as opções')
            messagebox.showerror('Não foi possível calcular', str(error), parent=self.grab_current() or self)
            return False
        finally:
            self.configure(cursor='')
        self.output.insert('end', '\n' + report)
        self.index_results()
        self.mark_dirty()
        self.output.see('end')
        self.status.set('ANOVA de um fator adicionada à sessão')
        if graph is not None:
            self.center_dialog(graph)
        return True

    def run_ttest(self, mode, first=None, second=None, perform_test=True, **options):
        self.worksheet.commit_edit()
        self.status.set('Calculando teste t…')
        self.configure(cursor='watch')
        self.update_idletasks()
        try:
            result = analyze_t_inputs(self.headers, self.rows, mode, first, second, **options)
            report = format_t_report(result, perform_test=perform_test)
        except ValueError as error:
            self.status.set('Cálculo não concluído · confira os dados e as opções')
            messagebox.showerror('Não foi possível calcular', str(error), parent=self.grab_current() or self)
            return False
        finally:
            self.configure(cursor='')
        self.output.insert('end', '\n' + report)
        self.index_results()
        self.mark_dirty()
        self.output.see('end')
        self.status.set(TITLES[mode] + ' adicionado à sessão')
        return True

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
