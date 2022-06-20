from typing import Union, Optional, List
from enum import Enum, IntEnum, auto
from pathlib import Path
import wandb
from typing import Dict, Any
import warnings
import numpy as np

from carl.context.sampling import get_default_context_and_bounds, sample_contexts
from experiments.common.utils.json_utils import lazy_json_dump


def log_contexts_wandb_traineval(train_contexts, eval_contexts):
    log_contexts_wandb(contexts=train_contexts, wandb_key="train/contexts")
    log_contexts_wandb(contexts=eval_contexts, wandb_key="eval/contexts")


def log_contexts_wandb(contexts: Dict[Any, Dict[str, Any]], wandb_key: str):
    table = wandb.Table(
        columns=sorted(contexts[0].keys()),
        data=[
            [contexts[idx][key] for key in sorted(contexts[idx].keys())]
            for idx in contexts.keys()
        ],
    )
    wandb.log({wandb_key: table}, step=0)


class ContextDifficulty(Enum):
    easy = 0.1
    medium = 0.25
    hard = 0.5


class NContexts(Enum):
    small = 100
    medium = 1000
    large = 10000


class AbstractContextSampler(object):
    pass


class ContextSampler(AbstractContextSampler):
    def __init__(
            self,
            env_name: str,
            context_feature_names: Optional[Union[List[str], str]] = None,
            seed: int = 842,
            difficulty: str = "easy",
            n_samples: Union[str, int] = 100,
            contexts_fn: str = "contexts.json",
            sigma_rel: Optional[float] = None,  # overrides difficulty
    ):
        super(ContextSampler, self).__init__()
        self.seed = seed
        self.contexts = None
        self.contexts_fn = contexts_fn
        self.env_name = env_name
        self.C_def, self.C_bounds = get_default_context_and_bounds(env_name=self.env_name)
        if context_feature_names is None:
            context_feature_names = []
        elif type(context_feature_names) == str and context_feature_names == "all":
            context_feature_names = list(self.C_def.keys())
        self.context_feature_names = context_feature_names

        if sigma_rel is None:
            if difficulty not in ContextDifficulty.__members__:
                raise ValueError("Please specify a valid difficulty. Valid options are: ",
                      list(ContextDifficulty.__members__.keys()))
            self.sigma_rel = ContextDifficulty[difficulty].value
        else:
            self.sigma_rel = sigma_rel

        if type(n_samples) == str:
            if n_samples not in NContexts.__members__:
                raise ValueError("Please specify a valid size. Valid options are: ",
                      list(NContexts.__members__.keys()))
            self.n_samples = NContexts[n_samples]
        elif type(n_samples) == int or type(n_samples) == float:
            self.n_samples = int(n_samples)
        else:
            raise ValueError(f"`n_samples` must be of type str "
                             f"or int, got {type(n_samples)}.")

        self.contexts = None

    def sample_contexts(self) -> Dict[Any, Dict[str, Any]]:
        if self.contexts is not None:
            warnings.warn("Return already sampled contexts.")
            return self.contexts

        context_feature_args = self.context_feature_names
        self.contexts = sample_contexts(
            env_name=self.env_name,
            num_contexts=self.n_samples,
            default_sample_std_percentage=self.sigma_rel,
            context_feature_args=context_feature_args,
            seed=self.seed
        )
        return self.contexts


def log_contexts_json(contexts, path: Union[str, Path]):
    path = Path(path)
    path.parent.mkdir(exist_ok=True, parents=True)
    lazy_json_dump(contexts, str(path))


if __name__ == "__main__":
    from rich import print
    env_name = "CARLPendulumEnv"
    cs = ContextSampler(
        env_name=env_name,
        difficulty="easy",
        n_samples=1,
        context_feature_names=["m", "l", "g"],
        seed=455
    )
    contexts = cs.sample_contexts()
    print(contexts)
