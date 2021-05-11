from typing import Generic
from typing import TypeVar
from typing import NewType
from typing import Mapping
from typing import Callable

A = TypeVar('A')

R = TypeVar('R')

class Predicate(Generic[A]): # Predicate[A] = Callable[A,bool] - unsupported by Python at the moment
    '''
    Predicate along with text description
    '''
    def __init__(self, expr: str, fn: Callable[[A], bool]):
        self.expr = expr
        self.fn = fn

    def __call__(self, a: A) -> bool:
        return self.fn(a)

    def And(self, other: 'Predicate[A]') -> 'Predicate[A]':
        return Predicate(self.expr + " and " + other.expr, lambda a: self(a) and other(a))

    def Or(self, other: 'Predicate[A]') -> 'Predicate[A]':
        return Predicate(self.expr + " or " + other.expr, lambda a: self(a) or other(a))

    def Not(self) -> 'Predicate[A]':
        return Predicate("not " + self.expr, lambda a: not self(a))

    def parens(self) -> 'Predicate[A]':
        return Predicate("(" + self.expr + ")", self.fn)

class TreeNode(Generic[A, R]):# in fact it's callable(Callable[[A], R]):
    """Root class representing an arbitrary tree node - either branching or result"""

    def __call__(self, a: A) -> R:
        pass


class DecisionTreeNode(TreeNode[A, R]):
    """Class represents a branching decision tree node"""
    def __init__(self, name, predicate: Predicate[A], on_true: TreeNode[A, R], on_false: TreeNode[A, R]):
        self.name = name
        self.predicate = predicate
        self.on_true = on_true
        self.on_false = on_false

    def __call__(self, a: A) -> R:
        flag = self.predicate(a)
        print(self.predicate.expr + " = " + str(flag))
        if  flag:
            return self.on_true(a)
        else:
            return self.on_false(a)


class ResultTreeNode(TreeNode[A, R]):
    """Only returns the result """

    def __init__(self, fn: Callable[[A], R]):
        self.fn = fn

    def __call__(self, a: A) -> R:
        return self.fn(a)
    
