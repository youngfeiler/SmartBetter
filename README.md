# SmartBetter

SmartBetter is the entire service that contains the market model:
- Historical Odds Pull-er
- Data pre-processing
- Model / Strategy configuration script
- Live-odds puller:
  * Reads market odds
  * Feeds to saved model
  * Notifies (texts) when opportunity arises
- Automatic bet placer:
  * Can place those bets on the proper site
 
OddsNet is all the stuff necessary for running the model to try to build a strategy that can beat the market
- Main.py runs the strategy maker with customizable parameters
- data_collector.py is a class that takes the data sheet and manipulates it in custimizable ways and formats it for the model
- model.py is a class that actually trains the specified model and tests its performance on validation data

SmartBetter is the software side of the platform. This stuff is really out of date because it's not hooked up to the new OddsNet model. It was running on the 'naive' model earlier in the year. This folder is full of a ton of shit: tests, experiments, depreciated classes and methods, its a mess.
- Main.py initializes the 'naive' model from earlier this year and can pull data, fuck with it, and use other scripts to send texts and place bets.
- current_odds_getter.py is more up-to-date. It might be able to run, idrk everything changes really fast. SmartBetter and OddsNet have to be connected for it all to run. Mess around with it if you desire.
- notification.py is the texting service. It just sends a text to a phone number. I can give your phone # access if you want to test it out, just let me know.
- This whole directory is a mess theres no point in detailing all the scripts, it's going to have to be reorganized....

Lastly, the data folder that's necessary for a lot of this to run is getting uploaded to dropbox rn. Text me. 
