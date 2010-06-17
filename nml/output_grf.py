from output_base import OutputBase
import Image
import os
from lz77 import LZ77


class OutputGRF(OutputBase):
    def __init__(self, filename, compress_grf, crop_sprites):
        self.file = open(filename, 'wb')
        self.compress_grf = compress_grf
        self.crop_sprites = crop_sprites

    def close(self):
        #terminate with 6 zero bytes (zero-size sprite + checksum)
        i = 0
        while i < 6:
            self.wb(0)
            i += 1
        self.file.close()

    def wb(self, byte):
        self.file.write(chr(byte))

    def print_byte(self, value):
        value = self.prepare_byte(value)
        self.wb(value)

    def print_bytex(self, value, pretty_print = None):
        self.print_byte(value)

    def print_word(self, value):
        value = self.prepare_word(value)
        self.wb(value & 0xFF)
        self.wb(value >> 8)

    def print_wordx(self, value):
        self.print_word(value)

    def print_dword(self, value):
        value = self.prepare_dword(value)
        self.wb(value & 0xFF)
        self.wb((value >> 8) & 0xFF)
        self.wb((value >> 16) & 0xFF)
        self.wb(value >> 24)

    def print_dwordx(self, value):
        self.print_dword(value)

    def _print_utf8(self, char):
        for c in unichr(char).encode('utf8'):
            self.print_byte(ord(c))

    def print_string(self, value, final_zero = True, force_ascii = False):
        if not force_ascii:
            self.print_byte(0xC3)
            self.print_byte(0x9E)
        i = 0
        while i < len(value):
            if value[i] == '\\':
                if value[i+1] in ('\\', 'n', '"'):
                    self.print_byte(ord(value[i+1]))
                    i += 2
                elif value[i+1] == 'U':
                    self._print_utf8(int(value[i+2:i+6], 16))
                    i += 6
                else:
                    self.print_byte(int(value[i+1:i+3], 16))
                    i += 3
            else:
                self._print_utf8(ord(value[i]))
                i += 1
        if final_zero: self.print_byte(0)

    def print_decimal(self, value, size):
        self.print_varx(value, size)

    def print_sprite_size(self, size):
        self.print_word(size)
        self.print_byte(0xFF)

    def newline(self):
        pass

    def next_sprite(self, is_real_sprite):
        pass

    def print_sprite(self, filename, sprite_info):
        im = Image.open(filename.value)
        if im.mode != "P":
            raise "Image file '%s' does not have a palette" % str(filename)
        x = sprite_info.xpos.value
        y = sprite_info.ypos.value
        size_x = sprite_info.xsize.value
        size_y = sprite_info.ysize.value
        sprite = im.crop((x, y, x + size_x, y + size_y))
        self.wsprite(sprite, sprite_info.xrel.value, sprite_info.yrel.value, sprite_info.compression.value)

    def print_empty_realsprite(self):
        self.print_sprite_size(1)
        self.print_byte(0)

    def wsprite_header(self, sprite, size, xoffset, yoffset, compression):
        size_x, size_y = sprite.size
        self.print_word(size + 8)
        self.print_byte(compression)
        self.print_byte(size_y)
        self.print_word(size_x)
        self.print_word(xoffset)
        self.print_word(yoffset)

    def wsprite_encoderegular_fakecompress(self, sprite, data, xoffset, yoffset, compression):
        self.wsprite_header(sprite, len(data), xoffset, yoffset, compression)
        i = 0
        while i < len(data):
            l = min(len(data) - i, 127)
            self.print_byte(l)
            while l > 0:
                self.print_byte(data[i])
                i+=1
                l-=1

    def wsprite_encoderegular(self, sprite, data, xoffset, yoffset, compression):
        if not self.compress_grf:
            self.wsprite_encoderegular_fakecompress(sprite, data, xoffset, yoffset, compression)
            return

        lz = LZ77(data)
        stream = lz.Encode()
        if (compression & 2) == 0: size = len(data)
        else: size = len(stream)
        self.wsprite_header(sprite, size, xoffset, yoffset, compression)
        for c in stream:
            self.print_byte(c)


    def wsprite_encodetile(self, sprite, xoffset, yoffset, compression):
        data = list(sprite.getdata())
        size_x, size_y = sprite.size
        if size_x > 255: raise "TODO: sprites wider then 255px are not supported"
        data_output = []
        offsets = size_y * [0]
        for y in range(size_y):
            offsets[y] = len(data_output) + 2 * size_y
            row_data = data[y*size_x : (y+1)*size_x]
            last = size_x - 1
            while last >= 0 and row_data[last] == 0: last -= 1
            if last == -1:
                data_output += [0x80, 0]
                continue
            x1 = 0
            while True:
                while x1 < size_x and row_data[x1] == 0: x1 += 1
                x2 = x1 + 1
                while x2 < size_x and row_data[x2] != 0: x2 += 1
                high_byte = x2 - x1
                if x2 == last + 1: high_byte |= 0x80
                data_output.append(high_byte)
                data_output.append(x1)
                data_output += row_data[x1 : x2]
                if x2 == last + 1: break
                x1 = x2 + 1
        output = []
        for offset in offsets:
            output.append(offset & 0xFF)
            output.append(offset >> 8)
        output += data_output
        self.wsprite_encoderegular(sprite, output, xoffset, yoffset, compression)

    def crop_sprite(self, sprite, xoffset, yoffset):
        data = list(sprite.getdata())
        size_x, size_y = sprite.size

        #Crop the top of the sprite
        y = 0
        while y < size_y:
            x = 0
            while x < size_x:
                if data[y * size_x + x] != 0: break
                x += 1
            if x != size_x: break
            y += 1
        if y != 0:
            yoffset += y
            sprite = sprite.crop((0, y, size_x, size_y))
            data = list(sprite.getdata())
            size_y -= y

        #Crop the bottom of the sprite
        y = size_y - 1
        while y >= 0:
            x = 0
            while x < size_x:
                if data[y * size_x + x] != 0: break
                x += 1
            if x != size_x: break
            y -= 1
        if y != size_y - 1:
            sprite = sprite.crop((0, 0, size_x, y + 1))
            data = list(sprite.getdata())
            size_y = y + 1

        #Crop the left of the sprite
        x = 0
        while x < size_x:
            y = 0
            while y < size_y:
                if data[y * size_x + x] != 0: break
                y += 1
            if y != size_y: break
            x += 1
        if x != 0:
            xoffset += x
            sprite = sprite.crop((x, 0, size_x, size_y))
            data = list(sprite.getdata())
            size_x -= x

        #Crop the right of the sprite
        x = size_x - 1
        while x >= 0:
            y = 0
            while y < size_y:
                if data[y * size_x + x] != 0: break
                y += 1
            if y != size_y: break
            x -= 1
        if x != size_x - 1:
            sprite = sprite.crop((0, 0, x + 1, size_y))
        return (sprite, xoffset, yoffset)

    def wsprite(self, sprite, xoffset, yoffset, compression):
        if self.crop_sprites and (compression & 0x40 == 0):
            all_blue = True
            for p in sprite.getdata():
                if p != 0:
                    all_blue = False
                    break
            if all_blue:
                sprite = sprite.crop((0, 0, 1, 1))
                xoffset = 0
                yoffset = 0
            else:
                sprite, xoffset, yoffset = self.crop_sprite(sprite, xoffset, yoffset)
        compression &= ~0x40
        if compression == 9:
            self.wsprite_encodetile(sprite, xoffset, yoffset, compression)
        elif compression == 1 or compression == 3:
            self.wsprite_encoderegular(sprite, list(sprite.getdata()), xoffset, yoffset, compression)
        else:
            raise "Invalid sprite compression"

    def print_named_filedata(self, filename):
        name = os.path.split(filename)[1]
        size = os.path.getsize(filename)
        total = 2 + len(name) + 1 + size
        self.print_sprite_size(total)
        self.print_bytex(0xff)
        self.print_bytex(len(name))
        self.print_string(name, force_ascii = True, final_zero = True)  # ASCII filenames seems sufficient.
        fp = open(filename, 'rb')
        while True:
            data = fp.read(1024)
            if len(data) == 0: break
            for d in data:
                self.print_bytex(ord(d))
        fp.close()

