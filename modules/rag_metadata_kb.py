"""
rag_metadata_kb.py
-------------------
Knowledge base of real-world Harvard Dataverse metadata examples.

Each entry has:
  - text:     Semantic signature used for similarity matching against a new file.
              Write it like a description of the dataset content and columns.
  - metadata: Template metadata dict (title / description / keywords / subject /
              geographic_coverage / time_period_start / time_period_end /
              data_source / license).

These entries cover the domains most relevant to MASBIO and similar
environmental / biomass / life-sciences research projects.
"""

from __future__ import annotations
from typing import List, Dict, Any

KNOWLEDGE_BASE: List[Dict[str, Any]] = [

    # ── 1. FAOSTAT Forestry biomass production ───────────────────────────────
    {
        "text": (
            "forestry production wood fuel roundwood biomass tonnes area country year "
            "FAOSTAT FAO forest coniferous non-coniferous production quantity"
        ),
        "metadata": {
            "title": "Global Forestry Biomass Production Statistics (FAOSTAT)",
            "description": (
                "Annual forestry biomass production data from FAO FAOSTAT, covering "
                "wood fuel, roundwood, and coniferous/non-coniferous outputs by country. "
                "Data sourced from national reporting to the Food and Agriculture "
                "Organization of the United Nations."
            ),
            "keywords": ["forestry", "biomass", "wood fuel", "roundwood", "FAOSTAT", "FAO"],
            "subject": "Earth and Environmental Sciences",
            "geographic_coverage": "Global",
            "time_period_start": "1961",
            "time_period_end": "2022",
            "data_source": "FAO FAOSTAT Forestry Production and Trade",
            "license": "CC0 1.0",
        },
    },

    # ── 2. Marine / saltwater biomass sensor data ────────────────────────────
    {
        "text": (
            "marine ocean saltwater biomass pH dissolved oxygen turbidity salinity "
            "temperature depth sensor measurement aquatic seawater coastal"
        ),
        "metadata": {
            "title": "Marine Biomass Sensor Measurements — Water Quality Parameters",
            "description": (
                "Field sensor measurements from marine and saltwater environments, "
                "including pH, dissolved oxygen, turbidity, salinity, and temperature "
                "recorded at multiple coastal monitoring stations. Data supports "
                "marine biomass productivity assessment."
            ),
            "keywords": ["marine", "biomass", "salinity", "dissolved oxygen", "pH", "sensor"],
            "subject": "Earth and Environmental Sciences",
            "geographic_coverage": "Coastal Marine Environments",
            "time_period_start": "2020",
            "time_period_end": "2024",
            "data_source": "MASBIO Field Sensor Network",
            "license": "CC0 1.0",
        },
    },

    # ── 3. Agricultural crop production ─────────────────────────────────────
    {
        "text": (
            "crop production yield harvest area tonnes hectares maize wheat rice "
            "soybean agricultural country region year FAOSTAT cereals food"
        ),
        "metadata": {
            "title": "Agricultural Crop Production and Yield Statistics",
            "description": (
                "Annual crop production data covering yield, harvested area, and "
                "production quantity for major cereal and food crops across countries "
                "and regions. Includes maize, wheat, rice, and soybean production "
                "metrics sourced from national agricultural statistics."
            ),
            "keywords": ["crop", "agriculture", "yield", "production", "cereals", "FAOSTAT"],
            "subject": "Agricultural Sciences",
            "geographic_coverage": "Global",
            "time_period_start": "1961",
            "time_period_end": "2023",
            "data_source": "FAO FAOSTAT Crops and Livestock Products",
            "license": "CC0 1.0",
        },
    },

    # ── 4. Bioenergy / biofuel production ────────────────────────────────────
    {
        "text": (
            "bioenergy biofuel ethanol biodiesel renewable energy production "
            "feedstock lignocellulosic biogas biomethane energy crops GJ TJ"
        ),
        "metadata": {
            "title": "Bioenergy and Biofuel Production Statistics",
            "description": (
                "National and regional production data for bioenergy carriers including "
                "bioethanol, biodiesel, biogas, and biomethane. Covers feedstock inputs, "
                "energy outputs in gigajoules, and production capacity across reporting "
                "countries under IEA and Eurostat frameworks."
            ),
            "keywords": ["bioenergy", "biofuel", "ethanol", "biodiesel", "renewable energy", "biomethane"],
            "subject": "Earth and Environmental Sciences",
            "geographic_coverage": "Global",
            "time_period_start": "2000",
            "time_period_end": "2023",
            "data_source": "IEA Bioenergy / Eurostat Energy Statistics",
            "license": "CC0 1.0",
        },
    },

    # ── 5. Carbon emissions & GHG ────────────────────────────────────────────
    {
        "text": (
            "carbon emissions CO2 greenhouse gas GHG methane nitrous oxide "
            "LULUCF land use forestry sector tonne CO2e climate change"
        ),
        "metadata": {
            "title": "Greenhouse Gas Emissions by Sector and Country",
            "description": (
                "Annual greenhouse gas emission inventories including CO₂, CH₄, and "
                "N₂O by sector (energy, agriculture, LULUCF, waste). Data compiled from "
                "national GHG inventories submitted to the UNFCCC, expressed in "
                "CO₂-equivalent tonnes."
            ),
            "keywords": ["GHG", "carbon emissions", "CO2", "climate change", "UNFCCC", "LULUCF"],
            "subject": "Earth and Environmental Sciences",
            "geographic_coverage": "Global",
            "time_period_start": "1990",
            "time_period_end": "2022",
            "data_source": "UNFCCC National GHG Inventories",
            "license": "CC0 1.0",
        },
    },

    # ── 6. Water quality monitoring ──────────────────────────────────────────
    {
        "text": (
            "water quality river lake freshwater pH conductivity nitrate phosphate "
            "turbidity dissolved oxygen monitoring station measurement mg/L"
        ),
        "metadata": {
            "title": "Freshwater Quality Monitoring — Physicochemical Parameters",
            "description": (
                "Longitudinal water quality measurements from freshwater monitoring "
                "stations including pH, electrical conductivity, nitrate, phosphate, "
                "and dissolved oxygen concentrations. Data supports assessment of "
                "aquatic ecosystem health and eutrophication risk."
            ),
            "keywords": ["water quality", "freshwater", "nitrate", "phosphate", "pH", "monitoring"],
            "subject": "Earth and Environmental Sciences",
            "geographic_coverage": "Europe",
            "time_period_start": "2010",
            "time_period_end": "2023",
            "data_source": "European Environment Agency (EEA) Water Quality Database",
            "license": "CC0 1.0",
        },
    },

    # ── 7. Land use & land cover change ─────────────────────────────────────
    {
        "text": (
            "land use land cover forest cropland grassland urban wetland "
            "deforestation LULUCF area hectares change satellite remote sensing"
        ),
        "metadata": {
            "title": "Land Use and Land Cover Change Statistics",
            "description": (
                "Temporal land use and land cover change data derived from satellite "
                "remote sensing and national inventories. Covers transitions between "
                "forest, cropland, grassland, wetland, and urban land classes with "
                "area estimates in hectares."
            ),
            "keywords": ["land use", "land cover", "deforestation", "LULUCF", "remote sensing", "forest"],
            "subject": "Earth and Environmental Sciences",
            "geographic_coverage": "Global",
            "time_period_start": "2000",
            "time_period_end": "2020",
            "data_source": "FAO Global Forest Resources Assessment / ESA CCI Land Cover",
            "license": "CC0 1.0",
        },
    },

    # ── 8. Fisheries & aquaculture ───────────────────────────────────────────
    {
        "text": (
            "fisheries catch aquaculture fish species tonnes production "
            "marine freshwater FAO fishing area capture wild harvest"
        ),
        "metadata": {
            "title": "Global Fisheries Capture and Aquaculture Production",
            "description": (
                "Annual fisheries statistics covering wild capture and aquaculture "
                "production by species, fishing area, and country. Data sourced from "
                "FAO FishStat database and covers both marine and inland freshwater "
                "fisheries in metric tonnes."
            ),
            "keywords": ["fisheries", "aquaculture", "capture", "fish production", "FAO", "FishStat"],
            "subject": "Agricultural Sciences",
            "geographic_coverage": "Global",
            "time_period_start": "1950",
            "time_period_end": "2021",
            "data_source": "FAO FishStat",
            "license": "CC0 1.0",
        },
    },

    # ── 9. Climate / meteorological data ────────────────────────────────────
    {
        "text": (
            "climate temperature precipitation rainfall wind speed humidity "
            "weather station meteorological monthly annual average min max"
        ),
        "metadata": {
            "title": "Meteorological Climate Observations Dataset",
            "description": (
                "Long-term meteorological observations from weather stations including "
                "daily and monthly averages of air temperature, precipitation, wind "
                "speed, and relative humidity. Data compiled from WMO Global Climate "
                "Observing System station network."
            ),
            "keywords": ["climate", "temperature", "precipitation", "meteorology", "WMO", "weather"],
            "subject": "Earth and Environmental Sciences",
            "geographic_coverage": "Global",
            "time_period_start": "1950",
            "time_period_end": "2023",
            "data_source": "WMO / NOAA Global Surface Summary of the Day",
            "license": "CC0 1.0",
        },
    },

    # ── 10. Biodiversity / species occurrence ────────────────────────────────
    {
        "text": (
            "biodiversity species occurrence abundance richness taxonomy "
            "GBIF iNaturalist observation habitat ecosystem survey"
        ),
        "metadata": {
            "title": "Biodiversity Species Occurrence and Abundance Records",
            "description": (
                "Species occurrence, abundance, and richness records from field surveys "
                "and citizen science platforms. Includes taxonomic classification, "
                "observation coordinates, date, and habitat type. Data supports "
                "biodiversity assessment and conservation planning."
            ),
            "keywords": ["biodiversity", "species", "occurrence", "GBIF", "taxonomy", "habitat"],
            "subject": "Medicine, Health and Life Sciences",
            "geographic_coverage": "Global",
            "time_period_start": "2000",
            "time_period_end": "2023",
            "data_source": "GBIF / iNaturalist",
            "license": "CC0 1.0",
        },
    },

    # ── 11. Algae / microalgae biomass ───────────────────────────────────────
    {
        "text": (
            "algae microalgae seaweed macroalgae biomass cultivation growth rate "
            "chlorophyll photosynthesis lipid protein productivity pond reactor"
        ),
        "metadata": {
            "title": "Microalgae and Seaweed Biomass Productivity Dataset",
            "description": (
                "Experimental and field measurements of microalgae and macroalgae "
                "biomass productivity, including growth rates, chlorophyll content, "
                "lipid and protein yields from cultivation systems. Supports research "
                "into algal bioenergy and blue bioeconomy applications."
            ),
            "keywords": ["algae", "microalgae", "seaweed", "biomass", "bioenergy", "blue economy"],
            "subject": "Earth and Environmental Sciences",
            "geographic_coverage": "Global",
            "time_period_start": "2010",
            "time_period_end": "2024",
            "data_source": "MASBIO Research Data / Literature Synthesis",
            "license": "CC0 1.0",
        },
    },

    # ── 12. Renewable energy statistics ─────────────────────────────────────
    {
        "text": (
            "renewable energy solar wind hydropower capacity installed MW GW "
            "electricity generation TWh country year IRENA IEA"
        ),
        "metadata": {
            "title": "Renewable Energy Capacity and Generation Statistics",
            "description": (
                "National installed capacity and electricity generation statistics for "
                "renewable energy sources including solar PV, onshore and offshore wind, "
                "hydropower, and geothermal. Data sourced from IRENA and IEA annual "
                "energy statistics, expressed in MW capacity and TWh generation."
            ),
            "keywords": ["renewable energy", "solar", "wind", "hydropower", "capacity", "IRENA"],
            "subject": "Earth and Environmental Sciences",
            "geographic_coverage": "Global",
            "time_period_start": "2000",
            "time_period_end": "2023",
            "data_source": "IRENA Renewable Energy Statistics / IEA",
            "license": "CC0 1.0",
        },
    },

    # ── 13. Soil quality & organic carbon ───────────────────────────────────
    {
        "text": (
            "soil organic carbon nitrogen pH texture clay sand silt bulk density "
            "fertility quality horizon profile land degradation"
        ),
        "metadata": {
            "title": "Soil Physical and Chemical Properties Dataset",
            "description": (
                "Soil profile measurements including organic carbon content, total "
                "nitrogen, pH, texture fractions (clay, silt, sand), and bulk density "
                "from field sampling campaigns. Data supports land degradation assessment "
                "and carbon stock estimation."
            ),
            "keywords": ["soil", "organic carbon", "nitrogen", "texture", "land degradation", "carbon stock"],
            "subject": "Earth and Environmental Sciences",
            "geographic_coverage": "Global",
            "time_period_start": "1990",
            "time_period_end": "2020",
            "data_source": "FAO ISRIC World Soil Database / LUCAS",
            "license": "CC0 1.0",
        },
    },

    # ── 14. Trade statistics (commodities) ───────────────────────────────────
    {
        "text": (
            "trade import export commodity value USD tonnes country year "
            "bilateral flow product HS code COMTRADE WTO"
        ),
        "metadata": {
            "title": "International Commodity Trade Statistics",
            "description": (
                "Bilateral import and export flows for agricultural and environmental "
                "commodities by country, partner, and year. Includes trade value in USD "
                "and quantity in metric tonnes, classified by HS commodity codes. "
                "Sourced from UN Comtrade database."
            ),
            "keywords": ["trade", "import", "export", "commodity", "Comtrade", "HS code"],
            "subject": "Social Sciences",
            "geographic_coverage": "Global",
            "time_period_start": "1995",
            "time_period_end": "2023",
            "data_source": "UN Comtrade / FAO FAOSTAT Trade",
            "license": "CC0 1.0",
        },
    },

    # ── 15. Air quality / atmospheric ────────────────────────────────────────
    {
        "text": (
            "air quality PM2.5 PM10 NO2 ozone SO2 particulate matter "
            "atmospheric concentration ppb μg/m3 monitoring station AQI"
        ),
        "metadata": {
            "title": "Ambient Air Quality Monitoring Measurements",
            "description": (
                "Continuous ambient air quality measurements from monitoring networks "
                "including PM2.5, PM10, NO₂, ozone, and SO₂ concentrations. Data "
                "expressed in μg/m³ and ppb at hourly and daily resolutions from "
                "urban and rural monitoring stations."
            ),
            "keywords": ["air quality", "PM2.5", "PM10", "NO2", "ozone", "pollution"],
            "subject": "Earth and Environmental Sciences",
            "geographic_coverage": "Europe",
            "time_period_start": "2010",
            "time_period_end": "2023",
            "data_source": "EEA AirBase / WHO Air Quality Database",
            "license": "CC0 1.0",
        },
    },

    # ── 16. Population & demographics ────────────────────────────────────────
    {
        "text": (
            "population demographics age gender income urban rural census "
            "household country region year World Bank UN"
        ),
        "metadata": {
            "title": "Population and Demographic Indicators by Country",
            "description": (
                "Annual population and demographic indicators including total population, "
                "age structure, urbanisation rate, and household income by country and "
                "region. Data compiled from UN World Population Prospects and World "
                "Bank Development Indicators."
            ),
            "keywords": ["population", "demographics", "urbanisation", "World Bank", "UN", "census"],
            "subject": "Social Sciences",
            "geographic_coverage": "Global",
            "time_period_start": "1960",
            "time_period_end": "2023",
            "data_source": "UN World Population Prospects / World Bank WDI",
            "license": "CC0 1.0",
        },
    },

    # ── 17. Forest carbon / REDD+ ────────────────────────────────────────────
    {
        "text": (
            "forest carbon stock biomass above-ground below-ground REDD+ "
            "deforestation degradation sequestration tCO2 national inventory"
        ),
        "metadata": {
            "title": "Forest Carbon Stock and Biomass Inventory",
            "description": (
                "National forest carbon stock estimates covering above-ground and "
                "below-ground biomass, dead wood, litter, and soil organic carbon. "
                "Data compiled from national forest inventory reports submitted under "
                "UNFCCC and FAO Global Forest Resources Assessment."
            ),
            "keywords": ["forest carbon", "biomass", "REDD+", "carbon stock", "deforestation", "sequestration"],
            "subject": "Earth and Environmental Sciences",
            "geographic_coverage": "Global",
            "time_period_start": "1990",
            "time_period_end": "2020",
            "data_source": "FAO Global Forest Resources Assessment / UNFCCC",
            "license": "CC0 1.0",
        },
    },

    # ── 18. Health / epidemiology ────────────────────────────────────────────
    {
        "text": (
            "health disease mortality morbidity incidence prevalence hospital "
            "patient clinical trial treatment outcome epidemiology WHO"
        ),
        "metadata": {
            "title": "Public Health Epidemiological Indicators Dataset",
            "description": (
                "Epidemiological data on disease incidence, mortality, and morbidity "
                "rates by country, age group, and year. Includes WHO reportable "
                "diseases, non-communicable disease burden, and healthcare utilisation "
                "metrics from national health information systems."
            ),
            "keywords": ["health", "epidemiology", "mortality", "disease", "WHO", "morbidity"],
            "subject": "Medicine, Health and Life Sciences",
            "geographic_coverage": "Global",
            "time_period_start": "2000",
            "time_period_end": "2023",
            "data_source": "WHO Global Health Observatory",
            "license": "CC0 1.0",
        },
    },

    # ── 19. Ocean / sea surface data ─────────────────────────────────────────
    {
        "text": (
            "ocean sea surface temperature SST chlorophyll primary productivity "
            "MODIS satellite oceanography bathymetry salinity current"
        ),
        "metadata": {
            "title": "Ocean Surface Temperature and Chlorophyll Remote Sensing Data",
            "description": (
                "Satellite-derived ocean surface parameters including sea surface "
                "temperature (SST), chlorophyll-a concentration, and primary "
                "productivity estimates. Data sourced from MODIS-Aqua and Sentinel-3 "
                "ocean colour products at monthly resolution."
            ),
            "keywords": ["ocean", "SST", "chlorophyll", "remote sensing", "MODIS", "primary productivity"],
            "subject": "Earth and Environmental Sciences",
            "geographic_coverage": "Global Oceans",
            "time_period_start": "2002",
            "time_period_end": "2023",
            "data_source": "NASA MODIS-Aqua / ESA Sentinel-3 OLCI",
            "license": "CC0 1.0",
        },
    },

    # ── 20. Energy policy & governance documents ─────────────────────────────
    {
        "text": (
            "energy policy legislation directive regulation governance document "
            "EU RED CORSIA sustainability criteria biofuel mandate"
        ),
        "metadata": {
            "title": "Bioenergy Governance and Policy Document Collection",
            "description": (
                "Curated collection of regulatory and policy documents governing "
                "bioenergy sustainability, including EU Renewable Energy Directive "
                "(RED III), CORSIA sustainability criteria, and national biofuel "
                "mandates. Annotated with jurisdiction, year, and policy scope."
            ),
            "keywords": ["policy", "governance", "bioenergy", "EU RED", "CORSIA", "sustainability"],
            "subject": "Social Sciences",
            "geographic_coverage": "European Union / Global",
            "time_period_start": "2009",
            "time_period_end": "2024",
            "data_source": "EUR-Lex / ICAO / National Legislation",
            "license": "CC0 1.0",
        },
    },
]
