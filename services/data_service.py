import pandas as pd
from config.settings import ROOT
def load_csv(name): return pd.read_csv(ROOT/"data"/name)
def patients(): return load_csv("patients.csv")
def providers(): return load_csv("providers.csv")
def consultations(): return load_csv("consultations.csv")
def health_workers(): return load_csv("health_workers.csv")
