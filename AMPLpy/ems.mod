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

# Surplus/Deficit
param surplus {t in 1..Timestamp} := max(pv_gen[t] - demand[t], 0);
param deficit {t in 1..Timestamp} := max(demand[t] - pv_gen[t], 0);

# Variables
var Sell {1..Timestamp} >= 0; # Whether to sell to the aggregator
var Store {0..Timestamp} >= 0; # Amount to store for period t+1
var Buy {1..Timestamp} >= 0; # Amount to use for own consumption
var Discharge {1..Timestamp} >= 0; # Energy taken from battery
var SoC {1..Timestamp} >= 0, <= battery_capacity; # Battery level at the end of t

# Maximize benefits at the end of the day
maximize Total_Benefit:
	sum {t in 1..Timestamp} market_price[t] * (Sell[t] * (1-agg_rate) - Buy[t] * (1 + dem_rate));

subject to Energy_Balance {t in 1..Timestamp}:
	demand[t] + Sell[t] + Store[t] = pv_gen[t] + Buy[t] + Discharge[t];

# Limit how much can be sold: as much as has been generated
subject to Solar_Balance {t in 1..Timestamp}:
	pv_gen[t] >= Sell[t];

# Solar energy can only be sold if the generation is bigger than the demand
subject to Surplus_State {t in 1..Timestamp}:
	Sell[t] + Store[t] <= surplus[t];
	
# In a deficit scenario, system can only rely on Purchasing or discharging battery
subject to Deficit_State {t in 1..Timestamp}:
	Buy[t] + Discharge[t] <= deficit[t];

# Battery balance
subject to Battery_Balance {t in 1..Timestamp}:
	SoC[t] = (if t = 1 then store0 else SoC[t-1]) + Store[t] - Discharge[t];

# Limit how much can be bought
subject to Home_Balance {t in 1..Timestamp}:
	Buy[t] <= demand[t];

# Initialize storing variable with 0, considering no previous storage amount
subject to Init_Storing:
	Store[0] = store0;

# Limit the storing capacity to the battery's capacity
subject to Storing_Limit {t in 1..Timestamp}:
	Store[t] + Store[t-1] <= battery_capacity;