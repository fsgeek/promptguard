"""
YAML configuration loader for PromptGuard.

Loads target model lists and evaluation model configurations from YAML files.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional
import yaml


@dataclass
class ModelConfig:
    """
    Configuration for target and evaluation models.

    Attributes:
        target_models: Dictionary mapping RLHF categories to model lists
        evaluation_models: List of models used for post-evaluation analysis
        all_target_models: Flattened list of all target models
    """
    target_models: Dict[str, List[str]]
    evaluation_models: List[str]

    @property
    def all_target_models(self) -> List[str]:
        """Flatten target_models dict into single list."""
        return [
            model
            for models in self.target_models.values()
            for model in models
        ]

    def get_target_models_by_category(self, category: str) -> List[str]:
        """
        Get target models for a specific RLHF category.

        Args:
            category: RLHF category (high_rlhf, moderate_rlhf, low_rlhf, non_rlhf)

        Returns:
            List of model names in that category

        Raises:
            KeyError: If category doesn't exist
        """
        return self.target_models[category]


def load_model_config(config_path: Optional[Path] = None) -> ModelConfig:
    """
    Load model configuration from YAML file.

    Args:
        config_path: Path to YAML config file. If None, uses default location.

    Returns:
        ModelConfig instance with loaded configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file has invalid structure
    """
    # Default to project root config/target_models.yaml
    if config_path is None:
        # Try to find project root by looking for pyproject.toml
        current = Path.cwd()
        while current != current.parent:
            if (current / "pyproject.toml").exists():
                config_path = current / "config" / "target_models.yaml"
                break
            current = current.parent

        # Fallback: relative to this file
        if config_path is None or not config_path.exists():
            config_path = Path(__file__).parent.parent.parent / "config" / "target_models.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Model config not found at {config_path}. "
            "Expected config/target_models.yaml in project root."
        )

    # Load YAML
    with open(config_path) as f:
        data = yaml.safe_load(f)

    # Validate structure
    if "target_models" not in data:
        raise ValueError("Config missing required key: target_models")
    if "evaluation_models" not in data:
        raise ValueError("Config missing required key: evaluation_models")

    return ModelConfig(
        target_models=data["target_models"],
        evaluation_models=data["evaluation_models"]
    )


def load_target_models(
    config_path: Optional[Path] = None,
    category: Optional[str] = None
) -> List[str]:
    """
    Load target model list from YAML config.

    Args:
        config_path: Path to YAML config file
        category: Optional RLHF category filter (high_rlhf, moderate_rlhf, low_rlhf, non_rlhf)

    Returns:
        List of target model names

    Examples:
        # Load all target models
        models = load_target_models()

        # Load only high RLHF models
        models = load_target_models(category="high_rlhf")
    """
    config = load_model_config(config_path)

    if category:
        return config.get_target_models_by_category(category)

    return config.all_target_models


def load_evaluation_models(config_path: Optional[Path] = None) -> List[str]:
    """
    Load evaluation model list from YAML config.

    Args:
        config_path: Path to YAML config file

    Returns:
        List of evaluation model names

    Example:
        models = load_evaluation_models()
    """
    config = load_model_config(config_path)
    return config.evaluation_models
