# File containing basic configurations for api
import pandas as pd

BMRS_base_url = "https://data.elexon.co.uk/bmrs/api/v1"
NG_carbon_intensity_base_url = "https://api.carbonintensity.org.uk"
PN_STREAM_ENDPOINT = '/datasets/pn/stream'

BESS_fleet = pd.read_excel("carbon_abatement_api/BESS_fleet.xlsx")

BESS_fleet.set_index('BMU ID', inplace=True)


# Change this if you'd like to use the user prompted method
# This limits it to only analyzing 1 asset at a time
user_prompted = False

output_path = 'outputs/' # change this to the root of the output directory you want

FROM_DATE = "2023-08-01"
TO_DATE = "2023-08-15"

# these are the BMUs that will be analyzed, unless you use the user-prompted method
# use the second line if you would like to analyze all of the BESS in UK
# BMUs_for_analysis = ['E_ARNKB-1', 'T_PINFB-1', 'E_PILLB-1', 'E_BHOLB-1', 'V__GHABI001', '2__MSTAT001']
BMUs_for_analysis = BESS_fleet.index


UK_regions_map = {
    1: 'North Scotland',
    2: 'South Scotland',
    3: 'North West England',
    4: 'North East England',
    5: 'Yorkshire and the Humber',
    6: 'North Wales, Merseyside, and Cheshire',
    7: 'South Wales',
    8: 'West Midlands',
    9: 'East Midlands',
    10: 'East England',
    11: 'South West England',
    12: 'South England',
    13: 'London',
    14: 'South East England'
}
