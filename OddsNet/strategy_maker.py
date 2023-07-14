
# takes in a series of arguments 
# makes the proper dataset and augments it properly
# trains the model and tests all the confidence thresholds 


# tests the best test model on validate 

from model import oddsNet
from data_collector import data_collector

class strategy_maker():
    def __init__(self, name, architecture= 'silu', learning_rate= .001, weight_decay=False, num_epochs=10, batch_size = 2048, pos_weight=1, from_stacked=True,  min_minutes_since_commence=-1000000, max_minutes_since_commence=240, min_avg_odds=0, max_avg_odds = 10000, min_ev=10, max_ev=10000, max_best_odds=100):
        
        self.dc = data_collector(from_stacked=from_stacked, min_minutes_since_commence=min_minutes_since_commence, max_minutes_since_commence=max_minutes_since_commence, min_avg_odds= min_avg_odds, max_avg_odds=max_avg_odds, min_ev=min_ev, max_best_odds=max_best_odds, ) 

        self.model = oddsNet(name=name, scaler=self.dc.scaler, train_data=self.dc.train_data, test_data=self.dc.test_data, val_data=self.dc.val_data, architecture=architecture, learning_rate=learning_rate, weight_decay=weight_decay, num_epochs=num_epochs, batch_size=batch_size, pos_weight=pos_weight)


        self.model.backtest()