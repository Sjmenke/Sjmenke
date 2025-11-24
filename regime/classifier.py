"""
Regime classifier for TQQQ Market Regime Detection Framework.
Classifies market conditions into Bull, Bear, or Choppy regimes.
"""

import yaml
import pandas as pd
from datetime import date
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import logging

from .evaluator import RuleEvaluator, ContextBuilder

logger = logging.getLogger(__name__)


class RegimeClassifier:
    """
    Classifies market regime based on configurable rules.

    Supports three regimes:
    - Bull: Favorable conditions for TQQQ (100% exposure)
    - Bear: Unfavorable conditions (0% exposure)
    - Choppy: Mixed conditions (0-50% exposure)
    """

    VALID_REGIMES = ['bull', 'bear', 'choppy']

    def __init__(self, rules_config: Optional[Dict[str, Any]] = None):
        """
        Initialize regime classifier.

        Args:
            rules_config: Dictionary with regime rules
                         If None, will attempt to load from default config file
        """
        self.rules_config = rules_config or self._load_default_rules()
        self.evaluator = RuleEvaluator()
        self._validate_rules()

    def _load_default_rules(self) -> Dict[str, Any]:
        """
        Load rules from default configuration file.

        Returns:
            Rules configuration dictionary
        """
        config_path = Path(__file__).parent.parent / 'config' / 'regime_rules.yaml'

        if not config_path.exists():
            logger.warning(f"Rules config not found at {config_path}, using minimal defaults")
            return self._get_minimal_rules()

        try:
            with open(config_path, 'r') as f:
                rules = yaml.safe_load(f)
                logger.info(f"Loaded regime rules from {config_path}")
                return rules
        except Exception as e:
            logger.error(f"Failed to load rules config: {e}")
            return self._get_minimal_rules()

    def _get_minimal_rules(self) -> Dict[str, Any]:
        """
        Get minimal default rules.

        Returns:
            Minimal rules configuration
        """
        return {
            'bull': {
                'conditions': ['default'],
                'exposure': 1.0,
                'strategy': 'all_must_pass'
            },
            'bear': {
                'conditions': [],
                'exposure': 0.0,
                'strategy': 'all_must_pass'
            },
            'choppy': {
                'conditions': ['default'],
                'exposure': 0.5,
                'strategy': 'all_must_pass'
            }
        }

    def _validate_rules(self) -> None:
        """Validate rules configuration."""
        for regime in self.VALID_REGIMES:
            if regime not in self.rules_config:
                logger.warning(f"Missing rules for regime: {regime}")
                continue

            regime_config = self.rules_config[regime]

            if 'conditions' not in regime_config:
                raise ValueError(f"Missing 'conditions' for {regime} regime")

            if 'exposure' not in regime_config:
                raise ValueError(f"Missing 'exposure' for {regime} regime")

            exposure = regime_config['exposure']
            if not isinstance(exposure, (int, float)) or exposure < 0 or exposure > 1:
                raise ValueError(f"Invalid exposure for {regime}: {exposure}")

    def classify(self, context: Dict[str, Any]) -> Tuple[str, float, Dict[str, Any]]:
        """
        Classify the current market regime.

        Args:
            context: Dictionary with current market data and indicator values

        Returns:
            Tuple of (regime, confidence_score, details)
            - regime: 'bull', 'bear', or 'choppy'
            - confidence_score: 0.0 to 1.0
            - details: Dictionary with evaluation details for each regime
        """
        self.evaluator.set_context(context)

        regime_scores = {}
        regime_details = {}

        # Evaluate each regime
        for regime in self.VALID_REGIMES:
            if regime not in self.rules_config:
                continue

            regime_config = self.rules_config[regime]
            conditions = regime_config['conditions']
            strategy = regime_config.get('strategy', 'all_must_pass')

            # Evaluate rules
            eval_result = self.evaluator.evaluate_rules(conditions)

            # Calculate score based on strategy
            if strategy == 'all_must_pass':
                passed = eval_result['passed'] == eval_result['total']
                score = 1.0 if passed else 0.0
            elif strategy == 'majority':
                score = eval_result['percentage'] / 100.0
            elif strategy == 'weighted_score':
                # For weighted scoring, assume equal weights if not specified
                weights = regime_config.get('weights', [1.0] * len(conditions))
                total_weight = sum(weights)
                weighted_sum = sum(
                    weight for (_, result), weight in zip(eval_result['results'], weights)
                    if result
                )
                score = weighted_sum / total_weight if total_weight > 0 else 0.0
            else:
                logger.warning(f"Unknown strategy '{strategy}' for {regime}, using all_must_pass")
                passed = eval_result['passed'] == eval_result['total']
                score = 1.0 if passed else 0.0

            regime_scores[regime] = score
            regime_details[regime] = {
                'score': score,
                'rules_passed': eval_result['passed'],
                'total_rules': eval_result['total'],
                'percentage': eval_result['percentage'],
                'exposure': regime_config['exposure'],
                'results': eval_result['results']
            }

        # Determine the regime
        # Priority order: Bear > Bull > Choppy (more conservative approach)
        # Only classify as Bull/Bear if score is high enough
        min_score_threshold = 0.7

        if regime_scores.get('bear', 0) >= min_score_threshold:
            selected_regime = 'bear'
            confidence = regime_scores['bear']
        elif regime_scores.get('bull', 0) >= min_score_threshold:
            selected_regime = 'bull'
            confidence = regime_scores['bull']
        else:
            # Default to choppy if no strong signal
            selected_regime = 'choppy'
            confidence = regime_scores.get('choppy', 0.5)

        logger.info(
            f"Classified regime: {selected_regime.upper()} "
            f"(confidence: {confidence:.2f}, "
            f"bull: {regime_scores.get('bull', 0):.2f}, "
            f"bear: {regime_scores.get('bear', 0):.2f})"
        )

        return selected_regime, confidence, regime_details

    def get_exposure_recommendation(
        self,
        regime: str,
        confidence: float,
        conservative_mode: bool = False
    ) -> float:
        """
        Get recommended TQQQ exposure based on regime and confidence.

        Args:
            regime: Classified regime
            confidence: Confidence score (0-1)
            conservative_mode: If True, reduce exposure in uncertain conditions

        Returns:
            Recommended exposure (0.0 to 1.0)
        """
        if regime not in self.rules_config:
            logger.warning(f"Unknown regime: {regime}, defaulting to 0% exposure")
            return 0.0

        base_exposure = self.rules_config[regime]['exposure']

        if conservative_mode and confidence < 0.8:
            # Reduce exposure if confidence is low
            adjusted_exposure = base_exposure * confidence
            logger.info(
                f"Conservative mode: Adjusted exposure from {base_exposure:.0%} "
                f"to {adjusted_exposure:.0%} due to confidence {confidence:.2f}"
            )
            return adjusted_exposure

        return base_exposure

    def classify_historical(
        self,
        ticker_data: Dict[str, pd.DataFrame],
        indicator_data: Dict[str, pd.DataFrame],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        Classify regime for historical dates.

        Args:
            ticker_data: Dictionary mapping ticker to OHLCV DataFrame
            indicator_data: Dictionary mapping indicator name to values DataFrame
            start_date: Start date for classification
            end_date: End date for classification

        Returns:
            DataFrame with columns: date, regime, confidence, exposure
        """
        # Get date range from the data
        all_dates = set()
        for df in ticker_data.values():
            if not df.empty:
                all_dates.update(df.index)

        if not all_dates:
            logger.error("No data available for classification")
            return pd.DataFrame()

        dates = sorted(all_dates)

        if start_date:
            dates = [d for d in dates if d >= pd.Timestamp(start_date)]
        if end_date:
            dates = [d for d in dates if d <= pd.Timestamp(end_date)]

        results = []

        for date_val in dates:
            # Build context for this date
            indicator_values = {}
            for ind_name, ind_df in indicator_data.items():
                if date_val in ind_df.index and not ind_df.loc[date_val].empty:
                    indicator_values[ind_name] = ind_df.loc[date_val].iloc[0] if isinstance(ind_df.loc[date_val], pd.Series) else ind_df.loc[date_val]

            context = ContextBuilder.build_context(ticker_data, indicator_values, date_val)

            # Classify
            regime, confidence, details = self.classify(context)

            # Get exposure
            exposure = self.get_exposure_recommendation(regime, confidence)

            results.append({
                'date': date_val,
                'regime': regime,
                'confidence': confidence,
                'exposure': exposure
            })

        df = pd.DataFrame(results)
        if not df.empty:
            df.set_index('date', inplace=True)

        return df


def load_classifier_from_config(config_path: Optional[Path] = None) -> RegimeClassifier:
    """
    Load regime classifier from configuration file.

    Args:
        config_path: Path to regime rules YAML file

    Returns:
        Initialized RegimeClassifier instance
    """
    if config_path and config_path.exists():
        with open(config_path, 'r') as f:
            rules = yaml.safe_load(f)
        return RegimeClassifier(rules)
    else:
        return RegimeClassifier()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create classifier
    classifier = RegimeClassifier()

    # Example context
    context = {
        'QQQ_price': 450.0,
        'SMA_50': 440.0,
        'SMA_200': 430.0,
        'VIX': 15.5,
        'RSI': 55.0,
        'MACD': 2.5,
    }

    # Classify
    regime, confidence, details = classifier.classify(context)

    print(f"\nClassified Regime: {regime.upper()}")
    print(f"Confidence: {confidence:.2%}")
    print(f"\nDetails for each regime:")

    for reg, det in details.items():
        print(f"\n{reg.upper()}:")
        print(f"  Score: {det['score']:.2f}")
        print(f"  Rules passed: {det['rules_passed']}/{det['total_rules']}")
        print(f"  Exposure: {det['exposure']:.0%}")

    # Get exposure recommendation
    exposure = classifier.get_exposure_recommendation(regime, confidence)
    print(f"\nRecommended TQQQ Exposure: {exposure:.0%}")
