# Global-CO-Emissions-Dashboard

---

### 4. CO₂ Emissions Dashboard
**File**: `README.md`

```markdown
# Global CO₂ Emissions Dashboard

![Emissions Map](visualization/world_map.png)

## 🌍 Project Overview
Interactive data visualization platform that:
- Analyzes 50+ years of emissions data
- Identifies 3 key emerging hotspots
- Processes 100K+ records from multiple sources

## 🛠 Setup Instructions

### Data Preparation
```bash
python data/prepare_data.py --sources=edgar,bp,iea

tableau-server --open=visualization/emissions_dashboard.twb
