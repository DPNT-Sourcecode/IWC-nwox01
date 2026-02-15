from solutions.HLO.hello_solution import HelloSolution


class TestHello:
    def test_hello_always_returns_hello_world(self) -> None:
        solution = HelloSolution()
        assert solution.hello("World") == "Hello, World!"
        assert solution.hello("Craftsman") == "Hello, World!"
        assert solution.hello("Mr. X") == "Hello, World!"
        assert solution.hello("") == "Hello, World!"
        assert solution.hello("Anyone") == "Hello, World!"

