# -*- coding: utf-8 -*-
from nml import generic
from output_base import OutputBase
import codecs
from nml import grfstrings

class OutputNFO(OutputBase):
    def __init__(self, filename):
        OutputBase.__init__(self)
        self.sprite_num = 0
        self.file = codecs.open(filename, 'w', 'utf-8')
        self.file.write('// Automatically generated by GRFCODEC. Do not modify!\n'
                        '// (Info version 7)\n'
                        '// Escapes: 2+ = 71 = D= = DR 2- = 70 = D+ = DF 2< = 7= = D- = DC 2> = 7! = Du* = DM 2u< = 7< = D* '
                                '= DnF 2u> = 7> = Du<< = DnC 2/ = 7G = D<< = DO 2% = 7g = D& 2u/ = 7gG = D| 2u% = 7GG '
                                '= Du/ 2* = 7gg = D/ 2& = 7c = Du% 2| = 7C = D% 2^ 2sto = 2s 2rst = 2r 2+ 2ror = 2rot\n'
                        '// Format: spritenum pcxfile xpos ypos compression ysize xsize xrel yrel\n\n')

    def close(self):
        assert not self._in_sprite
        self.file.close()

    def print_byte(self, value):
        value = self.prepare_byte(value)
        self.file.write("\\b" + str(value) + " ")

    def print_bytex(self, value, pretty_print = None):
        value = self.prepare_byte(value)
        if pretty_print is not None:
            self.file.write(pretty_print + " ")
            return
        self.file.write(generic.to_hex(value, 2) + " ")

    def print_word(self, value):
        value = self.prepare_word(value)
        self.file.write("\\w" + str(value) + " ")

    def print_wordx(self, value):
        value = self.prepare_word(value)
        self.file.write("\\wx" + generic.to_hex(value, 4) + " ")

    def print_dword(self, value):
        value = self.prepare_dword(value)
        self.file.write("\\d" + str(value) + " ")

    def print_dwordx(self, value):
        value = self.prepare_dword(value)
        self.file.write("\\dx" + generic.to_hex(value, 8) + " ")

    def print_string(self, value, final_zero = True, force_ascii = False):
        assert self._in_sprite
        self.file.write('"')
        if not force_ascii:
            self.file.write(u'Þ')
            self._byte_count += 2
        self.file.write(value)
        self._byte_count += grfstrings.get_string_size(value)
        self.file.write('" ')
        if final_zero: self.print_bytex(0)

    def print_decimal(self, value, size = None):
        assert self._in_sprite
        self.file.write(str(value) + " ")

    def newline(self):
        self.file.write("\n")

    def start_sprite(self, size, is_real_sprite = False):
        OutputBase.start_sprite(self, size)
        self.print_decimal(self.sprite_num, 2)
        self.sprite_num += 1
        if not is_real_sprite:
            self.file.write("* ")
            self.print_decimal(size)

    def print_sprite(self, filename, sprite_info):
        self.start_sprite(1, True)
        self.file.write(filename.value + " ")
        self.print_decimal(sprite_info.xpos.value)
        self.print_decimal(sprite_info.ypos.value)
        self.print_bytex(sprite_info.compression.value)
        self.print_decimal(sprite_info.ysize.value)
        self.print_decimal(sprite_info.xsize.value)
        self.print_decimal(sprite_info.xrel.value)
        self.print_decimal(sprite_info.yrel.value)
        self.end_sprite()

    def print_empty_realsprite(self):
        self.start_sprite(1)
        self.print_bytex(0)
        self.end_sprite()

    def print_named_filedata(self, filename):
        self.start_sprite(0, True)
        self.file.write("** " + filename)
        self.end_sprite()
