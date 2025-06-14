# Global CO₂ Emissions Dashboard  
**Goal**: Analyze 50 years of emissions trends and identify hotspots (p < 0.05).  

## **Key Findings**  
- **3 new hotspots** since 2015 (e.g., Country X with rising industrial emissions).  
- SQL-cleaned dataset (95% issues resolved).  

## **How to Run**  
1. Run SQL cleaning: `sqlite3 emissions.db < sql_scripts/data_cleaning.sql`  
2. Generate Tableau dashboard: Open `dashboards/emissions_tableau.twb`  

## **Data Sources**  
- [World Bank](https://data.worldbank.org/)  
- [Our World in Data](https://ourworldindata.org/co2-emissions)  
