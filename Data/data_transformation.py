from APICalls.api_call_btd import get_afrr_prices
from APICalls.api_call_elering import get_market_price, get_solar_production

def unify_data():
    """ Get all data from different API calls into a unified dataframe """

    afrr = None
    solar = None
    consumption = None
    prices = None

    # merge all dataframes into one

    # Save into this directory for MasterThesis python use and MasterThesisStudio for R Studio use