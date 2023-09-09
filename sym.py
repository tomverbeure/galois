

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
        s = f"({self.s})"
        return s

class SymLeafValue(SymNode):
    def __init__(self, val):
        self.val    = val

    def flatten(self):
        s = f"({self.val})"
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
    def __init__(self, a, b):
        self.node_a  = a
        self.node_b  = b

    def flatten(self):
        s = f"({self.node_a.flatten()} & {self.node_b.flatten()})"
        return s

class SymSum(SymNode):
    def __init__(self, a,b):
        self.node_a  = a
        self.node_b  = b

    def flatten(self):
        s = f"({self.node_a.flatten()} ^ {self.node_b.flatten()})"
        return s

class SymSumVector(SymNode):
    def __init__(self, vec):
        self.vec  = vec

    def flatten(self):
        s = ' ^ '.join(v.flatten() for v in self.vec)
        return s
