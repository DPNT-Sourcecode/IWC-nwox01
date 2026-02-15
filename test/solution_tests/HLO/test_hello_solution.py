from solutions.HLO.hello_solution import HelloSolution


class TestHello:
    def test_hello_with_name(self) -> None:
        solution = HelloSolution()
        assert solution.hello("World") == "Hello, World!"
        assert solution.hello("John") == "Hello, John!"
        assert solution.hello("") == "Hello, !"

    def test_hello_various_names(self) -> None:
        solution = HelloSolution()
        assert solution.hello("Alice") == "Hello, Alice!"
        assert solution.hello("Bob") == "Hello, Bob!"
