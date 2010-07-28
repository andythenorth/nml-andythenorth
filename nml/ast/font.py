from nml import expression, generic
from nml.actions import action12

class FontGlyphBlock(object):
    def __init__(self, param_list, sprite_list, pos):
        if not (2 <= len(param_list) <= 3):
            raise generic.ScriptError("font_glpyh-block requires 2 or 3 parameters, encountered " + str(len(param_list)), pos)
        self.font_size = param_list[0]
        self.base_char = param_list[1]
        if len(param_list) >= 3:
            self.pcx = param_list[2].reduce()
            if not isinstance(self.pcx, expression.StringLiteral):
                raise generic.ScriptError("font_glpyh-block parameter 3 'file' must be a string literal", self.pcx.pos)
        else:
            self.pcx = None
        self.sprite_list = sprite_list
        self.pos = pos

    def pre_process(self):
        pass

    def debug_print(self, indentation):
        print indentation*' ' + 'Load font glyphs, starting at', self.base_char
        print (indentation+2)*' ' + 'Font size:  ', self.font_size
        print (indentation+2)*' ' + 'Source:  ', self.pcx.value if self.pcx is not None else 'None'
        print (indentation+2)*' ' + 'Sprites:'
        for sprite in self.sprite_list:
            sprite.debug_print(indentation + 4)

    def get_action_list(self):
        return action12.parse_action12(self)
