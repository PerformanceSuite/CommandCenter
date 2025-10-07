"""
Tests for usage tracking and cost estimation
"""

import pytest
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.usage import UsageTracker


@pytest.fixture
def temp_files(monkeypatch):
    """Create temporary files for testing"""
    import config as config_module

    temp_dir = tempfile.mkdtemp()
    temp_dir_path = Path(temp_dir)

    usage_file = temp_dir_path / "usage.json"
    routing_file = temp_dir_path / "routing_config.json"

    monkeypatch.setattr(config_module, 'USAGE_FILE', usage_file)
    monkeypatch.setattr(config_module, 'ROUTING_CONFIG_FILE', routing_file)

    yield temp_dir_path

    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def tracker(temp_files):
    """Create tracker instance"""
    import tools.usage as usage_module
    usage_module._tracker = None

    from config import ensure_files_exist
    ensure_files_exist()

    return UsageTracker()


class TestUsageTracker:
    """Test usage tracking functionality"""

    def test_track_request(self, tracker):
        """Test tracking an API request"""
        result = tracker.track_request(
            provider="anthropic",
            input_tokens=1000,
            output_tokens=500,
            model="claude-3-5-sonnet-20241022",
            success=True
        )
        assert result["success"] is True
        assert result["provider"] == "anthropic"
        assert result["tokens_used"] == 1500
        assert result["cost"] > 0

    def test_track_multiple_requests(self, tracker):
        """Test tracking multiple requests"""
        tracker.track_request("anthropic", 1000, 500, "claude-3-5-sonnet", True)
        tracker.track_request("anthropic", 2000, 1000, "claude-3-5-sonnet", True)

        stats = tracker.get_usage_stats(provider="anthropic")
        assert stats["total_requests"] == 2
        assert stats["total_input_tokens"] == 3000
        assert stats["total_output_tokens"] == 1500

    def test_get_usage_stats_all_providers(self, tracker):
        """Test getting stats for all providers"""
        tracker.track_request("anthropic", 1000, 500, "claude-3-5-sonnet", True)
        tracker.track_request("openai", 500, 250, "gpt-4", True)

        stats = tracker.get_usage_stats()
        assert stats["success"] is True
        assert stats["total_requests"] == 2
        assert len(stats["providers"]) == 2

    def test_get_usage_stats_single_provider(self, tracker):
        """Test getting stats for single provider"""
        tracker.track_request("anthropic", 1000, 500, "claude-3-5-sonnet", True)

        stats = tracker.get_usage_stats(provider="anthropic")
        assert stats["success"] is True
        assert stats["provider"] == "anthropic"
        assert stats["total_requests"] == 1

    def test_get_usage_stats_nonexistent_provider(self, tracker):
        """Test getting stats for provider with no data"""
        stats = tracker.get_usage_stats(provider="nonexistent")
        assert stats["success"] is False

    def test_estimate_cost(self, tracker):
        """Test cost estimation"""
        result = tracker.estimate_cost(
            provider="anthropic",
            input_tokens=1000,
            output_tokens=500
        )
        assert result["success"] is True
        assert result["provider"] == "anthropic"
        assert "cost_breakdown" in result
        assert result["cost_breakdown"]["total_cost"] > 0

    def test_estimate_cost_zero_cost_provider(self, tracker):
        """Test cost estimation for free provider"""
        result = tracker.estimate_cost(
            provider="local",
            input_tokens=1000,
            output_tokens=500
        )
        assert result["success"] is True
        assert result["cost_breakdown"]["total_cost"] == 0

    def test_estimate_cost_unknown_provider(self, tracker):
        """Test cost estimation for unknown provider"""
        result = tracker.estimate_cost(
            provider="unknown",
            input_tokens=1000,
            output_tokens=500
        )
        assert result["success"] is False

    def test_check_budget_disabled(self, tracker):
        """Test budget check when disabled"""
        # Disable budget
        tracker.routing_config["budget"]["enabled"] = False

        result = tracker.check_budget()
        assert result["success"] is True
        assert result["budget_enabled"] is False

    def test_check_budget_enabled(self, tracker):
        """Test budget check when enabled"""
        # Enable budget
        tracker.routing_config["budget"]["enabled"] = True
        tracker.routing_config["budget"]["daily_limit"] = 10.0
        tracker.routing_config["budget"]["monthly_limit"] = 100.0

        result = tracker.check_budget()
        assert result["success"] is True
        assert result["budget_enabled"] is True
        assert "daily" in result
        assert "monthly" in result

    def test_budget_alert_threshold(self, tracker):
        """Test budget alert threshold"""
        # Set low limits to trigger alert
        tracker.routing_config["budget"]["enabled"] = True
        tracker.routing_config["budget"]["daily_limit"] = 1.0
        tracker.routing_config["budget"]["alert_threshold"] = 0.5

        # Track enough requests to exceed threshold
        for _ in range(100):
            tracker.track_request("anthropic", 1000, 500, "claude-3-5-sonnet", True)

        result = tracker.check_budget()
        # Should show high percentage or alert
        assert result["daily"]["spent"] > 0

    def test_success_rate_calculation(self, tracker):
        """Test success rate calculation"""
        # Track successful and failed requests
        tracker.track_request("anthropic", 1000, 500, "claude-3-5-sonnet", success=True)
        tracker.track_request("anthropic", 1000, 500, "claude-3-5-sonnet", success=True)
        tracker.track_request("anthropic", 1000, 500, "claude-3-5-sonnet", success=False)

        stats = tracker.get_usage_stats(provider="anthropic")
        # Should be 66.67% success rate (2 out of 3)
        assert 60 <= stats["success_rate"] <= 70

    def test_recent_stats(self, tracker):
        """Test recent stats filtering"""
        tracker.track_request("anthropic", 1000, 500, "claude-3-5-sonnet", True)

        stats = tracker.get_usage_stats(provider="anthropic", days=7)
        assert "recent_stats" in stats
        assert stats["recent_stats"]["days"] == 7

    def test_reset_stats_single_provider(self, tracker):
        """Test resetting stats for single provider"""
        tracker.track_request("anthropic", 1000, 500, "claude-3-5-sonnet", True)

        result = tracker.reset_stats(provider="anthropic")
        assert result["success"] is True

        # Verify stats were reset
        stats = tracker.get_usage_stats(provider="anthropic")
        assert stats["success"] is False  # No data should exist

    def test_reset_stats_all_providers(self, tracker):
        """Test resetting all stats"""
        tracker.track_request("anthropic", 1000, 500, "claude-3-5-sonnet", True)
        tracker.track_request("openai", 500, 250, "gpt-4", True)

        result = tracker.reset_stats()
        assert result["success"] is True

        # Verify all stats were reset
        stats = tracker.get_usage_stats()
        assert stats["total_requests"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
