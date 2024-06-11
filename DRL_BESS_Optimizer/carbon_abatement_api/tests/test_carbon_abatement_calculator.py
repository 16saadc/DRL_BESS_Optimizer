import pandas as pd
from datetime import datetime, timedelta
import pytest
from unittest.mock import Mock, patch, MagicMock
from carbon_abatement_api.nationalgrid_api_accessor import NationalGridApiAccessor
from carbon_abatement_api.bmrs_api_accessor import BmrsApiAccessor
from carbon_abatement_api.carbon_abatement_calculator import CarbonAbatementCalculator
import carbon_abatement_api.config as config


@pytest.fixture
def mock_BESS_fleet():
    mock_BESS_fleet = pd.DataFrame({
        "Name": ["Test"],
        "Owner": ["Test_Owner"],
        "Optimiser": ["Test_Optimiser"],
        "BMU ID": ["test"],
        "Energised": ["2023Q1"],
        "MW": [30],
        "MWh": [30],
        "Duration": [1],
        "Region": [1]
    }).set_index("BMU ID")
    return mock_BESS_fleet

# test data has to be padded with an extra value on each end to mimic how the data is retrieved
@pytest.fixture
def ci_mock_df_simple():
    data = {
        'settlementPeriod': [48, 1, 2, 3, 4, 5, 6, 7],
        'regionid': [6]*8,
        'dnoregion': ['region'] * 8,
        'shortname': ['reg'] * 8,
        'from': pd.to_datetime(['2023-04-30 23:30','2023-05-01 00:00', '2023-05-01 00:30', '2023-05-01 01:00', '2023-05-01 01:30', '2023-05-01 02:00', '2023-05-01 02:30', '2023-05-01 03:00']),
        'to': pd.to_datetime(['2023-05-01 00:00', '2023-05-01 00:30', '2023-05-01 01:00', '2023-05-01 01:30', '2023-05-01 02:00', '2023-05-01 02:30', '2023-05-01 03:00', '2023-05-01 03:30']),
        'regionalIntensity': [50]*8,
        'intensity.index': ['low']*8,
        'settlementDate': pd.to_datetime(['2023-05-01']*8).date,
        'nationalIntensity': [100]*8
    }
    return pd.DataFrame(data)

@pytest.fixture
def pn_mock_df_simple():
    data = {
        'dataset': ['PN'] * 8,
        'settlementDate': pd.to_datetime(['2023-05-01'] * 8),
        'timeFrom': pd.to_datetime(['2023-04-30 23:30','2023-05-01 00:00', '2023-05-01 00:30', '2023-05-01 01:00', '2023-05-01 01:30', '2023-05-01 02:00', '2023-05-01 02:30', '2023-05-01 03:00'])[::-1],
        'timeTo': pd.to_datetime(['2023-05-01 00:00', '2023-05-01 00:30', '2023-05-01 01:00', '2023-05-01 01:30', '2023-05-01 02:00', '2023-05-01 02:30', '2023-05-01 03:00', '2023-05-01 03:30'])[::-1],
        'settlementPeriod': [7, 6, 5, 4, 3, 2, 1, 48],
        'levelFrom': [0, 0, 2, 2, 0, -2, -2, 0],
        'levelTo': [0, 2, 2, 0, -2, -2, 0, 0],
        'bmUnit': ['test']*8,
        'nationalGridBmUnit': ['test']*8,
        'timeDifference': [0.500]*8,
        'time_gap': [timedelta(seconds=0)] * 8,
        'energyOut': [0, 0.5, 1.0, 0.5, 0.5, 1.0, 0.5, 0],
        'energyCharged': [None, None, None, None, 0.5, 1.0, 0.5, None],
        'energyDischarged': [None, 0.5, 1.0, 0.5, None, None, None, None],
    }
    return pd.DataFrame(data)


@pytest.fixture
def ci_mock_df_complex():
    data = {
        'settlementPeriod': [48, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'regionid': [6]*11,
        'dnoregion': ['region'] * 11,
        'shortname': ['reg'] * 11,
        'from': pd.to_datetime(['2023-04-30 23:30','2023-05-01 00:00', '2023-05-01 00:30', '2023-05-01 01:00', '2023-05-01 01:30', '2023-05-01 02:00', '2023-05-01 02:30', '2023-05-01 03:00', '2023-05-01 03:30', '2023-05-01 04:00', '2023-05-01 04:30']),
        'to': pd.to_datetime(['2023-05-01 00:00', '2023-05-01 00:30', '2023-05-01 01:00', '2023-05-01 01:30', '2023-05-01 02:00', '2023-05-01 02:30', '2023-05-01 03:00', '2023-05-01 03:30', '2023-05-01 04:00', '2023-05-01 04:30', '2023-05-01 05:00']),
        'regionalIntensity': [60, 50, 70, 70, 60, 80, 100, 120, 100, 150, 130],
        'intensity.index': ['low']*11,
        'settlementDate': pd.to_datetime(['2023-05-01']*11).date,
        # we just set nationalIntensity backwards to see if we get contrasting result to regional
        'nationalIntensity': [60, 50, 70, 70, 60, 80, 100, 120, 100, 150, 130][::-1],
    }
    return pd.DataFrame(data)


@pytest.fixture
def pn_mock_df_complex():
    # Ec = 5.0
    # Ed = 4.5
    # CIc_nat = 100
    # CId_nat = 85
    # CIc_reg = 67.5
    # CId_reg = 96.66667
    data = {
        'dataset': ['PN'] * 11,
        'settlementDate': pd.to_datetime(['2023-05-01'] * 11),
        'timeFrom': pd.to_datetime(['2023-04-30 23:30','2023-05-01 00:00', '2023-05-01 00:30', '2023-05-01 01:00', '2023-05-01 01:30', '2023-05-01 02:00', '2023-05-01 02:30', '2023-05-01 03:00', '2023-05-01 03:30', '2023-05-01 04:00', '2023-05-01 04:30'])[::-1],
        'timeTo': pd.to_datetime(['2023-05-01 00:00', '2023-05-01 00:30', '2023-05-01 01:00', '2023-05-01 01:30', '2023-05-01 02:00', '2023-05-01 02:30', '2023-05-01 03:00', '2023-05-01 03:30', '2023-05-01 04:00', '2023-05-01 04:30', '2023-05-01 05:00'])[::-1],
        'settlementPeriod': [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 48],
        'levelFrom': [0, 0, 2, 2, 2, 0, -5, -5, 0, 3, 0],
        'levelTo': [0, 2, 2, 2, 0, -5, -5, 0, 3, 0, 0],
        'bmUnit': ['test']*11,
        'nationalGridBmUnit': ['test']*11,
        'timeDifference': [0.500]*11,
        'time_gap': [timedelta(seconds=0)] * 11,
        'energyOut': [0, 0.5, 1.0, 1.0, 0.5, -1.25, -2.5, -1.25, 0.75, 0.75, 0],
        'energyCharged': [None, None, None, None, None, 1.25, 2.5, 1.25, None, None, None],
        'energyDischarged': [None, 0.5, 1.0, 1.0, 0.5, None, None, None, 0.75, 0.75, None]
    }
    return pd.DataFrame(data)




@pytest.fixture
def ci_mock_df_3():
    data = {
        'settlementPeriod': [48, 1, 2, 3, 4, 5],
        'regionid': [6]*6,
        'dnoregion': ['region'] * 6,
        'shortname': ['reg'] * 6,
        'from': pd.to_datetime(['2023-04-30 23:30','2023-05-01 00:00', '2023-05-01 00:30', '2023-05-01 01:00', '2023-05-01 01:30', '2023-05-01 02:00']),
        'to': pd.to_datetime(['2023-05-01 00:00', '2023-05-01 00:30', '2023-05-01 01:00', '2023-05-01 01:30', '2023-05-01 02:00', '2023-05-01 02:30']),
        'regionalIntensity': [50,50,60,20,40,80],
        'intensity.index': ['low']*6,
        'settlementDate': pd.to_datetime(['2023-05-01']*6).date,
        'nationalIntensity': [100,100,120,40,80,160]
    }
    return pd.DataFrame(data)

@pytest.fixture
def pn_mock_df_3():
    # Ed = 3
    # Ec = 0.5
    # CIc_reg = 40
    # CId_reg = 45
    # CIc_nat = 80
    # CId_nat = 56.66
    data = {
        'dataset': ['PN'] * 6,
        'settlementDate': pd.to_datetime(['2023-05-01'] * 6),
        'timeFrom': pd.to_datetime(['2023-04-30 23:30','2023-05-01 00:00', '2023-05-01 00:30', '2023-05-01 01:00', '2023-05-01 01:30', '2023-05-01 02:00'])[::-1],
        'timeTo': pd.to_datetime(['2023-05-01 00:00', '2023-05-01 00:30', '2023-05-01 01:00', '2023-05-01 01:30', '2023-05-01 02:00', '2023-05-01 02:30'])[::-1],
        'settlementPeriod': [5, 4, 3, 2, 1, 48],
        'levelFrom': [0, 0, 4, 2, 0, 0],
        'levelTo': [0, -2, 0, 4, 2, 0],
        'bmUnit': ['test']*6,
        'nationalGridBmUnit': ['test']*6,
        'timeDifference': [0.5]*6,
        'time_gap': [timedelta(seconds=0)] * 6,
        'energyOut': [0, -0.5, 1.0, 1.5, 0.5, 0],
        'energyCharged': [None, 0.5, None, None, None, None],
        'energyDischarged': [None, None, 1.0, 1.5, 0.5, None]
    }
    return pd.DataFrame(data)



@pytest.fixture
def carbon_abatement_calculator():
    return CarbonAbatementCalculator()

@pytest.fixture
def mock_bmrs_api_accessor():
    return MagicMock(spec=BmrsApiAccessor)

@pytest.fixture
def mock_nationalgrid_api_accessor():
    return MagicMock(spec=NationalGridApiAccessor)



@patch('carbon_abatement_api.config.BESS_fleet', mock_BESS_fleet)
def test_calculate_total_carbon_abated(carbon_abatement_calculator, mock_BESS_fleet, mock_bmrs_api_accessor, mock_nationalgrid_api_accessor, ci_mock_df_simple, pn_mock_df_simple):
    carbon_abatement_calculator.bmrs_api_accessor = mock_bmrs_api_accessor
    carbon_abatement_calculator.nationalgrid_api_accessor = mock_nationalgrid_api_accessor
    mock_nationalgrid_api_accessor.get_carbon_intensity.return_value = ci_mock_df_simple
    mock_bmrs_api_accessor.get_pn_stream_data.return_value = pn_mock_df_simple
    from_date = "2023-05-01"
    to_date = "2023-05-02"
    bmu_data = mock_BESS_fleet.loc['test']

    # use copy to not mess with original data for later tests
    full_data = carbon_abatement_calculator.map_dates_and_intensities(pn_mock_df_simple.copy(), ci_mock_df_simple.copy())
    assert len(full_data) == 8

    CIc_regional, CId_regional, CIc_national, CId_national = carbon_abatement_calculator.get_weighted_average_ci(full_data)

    assert CIc_regional == 50000
    assert CId_regional == 50000
    assert CIc_national == 100000
    assert CId_national == 100000

    result = carbon_abatement_calculator.calculate_total_carbon_abated(bmu_data, from_date, to_date)
    assert result['carbon_abated_regional (tCO2/MWh Discharged)'] == pytest.approx(0.0, 0.001)
    assert result['carbon_abated_national (tCO2/MWh Discharged)'] == pytest.approx(0.0, 0.001)

@patch('carbon_abatement_api.config.BESS_fleet', mock_BESS_fleet)
def test_calculate_total_carbon_abated_complex(carbon_abatement_calculator, mock_bmrs_api_accessor, mock_nationalgrid_api_accessor, ci_mock_df_complex, pn_mock_df_complex):
    carbon_abatement_calculator.bmrs_api_accessor = mock_bmrs_api_accessor
    carbon_abatement_calculator.nationalgrid_api_accessor = mock_nationalgrid_api_accessor
    mock_nationalgrid_api_accessor.get_carbon_intensity.return_value = ci_mock_df_complex
    mock_bmrs_api_accessor.get_pn_stream_data.return_value = pn_mock_df_complex
    from_date = "2023-05-01"
    to_date = "2023-05-02"
    mock_BESS_fleet.loc['test'] = {'Region': 'your_region', 'Name': 'test_name', 'MW': 'test_MW', 'MWh': 'test_MWh'}  # add other fields as necessary
    bmu = 'test'

    # use copy to not mess with original data for later tests
    full_data = carbon_abatement_calculator.map_dates_and_intensities(pn_mock_df_complex.copy(), ci_mock_df_complex.copy())
    assert len(full_data) == 11

    CIc_regional, CId_regional, CIc_national, CId_national = carbon_abatement_calculator.get_weighted_average_ci(full_data)

    assert CIc_regional == 67500
    assert CId_regional == pytest.approx(96666.670, 0.0001)
    assert CIc_national == 100000
    assert CId_national == 85000

    result = carbon_abatement_calculator.calculate_total_carbon_abated(from_date, to_date, bmu)
    assert result['carbon_abated_regional (gCO2/MWh Discharged)'] == pytest.approx(112000/4.5, 0.001)
    assert result['carbon_abated_national (gCO2/MWh Discharged)'] == pytest.approx(-125000/4.5, 0.001)

@patch('carbon_abatement_api.config.BESS_fleet', mock_BESS_fleet)
def test_calculate_total_carbon_abated_rand(carbon_abatement_calculator, mock_bmrs_api_accessor, mock_nationalgrid_api_accessor, ci_mock_df_3, pn_mock_df_3):
    carbon_abatement_calculator.bmrs_api_accessor = mock_bmrs_api_accessor
    carbon_abatement_calculator.nationalgrid_api_accessor = mock_nationalgrid_api_accessor
    mock_nationalgrid_api_accessor.get_carbon_intensity.return_value = ci_mock_df_3
    mock_bmrs_api_accessor.get_pn_stream_data.return_value = pn_mock_df_3
    from_date = "2023-05-01"
    to_date = "2023-05-02"
    bmu = 'test'

    # use copy to not mess with original data for later tests
    full_data = carbon_abatement_calculator.map_dates_and_intensities(pn_mock_df_3.copy(), ci_mock_df_3.copy())
    assert len(full_data) == 6

    CIc_regional, CId_regional, CIc_national, CId_national = carbon_abatement_calculator.get_weighted_average_ci(full_data)

    assert CIc_regional == 40000
    assert CId_regional == 45000
    assert CIc_national == 80000
    assert CId_national == 90000

    result = carbon_abatement_calculator.calculate_total_carbon_abated(from_date, to_date, bmu)
    assert result['carbon_abated_regional (tCO2/MWh Discharged)'] == pytest.approx(0.1025, 0.001)
    assert result['carbon_abated_national (tCO2/MWh Discharged)'] == pytest.approx(0.205, 0.001)
