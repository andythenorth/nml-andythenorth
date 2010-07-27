from nml.actions import action2
from nml import generic, expression, global_constants

class Action2Random(action2.Action2):
    def __init__(self, feature, name, type_byte, count, triggers, randbit, nrand, choices):
        action2.Action2.__init__(self, feature, name)
        self.type_byte = type_byte
        self.count = count
        self.triggers = triggers
        self.randbit = randbit
        self.nrand = nrand
        self.choices = choices

    def prepare_output(self):
        action2.Action2.prepare_output(self)
        for choice in self.choices:
            if isinstance(choice.result, expression.Identifier):
                choice.result = action2.remove_ref(choice.result.value)
            else:
                choice.result = choice.result.value | 0x8000

    def write(self, file):
        # <type> [<count>] <random-triggers> <randbit> <nrand> <set-ids>
        size = 4 + 2 * self.nrand + (self.count is not None)
        action2.Action2.write(self, file, size)
        file.print_bytex(self.type_byte)
        if self.count is not None: file.print_bytex(self.count)
        file.print_bytex(self.triggers)
        file.print_byte(self.randbit)
        file.print_bytex(self.nrand)
        file.newline()

        for choice in self.choices:
            for i in range(0, choice.resulting_prob):
                file.print_wordx(choice.result)
            file.newline()
        file.end_sprite()

class RandomChoice(object):
    def __init__ (self, probability, result):
        if isinstance(probability, expression.Identifier) and probability.value in ('dependent', 'independent'):
            self.probability = probability
        else:
            self.probability = probability.reduce_constant(global_constants.const_list)
            self.resulting_prob = self.probability.value
            if self.probability.value <= 0:
                raise generic.ScriptError("Value for probability should be higher than 0, encountered %d" % self.probability.value, self.probability.pos)
            if result is None:
                raise generic.ScriptError("Returning the computed value is not possible in a random_switch, as there is no computed value.", self.probability.pos)
        self.result = result.reduce(global_constants.const_list, False)

    def debug_print(self, indentation):
        print indentation*' ' + 'Probability:'
        self.probability.debug_print(indentation + 2)
        print indentation*' ' + 'Result:'
        if isinstance(self.result, expression.Identifier):
            print (indentation+2)*' ' + 'Go to switch:'
            self.result.debug_print(indentation + 4)
        else:
            self.result.debug_print(indentation + 2)

    def __str__(self):
        ret = str(self.probability)
        if isinstance(self.result, expression.Identifier):
            ret += ': %s;' % str(self.result)
        else:
            ret += ': return %s;' % str(self.result)
        return ret
