# Copyright 2017 The dm_control Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or  implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================

"""Planar Walker Domain."""

import collections
from multiprocessing.context import _force_start_method

from dm_control import mujoco
from dm_control.rl import control
from dm_control.suite import base
from dm_control.suite import common
from dm_control.suite.utils import randomizers
from dm_control.utils import containers
from dm_control.utils import rewards
from lxml import etree


_DEFAULT_TIME_LIMIT = 25
_CONTROL_TIMESTEP = .025

# Minimal height of torso over foot above which stand reward is 1.
_STAND_HEIGHT = 1.2

# Horizontal speeds (meters/second) above which move reward is 1.
_WALK_SPEED = 1
_RUN_SPEED = 8


SUITE = containers.TaggedTasks()


def get_model_and_assets():
  """Returns a tuple containing the model XML string and a dict of assets."""
  return common.read_model('walker.xml'), common.ASSETS


def adapt_context(xml_string, context):
  """Adapts and returns the xml_string of the model with the given context."""
  mjcf = etree.fromstring(xml_string)
  damping = mjcf.find("./default/joint")
  damping.set("damping", str(context["joint_damping"]))
  friction = mjcf.find("./default/geom")
  friction.set("friction", " ".join([
    str(context["friction_tangential"]), 
    str(context["friction_torsional"]), 
    str(context["friction_rolling"])])
  )
  actuators = mjcf.findall("./actuator/motor")
  for actuator in actuators:
    gear = actuator.get("gear")
    actuator.set("gear", str(int(float(gear) * context["actuator_strength"])))
  keys = []
  options = mjcf.findall("./option")
  gravity = " ".join([str(context["gravity_x"]), str(context["gravity_y"]), str(context["gravity_z"])])
  magnetic = " ".join([str(context["magnetic_x"]), str(context["magnetic_y"]), str(context["magnetic_z"])])
  wind = " ".join([str(context["wind_x"]), str(context["wind_y"]), str(context["wind_z"])])
  for option in options:
    for k, v in option.items():
      keys.append(k)
      if k == "gravity":
        option.set("gravity", gravity)
      elif k == "timestep":
        option.set("timestep", str(context["timestep"]))
      elif k == "magnetic":
        option.set("magnetic", magnetic)
      elif k == "wind":
        option.set("wind", wind)
  if "gravity" not in keys:
    mjcf.append(etree.Element("option", gravity=gravity))
  if "timestep" not in keys:
    mjcf.append(etree.Element("option", timestep=str(context["timestep"])))
  if "magnetic" not in keys:
    mjcf.append(etree.Element("option", magnetic=magnetic))
  if "wind" not in keys:
    mjcf.append(etree.Element("option", wind=wind))
  xml_string = etree.tostring(mjcf, pretty_print=True)
  return xml_string


@SUITE.add('benchmarking')
def stand_context(context={}, time_limit=_DEFAULT_TIME_LIMIT, random=None, environment_kwargs=None):
  """Returns the Stand task with the adapted context."""
  xml_string, assets = get_model_and_assets()
  if context != {}:
    xml_string = adapt_context(xml_string, context)
  physics = Physics.from_xml_string(xml_string, assets)
  task = PlanarWalker(move_speed=0, random=random)
  environment_kwargs = environment_kwargs or {}
  return control.Environment(
      physics, task, time_limit=time_limit, control_timestep=_CONTROL_TIMESTEP,
      **environment_kwargs)


@SUITE.add('benchmarking')
def walk_context(context={}, time_limit=_DEFAULT_TIME_LIMIT, random=None, environment_kwargs=None):
  """Returns the Walk task with the adapted context."""
  xml_string, assets = get_model_and_assets()
  if context != {}:
    xml_string = adapt_context(xml_string, context)
  physics = Physics.from_xml_string(xml_string, assets)
  task = PlanarWalker(move_speed=_WALK_SPEED, random=random)
  environment_kwargs = environment_kwargs or {}
  return control.Environment(
      physics, task, time_limit=time_limit, control_timestep=_CONTROL_TIMESTEP,
      **environment_kwargs)


@SUITE.add('benchmarking')
def run_context(context={}, time_limit=_DEFAULT_TIME_LIMIT, random=None, environment_kwargs=None):
  """Returns the Run task with the adapted context."""
  xml_string, assets = get_model_and_assets()
  if context != {}:
    xml_string = adapt_context(xml_string, context)
  physics = Physics.from_xml_string(xml_string, assets)
  task = PlanarWalker(move_speed=_RUN_SPEED, random=random)
  environment_kwargs = environment_kwargs or {}
  return control.Environment(
      physics, task, time_limit=time_limit, control_timestep=_CONTROL_TIMESTEP,
      **environment_kwargs)


class Physics(mujoco.Physics):
  """Physics simulation with additional features for the Walker domain."""

  def torso_upright(self):
    """Returns projection from z-axes of torso to the z-axes of world."""
    return self.named.data.xmat['torso', 'zz']

  def torso_height(self):
    """Returns the height of the torso."""
    return self.named.data.xpos['torso', 'z']

  def horizontal_velocity(self):
    """Returns the horizontal velocity of the center-of-mass."""
    return self.named.data.sensordata['torso_subtreelinvel'][0]

  def orientations(self):
    """Returns planar orientations of all bodies."""
    return self.named.data.xmat[1:, ['xx', 'xz']].ravel()


class PlanarWalker(base.Task):
  """A planar walker task."""

  def __init__(self, move_speed, random=None):
    """Initializes an instance of `PlanarWalker`.
    Args:
      move_speed: A float. If this value is zero, reward is given simply for
        standing up. Otherwise this specifies a target horizontal velocity for
        the walking task.
      random: Optional, either a `numpy.random.RandomState` instance, an
        integer seed for creating a new `RandomState`, or None to select a seed
        automatically (default).
    """
    self._move_speed = move_speed
    super().__init__(random=random)

  def initialize_episode(self, physics):
    """Sets the state of the environment at the start of each episode.
    In 'standing' mode, use initial orientation and small velocities.
    In 'random' mode, randomize joint angles and let fall to the floor.
    Args:
      physics: An instance of `Physics`.
    """
    randomizers.randomize_limited_and_rotational_joints(physics, self.random)
    super().initialize_episode(physics)

  def get_observation(self, physics):
    """Returns an observation of body orientations, height and velocites."""
    obs = collections.OrderedDict()
    obs['orientations'] = physics.orientations()
    obs['height'] = physics.torso_height()
    obs['velocity'] = physics.velocity()
    return obs

  def get_reward(self, physics):
    """Returns a reward to the agent."""
    standing = rewards.tolerance(physics.torso_height(),
                                 bounds=(_STAND_HEIGHT, float('inf')),
                                 margin=_STAND_HEIGHT/2)
    upright = (1 + physics.torso_upright()) / 2
    stand_reward = (3*standing + upright) / 4
    if self._move_speed == 0:
      return stand_reward
    else:
      move_reward = rewards.tolerance(physics.horizontal_velocity(),
                                      bounds=(self._move_speed, float('inf')),
                                      margin=self._move_speed/2,
                                      value_at_margin=0.5,
                                      sigmoid='linear')
      return stand_reward * (5*move_reward + 1) / 6