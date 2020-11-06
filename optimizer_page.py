import tkinter as tk
from tkinter import ttk

class OptimizerPage(tk.Frame):

    '''
    Widget Settings
    '''
    lineup_list_set = {
        'set': {'height':20, 'width':50, 'padx':2, 'pady':2, 'relief':tk.GROOVE, 'bd':2, 'state':tk.DISABLED},
        'pos': {'row':3, 'column':0, 'columnspan':8, 'pady':10, 'padx':10, 'sticky':'nsew'},
        'scroll' :{'row':3, 'column':7, 'pady':10, 'padx':10, 'sticky':'nse'} 
    }   
    percentages_set = {
        'set': {'height':20, 'width':50, 'padx':2, 'pady':2, 'relief':tk.GROOVE, 'bd':2, 'state':tk.DISABLED},
        'pos': {'row':3, 'column':8, 'columnspan':8, 'pady':10, 'padx':10, 'sticky':'nsew'},
        'scroll': {'row':3, 'column':15, 'pady':10, 'padx':10, 'sticky':'nse'}
    }
    team_button_set = {
        'pos': {'padx':5, 'pady':3, 'sticky':'w'}
    }
    entry_set = {
        'label_set': {'text':'Lineups:', 'font':('Calibri', 12)},
        'label_pos': {'row':2, 'column':8, 'columnspan':2, 'padx':3, 'sticky':'e'},
        'set': {'width':4, 'font':('Monaco', 12)},
        'pos': {'row':2, 'column':10, 'pady':10, 'sticky':'nsew'}
    }
    slider_set = {
        'set': {'from_':1, 'to':100, 'width':30, 'orient':tk.HORIZONTAL, 'showvalue':False},
        'pos': {'row':2, 'column':11, 'columnspan':4, 'pady':10, 'sticky':'nsew'}
    }
    o_button_set = {
        'set': {'height':2, 'width':12, 'text':'Optimize', 'bd':2, 'font':('Calibri', 12)},
        'pos': {'row':2, 'column':2, 'columnspan':4, 'pady':3, 'sticky':'nsew'}
    }

    def __init__(self, optimizer, parent, controller):
        tk.Frame.__init__(self, parent)
        #declares optimizer to be used in calculations
        self.optimizer = optimizer

        self.controller = controller
        
        #sets text boxes for lineups and percentages
        self.lineup_list = tk.Text(self, **self.lineup_list_set['set'])
        self.lineup_list.grid(**self.lineup_list_set['pos'])
        l_scroll = ttk.Scrollbar(self, command=self.lineup_list.yview)
        l_scroll.grid(**self.lineup_list_set['scroll'])
        self.lineup_list['yscrollcommand'] = l_scroll.set
        
        self.percentages = tk.Text(self, **self.percentages_set['set'])
        self.percentages.grid(**self.percentages_set['pos'])
        p_scroll = ttk.Scrollbar(self, command=self.percentages.yview)
        p_scroll.grid(**self.percentages_set['scroll'])
        self.percentages['yscrollcommand'] = p_scroll.set

        #sets team check buttons and associated variables
        team_buttons = {}
        self.team_vars = {}
        for i, team in enumerate(self.optimizer.teams):
            self.team_vars[team] = tk.IntVar()
            self.team_vars[team].set(1)
            team_buttons[team] = ttk.Checkbutton(self, text=team, variable=self.team_vars[team])
            if len(team_buttons) <= 16:
                team_buttons[team].grid(row=0, column=i, **self.team_button_set['pos'])
            else:
                team_buttons[team].grid(row=1, column=i%16, **self.team_button_set['pos'])

        #Sets entry and slider for number of lineups
        #num_lineups used in optimize function
        self.num_lineups = tk.IntVar()
        self.num_lineups.set(10)

        #Entry box
        e = tk.Label(self, **self.entry_set['label_set'])
        e.grid(**self.entry_set['label_pos'])
        entry = ttk.Entry(self, textvariable=self.num_lineups, **self.entry_set['set'])
        entry.grid(**self.entry_set['pos'])

        #slider
        slider = tk.Scale(self, variable=self.num_lineups, **self.slider_set['set'])
        slider.grid(**self.slider_set['pos'])

        #optimize button runs optimizer and outputs lineups in text box
        o_button = tk.Button(self, command=lambda: self.get_lineups(), **self.o_button_set['set'])
        o_button.grid(**self.o_button_set['pos'])
        
    #used in optimize button to optimize lineups and put in text box    
    def get_lineups(self):

        player_page = self.controller.get_page('Players')

        #sets excluded teams, excl players, and lock players for optimizer
        excl_teams = [team for team in self.team_vars if self.team_vars[team].get() == 0]
        self.optimizer.excl_teams = excl_teams

        excl_players = [player for player in player_page.excl_vars if player_page.excl_vars[player].get()==1]
        self.optimizer.excl_players = excl_players

        lock_players = [player for player in player_page.lock_vars if player_page.lock_vars[player].get()==1]
        self.optimizer.lock_players = lock_players

        #sets number of lineups for optimizer
        self.optimizer.num_lineups = self.num_lineups.get()

        #resets existing text in lineups and percentages
        self.lineup_list.config(state=tk.NORMAL)
        self.percentages.config(state=tk.NORMAL)
        self.lineup_list.delete(1.0, tk.END)
        self.percentages.delete(1.0, tk.END)

        #runs optimizer, converts to string, puts in text box
        self.optimizer.optimize()
        if bool(self.optimizer.lineups):
            for i, lineup in enumerate(self.optimizer.lineups.values()):
                df_string = lineup['players'].to_string(index=False, header=False)
                self.lineup_list.insert(tk.END,
                    '='*self.lineup_list_set['set']['width'] + '\n'+
                    'Lineup: ' + str(i+1) + '\n\n'+
                    df_string + '\n\n'+
                    'Points: '+str(lineup['points'])+'    '+'Salary: '+str(lineup['salary'])+'\n'+
                    '='*self.lineup_list_set['set']['width'] + '\n')
        else:        
            self.lineup_list.insert(tk.END,
                'Constraints do not allow for creation of lineups.'+'\n'+
                'To get optimal lineups, ensure locked and excluded'+'\n'+
                'players are valid.'
        )

        #updates percentages for each player
        try:                
            p_string = self.optimizer.percentages.to_string(index=False, header=False)
            self.percentages.insert(tk.END, p_string)
        except:
            pass

        self.lineup_list.config(state=tk.DISABLED)
        self.percentages.config(state=tk.DISABLED)
