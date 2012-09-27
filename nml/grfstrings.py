from __future__ import with_statement

__license__ = """
NML is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

NML is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with NML; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA."""

import os, codecs, glob
from nml import generic

def utf8_get_size(char):
    if char < 128: return 1
    if char < 2048: return 2
    if char < 65536: return 3
    return 4

DEFAULT_LANGUAGE = 0x7F

def validate_string(string):
    """
    Check if a given string refers to a string that is translated in the language 
    files and raise an error otherwise.

    @param string: The string to validate.
    @type  string: L{expression.String}
    """
    if string.name.value not in default_lang.strings:
        raise generic.ScriptError('Unknown string "%s"' % string.name.value, string.pos)

def is_ascii_string(string):
    """
    Check whether a given string can be written using the ASCII codeset or
    that we need unicode.

    @param string: The string to check.
    @type  string: C{basestring}

    @return: True iff the string is ascii-only.
    @rtype:  C{bool}
    """
    assert isinstance(string, basestring)
    i = 0
    while i < len(string):
        if string[i] != '\\':
            if ord(string[i]) >= 0x7B:
                return False
            i += 1
        else:
            if string[i+1] in ('\\', '"'):
                i += 2
            elif string[i+1] == 'U':
                return False
            else:
                i += 3
    return True

def get_string_size(string, final_zero = True, force_ascii = False):
    """
    Get the size (in bytes) of a given string.

    @param string: The string to check.
    @type  string: C{basestring}

    @param final_zero: Whether or not to account for a zero-byte directly after the string.
    @type  final_zero: C{bool}

    @param force_ascii: When true, make sure the string is written as ascii as opposed to unicode.
    @type  force_ascii: C{bool}

    @return: The length (in bytes) of the given string.
    @rtype:  C{int}

    @raise generic.ScriptError: force_ascii and not is_ascii_string(string).
    """
    size = 0
    if final_zero: size += 1
    if not is_ascii_string(string):
        if force_ascii:
            raise generic.ScriptError("Expected ascii string but got a unicode string")
        size += 2
    i = 0
    while i < len(string):
        if string[i] != '\\':
            size += utf8_get_size(ord(string[i]))
            i += 1
        else:
            if string[i+1] in ('\\', '"'):
                size += 1
                i += 2
            elif string[i+1] == 'U':
                size += utf8_get_size(int(string[i+2:i+6], 16))
                i += 6
            else:
                size += 1
                i += 3
    return size

def get_translation(string, lang_id = DEFAULT_LANGUAGE):
    """
    Get the translation of a given string in a certain language. If there is no
    translation available in the given language return the default translation.

    @param string: the string to get the translation for.
    @type  string: L{expression.String}

    @param lang_id: The language id of the language to translate the string into.
    @type  lang_id: C{int}

    @return: Translation of the given string in the given language.
    @rtype:  C{unicode}
    """
    for lang_pair in langs:
        langid, lang = lang_pair
        if langid != lang_id: continue
        if string.name.value not in lang.strings: break
        return lang.get_string(string, lang_id)
    return default_lang.get_string(string, lang_id)

def get_translations(string):
    """
    Get a list of language ids that have a translation for the given string.

    @param string: the string to get the translations for.
    @type  string: L{expression.String}

    @return: List of languages that translate the given string.
    @rtype:  C{list} of C{int}
    """
    translations = []
    for lang_pair in langs:
        langid, lang = lang_pair
        assert langid is not None
        if string.name.value in lang.strings and lang.get_string(string, langid) != default_lang.get_string(string, langid):
            translations.append(langid)

    # Also check for translated substrings
    import nml.expression
    for param in string.params:
        if not isinstance(param, nml.expression.String): continue
        param_translations = get_translations(param)
        translations.extend([langid for langid in param_translations if not langid in translations])

    return translations

def com_parse_comma(val, lang_id):
    val = val.reduce_constant()
    return str(val)

def com_parse_hex(val, lang_id):
    val = val.reduce_constant()
    return "0x%X" % val.value

def com_parse_string(val, lang_id):
    import nml.expression
    if not isinstance(val, (nml.expression.StringLiteral, nml.expression.String)):
        raise generic.ScriptError("Expected a (literal) string", val.pos)
    if isinstance(val, nml.expression.String):
        # Check that the string exists
        if val.name.value not in default_lang.strings:
            raise generic.ScriptError("Substring \"%s\" does not exist" % val.name.value, val.pos)
        return get_translation(val, lang_id)
    return val.value

commands = {
# Special characters / glyphs
'':               {'unicode': r'\0D',       'ascii': r'\0D'},
'{':              {'unicode': r'{',         'ascii': r'{'  },
'NBSP':           {'unicode': r'\U00A0'}, # character A0 is used as up arrow in TTD, so don't use ASCII here.
'COPYRIGHT':      {'unicode': r'\U00A9',    'ascii': r'\A9'},
'TRAIN':          {'unicode': r'\UE0B4',    'ascii': r'\B4'},
'LORRY':          {'unicode': r'\UE0B5',    'ascii': r'\B5'},
'BUS':            {'unicode': r'\UE0B6',    'ascii': r'\B6'},
'PLANE':          {'unicode': r'\UE0B7',    'ascii': r'\B7'},
'SHIP':           {'unicode': r'\UE0B8',    'ascii': r'\B8'},

# Change the font size.
'TINYFONT':       {'unicode': r'\0E',       'ascii': r'\0E'},
'BIGFONT':        {'unicode': r'\0F',       'ascii': r'\0F'},

'COMMA':          {'unicode': r'\UE07B',    'ascii': r'\7B', 'size': 4, 'parse': com_parse_comma},
'SIGNED_WORD':    {'unicode': r'\UE07C',    'ascii': r'\7C', 'size': 2, 'parse': com_parse_comma},
'UNSIGNED_WORD':  {'unicode': r'\UE07E',    'ascii': r'\7E', 'size': 2, 'parse': com_parse_comma},
'CURRENCY':       {'unicode': r'\UE07F',    'ascii': r'\7F', 'size': 4},
'STRING':         {'unicode': r'\UE080',    'ascii': r'\80', 'allow_case': True, 'size': 2, 'parse': com_parse_string},
'DATE1920_LONG':  {'unicode': r'\UE082',    'ascii': r'\82', 'size': 2},
'DATE1920_SHORT': {'unicode': r'\UE083',    'ascii': r'\83', 'size': 2},
'VELOCITY':       {'unicode': r'\UE084',    'ascii': r'\84', 'size': 2},
'SKIP':           {'unicode': r'\UE085',    'ascii': r'\85', 'size': 2},
'VOLUME':         {'unicode': r'\UE087',    'ascii': r'\87', 'size': 2},
'HEX':            {'unicode': r'\UE09A\08', 'ascii': r'\9A\08', 'size': 4, 'parse': com_parse_hex},
'STATION':        {'unicode': r'\UE09A\0C', 'ascii': r'\9A\0C', 'size': 2},
'WEIGHT':         {'unicode': r'\UE09A\0D', 'ascii': r'\9A\0D', 'size': 2},
'DATE_LONG':      {'unicode': r'\UE09A\16', 'ascii': r'\9A\16', 'size': 4},
'DATE_SHORT':     {'unicode': r'\UE09A\17', 'ascii': r'\9A\17', 'size': 4},
'POWER':          {'unicode': r'\UE09A\18', 'ascii': r'\9A\18', 'size': 2},
'VOLUME_SHORT':   {'unicode': r'\UE09A\19', 'ascii': r'\9A\19', 'size': 2},
'WEIGHT_SHORT':   {'unicode': r'\UE09A\1A', 'ascii': r'\9A\1A', 'size': 2},

# Colors
'BLUE':           {'unicode': r'\UE088',    'ascii': r'\88'},
'SILVER':         {'unicode': r'\UE089',    'ascii': r'\89'},
'GOLD':           {'unicode': r'\UE08A',    'ascii': r'\8A'},
'RED':            {'unicode': r'\UE08B',    'ascii': r'\8B'},
'PURPLE':         {'unicode': r'\UE08C',    'ascii': r'\8C'},
'LTBROWN':        {'unicode': r'\UE08D',    'ascii': r'\8D'},
'ORANGE':         {'unicode': r'\UE08E',    'ascii': r'\8E'},
'GREEN':          {'unicode': r'\UE08F',    'ascii': r'\8F'},
'YELLOW':         {'unicode': r'\UE090',    'ascii': r'\90'},
'DKGREEN':        {'unicode': r'\UE091',    'ascii': r'\91'},
'CREAM':          {'unicode': r'\UE092',    'ascii': r'\92'},
'BROWN':          {'unicode': r'\UE093',    'ascii': r'\93'},
'WHITE':          {'unicode': r'\UE094',    'ascii': r'\94'},
'LTBLUE':         {'unicode': r'\UE095',    'ascii': r'\95'},
'GRAY':           {'unicode': r'\UE096',    'ascii': r'\96'},
'DKBLUE':         {'unicode': r'\UE097',    'ascii': r'\97'},
'BLACK':          {'unicode': r'\UE098',    'ascii': r'\98'},


# Deprecated string codes
'DWORD_S':        {'unicode': r'\UE07B',    'ascii': r'\7B', 'deprecated': True, 'size': 4},
'PARAM':          {'unicode': r'\UE07B',    'ascii': r'\7B', 'deprecated': True, 'size': 4},
'WORD_S':         {'unicode': r'\UE07C',    'ascii': r'\7C', 'deprecated': True, 'size': 2},
'BYTE_S':         {'unicode': r'\UE07D',    'ascii': r'\7D', 'deprecated': True},
'WORD_U':         {'unicode': r'\UE07E',    'ascii': r'\7E', 'deprecated': True, 'size': 2},
'POP_WORD':       {'unicode': r'\UE085',    'ascii': r'\85', 'deprecated': True, 'size': 2},
'CURRENCY_QWORD': {'unicode': r'\UE09A\01', 'ascii': r'\9A\01', 'deprecated': True},
'PUSH_WORD':      {'unicode': r'\UE09A\03', 'ascii': r'\9A\03', 'deprecated': True},
'UNPRINT':        {'unicode': r'\UE09A\04', 'ascii': r'\9A\04', 'deprecated': True},
'BYTE_HEX':       {'unicode': r'\UE09A\06', 'ascii': r'\9A\06', 'deprecated': True},
'WORD_HEX':       {'unicode': r'\UE09A\07', 'ascii': r'\9A\07', 'deprecated': True, 'size': 2},
'DWORD_HEX':      {'unicode': r'\UE09A\08', 'ascii': r'\9A\08', 'deprecated': True, 'size': 4},
'QWORD_HEX':      {'unicode': r'\UE09A\0B', 'ascii': r'\9A\0B', 'deprecated': True},
'WORD_S_TONNES':  {'unicode': r'\UE09A\0D', 'ascii': r'\9A\0D', 'deprecated': True, 'size': 2},
}

special_commands = [
'P',
'G',
'G=',
]

def read_extra_commands(custom_tags_file):
    """
    @param custom_tags_file: Filename of the custom tags file.
    @type  custom_tags_file: C{str}
    """
    if not os.access(custom_tags_file, os.R_OK):
        #Failed to open custom_tags.txt, ignore this
        return
    line_no = 0
    for line in codecs.open(custom_tags_file, "r", "utf-8"):
        line_no += 1
        line = line.strip()
        if len(line) == 0 or line[0] == "#":
            pass
        else:
            i = line.find(':')
            if i == -1:
                raise generic.ScriptError("Line has no ':' delimiter", generic.LinePosition(custom_tags_file, line_no))
            name = line[:i].strip()
            value = line[i+1:]
            if name in commands:
                generic.print_warning('Overwriting existing tag "' + name + '"')
            commands[name] = {'unicode': value}
            if is_ascii_string(value):
                commands[name]['ascii'] = value


class StringCommand(object):
    def __init__(self, name, str_pos, pos):
        assert name in commands or name in special_commands
        self.name = name
        self.case = None
        self.arguments = []
        self.offset = None
        self.str_pos = str_pos
        self.pos = pos

    def set_arguments(self, arg_string):
        start = -1
        cur = 0
        quoted = False
        whitespace = " \t"
        while cur < len(arg_string):
            if start != -1:
                if (quoted and arg_string[cur] == '"') or (not quoted and arg_string[cur] in whitespace):
                    if not quoted and self.offset is None and len(self.arguments) == 0 and isint(arg_string[start:cur]) and self.name in ('P', 'G'):
                        self.offset = int(arg_string[start:cur])
                    else:
                        self.arguments.append(arg_string[start:cur])
                    start = -1
            elif arg_string[cur] not in whitespace:
                quoted = arg_string[cur] == '"'
                start = cur + 1 if quoted else cur
            cur += 1
        if start != -1 and not quoted:
            self.arguments.append(arg_string[start:])
            start = -1
        return start == -1

    def validate_arguments(self, lang):
        if lang.langid == DEFAULT_LANGUAGE: return
        if self.name == 'P':
            if not lang.has_plural_pragma():
                raise generic.ScriptError("Using {P} without a ##plural pragma", self.pos)
            if len(self.arguments) != lang.get_num_plurals():
                raise generic.ScriptError("Invalid number of arguments to plural command, expected %d but got %d" % (lang.get_num_plurals(), len(self.arguments)), self.pos)
        elif self.name == 'G':
            if not lang.has_gender_pragma():
                raise generic.ScriptError("Using {G} without a ##gender pragma", self.pos)
            if len(self.arguments) != len(lang.genders):
                raise generic.ScriptError("Invalid number of arguments to gender command, expected %d but got %d" % (len(lang.genders), len(self.arguments)), self.pos)
        elif self.name == 'G=':
            if not lang.has_gender_pragma():
                raise generic.ScriptError("Using {G=} without a ##gender pragma", self.pos)
            if len(self.arguments) != 1:
                raise generic.ScriptError("Invalid number of arguments to set-gender command, expected %d but got %d" % (1, len(self.arguments)), self.pos)
        elif len(self.arguments) != 0:
            raise generic.ScriptError("Unexpected arguments to command \"%s\"" % self.name, self.pos)

    def parse_string(self, str_type, lang, wanted_lang_id, stack, static_args):
        if self.name in commands:
            if not self.is_important_command():
                return commands[self.name][str_type]
            stack_pos = 0
            for (pos, size) in stack:
                if pos == self.str_pos:
                    break
                stack_pos += size
            self_size = commands[self.name]['size']
            stack.remove((self.str_pos, self_size))
            if self.str_pos < len(static_args):
                if 'parse' not in commands[self.name]:
                    raise generic.ScriptError("Provided a static argument for string command '%s' which is invalid" % self.name, self.pos)
                # Parse commands using the wanted (not current) lang id, so translations are used if present
                return commands[self.name]['parse'](static_args[self.str_pos], wanted_lang_id)
            prefix = u''
            suffix = u''
            if self.case:
                prefix += STRING_SELECT_CASE[str_type] + '\\%02X' % self.case
            if stack_pos + self_size > 8:
                raise generic.ScriptError("Trying to read an argument from the stack without reading the arguments before", self.pos)
            if self_size == 4 and stack_pos == 4:
                prefix += STRING_ROTATE[str_type] + STRING_ROTATE[str_type]
            elif self_size == 4 and stack_pos == 2:
                prefix += STRING_PUSH_WORD[str_type] + STRING_ROTATE[str_type] + STRING_ROTATE[str_type]
                suffix += STRING_SKIP[str_type]
            elif self_size == 2 and stack_pos == 6:
                prefix += STRING_ROTATE[str_type]
            elif self_size == 2 and stack_pos == 4:
                prefix += STRING_PUSH_WORD[str_type] + STRING_ROTATE[str_type]
                suffix += STRING_SKIP[str_type]
            elif self_size == 2 and stack_pos == 2:
                prefix += STRING_PUSH_WORD[str_type] + STRING_PUSH_WORD[str_type] + STRING_ROTATE[str_type]
                suffix += STRING_SKIP[str_type] + STRING_SKIP[str_type]
            else:
                assert stack_pos == 0
            return prefix + commands[self.name][str_type] + suffix
        assert self.name in special_commands
        # Create a local copy because we shouldn't modify the original
        offset = self.offset
        if offset is None:
            if not stack:
                raise generic.ScriptError("A plural or gender choice list {P} or {G} has to be followed by another string code or provide an offset", self.pos)
            offset = stack[0][0]
        offset -= len(static_args)
        if self.name == 'P':
            if offset < 0:
                return self.arguments[lang.static_plural_form(static_args[offset]) - 1]
            ret = BEGIN_PLURAL_CHOICE_LIST[str_type] + '\\%02X' % (0x80 + offset)
            for idx, arg in enumerate(self.arguments):
                if idx == len(self.arguments) - 1:
                    ret += CHOICE_LIST_DEFAULT[str_type]
                else:
                    ret += CHOICE_LIST_ITEM[str_type] + '\\%02X' % (idx + 1)
                ret += arg
            ret += CHOICE_LIST_END[str_type]
            return ret
        if self.name == 'G':
            if offset < 0:
                return self.arguments[lang.static_gender(static_args[offset]) - 1]
            ret = BEGIN_GENDER_CHOICE_LIST[str_type] + '\\%02X' % (0x80 + offset)
            for idx, arg in enumerate(self.arguments):
                if idx == len(self.arguments) - 1:
                    ret += CHOICE_LIST_DEFAULT[str_type]
                else:
                    ret += CHOICE_LIST_ITEM[str_type] + '\\%02X' % (idx + 1)
                ret += arg
            ret += CHOICE_LIST_END[str_type]
            return ret

    def get_type(self):
        if self.name in commands:
            if 'ascii' in commands[self.name]: return 'ascii'
            else: return 'unicode'
        if self.name == 'P' or self.name == 'G':
            for arg in self.arguments:
                if not is_ascii_string(arg): return 'unicode'
        return 'ascii'

    def is_important_command(self):
        if self.name in special_commands: return False
        return 'size' in commands[self.name]

    def get_arg_size(self):
        return commands[self.name]['size']

# Characters that are valid in hex numbers
VALID_HEX = "0123456789abcdefABCDEF"
def is_valid_hex(string):
    return all(c in VALID_HEX for c in string)

def validate_escapes(string, pos):
    """
    Validate that all escapes (starting with a backslash) are correct.
    When an invalid escape is encountered, an error is thrown

    @param string: String to validate
    @type string: C{unicode}

    @param pos: Position information
    @type pos: L{Position}
    """
    i = 0
    while i < len(string):
        # find next '\'
        i = string.find('\\', i)
        if i == -1: break

        if i+1 >= len(string):
            raise generic.ScriptError("Unexpected end-of-line encountered after '\\'", pos)
        if string[i+1] in ('\\', '"'):
            i += 2
        elif string[i+1] == 'U':
            if i+5 >= len(string) or not is_valid_hex(string[i+2:i+6]):
                raise generic.ScriptError("Expected 4 hexadecimal characters after '\\U'", pos)
            i += 6
        else:
            if i+2 >= len(string) or not is_valid_hex(string[i+1:i+3]):
                raise generic.ScriptError("Expected 2 hexadecimal characters after '\\'", pos)
            i += 3

class NewGRFString(object):
    def __init__(self, string, lang, pos):
        validate_escapes(string, pos)
        self.string = string
        self.cases = {}
        self.components = []
        self.pos = pos
        idx = 0
        while idx < len(string):
            if string[idx] != '{':
                j = string.find('{', idx)
                if j == -1:
                    self.components.append(string[idx:])
                    break
                self.components.append(string[idx:j])
                idx = j

            start = idx + 1
            end = start
            cmd_pos = None
            if start >= len(string):
                raise generic.ScriptError("Expected '}' before end-of-line.", pos)
            if string[start].isdigit():
                while end < len(string) and string[end].isdigit(): end += 1
                if end == len(string) or string[end] != ':':
                    raise generic.ScriptError("Error while parsing position part of string command", pos)
                cmd_pos = int(string[start:end])
                start = end + 1
                end = start
            #Read the command name
            while end < len(string) and string[end] not in '} =.': end += 1
            command_name = string[start:end]
            if end < len(string) and string[end] == '=':
                command_name += '='
            if command_name not in commands and command_name not in special_commands:
                raise generic.ScriptError("Undefined command \"%s\"" % command_name, pos)
            if command_name in commands and 'deprecated' in commands[command_name]:
                generic.print_warning("String code '%s' has been deprecated and will be removed soon" % command_name, pos)
                del commands[command_name]['deprecated']
            #
            command = StringCommand(command_name, cmd_pos, pos)
            if end >= len(string):
                raise generic.ScriptError("Missing '}' from command \"%s\"" % string[start:], pos)
            if string[end] == '.':
                if command_name not in commands or 'allow_case' not in commands[command_name]:
                    raise generic.ScriptError("Command \"%s\" can't have a case" % command_name, pos)
                case_start = end + 1
                end = case_start 
                while end < len(string) and string[end] not in '} ': end += 1
                case = string[case_start:end]
                if lang.cases is None or case not in lang.cases:
                    raise generic.ScriptError("Invalid case-name \"%s\"" % case, pos)
                command.case = lang.cases[case]
            if string[end] != '}':
                command.argument_is_assigment = string[end] == '='
                arg_start = end + 1
                end = string.find('}', end + 1)
                if end == -1 or not command.set_arguments(string[arg_start:end]):
                    raise generic.ScriptError("Missing '}' from command \"%s\"" % string[start:], pos)
            command.validate_arguments(lang)
            if command_name == 'G=' and self.components:
                raise generic.ScriptError("Set-gender command {G=} must be at the start of the string", pos)
            self.components.append(command)
            idx = end + 1

        if len(self.components) > 0 and isinstance(self.components[0], StringCommand) and self.components[0].name == 'G=':
            self.gender = self.components[0].arguments[0]
            if self.gender not in lang.genders:
                raise generic.ScriptError("Invalid gender name '%s'" % self.gender, pos)
            self.components.pop(0)
        else:
            self.gender = None
        cmd_pos = 0
        for cmd in self.components:
            if not (isinstance(cmd, StringCommand) and cmd.is_important_command()):
                continue
            if cmd.str_pos is None:
                cmd.str_pos = cmd_pos
            cmd_pos = cmd.str_pos + 1

    def get_type(self):
        for comp in self.components:
            if isinstance(comp, StringCommand):
                if comp.get_type() == 'unicode':
                    return 'unicode'
            else:
                if not is_ascii_string(comp): return 'unicode'
        for case in self.cases.values():
            if case.get_type() == 'unicode':
                return 'unicode'
        return 'ascii'

    def remove_non_default_commands(self):
        i = 0
        while i < len(self.components):
            comp = self.components[i]
            if isinstance(comp, StringCommand):
                if comp.name == 'P' or comp.name == 'G':
                    self.components[i] = comp.arguments[-1] if comp.arguments else ""
            i += 1

    def parse_string(self, str_type, lang, wanted_lang_id, static_args):
        ret = ""
        stack = [(idx, size) for idx, size in enumerate(self.get_command_sizes())]
        for comp in self.components:
            if isinstance(comp, StringCommand):
                ret += comp.parse_string(str_type, lang, wanted_lang_id, stack, static_args)
            else:
                ret += comp
        return ret

    def get_command_sizes(self):
        sizes = {}
        for cmd in self.components:
            if not (isinstance(cmd, StringCommand) and cmd.is_important_command()):
                continue
            if cmd.str_pos in sizes:
                raise generic.ScriptError("Two or more string commands are using the same argument", self.pos)
            sizes[cmd.str_pos] = cmd.get_arg_size()
        sizes_list = []
        for idx in range(len(sizes)):
            if idx not in sizes:
                raise generic.ScriptError("String argument %d is not used" % idx, self.pos)
            sizes_list.append(sizes[idx])
        return sizes_list

    def match_commands(self, other_string):
        return self.get_command_sizes() == other_string.get_command_sizes()

def isint(x, base = 10):
    try:
        int(x, base)
        return True
    except ValueError:
        return False

NUM_PLURAL_FORMS = 12

CHOICE_LIST_ITEM         = {'unicode': r'\UE09A\10', 'ascii': r'\9A\10'}
CHOICE_LIST_DEFAULT      = {'unicode': r'\UE09A\11', 'ascii': r'\9A\11'}
CHOICE_LIST_END          = {'unicode': r'\UE09A\12', 'ascii': r'\9A\12'}
BEGIN_GENDER_CHOICE_LIST = {'unicode': r'\UE09A\13', 'ascii': r'\9A\13'}
BEGIN_CASE_CHOICE_LIST   = {'unicode': r'\UE09A\14', 'ascii': r'\9A\14'}
BEGIN_PLURAL_CHOICE_LIST = {'unicode': r'\UE09A\15', 'ascii': r'\9A\15'}
SET_STRING_GENDER        = {'unicode': r'\UE09A\0E', 'ascii': r'\9A\0E'}
STRING_SKIP              = {'unicode': r'\UE085',    'ascii': r'\85'}
STRING_ROTATE            = {'unicode': r'\UE086',    'ascii': r'\86'}
STRING_PUSH_WORD         = {'unicode': r'\UE09A\03\20\20', 'ascii': r'\9A\03\20\20'}
STRING_SELECT_CASE       = {'unicode': r'\UE09A\0F', 'ascii': r'\9A\0F'}

# Mapping of language names to their code, borrowed from OpenTTD.
LANG_NAMES = {'af_ZA' : 0x1b,
              'ar_EG' : 0x14,
              'be_BY' : 0x10,
              'bg_BG' : 0x18,
              'ca_ES' : 0x22,
              'cs_CZ' : 0x15,
              'cv_RU' : 0x0B,
              'cy_GB' : 0x0f,
              'da_DK' : 0x2d,
              'de_DE' : 0x02,
              'el_GR' : 0x1e,
              'en_AU' : 0x3D,
              'en_GB' : 0x01,
              'en_US' : 0x00,
              'eo_EO' : 0x05,
              'es_ES' : 0x04,
              'et_EE' : 0x34,
              'eu_ES' : 0x21,
              'fa_IR' : 0x62,
              'fi_FI' : 0x35,
              'fo_FO' : 0x12,
              'fr_FR' : 0x03,
              'fy_NL' : 0x32,
              'ga_IE' : 0x08,
              'gl_ES' : 0x31,
              'he_IL' : 0x61,
              'hr_HR' : 0x38,
              'hu_HU' : 0x24,
              'id_ID' : 0x5a,
              'io_IO' : 0x06,
              'is_IS' : 0x29,
              'it_IT' : 0x27,
              'ja_JP' : 0x39,
              'ko_KR' : 0x3a,
              'lb_LU' : 0x23,
              'lt_LT' : 0x2b,
              'lv_LV' : 0x2a,
              'mk_MK' : 0x26,
              'mr_IN' : 0x11,
              'ms_MY' : 0x3c,
              'mt_MT' : 0x09,
              'nb_NO' : 0x2f,
              'nl_NL' : 0x1f,
              'nn_NO' : 0x0e,
              'pl_PL' : 0x30,
              'pt_BR' : 0x37,
              'pt_PT' : 0x36,
              'ro_RO' : 0x28,
              'ru_RU' : 0x07,
              'sk_SK' : 0x16,
              'sl_SI' : 0x2c,
              'sr_RS' : 0x0d,
              'sv_SE' : 0x2e,
              'ta_IN' : 0x0A,
              'th_TH' : 0x42,
              'tr_TR' : 0x3e,
              'uk_UA' : 0x33,
              'ur_PK' : 0x5c,
              'vi_VN' : 0x54,
              'zh_CN' : 0x56,
              'zh_TW' : 0x0c,
             }

class Language(object):
    """
    @ivar default: Whether the language is the default language.
    @type default: C{bool}

    @ivar langid: Language id of the language, if known.
    @type langid: C{None} or C{int}

    @ivar plural: Plural type.
    @type plural: C{None} or C{int}

    @ivar genders:
    @type genders:

    @ivar gender_map:
    @type gender_map:

    @ivar cases:
    @type cases:

    @ivar case_map:
    @type case_map:

    @ivar strings: Language strings of the file.
    @type strings: C{dict} of
    """
    def __init__(self, default):
        self.default = default
        self.langid = None
        self.plural = None
        self.genders = None
        self.gender_map = {}
        self.cases = None
        self.case_map = {}
        self.strings = {}

    def get_num_plurals(self):
        if self.plural is None: return 0
        num_plurals = {
            0: 2,
            1: 1,
            2: 2,
            3: 3,
            4: 5,
            5: 3,
            6: 3,
            7: 3,
            8: 4,
            9: 2,
            10: 3,
            11: 2,
            12: 4,
        }
        return num_plurals[self.plural]
        
    def has_plural_pragma(self):
        return self.plural is not None
    
    def has_gender_pragma(self):
        return self.genders is not None

    def static_gender(self, expr):
        import nml.expression
        if isinstance(expr, nml.expression.StringLiteral):
            return len(self.genders)
        if not isinstance(expr, nml.expression.String):
            raise generic.ScriptError("{G} can only refer to a string argument")
        parsed = self.get_string(expr, self.langid)
        if parsed.find(SET_STRING_GENDER['ascii']) == 0:
            return int(parsed[len(SET_STRING_GENDER['ascii']) + 1 : len(SET_STRING_GENDER['ascii']) + 3], 16)
        if parsed.find(SET_STRING_GENDER['unicode']) == 0:
            return int(parsed[len(SET_STRING_GENDER['unicode']) + 1 : len(SET_STRING_GENDER['unicode']) + 3], 16)
        return len(self.genders)

    def static_plural_form(self, expr):
        #Return values are the same as "Plural index" here:
        #http://newgrf-specs.tt-wiki.net/wiki/StringCodes#Using_plural_forms
        val = expr.reduce_constant().value
        if self.plural == 0:
            return 1 if val == 1 else 2
        if self.plural == 1:
            return 1
        if self.plural == 2:
            return 1 if val in (0, 1) else 2
        if self.plural == 3:
            if val % 10 == 1 and val % 100 != 11:
                return 1
            return 2 if val == 0 else 3
        if self.plural == 4:
            if val == 1:
                return 1
            if val == 2:
                return 2
            if 3 <= val <= 6:
                return 3
            if 7 <= val <= 10:
                return 4
            return 5
        if self.plural == 5:
            if val % 10 == 1 and val % 100 != 11:
                return 1
            if 2 <= (val % 10) <= 9 and not 12 <= (val % 100) <= 19:
                return 2
            return 3
        if self.plural == 6:
            if val % 10 == 1 and val % 100 != 11:
                return 1
            if 2 <= (val % 10) <= 4 and not 12 <= (val % 100) <= 14:
                return 2
            return 3
        if self.plural == 7:
            if val == 0:
                return 1
            if 2 <= (val % 10) <= 4 and not 12 <= (val % 100) <= 14:
                return 2
            return 3
        if self.plural == 8:
            if val % 100 == 1:
                return 1
            if val % 100 == 2:
                return 2
            if val % 100 in (3, 4):
                return 3
            return 4
        if self.plural == 9:
            if val % 10 == 1 and val % 100 != 11:
                return 1
            return 2
        if self.plural == 10:
            if val == 1:
                return 1
            if 2 <= val <= 4:
                return 2
            return 3
        if self.plural == 11:
            if val % 10 in (0, 1, 3, 6, 7, 8):
                return 1
            return 2
        if self.plural == 12:
            if val == 1:
                return 1
            if val == 0 or 2 <= (val % 100) <= 10:
                return 2
            if 11 <= (val % 100) <= 19:
                return 3
            return 4
        assert False, "Unknown plural type"

    def get_string(self, string, lang_id):
        """
        Lookup up a string by name/params and return the actual created string

        @param string: String object
        @type string: L{expression.String}

        @param lang_id: Language ID we are actually looking for. 
                This may differ from the ID of this language,
                if the string is missing from the target language.
        @type lang_id: C{int}

        @return: The created string
        @rtype: C{basestring}
        """
        string_id = string.name.value
        assert isinstance(string_id, basestring)
        assert string_id in self.strings
        assert lang_id == self.langid or self.langid == DEFAULT_LANGUAGE

        str_type = self.strings[string_id].get_type()
        parsed_string = ""
        if self.strings[string_id].gender is not None:
            parsed_string += SET_STRING_GENDER[str_type] + '\\%02X' % self.genders[self.strings[string_id].gender]
        if len(self.strings[string_id].cases) > 0:
            parsed_string += BEGIN_CASE_CHOICE_LIST[str_type]
            for case_name, case_string in self.strings[string_id].cases.iteritems():
                case_id = self.cases[case_name]
                parsed_string += CHOICE_LIST_ITEM[str_type] + ('\\%02X' % case_id) + case_string.parse_string(str_type, self, lang_id, string.params)
            parsed_string += CHOICE_LIST_DEFAULT[str_type]
        parsed_string += self.strings[string_id].parse_string(str_type, self, lang_id, string.params)
        if len(self.strings[string_id].cases) > 0:
            parsed_string += CHOICE_LIST_END[str_type]
        return parsed_string

    def handle_grflangid(self, data, pos):
        """
        Handle a 'grflangid' pragma.

        @param data: Data of the pragma.
        @type  data: C{unicode}
        """
        if self.langid is not None:
            raise generic.ScriptError("grflangid already set", pos)
        lang_text = data[1].strip()
        value = LANG_NAMES.get(lang_text)
        if value is None:
            try:
                value = int(lang_text, 16)
            except ValueError:
                raise generic.ScriptError("Invalid grflangid %r" % lang_text, pos)
        if value < 0 or value >= 0x7F:
            raise generic.ScriptError("Invalid grflangid", pos)
        self.langid = value

    def handle_plural(self, data, pos):
        """
        Handle a 'plural' pragma.

        @param data: Data of the pragma.
        @type  data: C{unicode}
        """
        if self.plural is not None:
            raise generic.ScriptError("plural form already set", pos)
        try:
            value = int(data[1], 16)
        except ValueError:
            raise generic.ScriptError("Invalid plural form", pos)
        if value < 0 or value > NUM_PLURAL_FORMS:
            raise generic.ScriptError("Invalid plural form", pos)
        self.plural = value


    def handle_gender(self, data, pos):
        """
        Handle a 'gender' pragma.

        @param data: Data of the pragma.
        @type  data: C{unicode}
        """
        if self.genders is not None:
            raise generic.ScriptError("Genders already defined", pos)
        self.genders = {}
        for idx, gender in enumerate(data[1].split()):
            self.genders[gender] = idx + 1
            self.gender_map[gender] = []

    def handle_map_gender(self, data, pos):
        """
        Handle a 'map_gender' pragma.

        @param data: Data of the pragma.
        @type  data: C{unicode}
        """
        if self.genders is None:
            raise generic.ScriptError("##map_gender is not allowed before ##gender", pos)
        genders = data[1].split()
        if len(genders) != 2:
            raise generic.ScriptError("Invalid ##map_gender line", pos)
        if genders[0] not in self.genders: 
            raise generic.ScriptError("Trying to map non-existing gender '%s'" % genders[0], pos)
        self.gender_map[genders[0]].append(genders[1])

    def handle_case(self, data, pos):
        """
        Handle a 'case' pragma.

        @param data: Data of the pragma.
        @type  data: C{unicode}
        """
        if self.cases is not None:
            raise generic.ScriptError("Cases already defined", pos)
        self.cases = {}
        for idx, case in enumerate(data[1].split()):
            self.cases[case] = idx + 1
            self.case_map[case] = []

    def handle_map_case(self, data, pos):
        """
        Handle a 'map_case' pragma.

        @param data: Data of the pragma.
        @type  data: C{unicode}
        """
        if self.cases is None:
            raise generic.ScriptError("##map_case is not allowed before ##case", pos)
        cases = data[1].split()
        if len(cases) != 2:
            raise generic.ScriptError("Invalid ##map_case line", pos)
        if cases[0] not in self.cases:
            raise generic.ScriptError("Trying to map non-existing case '%s'" % cases[0], pos)
        self.case_map[cases[0]].append(cases[1])

    def handle_text(self, data, pos):
        """
        Handle a text string.

        @param data: Data of the pragma.
        @type  data: C{unicode}
        """
        _type, string, case, value = data

        if string in self.strings and case is None:
            raise generic.ScriptError("String name \"%s\" is used multiple times" % string, pos)

        if self.default:
            self.strings[string] = NewGRFString(value, self, pos)
            self.strings[string].remove_non_default_commands()
        else:
            if string not in default_lang.strings:
                generic.print_warning("String name \"%s\" does not exist in master file" % string, pos)
                return

            newgrf_string = NewGRFString(value, self, pos)
            if not default_lang.strings[string].match_commands(newgrf_string):
                generic.print_warning("String commands don't match with english.lng", pos)
                return

            if case is None:
                self.strings[string] = newgrf_string
            else:
                if string not in self.strings:
                    generic.print_warning("String with case used before the base string", pos)
                    return
                if self.cases is None or case not in self.cases:
                    generic.print_warning("Invalid case name \"%s\"" % case, pos)
                    return
                if case in self.strings[string].cases:
                    raise generic.ScriptError("String name \"%s.%s\" is used multiple times" % (string, case), pos)
                if newgrf_string.gender:
                    generic.print_warning("Case-strings can't set the gender, only the base string can", pos)
                    return
                self.strings[string].cases[case] = newgrf_string



    def scan_line(self, line, pos):
        """
        Scan a line of a language file.

        @param line: Line to scan.
        @type  line: C{unicode}

        @param pos: Position information of the line.
        @type  pos: L{Position}

        @return: Contents of the scanned line:
                  - C{None} Nothing of interest found.
                  - (<pragma>, <value>) A pragma line has been found.
                  - ('string', <case>, <value>) A string with optional case has been found.
        @rtype:  C{None} or a C{tuple}
        """
        if len(line) == 0: return None # Silently ignore empty lines.

        if line[0] == '#':
            if len(line) > 2 and line[1] == '#' and line[2] != '#':
                # "##pragma" line.
                if self.default: return None # Default language ignores all pragmas.

                if line[:12] == "##grflangid ":  return ('grflangid',  line[12:])
                if line[:9]  == "##plural ":     return ('plural',     line[9:])
                if line[:9]  == "##gender ":     return ('gender',     line[9:])
                if line[:13] == "##map_gender ": return ('map_gender', line[13:])
                if line[:11] == "##map_case ":   return ('map_case',   line[11:])
                if line[:7]  == "##case ":       return ('case',       line[7:])
                raise generic.ScriptError("Invalid pragma", pos)

            return None # Normal comment

        # Must be a line defining a string.
        i = line.find(':')
        if i == -1:
            raise generic.ScriptError("Line has no ':' delimiter", pos)

        name = line[:i].strip()
        value = line[i + 1:]
        i = name.find('.') # Find a case.
        if i > 0:
            case = name[i + 1:]
            name = name[:i]
        else:
            case = None

        if self.default and case is not None: return None # Ignore cases for the default language
        return ('string', name, case, value)


    def handle_string(self, line, pos):
        funcs = { 'grflangid'  : self.handle_grflangid,
                  'plural'     : self.handle_plural,
                  'gender'     : self.handle_gender,
                  'map_gender' : self.handle_map_gender,
                  'map_case'   : self.handle_map_case,
                  'case'       : self.handle_case,
                  'string'     : self.handle_text }

        res = self.scan_line(line, pos)
        if res is not None: funcs[res[0]](res, pos)


default_lang = Language(True)
default_lang.langid = DEFAULT_LANGUAGE
langs = []

def parse_file(filename, default):
    """
    Read and parse a single language file.

    @param filename: The filename of the file to parse.
    @type  filename: C{str}

    @param default: True iff this is the default language.
    @type  default: C{bool}
    """
    lang = Language(False)
    try:
        with codecs.open(filename, "r", "utf-8") as f:
            for idx, line in enumerate(f):
                pos = generic.LinePosition(filename, idx + 1)
                line = line.rstrip('\n\r').lstrip(u'\uFEFF')
                # The default language is processed twice here. Once as fallback langauge
                # and once as normal language.
                if default: default_lang.handle_string(line, pos)
                lang.handle_string(line, pos)
    except UnicodeDecodeError:
        if default:
            raise generic.ScriptError("The default language file (\"%s\") contains non-utf8 characters." % filename)
        generic.print_warning("Language file \"%s\" contains non-utf8 characters. Ignoring (part of) the contents" % filename)
    except generic.ScriptError, err:
        if default: raise
        generic.print_warning("Error in language file \"%s\": %s" % (filename, err))
    else:
        if lang.langid is None:
            generic.print_warning("Language file \"%s\" does not contain a ##grflangid pragma" % filename)
        else:
            langs.append((lang.langid, lang))

def read_lang_files(lang_dir, default_lang_file):
    """
    Read the language files containing the translations for string constants
    used in the NML specification.

    @param lang_dir: Name of the directory containing the language files.
    @type  lang_dir: C{str}

    @param default_lang_file: Filename of the language file that has the
                              default translation which will be used as
                              fallback for other languages.
    @type  default_lang_file: C{str}
    """
    if not os.path.exists(lang_dir + os.sep + default_lang_file):
        generic.print_warning("Default language file \"%s\" doesn't exist" % (lang_dir + os.sep + default_lang_file))
        return
    parse_file(lang_dir + os.sep + default_lang_file, True)
    for filename in glob.glob(lang_dir + os.sep + "*.lng"):
        if filename.endswith(default_lang_file): continue
        parse_file(filename, False)
    langs.sort()
