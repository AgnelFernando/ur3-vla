import pandas as pd

class DummyAgent:
    def __init__(self, csv_file):
        self.dataframe = pd.read_csv(csv_file)
        self.current_index = 1

    def next(self):
        value = self.dataframe.iloc[self.current_index].values
        self.current_index += 1
        return value
        
    def is_last(self):
        return self.current_index >= len(self.dataframe) - 1
    
    def get_first(self):
        return self.dataframe.iloc[0].values