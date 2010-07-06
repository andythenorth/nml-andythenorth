from nml import generic
from nml.expression import ConstantNumeric, Array, StringLiteral

class Action0Property(object):
    """
    @ivar num: Number of the property.
    @type num: C{int}

    @ivar value: Value of the property.
    @type value: L{ConstantNumeric}

    @ivar size: Size of the storage, in bytes.
    @type size: C{int}
    """
    def __init__(self, num, value, size):
        self.num = num
        self.value = value
        self.size = size

        # Make sure the value fits in the size.
        biggest = 1 << (8 * size)
        if self.value.value >= biggest:
            raise generic.ScriptError("Action 0 property too large", value.pos)

    def write(self, file):
        file.print_bytex(self.num)
        self.value.write(file, self.size)
        file.newline()

    def get_size(self):
        return self.size + 1

properties = 0x12 * [None]

def train_weight_prop(value):
    value = value.reduce_constant()
    low_byte = ConstantNumeric(value.value & 0xFF)
    high_byte = ConstantNumeric(value.value >> 8)
    return [Action0Property(0x16, low_byte, 1), Action0Property(0x24, high_byte, 1)]

general_veh_props = {
    'reliability_decay' : {'size': 1, 'num': 0x02},
    'vehicle_life' : {'size': 1, 'num': 0x03},
    'model_life' : {'size': 1, 'num': 0x04},
    'climates_available' : {'size': 1, 'num': 0x06},
    'loading_speed' : {'size': 1, 'num': 0x07},
    'name': {'num': -1, 'string': None},
}

properties[0x00] = {
    'track_type' : {'size': 1, 'num': 0x05},
    'ai_special_flag' : {'size': 1, 'num': 0x08},
    'speed' : {'size': 2, 'num': 0x09, 'unit_type': 'speed', 'unit_conversion': 3.5790976},
    'power' : {'size': 2, 'num': 0x0B, 'unit_type': 'power'},
    'running_cost_factor' : {'size': 1, 'num': 0x0D},
    'running_cost_base' : {'size': 4, 'num': 0x0E},
    'sprite_id' : {'size': 1, 'num': 0x12},
    'dual_headed' : {'size': 1, 'num': 0x13},
    'cargo_capacity' : {'size': 1, 'num': 0x14},
    'cargo_type' : {'size': 1, 'num': 0x15},
    'weight' : {'custom_function': train_weight_prop, 'unit_type': 'weight', 'unit_conversion': 0.25},
    'cost_factor' : {'size': 1, 'num': 0x17},
    'ai_engine_rank' : {'size': 1, 'num': 0x18},
    'engine_class' : {'size': 1, 'num': 0x19},
    'extra_power_per_wagon' : {'size': 2, 'num': 0x1B, 'unit_type': 'power'},
    'refit_cost' : {'size': 1, 'num': 0x1C},
    'refittable_cargo_types' : {'size': 4, 'num': 0x1D},
    'callback_flags' : {'size': 1, 'num': 0x1E},
    'tractive_effort_coefficient' : {'size': 1, 'num': 0x1F, 'unit_conversion': 255},
    'air_drag_coefficient' : {'size': 1, 'num': 0x20, 'unit_conversion': 255},
    'shorten_vehicle' : {'size': 1, 'num': 0x21},
    'visual_effect' : {'size': 1, 'num': 0x22},
    'extra_weight_per_wagon' : {'size': 1, 'num': 0x23, 'unit_type': 'weight', 'unit_conversion': 0.25},
    'bitmask_vehicle_info' : {'size': 1, 'num': 0x25},
    'retire_early' : {'size': 1, 'num': 0x26},
    'misc_flags' : {'size': 1, 'num': 0x27},
    'refittable_cargo_classes' : {'size': 2, 'num': 0x28},
    'non_refittable_cargo_classes' : {'size': 2, 'num': 0x29},
    'introduction_date' : {'size': 4, 'num': 0x2A},
}
properties[0x00].update(general_veh_props)


def roadveh_speed_prop(value):
    value = value.reduce_constant()
    prop08 = ConstantNumeric(min(value.value, 0xFF))
    prop15 = ConstantNumeric(value.value / 4)
    return [Action0Property(0x08, prop08, 1), Action0Property(0x15, prop15, 1)]

properties[0x01] = {
    'speed': {'custom_function': roadveh_speed_prop, 'unit_type': 'speed', 'unit_conversion': 7.1581952},
    'running_cost_factor' : {'size': 1, 'num': 0x09},
    'running_cost_base' : {'size': 4, 'num': 0x0A},
    'sprite_id' : {'size': 1, 'num': 0x0E},
    'cargo_capacity' : {'size': 1, 'num': 0x0F},
    'cargo_type' : {'size': 1, 'num': 0x10},
    'cost_factor' : {'size': 1, 'num': 0x11},
    'sound_effect' : {'size': 1, 'num': 0x12},
    'power' : {'size': 1, 'num': 0x13, 'unit_type': 'power', 'unit_conversion': 0.1},
    'weight' : {'size': 1, 'num': 0x14, 'unit_type': 'weight'},
    'refittable_cargo_types' : {'size': 4, 'num': 0x16},
    'callback_flags' : {'size': 1, 'num': 0x17},
    'tractive_effort_coefficient' : {'size': 1, 'num': 0x18, 'unit_conversion': 255},
    'air_drag_coefficient' : {'size': 1, 'num': 0x19, 'unit_conversion': 255},
    'refit_cost' : {'size': 1, 'num': 0x1A},
    'retire_early' : {'size': 1, 'num': 0x1B},
    'misc_flags' : {'size': 1, 'num': 0x1C},
    'refittable_cargo_classes' : {'size': 2, 'num': 0x1D},
    'non_refittable_cargo_classes' : {'size': 2, 'num': 0x1E},
    'introduction_date' : {'size': 4, 'num': 0x1F},
}
properties[0x01].update(general_veh_props)

properties[0x02] = {
    'sprite_id' : {'size': 1, 'num': 0x08},
    'is_refittable' : {'size': 1, 'num': 0x09},
    'cost_factor' : {'size': 1, 'num': 0x0A},
    'speed' : {'size': 1, 'num': 0x0B, 'unit_type': 'speed', 'unit_conversion': 7.1581952},
    'cargo_type' : {'size': 1, 'num': 0x0C},
    'cargo_capacity' : {'size': 2, 'num': 0x0D},
    'running_cost_factor' : {'size': 1, 'num': 0x0F},
    'sound_effect' : {'size': 1, 'num': 0x10},
    'refittable_cargo_types' : {'size': 4, 'num': 0x11},
    'callback_flags' : {'size': 1, 'num': 0x12},
    'refit_cost' : {'size': 1, 'num': 0x15},
    'ocean_speed_fraction' : {'size': 1, 'num': 0x14},
    'canal_speed_fraction' : {'size': 1, 'num': 0x15},
    'retire_early' : {'size': 1, 'num': 0x16},
    'misc_flags' : {'size': 1, 'num': 0x17},
    'refittable_cargo_classes' : {'size': 2, 'num': 0x18},
    'non_refittable_cargo_classes' : {'size': 2, 'num': 0x19},
    'introduction_date' : {'size': 4, 'num': 0x1A},
}
properties[0x02].update(general_veh_props)

properties[0x03] = {
    'sprite_id' : {'size': 1, 'num': 0x08},
    'is_helicopter' : {'size': 1, 'num': 0x09},
    'is_large' : {'size': 1, 'num': 0x0A},
    'cost_factor' : {'size': 1, 'num': 0x0B},
    'speed' : {'size': 1, 'num': 0x0C, 'unit_type': 'speed', 'unit_conversion': 0.279617},
    'acceleration' : {'size': 1, 'num': 0x0D},
    'running_cost_factor' : {'size': 1, 'num': 0x0D},
    'passenger_capacity' : {'size': 2, 'num': 0x0F},
    'mail_capacity' : {'size': 1, 'num': 0x11},
    'sound_effect' : {'size': 1, 'num': 0x12},
    'refittable_cargo_types' : {'size': 4, 'num': 0x13},
    'callback_flags' : {'size': 1, 'num': 0x14},
    'refit_cost' : {'size': 1, 'num': 0x15},
    'retire_early' : {'size': 1, 'num': 0x16},
    'misc_flags' : {'size': 1, 'num': 0x17},
    'refittable_cargo_classes' : {'size': 2, 'num': 0x18},
    'non_refittable_cargo_classes' : {'size': 2, 'num': 0x19},
    'introduction_date' : {'size': 4, 'num': 0x1A},
}
properties[0x03].update(general_veh_props)

properties[0x09] = {
    'substitute': {'size': 1, 'num': 0x08},
    'override': {'size': 1, 'num': 0x09},
    'cargo_1': {'size': 2, 'num': 0x0A},
    'cargo_2': {'size': 2, 'num': 0x0B},
    'cargo_3': {'size': 2, 'num': 0x0C},
    'land_shape_flags': {'size': 1, 'num': 0x0D},
    'callback_flags': {'size': 1, 'num': 0x0E},
    'animation_info': {'size': 2, 'num': 0x0F},
    'animation_speed': {'size': 1, 'num': 0x10},
    'triggers_cb25': {'size': 1, 'num': 0x11},
    'special_flags': {'size': 1, 'num': 0x12},
}

def industry_layouts(value):
    return []

properties[0x0A] = {
    'substitute': {'size': 1, 'num': 0x08},
    'override': {'size': 1, 'num': 0x09},
    'layouts': {'custom_function': industry_layouts},
    'prod_flags': {'size': 1, 'num': 0x0B},
    'closure_msg': {'size': 2, 'num': 0x0C},
    'prod_increase_msg': {'size': 2, 'num': 0x0D},
    'prod_decrease_msg': {'size': 2, 'num': 0x0E},
    'fund_cost_multiplier': {'size': 1, 'num': 0x0F},
    'prod_cargo_types': {'size': 2, 'num': 0x10},
    'accept_cargo_types': {'size': 4, 'num': 0x11},
    'prod_multiplier_1': {'size': 1, 'num': 0x12},
    'prod_multiplier_2': {'size': 1, 'num': 0x13},
    'min_cargo_distr': {'size': 1, 'num': 0x14},
    'random_sound_effects': {'size': 0, 'num': 0x15},
    'conflicting_ind_types': {'size': 0, 'num': 0x16},
    'prob_random': {'size': 1, 'num': 0x17},
    'prob_in_game': {'size': 1, 'num': 0x18},
    'map_color': {'size': 1, 'num': 0x19},
    'spec_flags': {'size': 4, 'num': 0x1A},
    'new_ind_text': {'size': 2, 'num': 0x1B},
    'input_multiplier_1': {'size': 4, 'num': 0x1C},
    'input_multiplier_2': {'size': 4, 'num': 0x1D},
    'input_multiplier_3': {'size': 4, 'num': 0x1E},
    'name': {'size': 2, 'num': 0x1F, 'string': 0xDC},
    'prospect_chance': {'size': 4, 'num': 0x20, 'unit_conversion': 0xFFFFFFFF},
    'callback_flags_1': {'size': 1, 'num': 0x21},
    'callback_flags_2': {'size': 1, 'num': 0x22},
    'remove_cost_multiplier': {'size': 4, 'num': 0x23},
    'nearby_station_name': {'size': 2, 'num': 0x24, 'string': 0xDC},
}

class RailtypeListProp(object):
    def __init__(self, prop_num, railtype_list):
        self.prop_num = prop_num
        self.railtype_list = railtype_list

    def write(self, file):
        file.print_bytex(self.prop_num)
        file.print_byte(len(self.railtype_list))
        for railtype in self.railtype_list:
            railtype.write(file, 4)
        file.newline()

    def get_size(self):
        return len(self.railtype_list) * 4 + 2

def railtype_list(value, prop_num):
    if not isinstance(value, Array):
        raise generic.ScriptError("Railtype list must be an array of literal strings", value.pos)
    for val in value.values:
        if not isinstance(val, StringLiteral): raise generic.ScriptError("Railtype list must be an array of literal strings", val.pos)
    return [RailtypeListProp(prop_num, value.values)]

properties[0x10] = {
    'label': {'size': 4, 'num': 0x08, 'string_literal': 4},
    'name': {'size': 2, 'num': 0x09, 'string': 0xDC},
    'menu_text': {'size': 2, 'num': 0x0A, 'string': 0xDC},
    'build_window_caption': {'size': 2, 'num': 0x0B, 'string': 0xDC},
    'autoreplace_text': {'size': 2, 'num': 0x0C, 'string': 0xDC},
    'new_engine_text': {'size': 2, 'num': 0x0D, 'string': 0xDC},
    'compatible_railtype_list': {'custom_function': lambda x: railtype_list(x, 0x0E)},
    'powered_railtype_list': {'custom_function': lambda x: railtype_list(x, 0x0F)},
    'railtype_flags': {'size': 1, 'num': 0x10},
    'curve_speed_multiplier': {'size': 1, 'num': 0x11},
    'station_graphics': {'size': 1, 'num': 0x12},
    'construction_cost': {'size': 2, 'num': 0x13},
    'speed_limit': {'size': 2, 'num': 0x14, 'unit_type': 'speed', 'unit_conversion': 3.5790976},
    'acceleration_model': {'size': 1, 'num': 0x15},
    'map_color': {'size': 1, 'num': 0x16},
}

properties[0x11] = {
    'substitute': {'size': 1, 'num': 0x08},
    'override': {'size': 1, 'num': 0x09},
    'callback_flags': {'size': 1, 'num': 0x0E},
    'animation_info': {'size': 2, 'num': 0x0F},
    'animation_speed': {'size': 1, 'num': 0x10},
    'animation_triggers': {'size': 1, 'num': 0x11},
}
