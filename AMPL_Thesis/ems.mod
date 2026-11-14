# Thesis on cost of residential electricity optimization
# Inputs are 
# 	- consumption [kWh]
# 	- market prices [€/kWh]
# 	- solar energy generation [kWh]


param Timestamp > 0; # Time period of a day. Hourly granularity.

# Predicted values
param pv_gen {1..Timestamp} >= 0; # Forecast of solar generation [kWh]
param demand {1..Timestamp} >= 0; # Forecast of consumption [kWh]
param market_price {1..Timestamp} >=0; # Estimation of market price [€/kWh]

# Rates
param agg_rate >=0; # rate the aggregator requires [€/kWh]
param dem_rate >=0; # rate charged on top of market price for consumption [€/kWh]

#Storing
param store0 >=0;
param battery_capacity >=0; # Battery capacity in kWh

# Variables
var Sell {1..Timestamp} >= 0; # Whether to sell to the aggregator
var Store {0..Timestamp} >= 0; # Amount to store for period t+1
var Buy {1..Timestamp} >= 0; # Amount to use for own consumption

# Minimize cost at the end of the day
maximize Total_Benefit:
	sum {t in 1..Timestamp} (Sell[t] * pv_gen[t] * (market_price[t] - agg_rate)
							 - Buy[t] * demand[t] * (market_price[t] - dem_rate)));
					
subject to Energy_Balance {t in 1..Timestamp}:
	demand[t] + Sell[t] + Store[t] = pv_gen[t] + Buy[t] + Store[t-1];

# Limit how much can be sold: as much as has been generated
subject to Solar_Balance {t in 1..Timestamp}:
	pv_gen[t] >= Sell[t];

# Solar energy can only be sold if the generation is bigger than the demand
subject to Selling_Condition {t in 1..Timestamp}:
	pv_gen[t] <= demand[t] ==> Sell[t] = 0;

# If there is no solar generation, nothing can be stored
subject to Storing_Condition {t in 1..Timestamp}:
	pv_gen[t] == 0 ==> Store[t] = 0;

# Limit how much can be bought
subject to Home_Balance {t in 1..Timestamp}:
	Buy[t] <= demand[t];

# Initialize storing variable with 0, considering no previous storage amount	
subject to Init_Storing:
	Store[0] = store0;

# Limit the storing capacity to the battery's capacity
subject to Storing_Limit {t in 1..Timestamp}:
	Store[t] <= battery_capacity;