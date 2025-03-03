import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

# Load global CO2 emissions dataset
df = pd.read_csv("annual-co-emissions-by-region.csv")
df = df.rename(columns={"Entity": "country", "Code": "code", "Year": "year", "Annual CO₂ emissions": "total_co2_emissions"})
df = df[['country', 'code', 'year', 'total_co2_emissions']].dropna()
df = df[(df['year'] >= 1990) & (df['year'] <= 2020)]

# Load sector-based emissions dataset
df_sector = pd.read_csv("co-emissions-by-sector.csv")
df_sector = df_sector.rename(columns={
    "Entity": "country",
    "Year": "year",
    "Carbon dioxide emissions from buildings": "Buildings",
    "Carbon dioxide emissions from industry": "Industry",
    "Carbon dioxide emissions from land use change and forestry": "Land Use & Forestry",
    "Carbon dioxide emissions from other fuel combustion": "Other Fuel Combustion",
    "Carbon dioxide emissions from transport": "Transport",
    "Carbon dioxide emissions from manufacturing and construction": "Manufacturing & Construction",
    "Fugitive emissions of carbon dioxide from energy production": "Fugitive Energy Emissions",
    "Carbon dioxide emissions from electricity and heat": "Electricity & Heat",
    "Carbon dioxide emissions from bunker fuels": "Bunker Fuels"
})
# make the years stay between 1990-2020
df_sector = df_sector[(df_sector['year'] >= 1990) & (df_sector['year'] <= 2020)]

# keep only the numeric values for sector dataset
for col in df_sector.columns:
    if col not in ["country", "year"]:
        df_sector[col] = pd.to_numeric(df_sector[col], errors="coerce").apply(lambda x: max(x, 0))

# consistent axis, based on 1990-2020 data only
y_max_sector = 8000000000
co2_max = 15000000000

# new theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MINTY])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("🌍 CO₂ Emissions From 1990-2020", className="text-center text-primary mb-4"), width=12)
    ]),

    # Choropleth Map
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("🌎 Click on a country to view trends below!"),
                dbc.CardBody(dcc.Graph(id="choropleth-map"))
            ], className="shadow-lg"), width=12
        )
    ], className="mb-4"),

    # Country Trends & Sector Breakdown
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("📈 Country Emission Trends"),
                dbc.CardBody(dcc.Graph(id="country-trend"))
            ], className="shadow-lg"), width=6
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("🏭 Sector Breakdown"),
                dbc.CardBody(dcc.Graph(id="sector-breakdown"))
            ], className="shadow-lg"), width=6
        )
    ])
], fluid=True)


# Callbacks
@app.callback(
    Output("country-trend", "figure"),
    Input("choropleth-map", "clickData")
)
def update_country_trend(country_click):
    if country_click is None:
        return px.line(title="Click a country to see its CO₂ trend!")

    country_selected = country_click['points'][0]['location']
    country_df = df[df["country"] == country_selected]

    trend_fig = px.line(
        country_df, x="year", y="total_co2_emissions",
        title=f"Total CO₂ Emissions Over Time: {country_selected}",
        labels={"year": "Year", "total_co2_emissions": "CO₂ Emissions (Tonnes)"},
        template="plotly_white"
    )
    trend_fig.update_layout(yaxis=dict(range=[0, co2_max]))

    return trend_fig


@app.callback(
    Output("sector-breakdown", "figure"),
    [Input("country-trend", "clickData"),
     Input("choropleth-map", "clickData")]
)
def update_sector_breakdown(year_click, country_click):
    if year_click is None or country_click is None:
        return px.bar(title="Click on a year to see sector breakdown!")

    selected_year = year_click['points'][0]['x']
    country_selected = country_click['points'][0]['location']

    sector_df = df_sector[(df_sector["country"] == country_selected) & (df_sector["year"] == selected_year)]
    melted_df = sector_df.melt(id_vars=["country", "year"], var_name="Sector", value_name="Emissions")

    sector_fig = px.bar(
        melted_df, x="Sector", y="Emissions",
        title=f"Sector Breakdown of CO₂ Emissions: {country_selected} ({selected_year})",
        labels={"Sector": "Sector", "Emissions": "CO₂ Emissions (Tonnes)"},
        template="plotly_white"
    )
    sector_fig.update_layout(yaxis=dict(range=[0, y_max_sector]))

    return sector_fig


@app.callback(
    Output("choropleth-map", "figure"),
    [Input("country-trend", "clickData"),
     Input("choropleth-map", "clickData")]
)
def update_choropleth(year_click, country_click):
    if year_click is None:
        latest_year = df["year"].max()
    else:
        latest_year = year_click['points'][0]['x']

    filtered_df = df[df["year"] == latest_year]

    map_fig = px.choropleth(
        filtered_df,
        locations="country",
        locationmode="country names",
        color="total_co2_emissions",
        hover_data={"country": True, "total_co2_emissions": True},
        title=f"Global CO₂ Emissions in {latest_year}",
        color_continuous_scale="Reds",
        range_color=(filtered_df["total_co2_emissions"].min(), 15000000000),
        template="plotly_white"
    )

    # improve how globe looks
    map_fig.update_geos(
        projection_type="natural earth",
        showcoastlines=True,
        coastlinecolor="gray",
        showland=True,
        landcolor="lightgray",
        showocean=True,
        oceancolor="lightblue"
    )

    map_fig.update_layout(
        margin={"r":0, "t":40, "l":0, "b":0},
        coloraxis_colorbar=dict(title="Total CO₂ Emissions (Tonnes)")
    )

    return map_fig

if __name__ == "__main__":
    app.run_server(debug=True)
