from watchdog.services.cost_tracker import calculate_cost


class TestCostCalculation:
    def test_sonnet_cost(self):
        cost = calculate_cost("claude-sonnet-4-5-20250929", input_tokens=1000, output_tokens=500)
        # 1000 input tokens * $3/1M + 500 output tokens * $15/1M
        expected = (1000 / 1_000_000) * 3.0 + (500 / 1_000_000) * 15.0
        assert abs(cost - expected) < 0.0001

    def test_zero_tokens(self):
        cost = calculate_cost("claude-sonnet-4-5-20250929", input_tokens=0, output_tokens=0)
        assert cost == 0.0

    def test_large_call(self):
        cost = calculate_cost("claude-sonnet-4-5-20250929", input_tokens=100_000, output_tokens=4000)
        # Should be a few cents
        assert cost > 0
        assert cost < 1.0

    def test_unknown_model_uses_default(self):
        cost = calculate_cost("unknown-model", input_tokens=1000, output_tokens=1000)
        assert cost > 0
