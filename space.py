class Space:
    def __init__(self, name,
                 description,
                 projection_name = None,
                 projection_description = None,
                 projection_image = None,
                 x_pos = None,
                 y_pos = None):

        self.name = name
        self.description = description

        self.projection_name = projection_name
        self.projection_description = projection_description
        self.projection_image = projection_image

        self.x_pos = x_pos
        self.y_pos = y_pos