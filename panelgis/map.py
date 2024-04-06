import folium
import folium.plugins
import numpy as np
import panel as pn


class Layer:
    _levels = set()

    def __init__(self, **kwargs):
        for (k, v) in kwargs.items():
            setattr(self, f"_level_{k}", v)
            Layer._levels.add(k)
    
    def __getattr__(self, attr: str):
        if attr.startswith('__') and attr.endswith('__'):
            raise AttributeError
        
        if attr.startswith("_"):
            raise AttributeError

        level_name = f"_level_{attr}"
        if level_name in self.__dict__:
            return self.__dict__[level_name]
        return None
    
    def to_str(self, compact: bool = False):
        if compact:
            return ", ".join(str(getattr(self, level)) for level in Layer.levels() if getattr(self, level))

        return "\n".join(f"{level}: {getattr(self, level)}" for level in Layer.levels() if getattr(self, level))
    
    def __str__(self) -> str:
        return self.to_str(True)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Layer):
            return False
        for level in Layer._levels:
            if getattr(self, level) != getattr(other, level):
                return False
        return True
    
    def __hash__(self) -> int:
        return hash(tuple(str(getattr(self, level)) for level in Layer.levels()))
    
    @classmethod
    def levels(cls):
        return sorted(cls._levels)


class FeatureMap:
    def __init__(self, features, select_tiles, select_source, select_background=None, select_border=None, is_feature_active=None, height=None, width=None, custom_attribution="PanelGIS by S. Strömer"):
        self.features = features
        self._custom_attribution = custom_attribution

        self.select_tiles = select_tiles
        if self.select_tiles:
            self.select_tiles.param.watch(self.cb_update, "value")
        self.select_source = select_source
        if self.select_source:
            self.select_source.param.watch(self.cb_update, "value")

        self._backgrounds = {}
        self.select_background = select_background
        if self.select_background:
            self.select_background.param.watch(self.cb_update, "value")

        self._borders = {}
        self.select_border = select_border
        if self.select_border:
            self.select_border.param.watch(self.cb_update, "value")

        self.is_feature_active = is_feature_active

        self._make_folium_map()
        self.pane = pn.pane.plot.Folium(self.folium_map, name="folium_map_pane", height=height, width=width)

    def _make_folium_map(self, **kwargs):
        self.folium_map = folium.Map(tiles=None, zoom_delta=0.25, zoom_snap=0, prefer_canvas=True)
        f_tiles = {
            "none": folium.TileLayer("", attr=" "),
            "blank": folium.TileLayer(folium.utilities.image_to_url(np.array([[1, 1], [1, 1]])), attr=" "),
            "CartoDB (light)": folium.TileLayer("cartodbpositron"),
            "CartoDB (dark)": folium.TileLayer("cartodbdark_matter"),
            "OSM": folium.TileLayer("OpenStreetMap"),
        }

        if len(self.select_source.value) > 0:
            sources = ", ".join(str(it).upper() for it in self.select_source.value)
            sources = f"Data Sources: {[]}"
        else:
            sources = ""

        folium.TileLayer(
            f_tiles[self.select_tiles.value].tiles,
            attr=self._custom_attribution + f_tiles[self.select_tiles.value].options["attribution"] + sources
        ).add_to(self.folium_map)

        bg = self.select_background.value
        if bg is not None:
            if bg in self._backgrounds and self._backgrounds[bg] is not None:
                self._backgrounds[bg].add_to(self.folium_map)

        border = self.select_border.value
        if border is not None:
            if border in self._borders and self._borders[border] is not None:
                self._borders[border].add_to(self.folium_map)

        folium.plugins.Fullscreen(                                                         
                position                = "topright",                                   
                title                   = "Open in Fullscreen",                       
                title_cancel            = "Close Fullscreen",                      
                force_separate_button   = True,                                         
        ).add_to(self.folium_map)

        self.folium_map.fit_bounds([[46.33, 9.44], [49.03, 17.17]], padding_top_left=(20, 20), padding_bottom_right=(20, 20))

        return self.folium_map

    def _add_a_to_b(self, a, b):
        self.folium_map.add_child(
            folium.elements.ElementAddToElement(
                element_name=a.get_name(),
                element_parent_name=b.get_name(),
            ),
            name=a.get_name() + "_add_" + b.get_name(),
        )

    def _add_folium_features(self):
        for f in self.features:
            if not self.is_feature_active(f):
                continue
            
            f.add_to(self.folium_map)

    def _update_map(self):
        self._make_folium_map()
        self._add_folium_features()
        self.pane.object = self.folium_map

    def cb_update(self, event):
        self._update_map()

    def register_background(self, name, element):
        self._backgrounds[name] = element
    
    def register_border(self, name, element):
        self._borders[name] = element
