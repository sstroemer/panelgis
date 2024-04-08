from typing import Callable

import folium
import shapely

from .sources import SourceInfo
from .map import Layer


class Feature:
    STATE_INIT = "init"
    STATE_PREPROCESSED = "preproc"
    STATE_DROPPED = "drop"
    STATE_FINALIZED = "final"

    def __init__(
        self,
        source: str | dict,
        location: tuple | None = None,
        geojson: dict | None = None,
        layer: Layer = None,
        properties: dict | None = None,
        reduce_to_centroid: bool = False,
    ):
        self.source = SourceInfo(source) if isinstance(source, str) else SourceInfo(**source)
        self.layer = layer

        if geojson:
            if location:
                raise ValueError("Passing location and geojson at the same time is not supported")

            if geojson["type"] == "FeatureCollection":
                raise TypeError("Only `Feature` or `Geometry` objects supported, got `FeatureCollection`")

            if geojson["type"] == "Feature":
                self.geojson = geojson
                self.geojson["properties"] = self.geojson.get("properties", {})
            elif geojson["type"] in ["Point", "LineString", "Polygon"]:
                self.geojson = {"type": "Feature", "geometry": geojson, "properties": geojson.get("properties", {})}
            elif geojson["type"] in ["MultiPoint", "MultiLineString", "MultiPolygon"]:
                # TODO: this could havbe one level of depth missing in "geometry" to then process with "shapely.geometry.shape"
                self.geojson = {"type": "Feature", "geometry": geojson, "properties": geojson.get("properties", {})}
            else:
                raise TypeError("Unknown type in GeoJSON: " + geojson["type"])

            self.geojson["type"] = self.geojson.get("type", "")
            self.geojson["geometry"] = self.geojson.get("geometry", [])
            self.geojson["properties"] = self.geojson.get("properties", {})

        if location:
            self.geojson = {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [location[1], location[0]]},
                "properties": {},
            }

        if reduce_to_centroid:
            centroid = shapely.geometry.shape(self.geojson["geometry"]).centroid
            self.geojson["geometry"]["type"] = "Point"
            self.geojson["geometry"]["coordinates"] = [centroid.y, centroid.x]

        if properties:
            if self.geojson:
                for k, v in properties.items():
                    if k in self.geojson["properties"]:
                        raise ValueError(f"Property ({k}) already exists in GeoJSON")
                    self.geojson["properties"][k] = v
            else:
                self.geojson = {
                    "type": "Feature",
                    "geometry": {},
                    "properties": properties,
                }

        self._folium_element = None
        self.state = Feature.STATE_INIT

    def make_folium_element(
        self,
        tooltip: str | folium.GeoJsonTooltip | None = None,
        popup: str | folium.GeoJsonPopup | None = None,
        marker: folium.Element | None = folium.Marker,
        control: bool = False,
        show: bool = True,
        style=dict | Callable | None,
    ) -> folium.Element:
        self._folium_element = folium.GeoJson(
            data=self.geojson,
            style_function=(style if callable(style) else lambda _: style) if style else None,
            marker=marker,
            tooltip=tooltip,
            popup=popup,
            control=control,
            show=show,
        )
        # self._folium_element.data["features"][0]["properties"] = {
        #     k: v for (k, v) in self.properties.items() if not k.startswith("_")
        # }
        self.state = Feature.STATE_FINALIZED

    def add_to(self, parent: folium.Element) -> None:
        self._folium_element.add_to(parent)

    def drop(self) -> None:
        self._folium_element = None
        self.state = Feature.STATE_DROPPED

    @property
    def properties(self):
        return self.geojson["properties"]

    @property
    def geometry(self):
        return self.geojson["geometry"]


class FeatureCollection:
    def __init__(self, features = None):
        if features:
            if isinstance(features, list):
                self._features = features
            else:
                self._features = list(features)
        else:
            self._features = []

    def append(self, feature: Feature):
        self._features.append(feature)
        return self

    def extend(self, features: list[Feature]):
        self._features.extend(features)
        return self

    def filtered(
        self,
        source: str | SourceInfo | list[str] | list[SourceInfo] | None = None,
        layer: str | tuple | list[str] | list[tuple] | None = None,
        properties: dict | None = None,
        state: str | None = None,
        invert: bool = False,
    ):
        for feature in self._features:
            if source:
                if isinstance(source, str) and not feature.source.matches(SourceInfo(source)):
                    if invert:
                        yield feature
                    else:
                        continue
                if isinstance(source, SourceInfo) and not feature.source.matches(source):
                    if invert:
                        yield feature
                    else:
                        continue
                if isinstance(source, list):
                    if isinstance(source[0], str) and not any(feature.source.matches(SourceInfo(s)) for s in source):
                        if invert:
                            yield feature
                        else:
                            continue
                    if isinstance(source[0], SourceInfo) and not any(feature.source.matches(s) for s in source):
                        if invert:
                            yield feature
                        else:
                            continue
            if layer:
                if isinstance(layer, str | tuple) and feature.layer != layer:
                    if invert:
                        yield feature
                    else:
                        continue
                if isinstance(layer, list) and feature.layer not in layer:
                    if invert:
                        yield feature
                    else:
                        continue
            if properties:
                for (k, v) in properties.items():
                    if feature.properties.get(k, None) != v:
                        if invert:
                            yield feature
                        else:
                            continue
            if state:
                if feature.state != state:
                    if invert:
                        yield feature
                    else:
                        continue

            if not invert:
                yield feature
    
    def __iter__(self):
        return iter(self._features)

    def __len__(self):
        return len(self._features)

