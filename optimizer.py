import pandas as pd
import pulp

class Optimizer:

    def __init__(self, file_path, num_lineups=10):
        #player_master not to be manipulated
        self.player_master = self.initialize_df(file_path)
        #players is changed in team filtering
        self.players = self.player_master
        self.positions = self.set_indicators('position')
        self.teams = self.set_indicators('team')
        self.opp_skaters = self.set_opp_skaters()
        self.num_lineups = num_lineups
        self.n_players = len(self.players.index)
        self.p_vars = []
        self.t_vars = []
        self.lineups = {}
        self.excl_teams = []
        self.excl_players = []
        self.lock_players = []
        self.percentages = {}
        #keeps track of optimal status of lineups
        #0 is default, 1 means all linueps optimal, -1 means some lineups infeasible
        self.optimal_status = 0
        #keeps track of lineups create during optimization
        #used for possible loading bar
        self.lineups_created = 0

    #prepares df for program
    def initialize_df(self, file_path):
        df = pd.read_csv(file_path)
        df = df.sort_values(by=['last_name', 'first_name'])
        df = df.reset_index(drop=True)
        df['player_id'] = df.index
        df.insert(0, 'full_name', df['first_name'] + ' ' + df['last_name'])
        df['full_name'] = df['full_name'].apply(lambda name: f"{name[:19]:>19}")
        df['value'] = round(df['ppg_projection']/df['salary']*1000, 2)
        return df

    #sets indicator dictionary given column of dataframe
    def set_indicators(self, col):
        d = {i:[] for i in pd.Series(self.players[col]).unique()}
        for key in d:
            ind = self.players[col] == key
            ind = ind.astype(int)
            d[key] = ind
        return d

    #for each goalie, returns indicators for skaters opposing the goalie
    #used in goalie constraint
    def set_opp_skaters(self):
        opp = {i:[] for i in self.players.index if self.players.loc[i, 'position'] == 'G'}
        for goalie in opp:
            opp_skaters = (self.players['team']==self.players.loc[goalie, 'opp'])
            opp[goalie] = opp_skaters.astype(int)
        return opp


    #filters excluded teams from player df
    def filter_players(self):
        #filters out excluded teams and players
        self.players = self.player_master
        self.players = self.players.loc[~self.players['team'].isin(self.excl_teams)]
        self.players = self.players.loc[~self.players['player_id'].isin(self.excl_players)]

        #resets indicators, index, and number of players
        self.players = self.players.reset_index(drop=True)
        self.opp_skaters = self.set_opp_skaters()
        self.positions = self.set_indicators('position')
        self.teams = self.set_indicators('team')
        self.n_players = len(self.players.index)

    def optimize(self):
        self.lineups_created = 0
        self.filter_players()
        prob = pulp.LpProblem('Opti', pulp.LpMaximize)

        #adds decision variables
        self.p_vars = [pulp.LpVariable(str(player_id), cat='Binary') for player_id in range(self.n_players)]
        self.t_vars = [pulp.LpVariable(str(team), cat='Binary') for team in self.teams]   #to be used for team constraints only, not objective

        #adds objective function
        prob += (pulp.lpSum(self.players.loc[i, 'ppg_projection']*self.p_vars[i] for i in range(self.n_players)))
        
        #add player number constraints
        prob += (pulp.lpSum(self.p_vars[i] for i in range(self.n_players)) == 9)

        #add position constraints
        prob += (pulp.lpSum(self.positions['C'][i]*self.p_vars[i] for i in range(self.n_players)) == 2)
        prob += (pulp.lpSum(self.positions['W'][i]*self.p_vars[i] for i in range(self.n_players)) == 4)
        prob += (pulp.lpSum(self.positions['D'][i]*self.p_vars[i] for i in range(self.n_players)) == 2)
        prob += (pulp.lpSum(self.positions['G'][i]*self.p_vars[i] for i in range(self.n_players)) == 1)

        for team in self.teams:
            #adds number of players per team constraint
            prob += (pulp.lpSum(self.teams[team][i]*self.p_vars[i] for i in range(self.n_players)) <= 4)
            
            #contrains team variable to be 0 when no players from a team are added, 1 otherwise
            prob += (pulp.lpSum(self.teams[team][i]*self.p_vars[i] for i in range(self.n_players)) >= 
                    self.t_vars[list(self.teams).index(team)])

        #adds number of total teams constraint
        prob += (pulp.lpSum(team for team in self.t_vars) >= 3)

        #adds constraint where no skaters can face goalie
        for goalie in self.opp_skaters:
            prob += (6*self.p_vars[goalie] +
                pulp.lpSum(self.opp_skaters[goalie][j]*self.p_vars[j] for j in range(self.n_players)) <= 6)

        #adds locked players constraints
        for player in self.lock_players:
            prob += (self.p_vars[player] == 1)

        #add salary constraint
        prob += (pulp.lpSum(self.players.loc[i, 'salary']*self.p_vars[i] for i in range(self.n_players)) <= 55000)

        #creates list with optimal solutions
        self.lineups = self.load_lineups(prob)

        #sets dataframe with percentage of lineups a player is in
        self.percentages = self.set_percentages()

    #solves programming problems 
    def load_lineups(self, prob):
        #solves first problem, puts problem and linuep into respective dicts
        prob.solve()
        if prob.status != 1:
            self.optimal_status = -1
            return {}
        line_dict = {0: self.convert_lineups(self.p_vars)}
        prob_dict = {0: prob}
        self.lineups_created = 1

        #loop copies problem from previous lineup and adds a constraint forcing a new lineup
        for i in range(1, self.num_lineups):
            prob_dict[i] = prob_dict[i-1].copy()
            prob_dict[i] += (pulp.lpSum(self.p_vars[i] for i in range(self.n_players) if pulp.value(self.p_vars[i])==1) <= 8)
            prob_dict[i].solve()
            if prob_dict[i].status != 1:
                self.optimal_status = -1
                return line_dict
            line_dict[i] = self.convert_lineups(self.p_vars)
            self.lineups_created += 1

        #if all lineups are created, optimal status is 1 and line_dict returned
        self.optimal_status = 1
        return line_dict


    #converts decision variables to corresponding lineup
    def convert_lineups(self, lineup):
        #selects only players in given lineup
        p = list(map(bool, [pulp.value(v) for v in lineup]))
        l = self.players[p]

        #creates new dataframe to simplify lineup for printing
        player_df = l.filter(['position', 'full_name', 'team', 'salary', 'ppg_projection', 'value', 'player_id'])

        #orders lineup as seen in game
        player_df['position'] = pd.Categorical(player_df['position'], ['C', 'W', 'D', 'G'])
        player_df = player_df.sort_values(by='position')

        #resets index to original player id
        player_df = player_df.set_index('player_id')

        points = round(l['ppg_projection'].sum(),1)
        salary = l['salary'].sum()

        return {'players':player_df, 'points':points, 'salary':salary}

    def set_percentages(self):
        #combines all lineups into one dataframe to count players
        l = [lineup['players'] for lineup in self.lineups.values()]
        try:
            all_lineups = pd.concat(l)
        except:
            self.percentages = pd.DataFrame()
            return

        #puts percentages of each player into series indexed by player_id
        p = all_lineups.groupby('player_id').count().full_name
        p = p.apply(lambda x: round(x/len(self.lineups)*100, 1))

        #creates and orders percentages df
        percentages = self.player_master.filter(p.index, axis = 0)
        percentages = percentages.filter(['position', 'full_name', 'team', 'salary', 'ppg_projection' ])
        percentages.insert(2, 'percentages', p)
        percentages = percentages.sort_values(by='percentages', ascending=False)

        return percentages