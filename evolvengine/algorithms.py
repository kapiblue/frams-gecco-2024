import deap.algorithms

from . import types
from .experiments.dpga import dpga


def resolve_algorithm(
    config: types.RunConfig,
) -> types.EvolutionaryAlgorithm:
    if config.meta == types.MetaAlgorithm.SIMPLE:
        return deap.algorithms.eaSimple
    lambda_param = int(config.lambda_ * config.popsize)
    if config.meta == types.MetaAlgorithm.MU_PLUS_LAMBDA:
        return lambda *args, **kwargs: deap.algorithms.eaMuPlusLambda(
            *args, **kwargs, mu=config.popsize, lambda_=lambda_param
        )
    if config.meta == types.MetaAlgorithm.MU_COMMA_LAMBDA:
        return lambda *args, **kwargs: deap.algorithms.eaMuCommaLambda(
            *args, **kwargs, mu=config.popsize, lambda_=lambda_param
        )
    if config.meta == types.MetaAlgorithm.DPGA:
        return lambda *args, **kwargs: dpga(
            *args, **kwargs, config=config, save_period=5
        )
    raise ValueError(f"Unknown algorithm: {config.meta}")
