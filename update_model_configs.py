#!/usr/bin/env python3
"""
Update model_configs.json to include Fire Circle models and mark deprecated models.
"""
import json
from pathlib import Path

CONFIG_PATH = Path("/home/tony/projects/promptguard/config/model_configs.json")
FC_CONFIG_PATH = Path("/home/tony/projects/promptguard/config/fire_circle_models.json")

# Load existing config
with open(CONFIG_PATH) as f:
    config = json.load(f)

# Load Fire Circle validation results
with open(FC_CONFIG_PATH) as f:
    fc_config = json.load(f)

# Update metadata
config["metadata"]["last_updated"] = "2025-10-24"
config["metadata"]["note"] = "Updated to include validated Fire Circle models"

# Add Fire Circle tier
config["tier_definitions"]["fire_circle"] = {
    "description": "Validated frontier models for Fire Circle consensus evaluation",
    "cost_range": "$0.0003-$0.315 per Fire Circle participation (3 rounds)"
}

# Models to mark as deprecated (older GPT-4 variants superseded by GPT-5/4.1)
deprecated_model_substrings = ["gpt-4o-2024", "gpt-4o-mini-2024"]

# Mark deprecated models
for model in config["models"]:
    if any(substr in model["id"] for substr in deprecated_model_substrings):
        model["deprecated"] = True
        model["notes"] = model.get("notes", "") + " [DEPRECATED: Superseded by newer models]"

# Add Fire Circle models from validation
fc_models_to_add = []
for fc_model in fc_config["models"]:
    if fc_model["status"] != "available":
        continue  # Skip unavailable models

    # Check if already exists
    existing = any(m["id"] == fc_model["id"] for m in config["models"])
    if existing:
        # Update existing with Fire Circle info
        for model in config["models"]:
            if model["id"] == fc_model["id"]:
                model["fire_circle_validated"] = True
                model["fire_circle_cost_per_eval"] = fc_model["estimated_cost_per_fc_eval"]
                if "fire_circle" not in model.get("recommended_for", []):
                    model.setdefault("recommended_for", []).append("fire_circle")
        continue

    # Determine tier based on cost
    cost = fc_model["estimated_cost_per_fc_eval"]
    if cost < 0.002:
        tier = "budget"
        cost_per_eval = cost / 3  # Approximate single eval cost
    elif cost < 0.010:
        tier = "mid"
        cost_per_eval = cost / 3
    else:
        tier = "premium"
        cost_per_eval = cost / 2.5  # Premium models may have higher input ratio

    # Create new model entry
    new_model = {
        "id": fc_model["id"],
        "name": fc_model["id"].split("/")[-1].replace("-", " ").title(),
        "family": fc_model["id"].split("/")[0].title(),
        "tier": tier,
        "fire_circle_tier": "fire_circle",
        "input_price_per_1m": fc_model["pricing"]["input_per_mtok"],
        "output_price_per_1m": fc_model["pricing"]["output_per_mtok"],
        "cost_per_evaluation": round(cost_per_eval, 6),
        "fire_circle_cost_per_eval": fc_model["estimated_cost_per_fc_eval"],
        "fire_circle_validated": True,
        "capabilities": ["json", "reasoning", "structured_outputs"],
        "recommended_for": ["fire_circle", "comprehensive_testing"],
        "notes": f"Validated for Fire Circle 2025-10-24. {fc_model['notes']}"
    }
    fc_models_to_add.append(new_model)

# Add new Fire Circle models
config["models"].extend(fc_models_to_add)

# Add Fire Circle recommended configurations
config["fire_circle_configurations"] = {
    "small": {
        "description": fc_config["recommended_sets"]["small"]["description"],
        "models": fc_config["recommended_sets"]["small"]["models"],
        "total_cost_per_eval": fc_config["recommended_sets"]["small"]["total_cost_per_eval"],
        "use_cases": ["development", "testing", "quick_validation"]
    },
    "medium": {
        "description": fc_config["recommended_sets"]["medium"]["description"],
        "models": fc_config["recommended_sets"]["medium"]["models"],
        "total_cost_per_eval": fc_config["recommended_sets"]["medium"]["total_cost_per_eval"],
        "use_cases": ["production", "research", "default"],
        "recommended": True
    },
    "large": {
        "description": fc_config["recommended_sets"]["large"]["description"],
        "models": fc_config["recommended_sets"]["large"]["models"],
        "total_cost_per_eval": fc_config["recommended_sets"]["large"]["total_cost_per_eval"],
        "use_cases": ["comprehensive_research", "papers", "maximum_diversity"]
    }
}

# Write updated config
with open(CONFIG_PATH, "w") as f:
    json.dump(config, f, indent=2)

print(f"Updated {CONFIG_PATH}")
print(f"Added {len(fc_models_to_add)} new Fire Circle models")
print(f"Marked {sum(1 for m in config['models'] if m.get('deprecated'))} models as deprecated")
print(f"Total models now: {len(config['models'])}")
print("\nFire Circle configurations added:")
for size, info in config["fire_circle_configurations"].items():
    print(f"  {size.upper()}: {len(info['models'])} models, ${info['total_cost_per_eval']:.4f}/eval")
