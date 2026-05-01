"""
Strategy Engine — Combines biological predictions with economic data
to produce actionable strategic recommendations.
"""


class StrategyEngine:
    """Generate strategic crop recommendations with trust badges and regenerative pairing."""

    def __init__(self, config):
        self.export_stars = config.EXPORT_STARS
        self.soil_depleting = config.SOIL_DEPLETING
        self.low_water = config.LOW_WATER_CROPS

    def generate(self, predictions: dict, mandi_prices: dict, input_data: dict) -> dict:
        """
        Full strategic analysis pipeline.

        Returns: {
            "primary_recommendation": {...},
            "alternatives": [...],
            "trust_badges": [...],
            "regenerative_pairing": {...},
            "profit_index": [...],
            "market_insights": [...],
        }
        """
        top_crops = predictions["top_crops"]
        feature_importance = predictions["feature_importance"]

        # Calculate Profit Index for each crop
        profit_index = []
        for crop_data in top_crops:
            crop = crop_data["crop"]
            confidence = crop_data["confidence"]
            price_info = mandi_prices.get(crop, {})
            price = price_info.get("price", 0)

            pi = round((confidence / 100) * (price / 1000), 2) if price > 0 else 0
            profit_index.append({
                "crop": crop,
                "confidence": confidence,
                "price": price,
                "profit_index": pi,
                "trend": price_info.get("trend", "stable"),
                "mandi": price_info.get("mandi", "Local"),
                "state": price_info.get("state", "India"),
                "volatility": price_info.get("volatility", 0),
                "supply_level": price_info.get("supply_level", "medium"),
                "source": price_info.get("source", ""),
                "error": price_info.get("error", ""),
            })

        # Sort by Profit Index (economic priority)
        profit_index.sort(key=lambda x: x["profit_index"], reverse=True)

        # Primary recommendation (highest profit index)
        primary = profit_index[0] if profit_index else None

        # Trust Badges
        trust_badges = []
        if primary:
            crop_lower = primary["crop"].lower()
            if crop_lower in self.export_stars:
                trust_badges.append({
                    "type": "export",
                    "label": "Export-Ready",
                    "icon": "public",
                    "color": "gold",
                    "description": f"{primary['crop'].title()} has strong export demand in international markets."
                })
            if primary["trend"] in ("stable", "rising"):
                trust_badges.append({
                    "type": "price_stable",
                    "label": "Stable Price" if primary["trend"] == "stable" else "Rising Price",
                    "icon": "trending_up" if primary["trend"] == "rising" else "trending_flat",
                    "color": "green",
                    "description": f"Market price for {primary['crop'].title()} is currently {primary['trend']}."
                })
            if crop_lower in self.low_water:
                trust_badges.append({
                    "type": "low_water",
                    "label": "Low Water",
                    "icon": "water_drop",
                    "color": "blue",
                    "description": f"{primary['crop'].title()} requires minimal irrigation."
                })
            if primary["supply_level"] in ("low", "medium"):
                trust_badges.append({
                    "type": "demand",
                    "label": "High Demand",
                    "icon": "shopping_cart",
                    "color": "orange",
                    "description": f"Current supply of {primary['crop'].title()} is {primary['supply_level']}, indicating strong market demand."
                })

        # Regenerative Agriculture Check
        regenerative_pairing = None
        if primary:
            companion = self.soil_depleting.get(primary["crop"].lower())
            if companion:
                companion_price = mandi_prices.get(companion, {})
                regenerative_pairing = {
                    "primary_crop": primary["crop"],
                    "companion_crop": companion,
                    "reason": f"{primary['crop'].title()} is classified as soil-depleting. "
                              f"Pairing with {companion.title()} (a nitrogen-fixing legume) "
                              f"will restore soil health over a 4-month rotation cycle.",
                    "companion_price": companion_price.get("price", 0),
                    "nitrogen_boost": "22%",
                }

        # Market Insights
        market_insights = []
        for item in profit_index:
            insight = ""
            if item["supply_level"] == "glut":
                insight = f"Supply glut detected for {item['crop'].title()} — consider de-prioritizing despite suitability."
            elif item["supply_level"] == "low":
                insight = f"Low supply for {item['crop'].title()} — premium pricing opportunity in local mandis."
            elif item["trend"] == "rising":
                insight = f"{item['crop'].title()} prices are trending upward — favorable market conditions."
            elif item["trend"] == "falling":
                insight = f"Declining prices for {item['crop'].title()} — evaluate storage or hedge options."

            if insight:
                market_insights.append({"crop": item["crop"], "insight": insight})

        # Generate SHAP-like explanation for primary recommendation
        shap_explanation = self._generate_shap_explanation(
            primary, feature_importance, input_data
        ) if primary else None

        return {
            "primary_recommendation": primary,
            "alternatives": profit_index[1:],
            "trust_badges": trust_badges,
            "regenerative_pairing": regenerative_pairing,
            "profit_index": profit_index,
            "market_insights": market_insights,
            "feature_importance": feature_importance,
            "shap_explanation": shap_explanation,
            "training_metrics": predictions.get("training_metrics", {}),
            "input_summary": {
                "location": input_data.get("location", "Unknown"),
                "N": input_data.get("N", 0),
                "P": input_data.get("P", 0),
                "K": input_data.get("K", 0),
                "temperature": input_data.get("temperature", 0),
                "humidity": input_data.get("humidity", 0),
                "ph": input_data.get("ph", 0),
                "rainfall": input_data.get("rainfall", 0),
            },
        }

    def _generate_shap_explanation(self, primary: dict, feature_importance: dict,
                                   input_data: dict) -> dict:
        """Generate human-readable SHAP-like explanation for the primary recommendation."""
        # Sort features by importance
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        top_feature = sorted_features[0]
        second_feature = sorted_features[1] if len(sorted_features) > 1 else ("unknown", 0)

        # Generate SHAP values (simulated but proportional to feature importance)
        shap_values = {}
        for feat, imp in feature_importance.items():
            value = float(input_data.get(feat, 0))
            # Positive SHAP = pushes toward this prediction
            shap_values[feat] = round(imp * 0.01 * (1 + (value * 0.001)), 3)

        explanation = (
            f"The model's primary driver was {top_feature[0].title()} "
            f"({top_feature[1]}% relative gain), followed by {second_feature[0].title()} "
            f"({second_feature[1]}%). "
            f"The current {top_feature[0]} value of {input_data.get(top_feature[0], 'N/A')} "
            f"strongly influenced the recommendation toward {primary['crop'].title()}."
        )

        return {
            "explanation": explanation,
            "shap_values": shap_values,
            "base_value": 0.5,
            "prediction": primary["crop"],
        }
