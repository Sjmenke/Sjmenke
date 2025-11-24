"""
Rule evaluator for TQQQ Market Regime Detection Framework.
Evaluates logical conditions against market data and indicators.
"""

import re
import pandas as pd
from typing import Dict, Any, Optional, List
import logging
import operator

logger = logging.getLogger(__name__)


class RuleEvaluator:
    """
    Evaluates rule conditions against market data and indicator values.

    Supports conditions like:
    - "QQQ_price > SMA_50"
    - "VIX < 20"
    - "RSI > 40 AND RSI < 70"
    - "MACD > 0"
    """

    # Mapping of operators to functions
    OPERATORS = {
        '>': operator.gt,
        '>=': operator.ge,
        '<': operator.lt,
        '<=': operator.le,
        '==': operator.eq,
        '!=': operator.ne,
    }

    def __init__(self):
        """Initialize the rule evaluator."""
        self.context: Dict[str, Any] = {}

    def set_context(self, context: Dict[str, Any]) -> None:
        """
        Set the evaluation context with current values.

        Args:
            context: Dictionary mapping variable names to their values
                    e.g., {'QQQ_price': 450.0, 'SMA_50': 440.0, 'VIX': 15.5}
        """
        self.context = context
        logger.debug(f"Context set with {len(context)} variables")

    def evaluate_condition(self, condition: str) -> bool:
        """
        Evaluate a single condition.

        Args:
            condition: Condition string (e.g., "QQQ_price > SMA_50")

        Returns:
            True if condition is met, False otherwise
        """
        # Handle 'default' condition (always true)
        if condition.strip().lower() == 'default':
            return True

        try:
            # Handle compound conditions with AND/OR
            if ' AND ' in condition.upper():
                parts = re.split(r'\s+AND\s+', condition, flags=re.IGNORECASE)
                return all(self._evaluate_simple_condition(part.strip()) for part in parts)

            if ' OR ' in condition.upper():
                parts = re.split(r'\s+OR\s+', condition, flags=re.IGNORECASE)
                return any(self._evaluate_simple_condition(part.strip()) for part in parts)

            # Simple condition
            return self._evaluate_simple_condition(condition)

        except Exception as e:
            logger.error(f"Failed to evaluate condition '{condition}': {e}")
            return False

    def _evaluate_simple_condition(self, condition: str) -> bool:
        """
        Evaluate a simple condition (no AND/OR).

        Args:
            condition: Simple condition string (e.g., "VIX < 20")

        Returns:
            True if condition is met, False otherwise
        """
        # Parse the condition
        parsed = self._parse_condition(condition)
        if not parsed:
            logger.warning(f"Could not parse condition: {condition}")
            return False

        left_var, op_str, right_value = parsed

        # Get the value from context
        left_value = self.context.get(left_var)

        if left_value is None:
            logger.warning(f"Variable '{left_var}' not found in context")
            return False

        # Handle NaN values
        if pd.isna(left_value):
            logger.debug(f"Variable '{left_var}' has NaN value")
            return False

        # Get operator function
        op_func = self.OPERATORS.get(op_str)
        if not op_func:
            logger.warning(f"Unknown operator: {op_str}")
            return False

        # Evaluate
        try:
            result = op_func(float(left_value), float(right_value))
            logger.debug(f"Evaluated: {left_var}({left_value}) {op_str} {right_value} = {result}")
            return result
        except (ValueError, TypeError) as e:
            logger.error(f"Error evaluating {left_var} {op_str} {right_value}: {e}")
            return False

    def _parse_condition(self, condition: str) -> Optional[tuple]:
        """
        Parse a condition string into (variable, operator, value).

        Args:
            condition: Condition string (e.g., "VIX < 20")

        Returns:
            Tuple of (variable_name, operator, value) or None if parsing fails
        """
        # Pattern: variable operator value
        # Supports: >, >=, <, <=, ==, !=
        pattern = r'(\w+)\s*(>=|<=|>|<|==|!=)\s*(-?\d+\.?\d*)'

        match = re.match(pattern, condition.strip())
        if match:
            var_name = match.group(1)
            operator_str = match.group(2)
            value_str = match.group(3)

            try:
                value = float(value_str)
                return (var_name, operator_str, value)
            except ValueError:
                return None

        return None

    def evaluate_rules(self, rules: List[str]) -> Dict[str, Any]:
        """
        Evaluate a list of rules.

        Args:
            rules: List of condition strings

        Returns:
            Dictionary with evaluation results:
            - 'passed': Number of rules that passed
            - 'total': Total number of rules
            - 'percentage': Percentage of rules that passed
            - 'results': List of (rule, result) tuples
        """
        results = []
        passed = 0

        for rule in rules:
            result = self.evaluate_condition(rule)
            results.append((rule, result))
            if result:
                passed += 1

        total = len(rules)
        percentage = (passed / total * 100) if total > 0 else 0

        return {
            'passed': passed,
            'total': total,
            'percentage': percentage,
            'results': results
        }

    def check_all_pass(self, rules: List[str]) -> bool:
        """
        Check if all rules pass.

        Args:
            rules: List of condition strings

        Returns:
            True if all rules pass, False otherwise
        """
        return all(self.evaluate_condition(rule) for rule in rules)

    def check_majority_pass(self, rules: List[str], threshold: float = 0.5) -> bool:
        """
        Check if a majority of rules pass.

        Args:
            rules: List of condition strings
            threshold: Minimum percentage of rules that must pass (0.0 to 1.0)

        Returns:
            True if at least threshold percentage of rules pass
        """
        eval_result = self.evaluate_rules(rules)
        return (eval_result['percentage'] / 100) >= threshold

    def check_weighted_pass(
        self,
        rules: List[str],
        weights: List[float],
        threshold: float = 0.5
    ) -> bool:
        """
        Check if weighted sum of rules passes threshold.

        Args:
            rules: List of condition strings
            weights: List of weights for each rule
            threshold: Minimum weighted score to pass (0.0 to 1.0)

        Returns:
            True if weighted score >= threshold
        """
        if len(rules) != len(weights):
            logger.error("Number of rules and weights must match")
            return False

        weighted_sum = 0.0
        total_weight = sum(weights)

        for rule, weight in zip(rules, weights):
            if self.evaluate_condition(rule):
                weighted_sum += weight

        score = weighted_sum / total_weight if total_weight > 0 else 0
        return score >= threshold


class ContextBuilder:
    """
    Builds evaluation context from market data and indicator values.
    """

    @staticmethod
    def build_context(
        ticker_data: Dict[str, pd.DataFrame],
        indicator_values: Dict[str, float],
        date: Optional[pd.Timestamp] = None
    ) -> Dict[str, Any]:
        """
        Build evaluation context.

        Args:
            ticker_data: Dictionary mapping ticker to DataFrame
            indicator_values: Dictionary of indicator name to value
            date: Date to get price data for (if None, uses latest)

        Returns:
            Context dictionary with all available values
        """
        context = {}

        # Add indicator values
        context.update(indicator_values)

        # Add price data for each ticker
        for ticker, df in ticker_data.items():
            if df.empty:
                continue

            try:
                if date is not None:
                    # Get price at specific date
                    if date in df.index:
                        price = df.loc[date, 'close']
                    else:
                        # Find nearest date
                        nearest_idx = df.index.asof(date)
                        if pd.notna(nearest_idx):
                            price = df.loc[nearest_idx, 'close']
                        else:
                            continue
                else:
                    # Get latest price
                    price = df['close'].iloc[-1]

                context[f'{ticker}_price'] = float(price) if pd.notna(price) else None

            except Exception as e:
                logger.warning(f"Could not get price for {ticker}: {e}")
                continue

        # Add some derived values
        if 'SMA_SHORT' in context and 'SMA_LONG' in context:
            context['SMA_GOLDEN_CROSS'] = 1 if context['SMA_SHORT'] > context['SMA_LONG'] else 0

        return context


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.DEBUG)

    # Create evaluator
    evaluator = RuleEvaluator()

    # Set context
    context = {
        'QQQ_price': 450.0,
        'SMA_50': 440.0,
        'SMA_200': 430.0,
        'VIX': 15.5,
        'RSI': 55.0,
        'MACD': 2.5,
    }
    evaluator.set_context(context)

    # Test conditions
    conditions = [
        "QQQ_price > SMA_50",
        "SMA_50 > SMA_200",
        "VIX < 20",
        "RSI > 40 AND RSI < 70",
        "MACD > 0"
    ]

    print("Evaluating conditions:")
    for condition in conditions:
        result = evaluator.evaluate_condition(condition)
        print(f"  {condition}: {result}")

    # Test rule evaluation
    print("\nRule evaluation:")
    eval_result = evaluator.evaluate_rules(conditions)
    print(f"  Passed: {eval_result['passed']}/{eval_result['total']}")
    print(f"  Percentage: {eval_result['percentage']:.1f}%")

    print(f"\nAll pass: {evaluator.check_all_pass(conditions)}")
    print(f"Majority pass (>50%): {evaluator.check_majority_pass(conditions)}")
