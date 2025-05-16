import pandas as pd
import numpy as np
import sqlite3
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from sklearn.linear_model import LinearRegression
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

DATA_SOURCES = {
    'edgar': 'data/edgar_emissions.csv',
    'global_carbon': 'data/global_carbon_atlas.csv',
    'bp_stats': 'data/bp_statistical_review.csv'
}
DB_PATH = "data/emissions.db"
TABLEAU_DATA_EXPORT = "visualization/tableau_emissions_data.csv"

class CO2EmissionsAnalyzer:
    def __init__(self):
        self.engine = create_engine(f'sqlite:///{DB_PATH}')
        self.combined_data = None
        self.hotspots = None
        
    def load_and_clean_data(self):
        """Integrate and clean data from multiple sources"""
        try:
            dfs = []
            for name, path in DATA_SOURCES.items():
                df = pd.read_csv(path)
                df['source'] = name
                dfs.append(self._standardize_format(df))
            
            combined = pd.concat(dfs, ignore_index=True)
            combined = self._clean_combined_data(combined)
        
            combined.to_sql('global_emissions', self.engine, 
                          if_exists='replace', index=False)
            
            self.combined_data = combined
            print(f"Processed {len(combined):,} records from {len(dfs)} sources")
            return True
            
        except Exception as e:
            print(f"Data processing failed: {str(e)}")
            return False
    
    def _standardize_format(self, df):
        """Standardize different dataset formats"""
        column_map = {
            'country': 'country',
            'year': 'year',
            'co2': 'co2_emissions',
            'co2_per_capita': 'co2_per_capita',
            'iso_code': 'country_code'
        }
        
        df = df.rename(columns={k:v for k,v in column_map.items() if k in df.columns})

        if 'co2_emissions' in df.columns:
            if df['co2_emissions'].max() < 1e3:  
                df['co2_emissions'] *= 1e6
            elif df['co2_emissions'].max() < 1e6:  
                df['co2_emissions'] *= 1e3
                
        return df
    
    def _clean_combined_data(self, df):
        """Data cleaning pipeline"""
        df['co2_emissions'] = pd.to_numeric(df['co2_emissions'], errors='coerce')
        
        df = df[df['country'].notna()]
        df = df[df['year'] >= 1970]  
        
        grouped = df.groupby(['country', 'year', 'country_code'], as_index=False).agg({
            'co2_emissions': 'mean',
            'co2_per_capita': 'mean'
        })
        
        grouped.sort_values(['country', 'year'], inplace=True)
        grouped['co2_ma_5yr'] = grouped.groupby('country')['co2_emissions'].transform(
            lambda x: x.rolling(5, min_periods=3).mean()
        )
        
        return grouped
    
    def identify_hotspots(self, start_year=2015):
        """Identify emerging emissions hotspots"""
        try:
            recent = self.combined_data[self.combined_data['year'] >= start_year]
            
            hotspots = []
            for country in recent['country'].unique():
                country_data = recent[recent['country'] == country]
                if len(country_data) < 5:  
                    continue
                
                X = country_data['year'].values.reshape(-1, 1)
                y = country_data['co2_ma_5yr'].values
                
                model = LinearRegression()
                model.fit(X, y)
                
                slope = model.coef_[0]
                _, p_value = stats.linregress(X.flatten(), y)[3:5]
                
                if slope > 0 and p_value < 0.05:  
                    hotspots.append({
                        'country': country,
                        'growth_rate': slope,
                        'p_value': p_value,
                        'recent_emissions': y[-1]
                    })
            
            hotspots_df = pd.DataFrame(hotspots)
            self.hotspots = hotspots_df.sort_values('growth_rate', ascending=False).head(3)
            
            print("\nTop 3 Emerging Hotspots:")
            print(self.hotspots[['country', 'growth_rate']])
            
            return True
            
        except Exception as e:
            print(f"Hotspot analysis failed: {str(e)}")
            return False
    
    def prepare_tableau_data(self):
        """Prepare dataset for Tableau dashboard"""
        try:
            tableau_data = self.combined_data.copy()
            
            tableau_data['is_hotspot'] = tableau_data['country'].isin(
                self.hotspots['country'].values) if self.hotspots is not None else False
            
            Path("visualization").mkdir(exist_ok=True)
            tableau_data.to_csv(TABLEAU_DATA_EXPORT, index=False)
            print(f"\nTableau data exported to {TABLEAU_DATA_EXPORT}")
            
            return True
            
        except Exception as e:
            print(f"Tableau export failed: {str(e)}")
            return False
    
    def generate_visualizations(self):
        """Create exploratory visualizations"""
        try:
            if self.hotspots is not None:
                hotspot_data = self.combined_data[
                    self.combined_data['country'].isin(self.hotspots['country'])
                ]
                
                plt.figure(figsize=(12, 6))
                sns.lineplot(
                    data=hotspot_data,
                    x='year', 
                    y='co2_ma_5yr',
                    hue='country',
                    linewidth=2.5
                )
                plt.title("CO₂ Emissions Growth in Emerging Hotspots")
                plt.ylabel("CO₂ Emissions (metric tons)")
                plt.xlabel("Year")
                plt.grid(True)
                plt.savefig("visualization/hotspots_trend.png")
                plt.close()
            
            latest = self.combined_data[self.combined_data['year'] == 2020]
            fig = px.choropleth(
                latest,
                locations="country_code",
                color="co2_emissions",
                hover_name="country",
                color_continuous_scale="Viridis",
                title="Global CO₂ Emissions by Country (2020)"
            )
            fig.write_html("visualization/global_emissions_map.html")
            
            print("\nGenerated visualizations:")
            print("- Hotspots trend line chart")
            print("- Interactive emissions map")
            
            return True
            
        except Exception as e:
            print(f"Visualization failed: {str(e)}")
            return False

def main():
    analyzer = CO2EmissionsAnalyzer()
    
    print("Loading and cleaning data...")
    if not analyzer.load_and_clean_data():
        return
    
    print("\nIdentifying emission hotspots...")
    if not analyzer.identify_hotspots():
        return

    print("\nPreparing Tableau export...")
    analyzer.prepare_tableau_data()
    
    print("\nGenerating visualizations...")
    analyzer.generate_visualizations()
    
    print("\nProcess completed successfully!")

if __name__ == "__main__":
    from pathlib import Path
    main()