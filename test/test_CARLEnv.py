import unittest

import numpy as np

from carl.envs.classic_control.carl_pendulum import CARLPendulumEnv


class TestStateConstruction(unittest.TestCase):
    def test_hiddenstate(self):
        """
        Test if we set hide_context = True that we get the original, normal state.
        """
        env = CARLPendulumEnv(
            contexts={},
            hide_context=True,
            add_gaussian_noise_to_context=False,
            gaussian_noise_std_percentage=0.01,
            state_context_features=None,
        )
        env.reset()
        action = [0.01]  # torque
        state, reward, done, info = env.step(action=action)
        env.close()
        self.assertEqual(3, len(state))

    def test_visiblestate(self):
        """
        Test if we set hide_context = False and state_context_features=None that we get the normal state extended by
        all context features.
        """
        env = CARLPendulumEnv(
            contexts={},
            hide_context=False,
            add_gaussian_noise_to_context=False,
            gaussian_noise_std_percentage=0.01,
            state_context_features=None,
        )
        env.reset()
        action = [0.01]  # torque
        state, reward, done, info = env.step(action=action)
        env.close()
        self.assertEqual(8, len(state))

    def test_visiblestate_customnone(self):
        """
        Test if we set hide_context = False and state_context_features="changing_context_features" that we get the
        normal state, not extended by context features.
        """
        env = CARLPendulumEnv(
            contexts={},
            hide_context=False,
            add_gaussian_noise_to_context=False,
            gaussian_noise_std_percentage=0.01,
            state_context_features=["changing_context_features"],
        )
        env.reset()
        action = [0.01]  # torque
        state, reward, done, info = env.step(action=action)
        env.close()
        # Because we don't change any context features the state length should be 3
        self.assertEqual(3, len(state))

    def test_visiblestate_custom(self):
        """
        Test if we set hide_context = False and state_context_features=["g", "m"] that we get the
        normal state, extended by the context feature values of g and m.
        """
        env = CARLPendulumEnv(
            contexts={},
            hide_context=False,
            add_gaussian_noise_to_context=False,
            gaussian_noise_std_percentage=0.01,
            state_context_features=["g", "m"],
        )
        env.reset()
        action = [0.01]  # torque
        state, reward, done, info = env.step(action=action)
        env.close()
        # state should be of length 5 because we add two context features
        self.assertEqual(5, len(state))

    def test_visiblestate_changingcontextfeatures_nochange(self):
        """
        Test if we set hide_context = False and state_context_features="changing_context_features" that we get the
        normal state, extended by the context features which are changing in the set of contexts. Here: None are
        changing.
        """
        contexts = {
            "0": {"max_speed": 8.0, "dt": 0.05, "g": 10.0, "m": 1.0, "l": 1.0},
            "1": {"max_speed": 8.0, "dt": 0.05, "g": 10.0, "m": 1.0, "l": 1.0},
            "2": {"max_speed": 8.0, "dt": 0.05, "g": 10.0, "m": 1.0, "l": 1.0},
            "3": {"max_speed": 8.0, "dt": 0.05, "g": 10.0, "m": 1.0, "l": 1.0},
        }
        env = CARLPendulumEnv(
            contexts=contexts,
            hide_context=False,
            add_gaussian_noise_to_context=False,
            gaussian_noise_std_percentage=0.01,
            state_context_features=["changing_context_features"],
        )
        env.reset()
        action = [0.01]  # torque
        state, reward, done, info = env.step(action=action)
        env.close()
        # state should be of length 3 because all contexts are the same
        self.assertEqual(3, len(state))

    def test_visiblestate_changingcontextfeatures_change(self):
        """
        Test if we set hide_context = False and state_context_features="changing_context_features" that we get the
        normal state, extended by the context features which are changing in the set of contexts.
        Here: Two are changing.
        """
        contexts = {
            "0": {"max_speed": 8.0, "dt": 0.03, "g": 10.0, "m": 1.0, "l": 1.0},
            "1": {"max_speed": 8.0, "dt": 0.05, "g": 10.0, "m": 1.0, "l": 0.95},
            "2": {"max_speed": 8.0, "dt": 0.05, "g": 10.0, "m": 1.0, "l": 0.3},
            "3": {"max_speed": 8.0, "dt": 0.05, "g": 10.0, "m": 1.0, "l": 1.3},
        }
        env = CARLPendulumEnv(
            contexts=contexts,
            hide_context=False,
            add_gaussian_noise_to_context=False,
            gaussian_noise_std_percentage=0.01,
            state_context_features=["changing_context_features"],
        )
        env.reset()
        action = [0.01]  # torque
        state, reward, done, info = env.step(action=action)
        env.close()
        # state should be of length 5 because two features are changing (dt and l)
        self.assertEqual(5, len(state))

    def test_dict_observation_space(self):
        contexts = {"0": {"max_speed": 8.0, "dt": 0.03, "g": 10.0, "m": 1.0, "l": 1.0}}
        env = CARLPendulumEnv(
            contexts=contexts,
            hide_context=False,
            dict_observation_space=True,
            add_gaussian_noise_to_context=False,
            gaussian_noise_std_percentage=0.01,
            state_context_features=["changing_context_features"],
        )
        obs = env.reset()
        self.assertEqual(type(obs), dict)
        self.assertTrue("state" in obs)
        self.assertTrue("context" in obs)
        action = [0.01]  # torque
        next_obs, reward, done, info = env.step(action=action)
        env.close()


class TestEpisodeTermination(unittest.TestCase):
    def test_episode_termination(self):
        """
        Test if we set hide_context = True that we get the original, normal state.
        """
        ep_length = 100
        env = CARLPendulumEnv(
            contexts={},
            hide_context=True,
            add_gaussian_noise_to_context=False,
            gaussian_noise_std_percentage=0.01,
            state_context_features=None,
            max_episode_length=ep_length,
        )
        env.reset()
        action = [0.0]  # torque
        done = False
        counter = 0
        while not done:
            state, reward, done, info = env.step(action=action)
            counter += 1
            self.assertTrue(counter <= ep_length)
            if counter > ep_length:
                break
        env.close()


class TestContextFeatureScaling(unittest.TestCase):
    def test_context_feature_scaling_no(self):
        env = (
            CARLPendulumEnv(  # noqa: F841 local variable is assigned to but never used
                contexts={},
                hide_context=False,
                add_gaussian_noise_to_context=False,
                gaussian_noise_std_percentage=0.01,
                state_context_features=None,
                scale_context_features="no",
            )
        )

    def test_context_feature_scaling_by_mean(self):
        contexts = {
            # order is important because context "0" is checked in the test
            # because of the reset context "0" must come seond
            "1": {"max_speed": 16.0, "dt": 0.06, "g": 20.0, "m": 2.0, "l": 3.6},
            "0": {"max_speed": 8.0, "dt": 0.03, "g": 10.0, "m": 1.0, "l": 1.8},
        }
        env = CARLPendulumEnv(
            contexts=contexts,
            hide_context=False,
            add_gaussian_noise_to_context=False,
            gaussian_noise_std_percentage=0.01,
            state_context_features=None,
            scale_context_features="by_mean",
        )
        env.reset()
        action = [0.0]
        state, reward, done, info = env.step(action=action)
        n_c = len(contexts["0"])
        scaled_contexts = state[-n_c:]
        target = np.array([8 / 12, 0.03 / 0.045, 10 / 15, 1 / 1.5, 1.8 / 2.7])
        self.assertTrue(
            np.all(target == scaled_contexts),
            f"target {target} != actual {scaled_contexts}",
        )

    def test_context_feature_scaling_by_default(self):
        default_context = {
            "max_speed": 8.0,
            "dt": 0.05,
            "g": 10.0,
            "m": 1.0,
            "l": 1.0,
        }
        contexts = {
            "0": {"max_speed": 8.0, "dt": 0.03, "g": 10.0, "m": 1.0, "l": 1.8},
        }
        env = CARLPendulumEnv(
            contexts=contexts,
            hide_context=False,
            add_gaussian_noise_to_context=False,
            gaussian_noise_std_percentage=0.01,
            state_context_features=None,
            scale_context_features="by_default",
            default_context=default_context,
        )
        env.reset()
        action = [0.0]
        state, reward, done, info = env.step(action=action)
        n_c = len(default_context)
        scaled_contexts = state[-n_c:]
        self.assertTrue(np.all(np.array([1.0, 0.6, 1, 1, 1.8]) == scaled_contexts))

    def test_context_feature_scaling_by_default_nodefcontext(self):
        with self.assertRaises(ValueError):
            env = CARLPendulumEnv(  # noqa: F841 local variable is assigned to but never used
                contexts={},
                hide_context=False,
                add_gaussian_noise_to_context=False,
                gaussian_noise_std_percentage=0.01,
                state_context_features=None,
                scale_context_features="by_default",
                default_context=None,
            )

    def test_context_feature_scaling_unknown_init(self):
        with self.assertRaises(ValueError):
            env = CARLPendulumEnv(  # noqa: F841 local variable is assigned to but never used
                contexts={},
                hide_context=False,
                add_gaussian_noise_to_context=False,
                gaussian_noise_std_percentage=0.01,
                state_context_features=None,
                scale_context_features="bork",
            )

    def test_context_feature_scaling_unknown_step(self):
        env = (
            CARLPendulumEnv(  # noqa: F841 local variable is assigned to but never used
                contexts={},
                hide_context=False,
                add_gaussian_noise_to_context=False,
                gaussian_noise_std_percentage=0.01,
                state_context_features=None,
                scale_context_features="no",
            )
        )

        env.reset()
        env.scale_context_features = "bork"
        action = [0.01]  # torque
        with self.assertRaises(ValueError):
            next_obs, reward, done, info = env.step(action=action)


class TestInstanceModes(unittest.TestCase):
    def test_instance_mode_random(self):
        env = (
            CARLPendulumEnv(  # noqa: F841 local variable is assigned to but never used
                contexts={},
                hide_context=False,
                add_gaussian_noise_to_context=False,
                gaussian_noise_std_percentage=0.01,
                state_context_features=None,
                instance_mode="random",
            )
        )

    def test_instance_mode_roundrobin(self):
        env = (
            CARLPendulumEnv(  # noqa: F841 local variable is assigned to but never used
                contexts={},
                hide_context=False,
                add_gaussian_noise_to_context=False,
                gaussian_noise_std_percentage=0.01,
                state_context_features=None,
                instance_mode="rr",
            )
        )
        env = (
            CARLPendulumEnv(  # noqa: F841 local variable is assigned to but never used
                contexts={},
                hide_context=False,
                add_gaussian_noise_to_context=False,
                gaussian_noise_std_percentage=0.01,
                state_context_features=None,
                instance_mode="roundrobin",
            )
        )

    def test_instance_mode_unknown(self):
        with self.assertRaises(ValueError):
            env = CARLPendulumEnv(  # noqa: F841 local variable is assigned to but never used
                contexts={},
                hide_context=False,
                add_gaussian_noise_to_context=False,
                gaussian_noise_std_percentage=0.01,
                state_context_features=None,
                instance_mode="bork",
            )


if __name__ == "__main__":
    unittest.main()
