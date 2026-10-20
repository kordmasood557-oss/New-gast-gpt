
"""
Fast GPT — ABC Dual-NPU Thermal Scheduler
Prototype v0.2

Employed bees: explore nearby workload splits.
Onlooker bees: focus on promising candidates.
Scout bees: replace stagnant candidates.
"""

import random
from dataclasses import dataclass


@dataclass
class NPU:
    name: str
    temperature: float = 42.0
    max_temperature: float = 80.0


def simulate(split, steps=300):
    """Illustrative model only; not real hardware telemetry."""
    nodes = [NPU("NPU-A"), NPU("NPU-B")]
    energy = 0.0
    completed = 0.0
    peak = 0.0

    for _ in range(steps):
        for node, load in zip(nodes, [split, 1 - split]):
            power = 3.0 + 22.0 * load**2

            # Simplified heat generation and cooling
            node.temperature += (
                0.15 * power
                - 0.08 * (node.temperature - 30.0)
            )

            peak = max(peak, node.temperature)
            energy += power

            # Simulated thermal throttling
            factor = max(
                0.25,
                min(1.0, (85.0 - node.temperature) / 20.0)
            )
            completed += load * factor

    efficiency = completed / max(energy, 1e-9)

    # Penalize exceeding the design target
    penalty = max(0.0, peak - 70.0) * 0.003
    score = efficiency - penalty

    return {
        "split": split,
        "completed": completed,
        "energy": energy,
        "peak_c": peak,
        "efficiency": efficiency,
        "score": score,
    }


class BeeScheduler:
    def __init__(self, population=12, limit=7, seed=7):
        random.seed(seed)
        self.population = population
        self.limit = limit

    @staticmethod
    def clamp(x):
        return max(0.10, min(0.90, x))

    def search(self, iterations=40):
        # Food sources = candidate workload splits
        foods = [
            random.uniform(0.10, 0.90)
            for _ in range(self.population)
        ]
        results = [simulate(x) for x in foods]
        failures = [0] * self.population

        for _ in range(iterations):

            # 1. Employed bees: explore neighbors
            for i in range(self.population):
                k = random.choice([
                    j for j in range(self.population) if j != i
                ])
                candidate = self.clamp(
                    foods[i] + random.uniform(-1, 1)
                    * (foods[i] - foods[k])
                )
                result = simulate(candidate)

                if result["score"] > results[i]["score"]:
                    foods[i], results[i] = candidate, result
                    failures[i] = 0
                else:
                    failures[i] += 1

            # 2. Onlooker bees: favor better food sources
            minimum = min(r["score"] for r in results)
            weights = [
                max(1e-9, r["score"] - minimum + 1e-6)
                for r in results
            ]

            for _ in range(self.population):
                i = random.choices(
                    range(self.population), weights=weights, k=1
                )[0]
                k = random.choice([
                    j for j in range(self.population) if j != i
                ])
                candidate = self.clamp(
                    foods[i] + random.uniform(-1, 1)
                    * (foods[i] - foods[k])
                )
                result = simulate(candidate)

                if result["score"] > results[i]["score"]:
                    foods[i], results[i] = candidate, result
                    failures[i] = 0
                else:
                    failures[i] += 1

            # 3. Scout bees: abandon stagnant sources
            for i in range(self.population):
                if failures[i] >= self.limit:
                    foods[i] = random.uniform(0.10, 0.90)
                    results[i] = simulate(foods[i])
                    failures[i] = 0

        return max(results, key=lambda r: r["score"])


if __name__ == "__main__":
    scheduler = BeeScheduler()
    best = scheduler.search()

    print("Best workload split:")
    print(f"NPU-A: {best['split']:.1%}")
    print(f"NPU-B: {1 - best['split']:.1%}")
    print(f"Completed work: {best['completed']:.1f}")
    print(f"Energy units: {best['energy']:.1f}")
    print(f"Peak simulated temperature: {best['peak_c']:.1f} C")
    print(f"Efficiency: {best['efficiency']:.5f}")
