from src.mcscript.data.predicates.PredicateGenerator import SimplePredicateGenerator


class WeatherPredicate(SimplePredicateGenerator):
    def __init__(self):
        super().__init__("predicate_weather_raining", "predicate_weather_thundering")
