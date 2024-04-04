class SourceInfo:
    def __init__(self, name: str, url: str | None = None, layer: str | None = None, style: str | None = None):
        self.name = name
        self.url = url
        self.layer = layer
        self.style = style

    @classmethod
    def get_all_sources(cls) -> set:
        return SourceInfo._sources

    # def __repr__(self) -> str:
    #     ret = "SourceInfo("
    #     for attr in ["name", "url", "layer", "style"]:
    #         if getattr(self, attr):
    #             ret += f"{attr}={getattr(self, attr)}, "
    #     if ret[-1] == " ":
    #         ret = ret[:-2]
    #     return ret + ")"

    # def __str__(self) -> str:
    #     ret = "PanelGIS Source:"
    #     for attr in ["name", "url", "layer", "style"]:
    #         if getattr(self, attr):
    #             ret += f"\n\t{attr}: {getattr(self, attr)}"
    #     return ret

    def __eq__(self, other):
        if not isinstance(other, SourceInfo):
            return False
        for attr in ["name", "url", "layer", "style"]:
            if getattr(self, attr) != getattr(other, attr):
                return False
        return True

    def __hash__(self):
        return hash((self.name, self.url, self.layer, self.style))

    def matches(self, other):
        if not isinstance(other, SourceInfo):
            return False
        for attr in ["name", "layer", "style"]:
            if getattr(other, attr):
                if getattr(self, attr) != getattr(other, attr):
                    return False
        return True
