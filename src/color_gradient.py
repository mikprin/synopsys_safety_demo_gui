


class ColorGradient(object):
    green_to_grey = [
                "#0fa500",
                "#1aa409",
                "#21a211",
                "#27a117",
                "#2ca01c",
                "#319e20",
                "#359d24",
                "#389b27",
                "#3c9a2b",
                "#3f992e",
                "#429731",
                "#449634",
                "#479436",
                "#499339",
                "#4c923b",
                "#4e903e",
                "#508f40",
                "#528d43",
                "#548c45",
                "#558b47",
                "#578949",
                "#59884b",
                "#5a864d",
                "#5c8550",
                "#5d8352",
                "#5f8254",
                "#608156",
                "#617f58",
                "#627e5a",
                "#647c5b",
                "#657b5d",
                "#66795f",
                "#677861",
                "#687663",
                "#697565",
                "#6a7367",
                "#6b7269",
                "#6b706a",
                "#6c6f6c",
                "#6d6d6e",
                ]
        
    red_to_grey = [
                "#ba4f4f",
                "#b85050",
                "#b75151",
                "#b55251",
                "#b35352",
                "#b15453",
                "#b05554",
                "#ae5654",
                "#ac5755",
                "#aa5856",
                "#a95957",
                "#a75a58",
                "#a55b58",
                "#a35c59",
                "#a15d5a",
                "#a05d5b",
                "#9e5e5c",
                "#9c5f5c",
                "#9a605d",
                "#98615e",
                "#96615f",
                "#946260",
                "#926360",
                "#906361",
                "#8e6462",
                "#8c6563",
                "#8a6564",
                "#886664",
                "#866765",
                "#846766",
                "#826867",
                "#806968",
                "#7e6968",
                "#7b6a69",
                "#796a6a",
                "#776b6b",
                "#746b6c",
                "#726c6c",
                "#6f6c6d",
                "#6d6d6e",
]

    def __init__(self, mode="green_to_grey"):
        self.mode = mode
        self.last_color = 0
        if mode == "green_to_grey":
            self.colors = self.green_to_grey
        elif mode == "red_to_grey":
            self.colors = self.red_to_grey
        else:
            raise ValueError("Unknown mode: {}".format(mode))

    def reset_color(self):
        self.last_color = 0

    def get_color(self):
        color = self.colors[self.last_color]
        if self.last_color < len(self.colors) - 1:
            self.last_color += 1
            return color
        else:
            return color

    def get_color_range(self, start, end, step = 1 ):
        return self.colors[start:end:step]
        

