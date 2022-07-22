from typing import Optional, Union
import pytest

from helpermodules import timecheck


class Params:
    def __init__(self, name: str,
                 first_time: str,
                 expected_return: Union[int, str],
                 second_time: Optional[str] = "") -> None:
        self.name = name
        self.first_time = first_time
        self.expected_return = expected_return
        if second_time:
            self.second_time = second_time


# cases_get_difference_to_now = [
#     Params("get_difference_to_now_minutes_before", "02/18/2022, 10:42:23", expected_return="87"),
#     Params("get_difference_to_now_minutes_after", "02/18/2022, 10:50:45",  expected_return="469"),
#     Params("get_difference_to_now_hours", "02/18/2022, 10:42:56",  expected_return="8651"),
#     Params("get_difference_to_now_days", "02/16/2022, 08:18:45", expected_return="164149"),
# ]
cases_get_difference = [
    Params("get_difference_minutes_before", "02/18/2022, 10:42:23",
           second_time="02/18/2022, 10:40:56", expected_return=87),
    Params("get_difference_minutes_after", "02/18/2022, 10:50:45",
           second_time="02/18/2022, 10:42:56", expected_return=469),
    Params("get_difference_hours", "02/18/2022, 10:42:56", second_time="02/18/2022, 08:18:45", expected_return=8651),
    Params("get_difference_days", "02/18/2022, 08:18:45", second_time="02/16/2022, 10:42:56", expected_return=164149),
]

cases_duration_sum = [
    Params("duration_sum_minutes", "00:23", second_time="00:56", expected_return="1:19"),
    Params("duration_sum_hours", "08:18", second_time="01:56", expected_return="10:14"),
    Params("duration_sum_days", "18:8", second_time="10:24", expected_return="28:32"),
]

# @pytest.fixture(autouse=True)
# def set_up(monkeypatch):
#     mock_today = Mock(name="today", return_value="02/18/2022, 10:42")
#     monkeypatch.setattr(datetime, "today", mock_today)


@pytest.mark.parametrize("params", cases_get_difference, ids=[c.name for c in cases_get_difference])
def test_get_difference(params: Params):
    # execution
    diff = timecheck.get_difference(params.first_time, params.second_time)

    # evaluation
    assert params.expected_return == diff


@pytest.mark.parametrize("params", cases_duration_sum, ids=[c.name for c in cases_duration_sum])
def test_duration_sum(params: Params):
    # execution
    diff = timecheck.duration_sum(params.first_time, params.second_time)

    # evaluation
    assert params.expected_return == diff
