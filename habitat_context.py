"""Read-only terrain and mapped-infrastructure context for a field location."""

from math import asin, cos, radians, sin, sqrt
from typing import Any

import requests


OPEN_METEO_ELEVATION_URL = "https://api.open-meteo.com/v1/elevation"
OPEN_METEO_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OVERPASS_URLS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)
MAX_INFRASTRUCTURE_RADIUS_M = 1_000


def habitat_profile(latitude: float, longitude: float, requested_radius_km: int) -> dict[str, Any]:
    """Return a transparent, read-only terrain and OSM-infrastructure summary."""
    validate_coordinates(latitude, longitude)
    radius_m = min(max(int(requested_radius_km * 1000), 100), MAX_INFRASTRUCTURE_RADIUS_M)
    elevations = nearby_elevations(latitude, longitude)
    osm_summary = mapped_infrastructure(latitude, longitude, radius_m)
    climate_summary = climate_context(latitude, longitude)
    return {
        "latitude": latitude,
        "longitude": longitude,
        "radius_m": radius_m,
        "elevation_m": round(elevations[0]) if elevations else None,
        "elevation_samples_m": [round(value, 1) for value in elevations],
        "local_relief_m": round(max(elevations) - min(elevations)) if len(elevations) > 1 else None,
        **osm_summary,
        **climate_summary,
    }


def climate_context(latitude: float, longitude: float) -> dict[str, Any]:
    """Estimate Köppen climate and potential vegetation from 1991-2020 daily normals."""
    try:
        response = requests.get(
            OPEN_METEO_ARCHIVE_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "start_date": "1991-01-01",
                "end_date": "2020-12-31",
                "daily": "temperature_2m_mean,precipitation_sum",
                "timezone": "UTC",
            },
            timeout=30,
        )
        response.raise_for_status()
        daily = response.json().get("daily", {})
        temperatures, precipitation = monthly_normals(
            daily.get("time", []),
            daily.get("temperature_2m_mean", []),
            daily.get("precipitation_sum", []),
        )
        koppen = classify_koppen(temperatures, precipitation, latitude)
        return {
            "koppen_class": koppen["class"],
            "koppen_label": koppen["label"],
            "potential_vegetation": koppen["vegetation"],
            "vegetation_color": koppen["color"],
            "climate_period": "1991–2020",
        }
    except (requests.RequestException, ValueError, KeyError):
        return {
            "koppen_class": None,
            "koppen_label": "No disponible",
            "potential_vegetation": "No disponible: no se pudieron consultar normales climáticas.",
            "vegetation_color": "#6b7280",
            "climate_period": "1991–2020",
        }


def monthly_normals(times: list[str], temperatures: list[float | None], precipitation: list[float | None]) -> tuple[list[float], list[float]]:
    """Convert daily values into 12 monthly temperature and precipitation normals."""
    temperature_values: list[list[float]] = [[] for _ in range(12)]
    precipitation_totals: dict[tuple[str, int], float] = {}
    for timestamp, temperature, rain in zip(times, temperatures, precipitation):
        year, month = timestamp[:4], int(timestamp[5:7])
        if temperature is not None:
            temperature_values[month - 1].append(float(temperature))
        precipitation_totals[(year, month)] = precipitation_totals.get((year, month), 0.0) + float(rain or 0.0)
    if any(not values for values in temperature_values):
        raise ValueError("Faltan datos mensuales de temperatura.")
    years = {year for year, _ in precipitation_totals}
    if not years:
        raise ValueError("Faltan datos mensuales de precipitación.")
    monthly_temperature = [sum(values) / len(values) for values in temperature_values]
    monthly_precipitation = [
        sum(value for (_, entry_month), value in precipitation_totals.items() if entry_month == month) / len(years)
        for month in range(1, 13)
    ]
    return monthly_temperature, monthly_precipitation


def classify_koppen(monthly_temperature: list[float], monthly_precipitation: list[float], latitude: float) -> dict[str, str]:
    """Apply a documented, compact Köppen-Geiger approximation to monthly normals."""
    if len(monthly_temperature) != 12 or len(monthly_precipitation) != 12:
        raise ValueError("Köppen requiere doce valores mensuales.")
    annual_temperature = sum(monthly_temperature) / 12
    annual_precipitation = sum(monthly_precipitation)
    coldest, hottest, driest = min(monthly_temperature), max(monthly_temperature), min(monthly_precipitation)
    high_sun_months = {4, 5, 6, 7, 8, 9} if latitude >= 0 else {10, 11, 12, 1, 2, 3}
    high_sun_precipitation = sum(value for month, value in enumerate(monthly_precipitation, start=1) if month in high_sun_months)
    if high_sun_precipitation >= annual_precipitation * 0.7:
        dry_threshold = 20 * annual_temperature + 280
    elif high_sun_precipitation >= annual_precipitation * 0.3:
        dry_threshold = 20 * annual_temperature + 140
    else:
        dry_threshold = 20 * annual_temperature

    if annual_precipitation < dry_threshold:
        code = "BW" if annual_precipitation < dry_threshold / 2 else "BS"
        code += "h" if annual_temperature >= 18 else "k"
        return koppen_description(code)
    if coldest >= 18:
        if driest >= 60:
            return koppen_description("Af")
        if driest >= 100 - annual_precipitation / 25:
            return koppen_description("Am")
        winter_months = set(range(1, 13)) - high_sun_months
        winter_minimum = min(value for month, value in enumerate(monthly_precipitation, start=1) if month in winter_months)
        summer_minimum = min(value for month, value in enumerate(monthly_precipitation, start=1) if month in high_sun_months)
        return koppen_description("Aw" if winter_minimum < summer_minimum else "As")
    if hottest < 10:
        return koppen_description("ET" if hottest > 0 else "EF")

    main = "C" if coldest > 0 else "D"
    high_sun_minimum = min(value for month, value in enumerate(monthly_precipitation, start=1) if month in high_sun_months)
    low_sun_maximum = max(value for month, value in enumerate(monthly_precipitation, start=1) if month not in high_sun_months)
    low_sun_minimum = min(value for month, value in enumerate(monthly_precipitation, start=1) if month not in high_sun_months)
    high_sun_maximum = max(value for month, value in enumerate(monthly_precipitation, start=1) if month in high_sun_months)
    if high_sun_minimum < 40 and high_sun_minimum < low_sun_maximum / 3:
        season = "s"
    elif low_sun_minimum < high_sun_maximum / 10:
        season = "w"
    else:
        season = "f"
    warmth = "a" if hottest >= 22 else "b" if sum(value > 10 for value in monthly_temperature) >= 4 else "c"
    return koppen_description(main + season + warmth)


def koppen_description(code: str) -> dict[str, str]:
    """Map climate codes to careful biome-scale potential vegetation labels."""
    descriptions = {
        "Af": ("Tropical lluvioso", "Bosque tropical húmedo perennifolio", "#166534"),
        "Am": ("Tropical monzónico", "Bosque tropical monzónico", "#15803d"),
        "Aw": ("Tropical con estación seca", "Sabana y bosque tropical estacional", "#65a30d"),
        "As": ("Tropical con verano seco", "Bosque tropical estacional", "#84cc16"),
        "BWh": ("Desértico cálido", "Vegetación xerófila muy dispersa", "#d97706"),
        "BWk": ("Desértico frío", "Vegetación xerófila muy dispersa", "#b45309"),
        "BSh": ("Semiárido cálido", "Matorral xerófilo y pastizal seco", "#ca8a04"),
        "BSk": ("Semiárido frío", "Estepa y matorral seco", "#a16207"),
        "ET": ("Tundra", "Tundra o vegetación alpina", "#64748b"),
        "EF": ("Hielos perpetuos", "Sin vegetación potencial dominante", "#cbd5e1"),
    }
    label, vegetation, color = descriptions.get(code, ("Templado o continental", "Bosque o matorral templado, según condiciones locales", "#0f766e"))
    return {"class": code, "label": label, "vegetation": vegetation, "color": color}


def nearby_elevations(latitude: float, longitude: float, sample_distance_m: int = 250) -> list[float]:
    """Fetch elevation at the point plus nearby cardinal samples for local relief."""
    latitude_delta = sample_distance_m / 111_320
    longitude_delta = sample_distance_m / max(111_320 * cos(radians(latitude)), 0.01)
    points = [
        (latitude, longitude),
        (latitude + latitude_delta, longitude),
        (latitude - latitude_delta, longitude),
        (latitude, longitude + longitude_delta),
        (latitude, longitude - longitude_delta),
    ]
    response = requests.get(
        OPEN_METEO_ELEVATION_URL,
        params={
            "latitude": ",".join(f"{point[0]:.6f}" for point in points),
            "longitude": ",".join(f"{point[1]:.6f}" for point in points),
        },
        timeout=15,
    )
    response.raise_for_status()
    values = response.json().get("elevation", [])
    return [float(value) for value in values if value is not None]


def mapped_infrastructure(latitude: float, longitude: float, radius_m: int) -> dict[str, Any]:
    """Retrieve buildings and roads mapped in OpenStreetMap via a bounded query."""
    building_query = f"""
[out:json][timeout:25];
way["building"](around:{radius_m},{latitude:.6f},{longitude:.6f});
out count;
"""
    features_query = f"""
[out:json][timeout:25];
(
  way["building"](around:{radius_m},{latitude:.6f},{longitude:.6f});
  way["highway"~"^(motorway|trunk|primary|secondary|tertiary|residential|unclassified|service)$"](around:{radius_m},{latitude:.6f},{longitude:.6f});
);
out geom 150;
"""
    building_count = overpass_count(building_query)
    summary = summarize_osm_elements(overpass_request(features_query).get("elements", []))
    summary["mapped_buildings"] = building_count
    return summary


def overpass_count(query: str) -> int:
    elements = overpass_request(query).get("elements", [])
    if not elements:
        return 0
    return int(elements[0].get("tags", {}).get("total", 0))


def overpass_request(query: str) -> dict[str, Any]:
    """Use a small fallback pool because public Overpass instances can be busy."""
    last_error: Exception | None = None
    for endpoint in OVERPASS_URLS:
        try:
            response = requests.post(
                endpoint,
                data={"data": query},
                headers={"User-Agent": "StrepitusSilvae/0.1 (field-context demo)"},
                timeout=35,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as error:
            last_error = error
    raise RuntimeError("Los servidores públicos de OpenStreetMap están ocupados; intenta de nuevo en unos minutos.") from last_error


def summarize_osm_elements(elements: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate simple, non-authoritative infrastructure metrics and map layers."""
    buildings = []
    roads = []
    road_length_m = 0.0
    for element in elements:
        tags = element.get("tags", {})
        geometry = element.get("geometry", [])
        if tags.get("building") and len(geometry) >= 3:
            buildings.append(geojson_feature(geometry, "Polygon", tags))
        elif tags.get("highway") and len(geometry) >= 2:
            roads.append(geojson_feature(geometry, "LineString", tags))
            road_length_m += geometry_length_m(geometry)
    return {
        "mapped_buildings": len(buildings),
        "mapped_roads": len(roads),
        "mapped_road_length_km": round(road_length_m / 1000, 2),
        "building_features": buildings[:150],
        "road_features": roads[:150],
    }


def geojson_feature(geometry: list[dict[str, float]], geometry_type: str, tags: dict[str, Any]) -> dict[str, Any]:
    coordinates = [[point["lon"], point["lat"]] for point in geometry]
    if geometry_type == "Polygon":
        if coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])
        coordinates = [coordinates]
    return {"type": "Feature", "properties": {"type": tags.get("building") or tags.get("highway", "unknown")}, "geometry": {"type": geometry_type, "coordinates": coordinates}}


def geometry_length_m(geometry: list[dict[str, float]]) -> float:
    return sum(haversine_m(first["lat"], first["lon"], second["lat"], second["lon"]) for first, second in zip(geometry, geometry[1:]))


def haversine_m(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    radius_m = 6_371_000
    lat_delta = radians(latitude_b - latitude_a)
    lon_delta = radians(longitude_b - longitude_a)
    value = sin(lat_delta / 2) ** 2 + cos(radians(latitude_a)) * cos(radians(latitude_b)) * sin(lon_delta / 2) ** 2
    return 2 * radius_m * asin(sqrt(value))


def validate_coordinates(latitude: float, longitude: float) -> None:
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Las coordenadas están fuera de rango.")
