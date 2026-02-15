from solutions.SUM.sum_solution import SumSolution


class TestSum():
    def test_sum(self) -> None:
        assert SumSolution().compute(1, 2) == 3

