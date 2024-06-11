import pandas as pd
from datetime import datetime
import pytest
from unittest.mock import Mock, patch
from carbon_abatement_api.nationalgrid_api_accessor import NationalGridApiAccessor

@pytest.fixture
def carbon_intensity_mock_df():
    data = {
        'settlementPeriod': [1, 2, 3, 4, 5],
        'regionid': [6, 6, 6, 6, 6],
        'dnoregion': ['NA'] * 5,
        'shortname': ['NA'] * 5,
        'from': pd.to_datetime(['2023-05-01 00:00:00', '2023-05-01 00:30:00', '2023-05-01 01:00:00', '2023-05-01 01:30:00', '2023-05-01 02:00:00']),
        'to': pd.to_datetime(['2023-05-01T00:30Z', '2023-05-01T01:00Z', '2023-05-01T01:30Z', '2023-05-01T02:00Z', '2023-05-01 02:30:00']),
        'regionalIntensity': [58, 55, 62, 67, 58],
        'intensity.index': ['low', 'low', 'low', 'low', 'low'],
        'settlementDate': pd.to_datetime(['2023-04-30', '2023-05-01', '2023-05-01', '2023-05-01', '2023-05-01']).date,
        'nationalIntensity': [118, 123, 123, 125, 126]
    }
    return pd.DataFrame(data)


@pytest.fixture
def regional_intensity_mock_response():
    return {'data': {'regionid': 6, 'dnoregion': 'region', 'shortname': 'reg', 'data': [
                        {'from': '2023-05-30T00:00Z', 'to': '2023-05-30T00:30Z', 'intensity': {'forecast': 50, 'index': 'low'}, 'generationmix': [{'fuel': 'biomass', 'perc': 1}]},
                        {'from': '2023-05-30T00:30Z', 'to': '2023-05-30T01:00Z', 'intensity': {'forecast': 60, 'index': 'low'}, 'generationmix': [{'fuel': 'biomass', 'perc': 1}]},
                        {'from': '2023-05-30T01:00Z', 'to': '2023-05-30T01:30Z', 'intensity': {'forecast': 70, 'index': 'low'}, 'generationmix': [{'fuel': 'biomass', 'perc': 1}]}]}}



@pytest.fixture
def national_intensity_mock_response():
    return {'data': [{'from': '2023-05-30T00:00Z', 'to': '2023-05-30T00:30Z', 'intensity': {'forecast': 74, 'actual': 89, 'index': 'low'}},
                     {'from': '2023-05-30T00:30Z', 'to': '2023-05-30T01:00Z', 'intensity': {'forecast': 86, 'actual': 85, 'index': 'low'}},
                     {'from': '2023-05-30T01:00Z', 'to': '2023-05-30T01:30Z', 'intensity': {'forecast': 91, 'actual': 83, 'index': 'low'}}]}


@pytest.fixture
def regional_intensity_mock_df():
    data = {
        'settlementPeriod': [1, 2, 3],
        'regionid': [6]*3,
        'dnoregion': ['region'] * 3,
        'shortname': ['reg'] * 3,
        'from': pd.to_datetime(['2023-05-01 00:00:00', '2023-05-01 00:30:00', '2023-05-01 01:00:00']),
        'to': pd.to_datetime(['2023-05-01T00:30Z', '2023-05-01T01:00Z', '2023-05-01T01:30Z']),
        'regionalIntensity': [50, 60, 70],
        'intensity.index': ['low']*3,
        'settlementDate': pd.to_datetime(['2023-05-30']*3).date,
    }
    return pd.DataFrame(data)

@pytest.fixture
def national_intensity_mock_df():
    data = {
        'settlementPeriod': [1, 2, 3],
        'from': pd.to_datetime(['2023-05-01 00:00:00', '2023-05-01 00:30:00', '2023-05-01 01:00:00']),
        'to': pd.to_datetime(['2023-05-01T00:30Z', '2023-05-01T01:00Z', '2023-05-01T01:30Z']),
        'nationalIntensity': [89, 85, 83],
    }
    return pd.DataFrame(data)

@pytest.fixture
def nationalgrid_api_accessor():
    return NationalGridApiAccessor()

@patch('requests.get')
def test_get_regional_carbon_intensity(requests_get, nationalgrid_api_accessor, regional_intensity_mock_response):
    requests_get.return_value = Mock()
    requests_get.return_value.status_code = 200
    requests_get.return_value.json.return_value = regional_intensity_mock_response

    result = nationalgrid_api_accessor.get_regional_carbon_intensity(datetime(2023, 5, 30), datetime(2023, 5, 31), 6)
    expected = nationalgrid_api_accessor.process_regional_ci_data(requests_get.return_value)
    pd.testing.assert_frame_equal(result, expected)


@patch('requests.get')
def test_get_national_carbon_intensity(requests_get, nationalgrid_api_accessor, national_intensity_mock_response):
    requests_get.return_value = Mock()
    requests_get.return_value.status_code = 200
    requests_get.return_value.json.return_value = national_intensity_mock_response
    result = nationalgrid_api_accessor.get_national_carbon_intensity(datetime(2023, 5, 30), datetime(2023, 5, 31))
    expected = nationalgrid_api_accessor.process_national_ci_data(requests_get.return_value)
    pd.testing.assert_frame_equal(result, expected)


@patch('carbon_abatement_api.nationalgrid_api_accessor.NationalGridApiAccessor.get_regional_carbon_intensity')
@patch('carbon_abatement_api.nationalgrid_api_accessor.NationalGridApiAccessor.get_national_carbon_intensity')
def test_get_carbon_intensity(get_national_carbon_intensity, get_regional_carbon_intensity, nationalgrid_api_accessor, regional_intensity_mock_df, national_intensity_mock_df):
    get_regional_carbon_intensity.return_value = regional_intensity_mock_df
    get_national_carbon_intensity.return_value = national_intensity_mock_df

    result = nationalgrid_api_accessor.get_carbon_intensity('2023-05-30', '2023-05-31', 6, get_regional=True)

    expected = pd.merge(regional_intensity_mock_df, national_intensity_mock_df[['from', 'nationalIntensity']], on='from', how='left')

    pd.testing.assert_frame_equal(result, expected)
