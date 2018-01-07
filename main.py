from __future__ import division
import argparse
import csv
import datetime
import numpy as np
from scipy.stats import norm
import sys

class Team(object):
    def __init__(self, name):
        self._name = name
        self._record = []
    
    def __eq__(self, other):
        if not isinstance(other, Team):
            return False
        return self._name == other._name
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        return hash(self._name)
    
    def __repr__(self):
        return 'Team({})'.format(self._name)
    
    def get_name(self):
        return self._name
    
    def add_game(self, game):
        assert isinstance(game, Game)
        self._record.append(game)
    
    def get_opponents(self):
        opp_strs = []
        for game in self._record:
            opp_str = game.get_opp_name(self)
            opp_strs.append(opp_str)
        return opp_strs
    
    def get_win_loss(self):
        wins = 0
        losses = 0
        for game in self._record:
            margin = game.get_margin(self)
            if margin > 0:
                wins += 1
            else:
                losses += 1
        return wins, losses
    
    def print_record(self, ranking=None):
        wins, losses = self.get_win_loss()
        print '{} ({}-{})'.format(self._name, wins, losses)
        for game in self._record:
            game.print_game(self, ranking)

class Game(object):
    def __init__(self, date, team1, score1, team2, score2):
        assert isinstance(date, datetime.date)
        assert isinstance(team1, Team)
        assert isinstance(team2, Team)
        assert isinstance(score1, int) and score1 >= 0
        assert isinstance(score2, int) and score2 >= 0
        assert team1 != team2
        assert score1 != score2
        self._date = date
        self._team1 = team1
        self._score1 = score1
        self._team2 = team2
        self._score2 = score2
    
    def __repr__(self):
        team1_str = self._team1.get_name()
        team2_str = self._team2.get_name()
        return 'Game({} {:>2}-{:>2} {})'.format(team1_str, self._score1, self._score2, team2_str)
    
    def get_margin(self, team):
        '''Returns the scoring margin from the perspective of `team`. The
        margin is positive if `team` is the winner and negative if `team` is
        the loser. Raises error if `team` is not a participant in the game.'''
        assert team in [self._team1, self._team2]
        if team == self._team1:
            return self._score1 - self._score2
        else:
            return self._score2 - self._score1
    
    def get_opp_name(self, team):
        '''Returns the name of the opponent of `team`. Raises error if `team`
        is not a participant in the game.'''
        assert team in [self._team1, self._team2]
        if team == self._team1:
            return self._team2.get_name()
        else:
            return self._team1.get_name()
    
    def print_game(self, team, ranking=None):
        '''Prints the result of the game from the perspective of `team`. 
        Raises error if `team` is not a participant in the game.'''
        assert team in [self._team1, self._team2]
        if team == self._team1:
            ownscore = self._score1
            oppscore = self._score2
        else:
            ownscore = self._score2
            oppscore = self._score1
        date_str = self._date.isoformat()
        opp_str = self.get_opp_name(team)
        result = 'W' if ownscore > oppscore else 'L'
        if ranking is None:
            print '{} {} {:>2}-{:>2} {}'.format(date_str, result, ownscore, oppscore, opp_str)
        else:
            opp_rank = np.where(ranking == opp_str)[0][0] + 1
            print '{} {} {:>2}-{:>2} {:>4} {}'.format(date_str, result, ownscore, oppscore, '#'+str(opp_rank), opp_str)

def standardize_team_str(team_str):
    '''Converts a team name to a standardized version.'''
    if team_str[-3:] == ' St': #St -> State
        team_str += 'ate'
    std_dict = {'California': 'Cal',
                'Cent Michigan': 'C Michigan',
                'Coastal Car': 'Coastal Carolina',
                'C. Carolina': 'Coastal Carolina',
                'ECU': 'East Carolina',
                'FL Atlantic': 'FAU',
                'Florida Intl': 'FIU',
                'FSU': 'Florida State',
                "Hawai'i": 'Hawaii',
                'Kent': 'Kent State',
                'LA Tech': 'Louisiana Tech',
                'Miami': 'Miami FL',
                'Miami (OH)': 'Miami OH',
                'Miss State': 'Mississippi State',
                'Mississippi': 'Ole Miss',
                'MTSU': 'Mid Tennessee',
                'North Carolina State': 'NC State',
                'OSU': 'Ohio State',
                'Pitt': 'Pittsburgh',
                'South Florida': 'USF',
                'UConn': 'Connecticut',
                'UL Monroe': 'ULM',
                'ULL': 'Louisiana',
                'UMass': 'Massachusetts',
                'UNC': 'North Carolina',
                'UT San Antonio': 'UTSA',
                'UVA': 'Virginia',
                'VT': 'Virginia Tech',
                'WKU': 'W Kentucky'}
    if team_str in std_dict:
        return std_dict[team_str]
    else:
        return team_str

def read_fpi(fpifile):
    '''`fpifile` must be a CSV file where each row corresponds to a team. The
    file must have two columns in the following order:
        1. name of the team
        2. ESPN FPI score of the team
    Returns `fpi`, which maps standardized (with the function
    `standardize_team_str`) team names to the teams' FPI scores.'''
    fpi = {}
    with open(fpifile) as f:
        reader = csv.reader(f)
        for row in reader: #each row corresponds to a team
            row = map(lambda s: s.strip(), row)
            team_str, fpiscore = row
            team_str = standardize_team_str(team_str)
            fpiscore = float(fpiscore)
            fpi[team_str] = fpiscore
    return fpi

def read_data(datafile, fbs_list):
    '''`datafile` must be a CSV file where each row corresponds to a game. The
    file must have five columns in the following order:
        1. date of game (M/d/yyyy)
        2. name of team 1
        3. score of team 1
        4. name of team 2
        5. score of team 2
    `fbs_list` is a list of standardized (with the function
    `standardize_team_str`) names of FBS teams. Returns `teams`, which maps
    standardized team names to instances of class `Team`.'''
    teams = {}
    with open(datafile) as f:
        reader = csv.reader(f)
        for row in reader:
            row = map(lambda s: s.strip(), row)
            date_str, team1_str, score1_str, team2_str, score2_str = row
            team1_str = standardize_team_str(team1_str)
            team2_str = standardize_team_str(team2_str)
            if team1_str not in fbs_list:
                team1_str = 'FCS Teams'
            if team2_str not in fbs_list:
                team2_str = 'FCS Teams'
            assert not team1_str == team2_str == 'FCS Teams'
        
            #put the data into appropriate format
            month, day, year = map(int, date_str.split('/'))
            date = datetime.date(year, month, day)                
            if team1_str in teams:
                team1 = teams[team1_str]
            else:
                team1 = Team(team1_str)
                teams[team1_str] = team1
            score1 = int(score1_str)
            if team2_str in teams:
                team2 = teams[team2_str]
            else:
                team2 = Team(team2_str)
                teams[team2_str] = team2
            score2 = int(score2_str)
            
            #Add the game to the teams' records
            game = Game(date, team1, score1, team2, score2)
            team1.add_game(game)
            team2.add_game(game)    
    return teams

def solve(f, xmin, xmax, target):
    '''Binary search to find `x` such that `f(x)` is close enough to `target`.
    `f` must be monotonically increasing.'''
    while True:
        x = (xmin + xmax) / 2
        fx = f(x)
        if np.abs(fx - target) < 1e-6:
            return x
        if fx > target:
            xmax = x
        else:
            xmin = x

def exp_wins(rating_diffs):
    return np.sum(norm.cdf(rating_diffs/15))

def get_ratings(teams, fpi):
    '''The inputs are `teams`, a dictionary that maps team names to instances
    of class `Team`, and `fpi`, a dictionary that maps team names to the team's
    ESPN FPI score. Returns a tuple `(ranking, ratings)`. `ranking` is a list
    of team names sorted from best to worst, and `ratings` is a dictionary
    that maps team names to the team's rating.'''
    n = len(teams)
    ratings_array = np.zeros(n)
    teams_list = np.sort(teams.keys())
    
    while True:
        new_ratings_array = np.zeros(n)
        for team_str in teams_list:
            team = teams[team_str]
            team_idx = np.where(teams_list == team_str)[0][0]
            
            opp_strs = team.get_opponents()
            opp_idxs = np.searchsorted(teams_list, opp_strs, side='left')
            opp_ratings = ratings_array[opp_idxs]
            wins, _ = team.get_win_loss()
            
            #add a win and a loss against an imaginary team whose
            #strength equals the team's ESPN FPI score
            try:
                team_fpi = fpi[team_str]
            except KeyError:
                team_fpi = 0.0
            opp_ratings = np.concatenate((opp_ratings, team_fpi*np.ones(2)))
            wins += 1
            
            f = lambda x: exp_wins(x - opp_ratings)
            new_ratings_array[team_idx] = solve(f, -100, 100, wins)
        
        new_ratings_array -= np.mean(new_ratings_array)
        if np.sum(np.abs(new_ratings_array - ratings_array)) < 1e-2:
            ratings_array = new_ratings_array
            break
        else:
            ratings_array = new_ratings_array
    
    #sort from best to worst
    sort_idxs = np.argsort(ratings_array)[::-1]
    ranking = teams_list[sort_idxs]
    ratings_array = ratings_array[sort_idxs]
    
    ratings = {}
    for team_str, rating in zip(ranking, ratings_array):
        ratings[team_str] = rating
    return ranking, ratings

def print_ranking(teams, fpi, ranking, ratings, outfile=None):
    output = ''
    output += 'Game data from [Massey Ratings](https://www.masseyratings.com/data.php)\n\n'
    output += 'SoS: strength of schedule; average rating of opponents\n\n'
    output += "FPI: estimate of the team's strength, as predicted by\n"
    output += '[ESPN](http://www.espn.com/college-football/statistics/teamratings)\n\n'
    output += '{:^4} | {:^25} | {:^6} | {:^5} | {:^5} \n'.format('Rank', 'Team', 'Rating', 'SoS', 'FPI')
    output += '{:-^4}:| {:-^25} | {:-^6}:| {:-^5}:| {:-^5}:\n'.format('', '', '', '', '')
    for i in range(len(ranking)):
        team_str = ranking[i]
        team = teams[team_str]
        
        opp_strs = team.get_opponents()
        sos = 0.0
        m = len(opp_strs)
        for opp_str in opp_strs:
            sos += ratings[opp_str] / m
        
        rank = i+1
        win_loss_str = ' ({}-{})'.format(*team.get_win_loss())
        rating = ratings[team_str]
        try:
            team_fpi = fpi[team_str]
        except KeyError:
            team_fpi = np.nan
        output += '{:>4} | {:25} | {:6.2f} | {:5.1f} | {:5.1f}\n'.format(rank, team_str+win_loss_str, rating, sos, team_fpi)
    
    if outfile is None:
        print output
    else:
        with open(outfile, 'w') as f:
            f.write(output)
        print 'Output written to {}'.format(outfile)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Produces a ranking of college football teams for a given season')
    parser.add_argument('year', type=int, help='A 4-digit year representing the college football season')
    parser.add_argument('--out', help='The file where the ranking will be written; if not used, prints to stdout')
    parser.add_argument('--prebowl', action='store_true', help='If used, generates pre-bowl game ranking')
    if len(sys.argv) == 1: #if no arguments are given
        parser.print_help()
        sys.exit(2)
    args = parser.parse_args()
    if args.year < 2014 or args.year > 2017:
        raise ValueError('year must be between 2014 and 2017, inclusive')
    suffix = str(args.year)
    if args.prebowl:
        suffix += 'prebowl'
    
    datafile = 'data/massey{}.csv'.format(suffix)
    fpifile = 'data/fpi{}.csv'.format(suffix)
    outfile = args.out
    
    fpi = read_fpi(fpifile)
    fbs_list = fpi.keys()
    teams = read_data(datafile, fbs_list)
    assert set(fbs_list) ^ set(teams.keys()) == set(['FCS Teams'])
    ranking, ratings = get_ratings(teams, fpi)
    print_ranking(teams, fpi, ranking, ratings, outfile)