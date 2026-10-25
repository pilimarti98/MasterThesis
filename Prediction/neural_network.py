from config.config import CONFIG

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

# 1. Load dataset (e.g., binary or 0-1 scaled digits)
consumption = pd.read_csv(f"{CONFIG["ENV"]["PATH_TO_DIR"]}/Data/consumption_2026-05-02.csv")
consumption["consumptionKwh"] = consumption["consumptionKwh"] /consumption["consumptionKwh"].abs().max()

norm_consumption = consumption["consumptionKwh"]
values = np.array(norm_consumption, dtype=float)

# AR(1): predict each value from the preceding value
X = values[:-1].reshape(-1, 1)
y = values[1:]

# Small regularization helps avoid overfitting
model = Ridge(alpha=1.0)
model.fit(X, y)

intercept = float(model.intercept_)
phi = float(model.coef_[0])

# Estimate the unexplained variation
residuals = y - model.predict(X)
residuals = residuals - residuals.mean()

print("Intercept:", intercept)
print("Autoregressive coefficient:", phi)
print("Residual standard deviation:", residuals.std())

# Predict the next value
next_value = intercept + phi * values[-1]
print("Next-value prediction:", next_value)

# Generate 10 possible future sequences
rng = np.random.default_rng(42)
n_steps = 10
n_sequences = 10

simulations = np.zeros((n_sequences, n_steps))

for j in range(n_sequences):
    previous = values[-1]

    for t in range(n_steps):
        noise = rng.choice(residuals)
        current = intercept + phi * previous + noise

        simulations[j, t] = current
        previous = current

print("Generated future sequences:")
print(simulations)