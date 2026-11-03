from pathlib import Path
import tkinter as tk
from tkinter import ttk,messagebox
from excel_import import excel_sheets,read_excel


class ExcelDialog(tk.Toplevel):
    def __init__(self,parent,path):
        sheets=excel_sheets(path)
        super().__init__(parent);self.parent,self.path=parent,path
        self.title('Importar Excel');self.transient(parent);self.geometry('850x500');self.initial_size=(850,500)
        body=ttk.Frame(self,padding=16);body.pack(fill='both',expand=True)
        ttk.Label(body,text=Path(path).name,style='Title.TLabel').pack(fill='x')
        row=ttk.Frame(body);row.pack(fill='x',pady=10)
        ttk.Label(row,text='Aba:').pack(side='left');self.sheet=ttk.Combobox(row,state='readonly',values=[s['name'] for s in sheets],width=24)
        self.sheet.current(0);self.sheet.pack(side='left',padx=8)
        ttk.Label(row,text='Intervalo (ex.: A4:B20):').pack(side='left');self.cell_range=ttk.Entry(row,width=16);self.cell_range.pack(side='left',padx=8)
        self.header=tk.BooleanVar(self,value=True)
        ttk.Checkbutton(body,text='Primeira linha do intervalo contém os nomes das colunas',variable=self.header).pack(anchor='w')
        ttk.Button(body,text='Atualizar prévia',command=self.preview).pack(anchor='w',pady=8)
        self.table=ttk.Treeview(body,show='headings',height=9);self.table.pack(fill='both',expand=True)
        self.message=ttk.Label(body,text='Escolha somente o bloco desejado, sem enunciados. A importação inicia um novo projeto.',wraplength=790)
        self.message.pack(anchor='w',pady=8)
        actions=ttk.Frame(body);actions.pack(fill='x')
        ttk.Button(actions,text='Cancelar',command=self.destroy).pack(side='right')
        ttk.Button(actions,text='Importar',command=self.submit).pack(side='right',padx=8)
        self.bind('<Escape>',lambda e:self.destroy());parent.center_dialog(self);self.grab_set()

    def read(self):return read_excel(self.path,self.sheet.get(),self.cell_range.get(),self.header.get())

    def preview(self):
        try:headers,rows,meta=self.read()
        except (ValueError,OSError) as error:
            self.message.configure(text=str(error));return
        self.table.delete(*self.table.get_children());self.table.configure(columns=list(range(min(8,len(headers)))))
        for i,name in enumerate(headers[:8]):self.table.heading(i,text=name);self.table.column(i,width=90)
        for row in rows[:8]:self.table.insert('','end',values=row[:8])
        self.message.configure(text=f'{len(rows)} linhas e {len(headers)} colunas. Prévia: primeiras 8 linhas/colunas. '+meta['note'])

    def submit(self):
        try:headers,rows,meta=self.read()
        except (ValueError,OSError) as error:
            messagebox.showerror('Não foi possível importar',str(error),parent=self);return
        if self.parent.import_excel_data(headers,rows,meta,self.path):self.destroy()
