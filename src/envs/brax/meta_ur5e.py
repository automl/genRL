import numpy as np
import copy
import json
import brax
from brax.envs.wrappers import GymWrapper
from brax.envs.ur5e import Ur5e, _SYSTEM_CONFIG
from src.envs.meta_env import MetaEnv
from google.protobuf import json_format, text_format
from google.protobuf.json_format import MessageToDict
from typing import Optional, Dict
from numpyencoder import NumpyEncoder
from src.trial_logger import TrialLogger

DEFAULT_CONTEXT = {
    "joint_stiffness": 40000,
    "gravity": -9.81,
    "friction": 0.6,
    "angular_damping": -0.05,
    "actuator_strength": 100,
    "joint_angular_damping": 50,
    "target_radius": 0.02,
    "target_distance": 0.5,
}

CONTEXT_BOUNDS = {
    "joint_stiffness": (1, np.inf, int),
    "gravity": (-np.inf, -0.1, float),
    "friction": (-np.inf, np.inf, float),
    "angular_damping": (-np.inf, np.inf, float),
    "actuator_strength": (1, np.inf, int),
    "joint_angular_damping": (0, 360, int),
    "target_radius": (0.01, np.inf, float),
    "target_distance": (0.01, np.inf, float)
}


class MetaUr5e(MetaEnv):
    def __init__(
            self,
            env: Ur5e = Ur5e,
            contexts: Dict[str, Dict] = {},
            instance_mode="rr",
            hide_context=False,
            add_gaussian_noise_to_context: bool = False,
            gaussian_noise_std_percentage: float = 0.01,
            logger: Optional[TrialLogger] = None
    ):
        env = GymWrapper(env)
        self.base_config = MessageToDict(text_format.Parse(_SYSTEM_CONFIG, brax.Config()))
        if not contexts:
            contexts = {0: DEFAULT_CONTEXT}
        super().__init__(
            env=env,
            contexts=contexts,
            instance_mode=instance_mode,
            hide_context=hide_context,
            add_gaussian_noise_to_context=add_gaussian_noise_to_context,
            gaussian_noise_std_percentage=gaussian_noise_std_percentage,
            logger=logger
        )
        self.whitelist_gaussian_noise = list(DEFAULT_CONTEXT.keys())  # allow to augment all values
        self._update_context()

    def _update_context(self):
        config = copy.deepcopy(self.base_config)
        config["gravity"] = {"z": self.context["gravity"]}
        config["friction"] = self.context["friction"]
        config["angularDamping"] = self.context["angular_damping"]
        for j in range(len(config["joints"])):
            config["joints"][j]["angularDamping"] = self.context["joint_angular_damping"]
            config["joints"][j]["stiffness"] = self.context["joint_stiffness"]
        for a in range(len(config["actuators"])):
            config["actuators"][a]["strength"] = self.context["actuator_strength"]
        config["bodies"][0]["mass"] = self.context["torso_mass"]
        # This converts the dict to a JSON String, then parses it into an empty brax config
        self.env.sys = brax.System(json_format.Parse(json.dumps(config, cls=NumpyEncoder), brax.Config()))
        self.env.target_idx = self.env.sys.body_idx['Target']
        self.env.torso_idx = self.env.sys.body_idx['wrist_3_link']
        self.env.target_radius = self.context["target_radius"]
        self.env.target_distance = self.context["target_distance"]

    def __getattr__(self, name):
        if name in ["sys", "target_idx", "torso_idx", "target_radius", "target_distance"]:
            return getattr(self.env._environment, name)
        else:
            return getattr(self, name)