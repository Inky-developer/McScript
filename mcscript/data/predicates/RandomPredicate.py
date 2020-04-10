from mcscript.data.predicates.predicateGenerator import SimplePredicateGenerator


class RandomPredicate(SimplePredicateGenerator):
    def __init__(self):
        super().__init__("predicate_random_even")
