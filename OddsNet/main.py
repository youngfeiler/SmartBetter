from strategy_maker import strategy_maker


if __name__ == '__main__':
    architecture = 'silu'
    num_epochs = 50
    name = 'eng_features_1'
    min_ev = 0
    max_ev = 50
    max_best_odds = 20
    min_best_odds = 0
    max_minutes_since_commence = 150
    batch_size=512
    learning_rate = 0.001

    strat = strategy_maker(name=name, architecture=architecture, num_epochs=num_epochs, min_ev=min_ev, max_ev = max_ev, max_best_odds=max_best_odds, max_minutes_since_commence=max_minutes_since_commence, batch_size=batch_size, learning_rate = learning_rate, from_stacked=True)

    print("Done")