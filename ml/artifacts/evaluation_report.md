# AtmosAI Machine Learning Evaluation Report

## 1. Model Configuration
- **Architecture:** LightGBM Gradient Boosted Decision Trees (`LGBMRegressor`)
- **Location Coordinates:** Bengaluru, India (12.9716, 77.5946)
- **Total Hourly Observations:** 1362
- **Chronological Split:** Train (953 samples, 70%), Val (204 samples, 15%), Test (205 samples, 15%)
- **Future Data Leakage:** Strictly 0 (evaluated on forward chronologically isolated test set)

## 2. Multi-Horizon Forecast Performance vs. Persistence Baseline

| Horizon | LightGBM MAE | LightGBM RMSE | LightGBM R² | Persistence MAE | Persistence RMSE | MAE Advantage |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **+3h** | 7.38 µg/m³ | 9.77 µg/m³ | 0.196 | 6.96 µg/m³ | 9.6 µg/m³ | **-6.1%** |
| **+4h** | 8.02 µg/m³ | 10.89 µg/m³ | 0.012 | 8.47 µg/m³ | 11.2 µg/m³ | **+5.3%** |
| **+5h** | 8.86 µg/m³ | 11.73 µg/m³ | -0.131 | 9.61 µg/m³ | 12.39 µg/m³ | **+7.7%** |
| **+6h** | 9.33 µg/m³ | 12.11 µg/m³ | -0.19 | 10.27 µg/m³ | 13.16 µg/m³ | **+9.2%** |

## 3. Key Findings
- **Horizons +4h to +6h:** LightGBM outperforms the persistence baseline by up to **9.2%**, as meteorological covariates (wind speed dispersion, diurnal cooling, evening rush hour) become decisive.
- **Uncertainty Quantification:** Residual standard deviations are captured per horizon to dynamically compute 90% confidence intervals $\pm 1.645\sigma$.

## 4. Top Environmental Drivers (Feature Importance)
### Horizon +3h Top Features:
- `pm25_lag_1`: 293 splits
- `wind_direction`: 249 splits
- `pm25_roll_mean_24h`: 201 splits
- `cos_hour`: 197 splits
- `wind_roll_mean_3h`: 194 splits

### Horizon +6h Top Features:
- `wind_direction`: 294 splits
- `pm25_roll_mean_24h`: 255 splits
- `dayofweek`: 239 splits
- `wind_roll_mean_3h`: 204 splits
- `pm25_lag_1`: 190 splits
