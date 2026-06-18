

class SymNode:
    def __init__(self):
        pass

    def flatten(self):
        return "<SymNode>"

    def __repr__(self):
        return self.flatten()

class SymSymbol(SymNode):
    def __init__(self, s):
        self.s      = s
    
    def flatten(self):
        s = f"{self.s}"
        return s

class SymLeafValue(SymNode):
    def __init__(self, val):
        self.val    = val

    def flatten(self):
        s = f"{self.val}"
        return s


class SymZero(SymLeafValue):
    def __init__(self):
        super().__init__(0)
        pass

class SymOne(SymLeafValue):
    def __init__(self):
        super().__init__(1)
        pass

class SymFactor(SymNode):
    nr_facts = 0

    def __init__(self, a, b):
        self.node_a  = a
        self.node_b  = b

        SymFactor.nr_facts += 1

    def flatten(self):
        s = f"({self.node_a.flatten()} & {self.node_b.flatten()})"
        return s

class SymSum(SymNode):
    nr_sums = 0

    def __init__(self, a, b=None):
        if b is None:
            vec = list(a)
            if len(vec) == 0:
                raise ValueError("SymSum vector must contain at least one operand")

            if len(vec) == 1:
                self.node_a = vec[0]
                self.node_b = None
                return

            mid = len(vec) // 2
            self.node_a = self.from_vec(vec[:mid])
            self.node_b = self.from_vec(vec[mid:])
        else:
            self.node_a  = a
            self.node_b  = b

        SymSum.nr_sums += 1

    def from_vec(self, vec):
        if len(vec) == 1:
            return vec[0]

        mid = len(vec) // 2
        return SymSum(self.from_vec(vec[:mid]), self.from_vec(vec[mid:]))


    def flatten(self):
        if self.node_b is None:
            return self.node_a.flatten()

        s = f"({self.node_a.flatten()} ^ {self.node_b.flatten()})"
        return s

class SymSumVector(SymNode):
    def __init__(self, vec):
        self.vec  = vec

        SymSum.nr_sums += len(vec)-1

    def flatten(self):
        s = ' ^ '.join(v.flatten() for v in self.vec)
        return s
