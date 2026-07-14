import tempfile
import unittest
from pathlib import Path

import numpy as np

from sugarscape import Config, SugarScape, gini


class SugarScapeTests(unittest.TestCase):
    def test_same_seed_is_reproducible(self):
        config = Config(size=20, initial_agents=40, seed=123)
        first = SugarScape(config)
        second = SugarScape(config)
        first.run(15)
        second.run(15)
        self.assertEqual(first.history, second.history)

    def test_occupancy_stays_consistent(self):
        world = SugarScape(Config(size=20, initial_agents=70, seed=7))
        for _ in range(30):
            world.step()
            self.assertEqual(len(world.agents), len(world.occupied))
            self.assertEqual(len(set(world.occupied)), len(world.occupied))
            for position, agent_id in world.occupied.items():
                agent = world.agents[agent_id]
                self.assertEqual(position, (agent.x, agent.y))

    def test_resources_respect_capacity(self):
        world = SugarScape(Config(size=12, initial_agents=20, grow_rate=2, seed=4))
        world.run(10)
        self.assertTrue(np.all(world.sugar >= 0))
        self.assertTrue(np.all(world.sugar <= world.capacity))

    def test_gini_known_values(self):
        self.assertEqual(gini([]), 0.0)
        self.assertEqual(gini([5, 5, 5]), 0.0)
        self.assertAlmostEqual(gini([0, 0, 0, 10]), 0.75)

    def test_csv_export(self):
        world = SugarScape(Config(size=10, initial_agents=10, seed=1))
        world.run(2)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "stats.csv"
            world.export_csv(path)
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        self.assertEqual(len(lines), 4)
        self.assertIn("population", lines[0])

    def test_invalid_population_is_rejected(self):
        with self.assertRaises(ValueError):
            SugarScape(Config(size=10, initial_agents=101))


if __name__ == "__main__":
    unittest.main()
