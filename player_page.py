import tkinter as tk
from tkinter import ttk
import pandas as pd
from scrollable_frame import ScrollableFrame

class PlayerPage(tk.Frame):

    def __init__(self, optimizer, parent, controller):
        tk.Frame.__init__(self, parent)
        #prepares player dataframe used throughout frame
        self.player_master = optimizer.player_master.filter(
            ['position', 'name', 'team', 'salary', 'ppg_projection', 'value']
        )

        #declares scrollable frame for excl and lock buttons
        #borrows from class found online
        player_frame = ScrollableFrame(self, 420, 400)
        player_frame.grid(column=0, row=1, padx=10, pady=(0,10), rowspan=3)

        #adds excl and lock labels
        tk.Label(self, text='Excl | Lock').grid(column=0, row=0, sticky='sw', padx=4, pady=(10,0))

        #creates and places lock and exclusion buttons
        self.excl_buttons = {}
        self.lock_buttons = {}
        self.excl_vars = {}
        self.lock_vars = {}
        for i, player in enumerate(self.player_master.index):
            #excl buttons
            self.excl_vars[player] = tk.IntVar()
            self.excl_vars[player].set(0)
            self.excl_buttons[player] = ttk.Checkbutton(
                player_frame.scrollable_frame,
                variable=self.excl_vars[player],
                command=lambda x=player: self.toggle_excl(x)
            )
            self.excl_buttons[player].grid(row=i, column=0)

            #lock buttons
            self.lock_vars[player] = tk.IntVar()
            self.lock_vars[player].set(0)
            self.lock_buttons[player] = ttk.Checkbutton(
                player_frame.scrollable_frame,
                variable=self.lock_vars[player],
                command=lambda x=player: self.toggle_lock(x)
            )
            self.lock_buttons[player].grid(row=i, column=1)

        #adds labels to scrollframe with player info
        player_labels = {}
        self.player_text = self.player_master.to_string(header=False, index=False, justify='right').splitlines()
        for i in range(len(self.player_master.index)):
            player_labels[i] = tk.Label(
                player_frame.scrollable_frame,
                text=self.player_text[i],
                anchor='w',
                font=('Consolas', 11),
                bg='white'
            )
            player_labels[i].grid(column=3, row=i, sticky='w')

        #adds text box for exluded players
        tk.Label(self, text="Excluded:", font=('Calibri', 11)).grid(row=0, column=1, sticky='sw')
        self.excl_text = tk.Text(self, height=10, width=50, state=tk.DISABLED)
        self.excl_text.grid(row=1, column=1, sticky='ns', padx=(0,10))
        e_scroll = ttk.Scrollbar(self, command=self.excl_text.yview)
        e_scroll.grid(row=1, column=1, sticky='nse', padx=(0,10))
        self.excl_text['yscrollcommand'] = e_scroll.set

        #adds text box for locked players
        tk.Label(self, text="Locked:", font=('Calibri', 11)).grid(row=2, column=1, sticky='sw')
        self.lock_text = tk.Text(self, height=10, width=50, state=tk.DISABLED)
        self.lock_text.grid(row=3, column=1, sticky='ns', pady=(0,10), padx=(0,10))
        l_scroll = ttk.Scrollbar(self, command=self.lock_text.yview)
        l_scroll.grid(row=3, column=1, sticky='nse', pady=(0,10), padx=(0,10))
        self.lock_text['yscrollcommand'] = l_scroll.set

        #dataframes to be converted to string in toggle functions
        self.excl_df = pd.DataFrame()
        self.lock_df = pd.DataFrame()

    #function used when check button clicked
    def toggle_excl(self, player):
        #if button is checked after click, disable lock button and add player data to df
        if self.excl_vars[player].get() == 1:
            self.lock_buttons[player].configure(state = tk.DISABLED)
            self.excl_df = pd.concat([self.excl_df, self.player_master.iloc[[player]]])
        #if button is empty after click, reenable lock button and remove data
        else:
            self.lock_buttons[player].configure(state = tk.NORMAL)
            self.excl_df = self.excl_df.drop(player)

        #converts data frame to string and adds to text box
        df_text = self.excl_df.to_string(header=False, index=False, justify='right')
        self.excl_text.config(state=tk.NORMAL)
        self.excl_text.delete(1.0, tk.END)
        if not self.excl_df.empty:
            self.excl_text.insert(tk.END, df_text)
        self.excl_text.config(state=tk.DISABLED)

    #same function as toggle_excl with names switched
    def toggle_lock(self, player):    
        if self.lock_vars[player].get() == 1:
            self.excl_buttons[player].configure(state = tk.DISABLED)
            self.lock_df = pd.concat([self.lock_df, self.player_master.iloc[[player]]])
        else:
            self.excl_buttons[player].configure(state = tk.NORMAL)
            self.lock_df = self.lock_df.drop(player)
            
        df_text = self.lock_df.to_string(header=False, index=False, justify='right')
        self.lock_text.config(state=tk.NORMAL)
        self.lock_text.delete(1.0, tk.END)
        if not self.lock_df.empty:
            self.lock_text.insert(tk.END, df_text)
        self.lock_text.config(state=tk.DISABLED)