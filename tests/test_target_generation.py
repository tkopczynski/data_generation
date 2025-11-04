"""Tests for target variable generation."""

import statistics

import pytest

from data_generation.core.generator import generate_data
from data_generation.tools.schema_validation import SchemaValidationError


class TestRuleBasedTargets:
    """Test rule-based target generation."""

    def test_rule_based_single_condition(self):
        """Test single condition with high probability."""
        schema = [
            {"name": "amount", "type": "currency", "config": {"min": 10.0, "max": 10000.0}},
            {
                "name": "is_fraud",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "rule_based",
                        "rules": [
                            {
                                "conditions": [
                                    {"feature": "amount", "operator": ">", "value": 5000}
                                ],
                                "probability": 0.9
                            }
                        ],
                        "default_probability": 0.05,
                    }
                },
            },
        ]

        data = generate_data(schema, 1000)

        # Count fraud for high-value transactions
        high_value_fraud = sum(
            1 for row in data if row["amount"] > 5000 and row["is_fraud"]
        )
        high_value_total = sum(1 for row in data if row["amount"] > 5000)

        if high_value_total > 0:
            fraud_rate = high_value_fraud / high_value_total
            # Should be around 90% ±10%
            assert 0.8 <= fraud_rate <= 1.0, f"Expected ~90% fraud rate, got {fraud_rate:.2%}"

    def test_rule_based_default_probability(self):
        """Test default probability when no rules match."""
        schema = [
            {"name": "amount", "type": "currency", "config": {"min": 10.0, "max": 1000.0}},
            {
                "name": "is_fraud",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "rule_based",
                        "rules": [
                            {
                                "conditions": [
                                    {"feature": "amount", "operator": ">", "value": 5000}
                                ],
                                "probability": 0.9
                            }
                        ],
                        "default_probability": 0.1,
                    }
                },
            },
        ]

        data = generate_data(schema, 1000)

        # All amounts are < 5000, so should use default probability
        fraud_count = sum(1 for row in data if row["is_fraud"])
        fraud_rate = fraud_count / len(data)

        # Should be around 10% ±5%
        assert 0.05 <= fraud_rate <= 0.15, f"Expected ~10% default fraud rate, got {fraud_rate:.2%}"

    def test_rule_based_multiple_conditions_and(self):
        """Test multiple conditions with AND logic."""
        schema = [
            {"name": "amount", "type": "currency", "config": {"min": 10.0, "max": 10000.0}},
            {"name": "hour", "type": "int", "config": {"min": 0, "max": 23}},
            {
                "name": "is_fraud",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "rule_based",
                        "rules": [
                            {
                                "conditions": [
                                    {"feature": "amount", "operator": ">", "value": 5000},
                                    {"feature": "hour", "operator": ">=", "value": 22}
                                ],
                                "probability": 0.9
                            }
                        ],
                        "default_probability": 0.05,
                    }
                },
            },
        ]

        data = generate_data(schema, 1000)

        # Check rule matches (amount > 5000 AND hour >= 22)
        matching_rows = [row for row in data if row["amount"] > 5000 and row["hour"] >= 22]
        if len(matching_rows) > 10:
            fraud_rate = sum(1 for row in matching_rows if row["is_fraud"]) / len(matching_rows)
            assert fraud_rate > 0.7, f"Expected high fraud rate for matching conditions, got {fraud_rate:.2%}"

        # Check non-matching rows use default
        non_matching = [row for row in data if row["amount"] <= 5000 or row["hour"] < 22]
        if len(non_matching) > 100:
            fraud_rate = sum(1 for row in non_matching if row["is_fraud"]) / len(non_matching)
            assert fraud_rate < 0.15, f"Expected low fraud rate for non-matching, got {fraud_rate:.2%}"

    def test_rule_based_multiple_rules_priority(self):
        """Test that first matching rule wins."""
        schema = [
            {"name": "amount", "type": "currency", "config": {"min": 10.0, "max": 10000.0}},
            {"name": "hour", "type": "int", "config": {"min": 0, "max": 23}},
            {
                "name": "is_fraud",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "rule_based",
                        "rules": [
                            {
                                "conditions": [
                                    {"feature": "amount", "operator": ">", "value": 5000},
                                    {"feature": "hour", "operator": ">=", "value": 22}
                                ],
                                "probability": 0.9
                            },
                            {
                                "conditions": [
                                    {"feature": "amount", "operator": ">", "value": 5000}
                                ],
                                "probability": 0.6
                            }
                        ],
                        "default_probability": 0.05,
                    }
                },
            },
        ]

        data = generate_data(schema, 1000)

        # First rule should match (amount > 5000 AND hour >= 22) → 90%
        first_rule_matches = [row for row in data if row["amount"] > 5000 and row["hour"] >= 22]
        if len(first_rule_matches) > 10:
            fraud_rate = sum(1 for row in first_rule_matches if row["is_fraud"]) / len(first_rule_matches)
            assert fraud_rate > 0.7, "First rule should have ~90% fraud rate"

        # Second rule matches (amount > 5000 but hour < 22) → 60%
        second_rule_matches = [row for row in data if row["amount"] > 5000 and row["hour"] < 22]
        if len(second_rule_matches) > 10:
            fraud_rate = sum(1 for row in second_rule_matches if row["is_fraud"]) / len(second_rule_matches)
            assert 0.4 <= fraud_rate <= 0.8, f"Second rule should have ~60% fraud rate, got {fraud_rate:.2%}"

    def test_rule_based_operators(self):
        """Test all supported operators."""
        schema = [
            {"name": "score", "type": "int", "config": {"min": 0, "max": 100}},
            {
                "name": "pass_gt",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "rule_based",
                        "rules": [
                            {
                                "conditions": [{"feature": "score", "operator": ">", "value": 80}],
                                "probability": 1.0
                            }
                        ],
                        "default_probability": 0.0,
                    }
                },
            },
            {
                "name": "pass_gte",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "rule_based",
                        "rules": [
                            {
                                "conditions": [{"feature": "score", "operator": ">=", "value": 60}],
                                "probability": 1.0
                            }
                        ],
                        "default_probability": 0.0,
                    }
                },
            },
        ]

        data = generate_data(schema, 100)

        # Test > operator
        for row in data:
            if row["score"] > 80:
                assert row["pass_gt"] is True, f"Score {row['score']} > 80 should pass"
            else:
                assert row["pass_gt"] is False, f"Score {row['score']} <= 80 should fail"

        # Test >= operator
        for row in data:
            if row["score"] >= 60:
                assert row["pass_gte"] is True, f"Score {row['score']} >= 60 should pass"
            else:
                assert row["pass_gte"] is False, f"Score {row['score']} < 60 should fail"

    def test_rule_based_missing_feature(self):
        """Test that missing features cause condition to fail."""
        schema = [
            {"name": "amount", "type": "currency", "config": {"min": 10.0, "max": 1000.0}},
            {
                "name": "is_fraud",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "rule_based",
                        "rules": [
                            {
                                "conditions": [
                                    {"feature": "nonexistent_field", "operator": ">", "value": 100}
                                ],
                                "probability": 1.0
                            }
                        ],
                        "default_probability": 0.1,
                    }
                },
            },
        ]

        data = generate_data(schema, 100)

        # All should use default probability since condition references missing field
        fraud_rate = sum(1 for row in data if row["is_fraud"]) / len(data)
        assert 0.05 <= fraud_rate <= 0.15, "Should use default probability for missing feature"


class TestProbabilisticTargets:
    """Test probabilistic target generation."""

    def test_probabilistic_positive_weight(self):
        """Test positive feature weight increases probability."""
        schema = [
            {"name": "score", "type": "int", "config": {"min": 0, "max": 100}},
            {
                "name": "pass",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "probabilistic",
                        "base_probability": 0.0,
                        "feature_weights": {"score": 0.01},  # +1% per point
                        "min_probability": 0.0,
                        "max_probability": 1.0,
                    }
                },
            },
        ]

        data = generate_data(schema, 1000)

        # High scores should have higher pass rate
        high_score_pass = sum(1 for row in data if row["score"] >= 80 and row["pass"])
        high_score_total = sum(1 for row in data if row["score"] >= 80)

        low_score_pass = sum(1 for row in data if row["score"] <= 20 and row["pass"])
        low_score_total = sum(1 for row in data if row["score"] <= 20)

        if high_score_total > 0 and low_score_total > 0:
            high_rate = high_score_pass / high_score_total
            low_rate = low_score_pass / low_score_total

            # High scores should have significantly higher pass rate
            assert high_rate > low_rate + 0.3, f"High rate {high_rate:.2%} should exceed low rate {low_rate:.2%} by >30%"

    def test_probabilistic_negative_weight(self):
        """Test negative feature weight decreases probability."""
        schema = [
            {"name": "tenure_months", "type": "int", "config": {"min": 0, "max": 120}},
            {
                "name": "will_churn",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "probabilistic",
                        "base_probability": 0.5,
                        "feature_weights": {"tenure_months": -0.004},  # -0.4% per month
                        "min_probability": 0.0,
                        "max_probability": 1.0,
                    }
                },
            },
        ]

        data = generate_data(schema, 1000)

        # New customers should churn more than long-term customers
        new_churn = sum(1 for row in data if row["tenure_months"] <= 10 and row["will_churn"])
        new_total = sum(1 for row in data if row["tenure_months"] <= 10)

        veteran_churn = sum(1 for row in data if row["tenure_months"] >= 100 and row["will_churn"])
        veteran_total = sum(1 for row in data if row["tenure_months"] >= 100)

        if new_total > 0 and veteran_total > 0:
            new_rate = new_churn / new_total
            veteran_rate = veteran_churn / veteran_total

            assert new_rate > veteran_rate + 0.2, f"New customers ({new_rate:.2%}) should churn more than veterans ({veteran_rate:.2%})"

    def test_probabilistic_multiple_weights(self):
        """Test combining multiple feature weights."""
        schema = [
            {"name": "tenure_months", "type": "int", "config": {"min": 0, "max": 60}},
            {"name": "support_tickets", "type": "int", "config": {"min": 0, "max": 20}},
            {
                "name": "will_churn",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "probabilistic",
                        "base_probability": 0.25,
                        "feature_weights": {
                            "tenure_months": -0.005,  # -0.5% per month
                            "support_tickets": 0.03,   # +3% per ticket
                        },
                        "min_probability": 0.05,
                        "max_probability": 0.90,
                    }
                },
            },
        ]

        data = generate_data(schema, 1000)

        # New customer with many tickets → high churn
        high_risk = [
            row for row in data
            if row["tenure_months"] <= 5 and row["support_tickets"] >= 10
        ]
        if len(high_risk) > 5:
            churn_rate = sum(1 for row in high_risk if row["will_churn"]) / len(high_risk)
            assert churn_rate > 0.5, f"High-risk customers should have high churn rate, got {churn_rate:.2%}"

        # Long-term customer with few tickets → low churn
        low_risk = [
            row for row in data
            if row["tenure_months"] >= 50 and row["support_tickets"] <= 2
        ]
        if len(low_risk) > 5:
            churn_rate = sum(1 for row in low_risk if row["will_churn"]) / len(low_risk)
            assert churn_rate < 0.3, f"Low-risk customers should have low churn rate, got {churn_rate:.2%}"

    def test_probabilistic_clamping(self):
        """Test min/max probability clamping."""
        schema = [
            {"name": "score", "type": "int", "config": {"min": 0, "max": 100}},
            {
                "name": "result",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "probabilistic",
                        "base_probability": 0.5,
                        "feature_weights": {"score": 0.02},  # Would go > 1.0 without clamping
                        "min_probability": 0.1,
                        "max_probability": 0.9,  # Clamped
                    }
                },
            },
        ]

        data = generate_data(schema, 1000)

        # Even with score=100 (prob=0.5+2.0=2.5), should clamp to 0.9
        # So we should never see 100% True for high scores
        very_high_score = [row for row in data if row["score"] >= 95]
        if len(very_high_score) >= 20:
            true_count = sum(1 for row in very_high_score if row["result"])
            # Should be around 90%, not 100%
            assert true_count < len(very_high_score), "Should not be 100% true (clamped to 90%)"

    def test_probabilistic_missing_feature(self):
        """Test that missing features are ignored in weight calculation."""
        schema = [
            {"name": "score", "type": "int", "config": {"min": 50, "max": 50}},  # Fixed value
            {
                "name": "result",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "probabilistic",
                        "base_probability": 0.5,
                        "feature_weights": {
                            "score": 0.01,
                            "nonexistent": 0.5  # Should be ignored
                        },
                        "min_probability": 0.0,
                        "max_probability": 1.0,
                    }
                },
            },
        ]

        data = generate_data(schema, 1000)

        # Probability should be 0.5 + (50 * 0.01) = 1.0 (ignoring nonexistent feature)
        # So nearly all should be True
        true_count = sum(1 for row in data if row["result"])
        true_rate = true_count / len(data)
        assert true_rate > 0.95, f"Expected ~100% true rate, got {true_rate:.2%}"


class TestTargetWithQualityDegradation:
    """Test targets with quality degradation applied."""

    def test_target_with_nulls(self):
        """Test target can have null values via quality_config."""
        schema = [
            {"name": "x", "type": "int", "config": {"min": 1, "max": 10}},
            {
                "name": "y",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "rule_based",
                        "rules": [
                            {
                                "conditions": [{"feature": "x", "operator": ">", "value": 5}],
                                "probability": 1.0
                            }
                        ],
                        "default_probability": 0.0,
                    },
                    "quality_config": {"null_rate": 0.2},
                },
            },
        ]

        data = generate_data(schema, 1000)

        null_count = sum(1 for row in data if row["y"] is None)
        null_rate = null_count / len(data)

        # Should have ~20% nulls ±3%
        assert 0.17 <= null_rate <= 0.23, f"Expected ~20% null rate, got {null_rate:.2%}"

    def test_target_with_duplicates(self):
        """Test target can have duplicates via quality_config."""
        schema = [
            {"name": "x", "type": "int", "config": {"min": 1, "max": 100}},
            {
                "name": "y",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "probabilistic",
                        "base_probability": 0.5,
                        "feature_weights": {},
                    },
                    "quality_config": {"duplicate_rate": 0.3},
                },
            },
        ]

        data = generate_data(schema, 1000)

        # Just verify it doesn't crash and produces valid data
        assert len(data) == 1000
        assert all("y" in row for row in data)


class TestTargetValidation:
    """Test target_config validation."""

    def test_missing_generation_mode(self):
        """Test error when generation_mode is missing."""
        schema = [
            {
                "name": "target",
                "type": "bool",
                "config": {"target_config": {"rules": []}},
            }
        ]

        with pytest.raises(SchemaValidationError, match="generation_mode"):
            generate_data(schema, 10)

    def test_invalid_generation_mode(self):
        """Test error for invalid generation_mode."""
        schema = [
            {
                "name": "target",
                "type": "bool",
                "config": {
                    "target_config": {"generation_mode": "invalid_mode"}
                },
            }
        ]

        with pytest.raises(SchemaValidationError, match="invalid generation_mode"):
            generate_data(schema, 10)

    def test_rule_based_missing_rules(self):
        """Test error when rules are missing."""
        schema = [
            {
                "name": "target",
                "type": "bool",
                "config": {
                    "target_config": {"generation_mode": "rule_based"}
                },
            }
        ]

        with pytest.raises(SchemaValidationError, match="requires 'rules'"):
            generate_data(schema, 10)

    def test_rule_based_missing_conditions(self):
        """Test error when conditions are missing in a rule."""
        schema = [
            {"name": "x", "type": "int", "config": {"min": 1, "max": 10}},
            {
                "name": "target",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "rule_based",
                        "rules": [{"probability": 0.5}]  # Missing conditions
                    }
                },
            }
        ]

        with pytest.raises(SchemaValidationError, match="missing 'conditions'"):
            generate_data(schema, 10)

    def test_rule_based_invalid_operator(self):
        """Test error for invalid operator."""
        schema = [
            {"name": "x", "type": "int", "config": {"min": 1, "max": 10}},
            {
                "name": "target",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "rule_based",
                        "rules": [
                            {
                                "conditions": [
                                    {"feature": "x", "operator": "INVALID", "value": 5}
                                ],
                                "probability": 0.5
                            }
                        ]
                    }
                },
            }
        ]

        with pytest.raises(SchemaValidationError, match="invalid operator"):
            generate_data(schema, 10)

    def test_probabilistic_missing_feature_weights(self):
        """Test error when feature_weights are missing."""
        schema = [
            {
                "name": "target",
                "type": "bool",
                "config": {
                    "target_config": {"generation_mode": "probabilistic"}
                },
            }
        ]

        with pytest.raises(SchemaValidationError, match="requires 'feature_weights'"):
            generate_data(schema, 10)

    def test_invalid_probability_value(self):
        """Test error for probability outside [0, 1]."""
        schema = [
            {"name": "x", "type": "int", "config": {"min": 1, "max": 10}},
            {
                "name": "target",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "rule_based",
                        "rules": [
                            {
                                "conditions": [{"feature": "x", "operator": ">", "value": 5}],
                                "probability": 1.5  # Invalid
                            }
                        ]
                    }
                },
            }
        ]

        with pytest.raises(SchemaValidationError, match="probability must be between 0 and 1"):
            generate_data(schema, 10)


class TestTargetOrdering:
    """Test that features must come before targets."""

    def test_target_can_reference_earlier_features(self):
        """Test that targets can reference all earlier feature columns."""
        schema = [
            {"name": "feature1", "type": "int", "config": {"min": 1, "max": 10}},
            {"name": "feature2", "type": "int", "config": {"min": 1, "max": 10}},
            {
                "name": "target",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "rule_based",
                        "rules": [
                            {
                                "conditions": [
                                    {"feature": "feature1", "operator": ">", "value": 5},
                                    {"feature": "feature2", "operator": ">", "value": 5}
                                ],
                                "probability": 1.0
                            }
                        ],
                        "default_probability": 0.0
                    }
                },
            },
        ]

        data = generate_data(schema, 100)

        # Verify logic works correctly
        for row in data:
            if row["feature1"] > 5 and row["feature2"] > 5:
                assert row["target"] is True
            else:
                assert row["target"] is False


class TestSingleModeConstraint:
    """Test that all targets must use the same generation mode."""

    def test_mixed_modes_raises_error(self):
        """Test that mixing rule_based and probabilistic modes raises an error."""
        schema = [
            {"name": "x", "type": "int", "config": {"min": 1, "max": 10}},
            {
                "name": "target1",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "rule_based",
                        "rules": [
                            {
                                "conditions": [{"feature": "x", "operator": ">", "value": 5}],
                                "probability": 1.0
                            }
                        ]
                    }
                },
            },
            {
                "name": "target2",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "probabilistic",
                        "feature_weights": {"x": 0.1}
                    }
                },
            },
        ]

        with pytest.raises(SchemaValidationError, match="same generation_mode"):
            generate_data(schema, 10)

    def test_same_mode_multiple_targets_allowed(self):
        """Test that multiple targets with the same mode are allowed."""
        schema = [
            {"name": "x", "type": "int", "config": {"min": 1, "max": 10}},
            {
                "name": "target1",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "probabilistic",
                        "feature_weights": {"x": 0.1}
                    }
                },
            },
            {
                "name": "target2",
                "type": "bool",
                "config": {
                    "target_config": {
                        "generation_mode": "probabilistic",
                        "feature_weights": {"x": -0.05}
                    }
                },
            },
        ]

        # Should not raise
        data = generate_data(schema, 100)
        assert len(data) == 100
