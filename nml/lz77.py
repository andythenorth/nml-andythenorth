
class LZ77(object):
    def __init__(self, data):
        self.position = 0
        self.stream = data

    def Encode(self):
        output = ""
        literal_bytes = ""
        while self.position < len(self.stream):
            overlap_len = 0
            # Loop through the lookahead buffer.
            for i in range(3, min(len(self.stream) - self.position + 1, 16)):
                # Set pattern to find the longest match.
                pattern = self.stream[self.position:self.position+i]
                # Find the pattern match in the window.
                start_pos = max(0, self.position - (1 << 11) + 1)
                result = self.stream.find(pattern, start_pos, self.position)
                # If match failed, we've found the longest.
                if result < 0: break
                p = self.position - result
                overlap_len = i
            if overlap_len > 0:
                if len(literal_bytes) > 0:
                    output += chr(len(literal_bytes))
                    output += literal_bytes
                    literal_bytes = ""
                val = ((-overlap_len) << 3) & 0xFF | (p >> 8)
                if val < 0: val += 256
                output += chr(val)
                output += chr(p & 0xFF)
                self.position += overlap_len
            else:
                literal_bytes += self.stream[self.position]
                if len(literal_bytes) == 0x80:
                    output += chr(0)
                    output += literal_bytes
                    literal_bytes = ""
                self.position += 1
        if len(literal_bytes) > 0:
            output += chr(len(literal_bytes))
            output += literal_bytes
        return output

