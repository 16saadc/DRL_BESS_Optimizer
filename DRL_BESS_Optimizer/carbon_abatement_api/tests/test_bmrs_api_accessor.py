import pytest
from unittest.mock import Mock, patch
from carbon_abatement_api.bmrs_api_accessor import BmrsApiAccessor
import pandas as pd


@pytest.fixture
def accessor():
    return BmrsApiAccessor()

@pytest.fixture
def pn_df_zero():
    data = {
        'dataset': ['PN'] * 6,
        'settlementDate': pd.to_datetime(['2023-05-31'] * 6),
        'timeFrom': pd.to_datetime(['2023-05-31 00:00', '2023-05-31 00:30', '2023-05-31 01:00', '2023-05-31 01:30', '2023-05-31 02:00', '2023-05-31 02:30'])[::-1],
        'timeTo': pd.to_datetime(['2023-05-31 00:30', '2023-05-31 01:00', '2023-05-31 01:30', '2023-05-31 02:00', '2023-05-31 02:30', '2023-05-31 03:00'])[::-1],
        'settlementPeriod': [6, 5, 4, 3, 2, 1],
        'levelFrom': [-2, -2, 0, 2, 2, 0],
        'levelTo': [0, -2, -2, 0, 2, 2],
    }
    return pd.DataFrame(data)

@pytest.fixture
def pn_df_positive():
    data = {
        'dataset': ['PN'] * 6,
        'settlementDate': pd.to_datetime(['2023-05-31'] * 6),
        'timeFrom': pd.to_datetime(['2023-05-31 00:00', '2023-05-31 00:30', '2023-05-31 01:00', '2023-05-31 01:30', '2023-05-31 02:00', '2023-05-31 02:30'])[::-1],
        'timeTo': pd.to_datetime(['2023-05-31 00:30', '2023-05-31 01:00', '2023-05-31 01:30', '2023-05-31 02:00', '2023-05-31 02:30', '2023-05-31 03:00'])[::-1],
        'settlementPeriod': [6, 5, 4, 3, 2, 1],
        'levelFrom': [-2, -2, 0, 2, 4, 0],
        'levelTo': [0, -2, -2, 0, 2, 4],
    }
    return pd.DataFrame(data)

@pytest.fixture
def pn_df_negative():
    data = {
        'dataset': ['PN'] * 6,
        'settlementDate': pd.to_datetime(['2023-05-31'] * 6),
        'timeFrom': pd.to_datetime(['2023-05-31 00:00', '2023-05-31 00:30', '2023-05-31 01:00', '2023-05-31 01:30', '2023-05-31 02:00', '2023-05-31 02:30'])[::-1],
        'timeTo': pd.to_datetime(['2023-05-31 00:30', '2023-05-31 01:00', '2023-05-31 01:30', '2023-05-31 02:00', '2023-05-31 02:30', '2023-05-31 03:00'])[::-1],
        'settlementPeriod': [6, 5, 4, 3, 2, 1],
        'levelFrom': [-2, -4, 0, 2, 2, 0],
        'levelTo': [0, -4, -2, 0, 2, 2],
    }
    return pd.DataFrame(data)

@pytest.fixture
def pn_df_timediff():
    data = {
        'dataset': ['PN'] * 6,
        'settlementDate': pd.to_datetime(['2023-05-31'] * 6),
        'timeFrom': pd.to_datetime(['2023-05-31 00:00', '2023-05-31 00:10', '2023-05-31 00:30', '2023-05-31 01:00', '2023-05-31 01:20', '2023-05-31 01:30'])[::-1],
        'timeTo': pd.to_datetime(['2023-05-31 00:10', '2023-05-31 00:30', '2023-05-31 01:00', '2023-05-31 01:20', '2023-05-31 01:30', '2023-05-31 02:00'])[::-1],
        'settlementPeriod': [4, 3, 3, 2, 1, 1],
        'levelFrom': [-2, -2, 0, 2, 4, 0],
        'levelTo': [0, -2, -2, 0, 2, 4],
    }

    return pd.DataFrame(data)

def test_process_pn_data(accessor, pn_df_zero):
    result = accessor.process_pn_data(pn_df_zero, '2023-05-31', '2023-06-01')
    assert len(result) == 6
    assert result['energyOut'].sum() == 0
    assert result['timeDifference'].eq(0.5).all()

def test_process_pn_data_time_diff(accessor, pn_df_timediff):
    result = accessor.process_pn_data(pn_df_timediff, '2023-05-31', '2023-06-01')
    assert len(result) == 6
    assert result['timeDifference'].equals(pd.Series([10/60, 20/60, 30/60, 20/60, 10/60, 30/60][::-1]))

def test_process_pn_data_positive_energyOut(accessor, pn_df_positive):
    result = accessor.process_pn_data(pn_df_positive, '2023-05-31', '2023-06-01')
    assert result['energyOut'].sum() == 1
    assert result['energyCharged'].sum() == 2
    assert result['energyDischarged'].sum() == 3

def test_process_pn_data_negative_energyOut(accessor, pn_df_negative):
    result = accessor.process_pn_data(pn_df_negative, '2023-05-31', '2023-06-01')
    assert result['energyOut'].sum() == -1

def test_fill_time_gaps(accessor, pn_df_zero):
    pn_df_zero['timeFrom'] = pd.to_datetime(['2023-05-31 00:00', '2023-05-31 00:30', '2023-05-31 01:00', '2023-05-31 01:30', '2023-05-31 02:30', '2023-05-31 03:00'])[::-1]
    pn_df_zero['timeTo'] = pd.to_datetime(['2023-05-31 00:30', '2023-05-31 01:00', '2023-05-31 01:30', '2023-05-31 02:00', '2023-05-31 03:00', '2023-05-31 03:30'])[::-1]
    result = accessor.process_pn_data(pn_df_zero, '2023-05-31', '2023-06-01')
    assert len(result) == 7  # One gap should be filled

def test_insert_row(accessor, pn_df_zero):
    df_insert = pn_df_zero.iloc[0]
    result = accessor.insert_row(pn_df_zero, 1, df_insert)
    assert len(result) == len(pn_df_zero) + 1  # One row should be inserted

def test_fill_time_gaps_no_gaps(accessor, pn_df_zero):
    result = accessor.process_pn_data(pn_df_zero, '2023-05-31', '2023-06-01')
    assert result.equals(pn_df_zero)

@patch('requests.get')
def test_pn_stream_api_call(mock_get, accessor):
    mock_response = Mock()
    mock_get.return_value = mock_response
    mock_response.status_code = 200
    mock_response.text = '[{"levelFrom":0, "levelTo":-2}]'
    result = accessor.pn_stream_api_call('http://example.com', {})
    assert len(result) == 1


@patch('requests.get')
def test_get_pn_stream_data_error_response(mock_get, accessor):
    mock_response = Mock()
    mock_get.return_value = mock_response
    mock_response.status_code = 400
    mock_response.text = 'Bad request'
    with pytest.raises(Exception) as e_info:
        accessor.get_pn_stream_data('/test-endpoint', '2023-05-31', '2023-06-01')
    assert str(e_info.value) == '400, Bad request'


@patch('requests.get')
def test_get_pn_stream_data_empty_response(mock_get, accessor):
    mock_response = Mock()
    mock_get.return_value = mock_response
    mock_response.status_code = 200
    mock_response.text = '[]'
    with pytest.raises(Exception) as e_info:
        accessor.get_pn_stream_data('/test-endpoint', '2023-05-31', '2023-06-01')
    assert str(e_info.value) == 'No data is available for this BMU between the dates provided'
