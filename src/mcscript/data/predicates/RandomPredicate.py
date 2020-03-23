from src.mcscript.data.predicates.PredicateGenerator import SimplePredicateGenerator


class RandomPredicate(SimplePredicateGenerator):
    def __init__(self):
        super().__init__("predicate_random_even")
