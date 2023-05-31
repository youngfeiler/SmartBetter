# import pandas as pd
# import numpy as np
# from sklearn.compose import ColumnTransformer
# from sklearn.preprocessing import OneHotEncoder, StandardScaler
# from sklearn.metrics import mean_squared_error
#
# from sklearn.linear_model import LogisticRegression
# from sklearn.model_selection import train_test_split
#
# def run():
#
#     # Encodes the categorical variables and sets the target variable
#     df = clean_data(7)
#
#     # Defines the features and the target
#     X = df.iloc[:, :-1]  # select all rows and all columns except the last column
#     y = df.iloc[:, -1]  # select all rows and the last column
#
#     # Split the data into training and test sets
#     X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
#
#     # Create an instance of the LogisticRegression class
#     clf = LogisticRegression(random_state=42, max_iter=10000)
#
#     # Train the model on the training data
#     clf.fit(X_train, y_train)
#
#     # Test the model on the test data
#     accuracy = clf.score(X_test, y_test)
#
#     #print("Accuracy for this ml model last year was: {:.2f}% ... Lets see if it will work today...".format(accuracy * 100))
#
#     return clf
#
#
#
#
#
#
# def clean_data(each):
#     ohe = OneHotEncoder()
#
#     df = pd.read_csv(f"/Users/stefanfeiler/Desktop/golden data set insights/results/{each}d/results_{each}d_5s.csv")
#
#     df1 = df[['accurate_bookmaker_implied_prob', 'sportsbook_used_odds', 'sportsbook_used_ev', 'result_10_ev']]
#
#
#     # Fit and transform the 'sportsbook_used' column
#     ohe_df = pd.DataFrame(ohe.fit_transform(df[['sportsbook_used']]).toarray(), columns=[col + '_X' for col in ohe.get_feature_names_out(['sportsbook_used'])])
#
#
#     # Concatenate the original DataFrame with the one-hot encoded DataFrame
#     result = df1.join(ohe_df)
#
#     # Fit and transform the 'accurate_bookmaker' column
#     ohe_df = pd.DataFrame(ohe.fit_transform(df[['accurate_bookmaker']]).toarray(), columns=[col + '_X' for col in ohe.get_feature_names_out(['accurate_bookmaker'])])
#
#
#     # Concatenate the original DataFrame with the one-hot encoded DataFrame
#     result = result.join(ohe_df)
#
#     result['target'] = np.where(result['result_10_ev'] >= 0, 1, 0)
#
#     df_filtered = result[result['result_10_ev'].notna()].copy()
#
#     df_filtered = df_filtered.drop(columns=['result_10_ev'])
#
#     return df_filtered
#
#
#
# if __name__ == '__main__':
#     run()