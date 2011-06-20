from nml import generic, global_constants, expression, nmlop
from nml.actions import action2, action6, actionD, action1, action2var, real_sprite
from nml.ast import switch_range

class Action2Layout(action2.Action2):
    def __init__(self, feature, name, ground_sprite, sprite_list):
        action2.Action2.__init__(self, feature, name)
        assert ground_sprite.type == Action2LayoutSpriteType.GROUND
        self.ground_sprite = ground_sprite
        self.sprite_list = sprite_list

    def write(self, file):
        advanced = any(x.is_advanced_sprite() for x in self.sprite_list + [self.ground_sprite])
        size = 5
        if advanced: size += self.ground_sprite.get_registers_size()
        for sprite in self.sprite_list:
            if sprite.type == Action2LayoutSpriteType.CHILD:
                size += 7
            else:
                size += 10
            if advanced: size += sprite.get_registers_size()
        if len(self.sprite_list) == 0:
            size += 9

        action2.Action2.write_sprite_start(self, file, size)
        if advanced:
            file.print_byte(0x40 | len(self.sprite_list))
        else:
            file.print_byte(len(self.sprite_list))
        self.ground_sprite.write_sprite_number(file)
        if advanced:
            self.ground_sprite.write_flags(file)
            self.ground_sprite.write_registers(file)
        file.newline()
        if len(self.sprite_list) == 0:
            file.print_dwordx(0) #sprite number 0 == no sprite
            for i in range(0, 5):
                file.print_byte(0) #empty bounding box. Note that number of zeros is 5, not 6
        else:
            for sprite in self.sprite_list:
                sprite.write_sprite_number(file)
                if advanced: sprite.write_flags(file)
                file.print_byte(sprite.get_param('xoffset'))
                file.print_byte(sprite.get_param('yoffset'))
                if sprite.type == Action2LayoutSpriteType.CHILD:
                    file.print_bytex(0x80)
                else:
                    #normal building sprite
                    file.print_byte(sprite.get_param('zoffset'))
                    file.print_byte(sprite.get_param('xextent'))
                    file.print_byte(sprite.get_param('yextent'))
                    file.print_byte(sprite.get_param('zextent'))
                if advanced: sprite.write_registers(file)
                file.newline()
        file.end_sprite()


class Action2LayoutSpriteType(object):
    GROUND   = 0
    BUILDING = 1
    CHILD    = 2

#these keywords are used to identify a ground/building/childsprite
layout_sprite_types = {
    'ground'      : Action2LayoutSpriteType.GROUND,
    'building'    : Action2LayoutSpriteType.BUILDING,
    'childsprite' : Action2LayoutSpriteType.CHILD,
}

class Action2LayoutSprite(object):
    def __init__(self, type, pos = None):
        self.type = type
        self.pos = pos
        self.params = {
            'sprite'        : {'value': None, 'validator': self._validate_sprite},
            'recolour_mode' : {'value': 0,  'validator': self._validate_recolour_mode},
            'palette'       : {'value': expression.ConstantNumeric(0), 'validator': self._validate_palette},
            'always_draw'   : {'value': 0,  'validator': self._validate_always_draw},
            'xoffset'       : {'value': 0,  'validator': self._validate_bounding_box},
            'yoffset'       : {'value': 0,  'validator': self._validate_bounding_box},
            'zoffset'       : {'value': 0,  'validator': self._validate_bounding_box},
            'xextent'       : {'value': 16, 'validator': self._validate_bounding_box},
            'yextent'       : {'value': 16, 'validator': self._validate_bounding_box},
            'zextent'       : {'value': 16, 'validator': self._validate_bounding_box},
            'hide_sprite'   : {'value': None, 'validator': self._validate_hide_sprite},
        }
        for i in self.params:
            self.params[i]['is_set'] = False
        self.temp_registers = []
        self.sprite_from_action1 = False
        self.palette_from_action1 = False

    def is_advanced_sprite(self):
        return self.is_set('hide_sprite') or self.palette_from_action1

    def get_registers_size(self):
        size = 0
        if self.is_set('hide_sprite'):
            size += 1
        size += 2
        return size

    def write_flags(self, file):
        flags = 0
        if self.is_set('hide_sprite'):
            flags |= 0x0001
        if self.palette_from_action1:
            flags |= 1 << 3
        file.print_wordx(flags)

    def write_registers(self, file):
        if self.is_set('hide_sprite'):
            file.print_bytex(self.get_param('hide_sprite').tmp_var.mask.value)

    def write_sprite_number(self, file):
        num = self.get_sprite_number()
        if isinstance(num, expression.ConstantNumeric):
            num.write(file, 4)
        else:
            file.print_dwordx(0)

    def get_sprite_number(self):
        # Layout of sprite number
        # bit  0 - 13: Sprite number
        # bit 14 - 15: Recolour mode (normal/transparent/remap)
        # bit 16 - 29: Palette sprite number
        # bit 30: Always draw sprite, even in transparent mode
        # bit 31: This is a custom sprite (from action1), not a TTD sprite
        if not self.is_set('sprite'):
            raise generic.ScriptError("'sprite' must be set for this layout sprite", self.pos)

        # Make sure that recolouring is set correctly
        if self.get_param('recolour_mode') == 0 and self.is_set('palette'):
            raise generic.ScriptError("'palette' may not be set when 'recolour_mode' is RECOLOUR_NONE.")
        elif self.get_param('recolour_mode') != 0 and not self.is_set('palette'):
            raise generic.ScriptError("'palette' must be set when 'recolour_mode' is not set to RECOLOUR_NONE.")

        # add the constant terms first
        sprite_num = self.get_param('recolour_mode') << 14
        if self.get_param('always_draw'):
            sprite_num |= 1 << 30
        if self.sprite_from_action1:
            sprite_num |= 1 << 31

        add_sprite = False
        sprite = self.get_param('sprite')
        if isinstance(sprite, expression.ConstantNumeric):
            sprite_num |= sprite.value
        else:
            add_sprite = True

        add_palette = False
        palette = self.get_param('palette')
        if isinstance(palette, expression.ConstantNumeric):
            sprite_num |= palette.value << 16
        else:
            add_palette = True

        expr = expression.ConstantNumeric(sprite_num, sprite.pos)
        if add_sprite:
            expr = expression.BinOp(nmlop.ADD, sprite, expr, sprite.pos)
        if add_palette:
            expr = expression.BinOp(nmlop.ADD, palette, expr, sprite.pos)
        return expr.reduce()

    def get_param(self, name):
        assert name in self.params
        return self.params[name]['value']

    def is_set(self, name):
        assert name in self.params
        return self.params[name]['is_set']

    def set_param(self, name, value):
        assert isinstance(name, expression.Identifier)
        assert isinstance(value, expression.Expression) or isinstance(value, action2.SpriteGroupRef)
        name = name.value
        if name == 'ttdsprite':
            name = 'sprite'
            generic.print_warning("Using 'ttdsprite' in sprite layouts is deprecated, use 'sprite' instead", value.pos)

        if not name in self.params:
            raise generic.ScriptError("Unknown sprite parameter '%s'" % name, value.pos)
        if self.is_set(name):
            raise generic.ScriptError("Sprite parameter '%s' can be set only once per sprite." % name, value.pos)

        self.params[name]['value'] = self.params[name]['validator'](name, value)
        self.params[name]['is_set'] = True

    def resolve_spritegroup_ref(self, sg_ref):
        """
        Resolve a reference to a (sprite/palette) sprite group

        @param sg_ref: Reference to a sprite group
        @type sg_ref: L{SpriteGroupRef}

        @return: Sprite number (index of action1 set) to use
        @rtype: L{Expression}
        """
        spriteset = action2.resolve_spritegroup(sg_ref.name)

        # TODO fix this to use ASL bit1/2
        if len(sg_ref.param_list) == 0:
            offset = 0
        elif len(sg_ref.param_list) == 1:
            id_dicts = [(spriteset.labels, lambda val, pos: expression.ConstantNumeric(val, pos))]
            offset = sg_ref.param_list[0].reduce_constant(global_constants.const_list + id_dicts).value
            generic.check_range(offset, 0, len(real_sprite.parse_sprite_list(spriteset.sprite_list, spriteset.pcx)) - 1, "offset within spriteset", sg_ref.pos)
        else:
            raise generic.ScriptError("Expected 0 or 1 parameter, got " + str(len(sg_ref.param_list)), sg_ref.pos)

        num = action1.get_action1_index(spriteset) + offset
        generic.check_range(num, 0, (1 << 14) - 1, "sprite", sg_ref.pos)
        return expression.ConstantNumeric(num)

    def _validate_sprite(self, name, value):
        if isinstance(value, action2.SpriteGroupRef):
            self.sprite_from_action1 = True
            return self.resolve_spritegroup_ref(value)
        else:
            if isinstance(value, expression.ConstantNumeric):
                generic.check_range(value.value, 0, (1 << 14) - 1, "sprite", value.pos)
            self.sprite_from_action1 = False
            return value

    def _validate_recolour_mode(self, name, value):
        if not isinstance(value, expression.ConstantNumeric):
            raise generic.ScriptError("Expected a compile-time constant.", value.pos)

        if not value.value in (0, 1, 2):
            raise generic.ScriptError("Value of 'recolour_mode' must be RECOLOUR_NONE, RECOLOUR_TRANSPARENT or RECOLOUR_REMAP.")
        return value.value

    def _validate_palette(self, name, value):
        if isinstance(value, action2.SpriteGroupRef):
            self.palette_from_action1 = True
            return self.resolve_spritegroup_ref(value)
        else:
            if isinstance(value, expression.ConstantNumeric):
                generic.check_range(value.value, 0, (1 << 14) - 1, "palette", value.pos)
            self.palette_from_action1 = False
            return value

    def _validate_always_draw(self, name, value):
        if not isinstance(value, expression.ConstantNumeric):
            raise generic.ScriptError("Expected a compile-time constant number.", value.pos)
        # Not valid for ground sprites, raise error
        if self.type == Action2LayoutSpriteType.GROUND:
            raise generic.ScriptError("'always_draw' may not be set for groundsprites, these are always drawn anyways.", value.pos)

        if value.value not in (0, 1):
            raise generic.ScriptError("Value of 'always_draw' should be 0 or 1", value.pos)
        return value.value

    def _validate_bounding_box(self, name, value):
        if not isinstance(value, expression.ConstantNumeric):
            raise generic.ScriptError("Expected a compile-time constant number.", value.pos)
        val = value.value

        if self.type == Action2LayoutSpriteType.GROUND:
            raise generic.ScriptError(name + " can not be set for ground sprites", value.pos)
        elif self.type == Action2LayoutSpriteType.CHILD:
            if name not in ('xoffset', 'yoffset'):
                raise generic.ScriptError(name + " can not be set for child sprites", value.pos)
            generic.check_range(val, 0, 255, name, value.pos)
        else:
            assert self.type == Action2LayoutSpriteType.BUILDING
            if name in ('xoffset', 'yoffset', 'zoffset'):
                generic.check_range(val, -128, 127, name, value.pos)
            else:
                generic.check_range(val, 0, 255, name, value.pos)
        return val

    def _validate_hide_sprite(self, name, value):
        store_tmp = action2var.VarAction2StoreTempVar()
        load_tmp = action2var.VarAction2LoadTempVar(store_tmp)
        self.temp_registers.append((store_tmp, expression.Not(value)))
        return load_tmp

def get_layout_action2s(spritegroup):
    ground_sprite = None
    building_sprites = []
    actions = []

    feature = spritegroup.feature.value
    if feature not in action2.features_sprite_layout:
        raise generic.ScriptError("Sprite layouts are not supported for feature '%02X'." % feature)

    all_spritesets = []
    for layout_sprite in spritegroup.layout_sprite_list:
        for param in layout_sprite.param_list:
            if param.name.value in ('sprite', 'palette') and isinstance(param.value, action2.SpriteGroupRef):
                all_spritesets.append(action2.resolve_spritegroup(param.value.name))
    actions.extend(action1.add_to_action1(all_spritesets, feature))

    temp_registers = []
    for layout_sprite in spritegroup.layout_sprite_list:
        if layout_sprite.type.value not in layout_sprite_types:
            raise generic.ScriptError("Invalid sprite type '%s' encountered. Expected 'ground', 'building', or 'childsprite'." % layout_sprite.type.value, layout_sprite.type.pos)
        sprite = Action2LayoutSprite(layout_sprite_types[layout_sprite.type.value], layout_sprite.pos)
        for param in layout_sprite.param_list:
            sprite.set_param(param.name, param.value)
        temp_registers.extend(sprite.temp_registers)
        if sprite.type == Action2LayoutSpriteType.GROUND:
            if ground_sprite is not None:
                raise generic.ScriptError("Sprite layout can have no more than one ground sprite", spritegroup.pos)
            ground_sprite = sprite
        else:
            building_sprites.append(sprite)

    if ground_sprite is None:
        if len(building_sprites) == 0:
            #no sprites defined at all, that's not very much.
            raise generic.ScriptError("Sprite layout requires at least one sprite", spritegroup.pos)
        #set to 0 for no ground sprite
        ground_sprite = Action2LayoutSprite(Action2LayoutSpriteType.GROUND)
        ground_sprite.set_param(expression.Identifier('sprite'), expression.ConstantNumeric(0))

    action6.free_parameters.save()
    act6 = action6.Action6()

    extra_varact2_actions = None
    if temp_registers:
        varact2parser = action2var.Varaction2Parser(feature)
        for reg_expr_pair in temp_registers:
            reg, expr = reg_expr_pair
            varact2parser.parse(action2var.reduce_varaction2_expr(expr, feature))
            varact2parser.var_list.append(nmlop.STO_TMP)
            varact2parser.var_list.append(reg)
            varact2parser.var_list.append(nmlop.VAL2)
            varact2parser.var_list_size += reg.get_size() + 2
        #Remove the last VAL2 operator
        varact2parser.var_list.pop()
        varact2parser.var_list_size -= 1
        
        extra_varact2_actions = varact2parser.extra_actions
        extra_act6 = action6.Action6()
        for mod in varact2parser.mods:
            extra_act6.modify_bytes(mod.param, mod.size, mod.offset + offset)
        if len(extra_act6.modifications) > 0: extra_varact2_actions.append(extra_act6)

        orig_name = spritegroup.name.value
        spritegroup.name = expression.Identifier('%s@orig' % orig_name)
        action2.register_spritegroup(spritegroup)
        varaction2 = action2var.Action2Var(feature, '%s@registers' % orig_name, 0x89)
        varaction2.var_list = varact2parser.var_list
        ref = action2.SpriteGroupRef(spritegroup.name, [], None)
        varaction2.ranges.append(switch_range.SwitchRange(expression.ConstantNumeric(0), expression.ConstantNumeric(0), ref, comment=''))
        varaction2.default_result = ref
        varaction2.default_comment = ''
        
        extra_varact2_actions.append(varaction2)

    offset = 4
    sprite_num = ground_sprite.get_sprite_number()
    if not isinstance(sprite_num, expression.ConstantNumeric):
        param, extra_actions = actionD.get_tmp_parameter(sprite_num)
        actions.extend(extra_actions)
        act6.modify_bytes(param, 4, offset)
    offset += 4
    offset += ground_sprite.get_registers_size()

    for sprite in building_sprites:
        sprite_num = sprite.get_sprite_number()
        if not isinstance(sprite_num, expression.ConstantNumeric):
            param, extra_actions = actionD.get_tmp_parameter(sprite_num)
            actions.extend(extra_actions)
            act6.modify_bytes(param, 4, offset)
        offset += sprite.get_registers_size()
        offset += 7 if sprite.type == Action2LayoutSpriteType.CHILD else 10

    if len(act6.modifications) > 0:
        actions.append(act6)

    layout_action = Action2Layout(feature, spritegroup.name.value, ground_sprite, building_sprites)
    actions.append(layout_action)
    if extra_varact2_actions:
        actions.extend(extra_varact2_actions)
        spritegroup.set_action2(extra_varact2_actions[-1])
        extra_varact2_actions[-1].references.append(action2.Action2Reference(layout_action, False))
        layout_action.num_refs += 1
    else:
        spritegroup.set_action2(layout_action)

    action6.free_parameters.restore()
    return actions
