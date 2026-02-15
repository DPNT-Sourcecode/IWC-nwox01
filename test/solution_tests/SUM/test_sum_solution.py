from solutions.SUM.sum_solution import SumSolution


class TestSum:
    def setup_method(self):
        self.solution = SumSolution()

    def test_basic_addition(self):
        """Test basic addition of two positive numbers."""
        assert self.solution.compute(1, 1) == 2
        assert self.solution.compute(1, 2) == 3
        assert self.solution.compute(5, 7) == 12

    def test_zero_values(self):
        """Test addition with zero."""
        assert self.solution.compute(0, 0) == 0
        assert self.solution.compute(0, 5) == 5
        assert self.solution.compute(5, 0) == 5

    def test_boundary_values(self):
        """Test with boundary values (0-100 range)."""
        assert self.solution.compute(100, 0) == 100
        assert self.solution.compute(0, 100) == 100
        assert self.solution.compute(100, 100) == 200
        assert self.solution.compute(50, 50) == 100

    def test_various_combinations(self):
        """Test various number combinations."""
        assert self.solution.compute(45, 55) == 100
        assert self.solution.compute(23, 77) == 100
        assert self.solution.compute(1, 99) == 100
        assert self.solution.compute(33, 67) == 100


