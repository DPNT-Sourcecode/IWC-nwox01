from solutions.HLO.hello_solution import HelloSolution


class TestHello:
    def test_hello_always_returns_hello_world(self) -> None:
        solution = HelloSolution()
        assert solution.hello("John") == "Hello, John!"
        assert solution.hello("Craftsman") == "Hello, Craftsman!"
        assert solution.hello("Mr. X") == "Hello, Mr. X!"
        assert solution.hello("Alice") == "Hello, Alice!"
        assert solution.hello("World") == "Hello, World!"


