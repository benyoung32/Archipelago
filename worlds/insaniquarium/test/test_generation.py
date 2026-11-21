#!/usr/bin/env python3
"""
Comprehensive Archipelago Generation Test Script for Insaniquarium Deluxe.

Iterates through variations of allowed options and tests multiworld generation
multiple times (seeds) for each variation to detect logic locks, fill errors,
item/location mismatches, and rule regressions.

Usage Examples:
    # Test each option in isolation with 3 seeds each (default)
    python worlds/insaniquarium/test/test_generation.py

    # Test with 5 seeds per option variation
    python worlds/insaniquarium/test/test_generation.py --seeds 5

    # Run game presets and archetypes
    python worlds/insaniquarium/test/test_generation.py --mode presets

    # Run pairwise (all-pairs) combinatorial testing across key gameplay options
    python worlds/insaniquarium/test/test_generation.py --mode matrix

    # Run full Cartesian product on specific options
    python worlds/insaniquarium/test/test_generation.py --mode cartesian --combine starting_tank egg_pieces_per_level cyrax_required

    # Random fuzzing with 20 combinations across all options
    python worlds/insaniquarium/test/test_generation.py --mode random --count 20

    # Run everything (presets + isolated + matrix)
    python worlds/insaniquarium/test/test_generation.py --mode all

    # Reproduce a specific failing configuration and seed with full traceback
    python worlds/insaniquarium/test/test_generation.py --reproduce '{"aliensanity": false}' --seed 80025741982462456590

    # List all discovered options, types, defaults, and allowed test values
    python worlds/insaniquarium/test/test_generation.py --list-options
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
import itertools
import json
import os
from pathlib import Path
import random
import sys
import time
import traceback
from typing import Any, Dict, List, Optional, Set, Tuple, Type

# Ensure Archipelago repository root is in sys.path
_current = Path(__file__).resolve().parent
REPO_ROOT = _current
for _p in [_current] + list(_current.parents):
    if (_p / "Generate.py").is_file() or (_p / ".git").is_dir():
        REPO_ROOT = _p
        break
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Archipelago imports
import ModuleUpdate
from worlds.AutoWorld import AutoWorldRegister, call_all
from BaseClasses import CollectionState, MultiWorld, Location
from Fill import distribute_items_restrictive, FillError
from Options import (
    Choice,
    CommonOptions,
    DefaultOnToggle,
    Option,
    OptionError,
    PerGameCommonOptions,
    Range,
    TextChoice,
    Toggle,
)
from test.general import setup_multiworld


# ---------------------------------------------------------------------------
# ANSI Terminal Colors
# ---------------------------------------------------------------------------
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

    @classmethod
    def disable(cls):
        cls.RESET = ""
        cls.BOLD = ""
        cls.DIM = ""
        cls.RED = ""
        cls.GREEN = ""
        cls.YELLOW = ""
        cls.BLUE = ""
        cls.MAGENTA = ""
        cls.CYAN = ""
        cls.WHITE = ""


# Auto-enable ANSI colors on Windows 10/11 terminals
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------
@dataclass
class OptionDomain:
    name: str
    option_class: Type[Option]
    option_type: str  # 'choice', 'toggle', 'range', 'other'
    default_value: Any
    allowed_values: List[Any]
    display_name: str
    description: str


@dataclass
class TestCaseConfig:
    name: str
    options: Dict[str, Any]
    category: str
    tags: List[str] = field(default_factory=list)


@dataclass
class GenerationResult:
    config_name: str
    options: Dict[str, Any]
    seed: int
    success: bool
    status: str  # 'PASS', 'FAIL', 'EXPECTED_ERROR', 'SKIPPED'
    duration: float
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    traceback_str: Optional[str] = None
    locations_count: int = 0
    items_count: int = 0
    sphere_count: int = 0


# ---------------------------------------------------------------------------
# Option Introspection & Domain Extraction
# ---------------------------------------------------------------------------
def get_option_domains(
    world_type: Any,
    include_common: bool = False,
    range_sample_step: int = 25,
) -> Dict[str, OptionDomain]:
    """
    Introspects the world's options dataclass and extracts allowed variations
    for each option based on its type and constraints.
    """
    options_dc = world_type.options_dataclass
    common_keys = (
        set(PerGameCommonOptions.type_hints.keys())
        if hasattr(PerGameCommonOptions, "type_hints")
        else set()
    )
    domains: Dict[str, OptionDomain] = {}

    for opt_name, opt_cls in options_dc.type_hints.items():
        if not include_common and opt_name in common_keys:
            continue

        display_name = getattr(opt_cls, "display_name", opt_name)
        doc = (getattr(opt_cls, "__doc__", "") or "").strip()
        default_val = getattr(opt_cls, "default", None)
        allowed_values: List[Any] = []

        if issubclass(opt_cls, Toggle):
            opt_type = "toggle"
            allowed_values = [False, True]
        elif issubclass(opt_cls, (Choice, TextChoice)):
            opt_type = "choice"
            if hasattr(opt_cls, "options") and isinstance(opt_cls.options, dict):
                allowed_values = list(opt_cls.options.keys())
            elif hasattr(opt_cls, "name_lookup") and isinstance(opt_cls.name_lookup, dict):
                allowed_values = list(opt_cls.name_lookup.values())
            else:
                opts = [
                    attr[7:]
                    for attr in dir(opt_cls)
                    if attr.startswith("option_") and not callable(getattr(opt_cls, attr))
                ]
                allowed_values = opts if opts else [0, 1]
        elif issubclass(opt_cls, Range):
            opt_type = "range"
            r_start = getattr(opt_cls, "range_start", 0)
            r_end = getattr(opt_cls, "range_end", 1)
            span = r_end - r_start

            if span <= 5:
                # Small range: test every single integer
                allowed_values = list(range(r_start, r_end + 1))
            else:
                # Larger range: boundary values + default + key quartiles/samples
                points: Set[int] = {r_start, r_end}
                if default_val is not None and r_start <= default_val <= r_end:
                    points.add(default_val)
                step = max(1, span // 4)
                for pt in range(r_start, r_end, step):
                    points.add(pt)
                allowed_values = sorted(points)
        else:
            opt_type = "other"
            allowed_values = [default_val]

        domains[opt_name] = OptionDomain(
            name=opt_name,
            option_class=opt_cls,
            option_type=opt_type,
            default_value=default_val,
            allowed_values=allowed_values,
            display_name=display_name,
            description=doc,
        )

    return domains


# ---------------------------------------------------------------------------
# Test Case Generation Strategies
# ---------------------------------------------------------------------------
def generate_isolated_test_cases(domains: Dict[str, OptionDomain]) -> List[TestCaseConfig]:
    """
    Generates test cases where each option is varied across all its allowed values
    in isolation while keeping every other option at its default.
    """
    test_cases: List[TestCaseConfig] = []

    # Baseline: All Defaults
    test_cases.append(
        TestCaseConfig(
            name="Baseline Defaults",
            options={},
            category="baseline",
            tags=["default"],
        )
    )

    for opt_name, domain in sorted(domains.items()):
        for val in domain.allowed_values:
            test_cases.append(
                TestCaseConfig(
                    name=f"{opt_name} = {val}",
                    options={opt_name: val},
                    category="isolated",
                    tags=[opt_name, domain.option_type],
                )
            )

    return test_cases


def generate_presets_test_cases() -> List[TestCaseConfig]:
    """
    Generates realistic, stressful, and boundary game configurations for Insaniquarium Deluxe.
    """
    presets = [
        TestCaseConfig(
            name="Preset: All Defaults",
            options={},
            category="preset",
            tags=["vanilla", "default"],
        ),
        TestCaseConfig(
            name="Preset: Starting Tank 1 (Cyrax Victory)",
            options={"starting_tank": 1, "cyrax_required": True, "time_trial_required": False, "challenge_mode_required": False},
            category="preset",
            tags=["starting_tank", "goals"],
        ),
        TestCaseConfig(
            name="Preset: Starting Tank 2 (Time Trials Victory)",
            options={"starting_tank": 2, "cyrax_required": False, "time_trial_required": True, "challenge_mode_required": False},
            category="preset",
            tags=["starting_tank", "goals"],
        ),
        TestCaseConfig(
            name="Preset: Starting Tank 3 (Challenge Mode Victory)",
            options={"starting_tank": 3, "cyrax_required": False, "time_trial_required": False, "challenge_mode_required": True},
            category="preset",
            tags=["starting_tank", "goals"],
        ),
        TestCaseConfig(
            name="Preset: Starting Tank 4 (All 3 Goals Required)",
            options={"starting_tank": 4, "cyrax_required": True, "time_trial_required": True, "challenge_mode_required": True},
            category="preset",
            tags=["starting_tank", "goals", "all_goals"],
        ),
        TestCaseConfig(
            name="Preset: Randomized Tank (Cyrax + TT + CM)",
            options={"starting_tank": 0, "cyrax_required": True, "time_trial_required": True, "challenge_mode_required": True},
            category="preset",
            tags=["starting_tank", "all_goals"],
        ),
        TestCaseConfig(
            name="Preset: Maximum Checks (Egg3, 4 Bonus Pets, TT, CM, Aliensanity)",
            options={
                "egg_pieces_per_level": 3,
                "bonus_pet_locations": 4,
                "include_time_trials": True,
                "include_challenge_mode": True,
                "aliensanity": True,
                "alien_randomization": True,
            },
            category="preset",
            tags=["locations", "max_locations"],
        ),
        TestCaseConfig(
            name="Preset: Egg Pieces 2 per Level (TT + CM + Bonus Pets 4)",
            options={
                "egg_pieces_per_level": 2,
                "include_time_trials": True,
                "include_challenge_mode": True,
                "bonus_pet_locations": 4,
                "aliensanity": True,
            },
            category="preset",
            tags=["locations", "egg_pieces_2"],
        ),
        TestCaseConfig(
            name="Preset: Alien Randomization Disabled (Vanilla Alien Spawns)",
            options={"alien_randomization": False, "aliensanity": True},
            category="preset",
            tags=["aliens"],
        ),
        TestCaseConfig(
            name="Preset: Aliensanity Disabled with Alien Randomization",
            options={"aliensanity": False, "alien_randomization": True},
            category="preset",
            tags=["aliens"],
        ),
        TestCaseConfig(
            name="Preset: Free Upgrades",
            options={"upgrade_availability": "free"},
            category="preset",
            tags=["upgrades"],
        ),
        TestCaseConfig(
            name="Preset: Always Applied Upgrades",
            options={"upgrade_availability": "always"},
            category="preset",
            tags=["upgrades"],
        ),
        TestCaseConfig(
            name="Preset: Normal Price Upgrades",
            options={"upgrade_availability": "normal_price"},
            category="preset",
            tags=["upgrades"],
        ),
        TestCaseConfig(
            name="Preset: High Chaos Traps (100% Trap Chance, Attack & Famine)",
            options={
                "trap_chance": 100,
                "alien_attack_trap_weight": 80,
                "famine_trap_weight": 80,
            },
            category="preset",
            tags=["traps"],
        ),
        TestCaseConfig(
            name="Preset: Death Link (Kill All Fish, Threshold 1)",
            options={
                "death_link": True,
                "death_link_effect": "kill_all_fish",
                "death_link_amnesty": 1,
            },
            category="preset",
            tags=["death_link"],
        ),
        TestCaseConfig(
            name="Preset: Death Link (Activate Trap, Threshold 25)",
            options={
                "death_link": True,
                "death_link_effect": "activate_trap",
                "death_link_amnesty": 25,
            },
            category="preset",
            tags=["death_link"],
        ),
        TestCaseConfig(
            name="Preset: Zero Pet Slots (0 Starting, 0 Items)",
            options={"starting_pet_slots": 0, "pet_slot_items": 0},
            category="preset",
            tags=["pet_slots"],
        ),
        TestCaseConfig(
            name="Preset: Max Pet Slots (24 Starting, 24 Items)",
            options={"starting_pet_slots": 24, "pet_slot_items": 24},
            category="preset",
            tags=["pet_slots"],
        ),
        TestCaseConfig(
            name="Preset: Minimal Locations (Expected OptionError - Too Few Locations)",
            options={
                "egg_pieces_per_level": 2,
                "include_time_trials": False,
                "include_challenge_mode": False,
                "bonus_pet_locations": 0,
                "aliensanity": False,
            },
            category="preset",
            tags=["locations", "expected_option_error"],
        ),
    ]
    return presets


def generate_cartesian_test_cases(
    domains: Dict[str, OptionDomain],
    selected_options: Optional[List[str]] = None,
    limit: int = 500,
) -> List[TestCaseConfig]:
    """
    Generates Cartesian product across selected options.
    If selected_options is None, selects the most critical gameplay/logic options.
    """
    if not selected_options:
        candidate_keys = [
            "starting_tank",
            "egg_pieces_per_level",
            "cyrax_required",
            "time_trial_required",
            "challenge_mode_required",
            "upgrade_availability",
            "bonus_pet_locations",
            "aliensanity",
            "alien_randomization",
        ]
        selected_options = [k for k in candidate_keys if k in domains]

    keys = [k for k in selected_options if k in domains]
    value_lists = [domains[k].allowed_values for k in keys]

    configs: List[TestCaseConfig] = []
    for combo in itertools.product(*value_lists):
        opts = dict(zip(keys, combo))
        name_parts = [f"{k}={v}" for k, v in opts.items()]
        name = "Cartesian: " + ", ".join(name_parts)
        configs.append(
            TestCaseConfig(
                name=name,
                options=opts,
                category="cartesian",
                tags=keys,
            )
        )
        if len(configs) >= limit:
            break

    return configs


def generate_pairwise_test_cases(
    domains: Dict[str, OptionDomain],
    selected_options: Optional[List[str]] = None,
) -> List[TestCaseConfig]:
    """
    Generates a Pairwise (All-Pairs) covering array across options.
    Ensures that for every pair of options (A, B), all combinations of their
    allowed values are tested together in at least one test case.
    """
    if not selected_options:
        candidate_keys = [
            "starting_tank",
            "egg_pieces_per_level",
            "cyrax_required",
            "time_trial_required",
            "challenge_mode_required",
            "upgrade_availability",
            "bonus_pet_locations",
            "include_time_trials",
            "include_challenge_mode",
            "aliensanity",
            "alien_randomization",
            "death_link",
            "death_link_effect",
            "starting_pet_slots",
            "pet_slot_items",
        ]
        selected_options = [k for k in candidate_keys if k in domains]

    keys = [k for k in selected_options if k in domains]
    if len(keys) < 2:
        return generate_isolated_test_cases(domains)

    uncovered_pairs: Set[Tuple[str, Any, str, Any]] = set()
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            k1, k2 = keys[i], keys[j]
            for v1 in domains[k1].allowed_values:
                for v2 in domains[k2].allowed_values:
                    uncovered_pairs.add((k1, v1, k2, v2))

    test_cases: List[TestCaseConfig] = []
    case_idx = 1

    while uncovered_pairs:
        first_pair = next(iter(uncovered_pairs))
        k1, v1, k2, v2 = first_pair
        candidate_test = {k: domains[k].default_value for k in keys}
        candidate_test[k1] = v1
        candidate_test[k2] = v2

        remaining_keys = [k for k in keys if k != k1 and k != k2]
        random.shuffle(remaining_keys)

        for rk in remaining_keys:
            best_val = domains[rk].default_value
            best_cover_count = -1

            for val in domains[rk].allowed_values:
                count = 0
                for ak, av in candidate_test.items():
                    if (ak, av, rk, val) in uncovered_pairs or (rk, val, ak, av) in uncovered_pairs:
                        count += 1
                if count > best_cover_count:
                    best_cover_count = count
                    best_val = val

            candidate_test[rk] = best_val

        covered_in_this_run = set()
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                ki, kj = keys[i], keys[j]
                vi, vj = candidate_test[ki], candidate_test[kj]
                if (ki, vi, kj, vj) in uncovered_pairs:
                    covered_in_this_run.add((ki, vi, kj, vj))
                if (kj, vj, ki, vi) in uncovered_pairs:
                    covered_in_this_run.add((kj, vj, ki, vi))

        uncovered_pairs -= covered_in_this_run

        test_cases.append(
            TestCaseConfig(
                name=f"Pairwise #{case_idx} ({len(covered_in_this_run)} pairs covered)",
                options=candidate_test,
                category="pairwise",
                tags=["pairwise"],
            )
        )
        case_idx += 1

        if case_idx > 250:
            break

    return test_cases


def generate_random_fuzz_test_cases(
    domains: Dict[str, OptionDomain],
    count: int = 25,
) -> List[TestCaseConfig]:
    """
    Generates N random test cases sampled uniformly from all allowed option values.
    """
    test_cases: List[TestCaseConfig] = []
    for i in range(1, count + 1):
        opts = {}
        for k, domain in domains.items():
            opts[k] = random.choice(domain.allowed_values)
        test_cases.append(
            TestCaseConfig(
                name=f"Random Fuzz #{i}",
                options=opts,
                category="random_fuzz",
                tags=["fuzz"],
            )
        )
    return test_cases


# ---------------------------------------------------------------------------
# Core Generation & Verification Worker
# ---------------------------------------------------------------------------
def run_single_generation(
    game_name: str,
    config: TestCaseConfig,
    seed: int,
) -> GenerationResult:
    """
    Performs full Archipelago multiworld generation and comprehensive invariant
    checks for a single configuration and seed.
    """
    start_time = time.perf_counter()
    world_type = AutoWorldRegister.world_types[game_name]

    expected_option_error = "expected_option_error" in config.tags

    try:
        # Step 1: MultiWorld Setup with provided options
        multiworld = setup_multiworld([world_type], seed=seed, options=[config.options])
        player = 1
        world = multiworld.worlds[player]

        # Step 2: Distribution and Item Fill
        distribute_items_restrictive(multiworld)

        # Step 3: Post-Fill and Finalization
        call_all(multiworld, "post_fill")
        call_all(multiworld, "finalize_multiworld")

        # Step 4: Verification - Beatability Check
        if not multiworld.can_beat_game():
            raise AssertionError(f"Seed {seed} generated successfully but is NOT beatable!")

        # Step 5: Verification - Sphere Progression Reachability Walk
        locations = list(multiworld.get_locations(player))
        state = CollectionState(multiworld)
        sphere_count = 0

        while locations:
            sphere: List[Location] = []
            for n in range(len(locations) - 1, -1, -1):
                if locations[n].can_reach(state):
                    sphere.append(locations.pop(n))

            if not sphere:
                access_opt = getattr(world.options, "accessibility", None)
                if access_opt and getattr(access_opt, "value", None) == 1:  # minimal
                    break
                unreached = [loc.name for loc in locations]
                raise AssertionError(f"Unreachable locations remaining in logic: {unreached[:10]}...")

            sphere_count += 1
            for loc in sphere:
                if loc.item:
                    state.collect(loc.item, True, loc)

        if not multiworld.has_beaten_game(state, player):
            raise AssertionError(f"Collected all accessible locations, but cannot beat the game on seed {seed}!")

        # Step 6: Verification - Item & Location Pool Integrity
        unfilled = multiworld.get_unfilled_locations(player)
        if len(unfilled) > 0:
            raise AssertionError(f"{len(unfilled)} unfilled locations remaining after generation: {[l.name for l in unfilled[:5]]}")

        all_locations = list(multiworld.get_locations(player))
        placed_items = [loc.item for loc in all_locations if loc.item and loc.item.code]
        if len(multiworld.itempool) > len(placed_items):
            raise AssertionError(f"Unplaced items remaining in itempool: {len(multiworld.itempool)} > {len(placed_items)}")

        # Step 7: Verification - Precollected Starting Tank
        if hasattr(world, "starting_tank_unlock") and world.starting_tank_unlock:
            precollected_names = [it.name for it in multiworld.precollected_items[player]]
            if world.starting_tank_unlock not in precollected_names:
                raise AssertionError(
                    f"Starting tank unlock '{world.starting_tank_unlock}' was not precollected in seed {seed}!"
                )

        # Step 8: Verification - Slot Data Serializability & Consistency
        slot_data = world.fill_slot_data()
        if not isinstance(slot_data, dict):
            raise AssertionError("fill_slot_data() did not return a dictionary!")
        try:
            json.dumps(slot_data)
        except Exception as json_err:
            raise AssertionError(f"fill_slot_data() is not JSON-serializable: {json_err}")

        # Step 9: Verification - Alien Randomization Constraints
        if config.options.get("alien_randomization", world.options.alien_randomization.value):
            alien_rando_data = slot_data.get("alien_randomization", {})
            if alien_rando_data:
                valid_tanks = {"Tank 1", "Tank 2", "Tank 3", "Tank 4"}
                if set(alien_rando_data.keys()) != valid_tanks:
                    raise AssertionError(f"alien_randomization missing tanks: {set(alien_rando_data.keys())} != {valid_tanks}")
                for tank_name, aliens in alien_rando_data.items():
                    if not (3 <= len(aliens) <= 4):
                        raise AssertionError(f"{tank_name} has {len(aliens)} aliens, expected 3-4: {aliens}")

        duration = time.perf_counter() - start_time
        return GenerationResult(
            config_name=config.name,
            options=config.options,
            seed=seed,
            success=True,
            status="PASS",
            duration=duration,
            locations_count=len(all_locations),
            items_count=len(placed_items),
            sphere_count=sphere_count,
        )

    except OptionError as opt_err:
        duration = time.perf_counter() - start_time
        if expected_option_error or "too few locations" in str(opt_err):
            return GenerationResult(
                config_name=config.name,
                options=config.options,
                seed=seed,
                success=True,
                status="EXPECTED_ERROR",
                duration=duration,
                error_type="OptionError (Expected)",
                error_message=str(opt_err),
            )
        else:
            return GenerationResult(
                config_name=config.name,
                options=config.options,
                seed=seed,
                success=False,
                status="FAIL",
                duration=duration,
                error_type="OptionError (Unexpected)",
                error_message=str(opt_err),
                traceback_str=traceback.format_exc(),
            )

    except Exception as exc:
        duration = time.perf_counter() - start_time
        return GenerationResult(
            config_name=config.name,
            options=config.options,
            seed=seed,
            success=False,
            status="FAIL",
            duration=duration,
            error_type=type(exc).__name__,
            error_message=str(exc),
            traceback_str=traceback.format_exc(),
        )


def _worker_wrapper(args_tuple: Tuple[str, TestCaseConfig, int]) -> GenerationResult:
    game_name, config, seed = args_tuple
    return run_single_generation(game_name, config, seed)


# ---------------------------------------------------------------------------
# Test Runner Orchestration
# ---------------------------------------------------------------------------
class GenerationTestRunner:
    def __init__(
        self,
        game_name: str = "Insaniquarium Deluxe",
        seeds_per_config: int = 3,
        base_seed: int = 10000,
        max_workers: Optional[int] = None,
        stop_on_failure: bool = False,
        verbose: bool = False,
    ):
        self.game_name = game_name
        self.seeds_per_config = seeds_per_config
        self.base_seed = base_seed
        self.max_workers = max_workers or min(8, os.cpu_count() or 1)
        self.stop_on_failure = stop_on_failure
        self.verbose = verbose

        self.world_type = AutoWorldRegister.world_types[game_name]
        self.domains = get_option_domains(self.world_type)

    def print_option_table(self):
        """Displays all introspected options and their tested values in a clean table."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}Discovered Options for {self.game_name}:{Colors.RESET}")
        print("=" * 95)
        print(f"{'Option Name':<28} | {'Type':<8} | {'Default':<10} | {'Allowed / Sampled Values'}")
        print("-" * 95)
        for name, domain in sorted(self.domains.items()):
            vals_str = str(domain.allowed_values)
            if len(vals_str) > 45:
                vals_str = vals_str[:42] + "..."
            print(f"{name:<28} | {domain.option_type:<8} | {str(domain.default_value):<10} | {vals_str}")
        print("=" * 95)
        print(f"Total options: {len(self.domains)}\n")

    def run_suite(
        self,
        test_cases: List[TestCaseConfig],
    ) -> List[GenerationResult]:
        """
        Executes the provided test cases across multiple seeds in parallel or sequentially.
        """
        tasks: List[Tuple[str, TestCaseConfig, int]] = []
        for config in test_cases:
            cfg_hash = abs(hash(json.dumps(config.options, sort_keys=True))) % 100000
            for s_idx in range(self.seeds_per_config):
                seed = self.base_seed + cfg_hash + (s_idx * 17)
                tasks.append((self.game_name, config, seed))

        total_runs = len(tasks)
        print(
            f"{Colors.BOLD}{Colors.BLUE}[*] Starting Generation Suite:{Colors.RESET} "
            f"{len(test_cases)} configurations × {self.seeds_per_config} seeds = {Colors.BOLD}{total_runs}{Colors.RESET} total generations"
        )
        print(f"{Colors.DIM}Using {self.max_workers} worker processes. Base seed: {self.base_seed}{Colors.RESET}\n")

        results: List[GenerationResult] = []
        passed_count = 0
        failed_count = 0
        expected_err_count = 0
        start_time = time.perf_counter()

        def handle_result(res: GenerationResult):
            nonlocal passed_count, failed_count, expected_err_count
            results.append(res)
            completed = len(results)
            elapsed = time.perf_counter() - start_time
            rate = completed / elapsed if elapsed > 0 else 0

            if res.status == "PASS":
                passed_count += 1
                status_colored = f"{Colors.GREEN}[PASS]{Colors.RESET}"
            elif res.status == "EXPECTED_ERROR":
                expected_err_count += 1
                status_colored = f"{Colors.YELLOW}[EXPECTED_ERR]{Colors.RESET}"
            else:
                failed_count += 1
                status_colored = f"{Colors.RED}{Colors.BOLD}[FAIL]{Colors.RESET}"

            pct = (completed / total_runs) * 100
            sys.stdout.write(
                f"\r{Colors.BOLD}[{completed:4d}/{total_runs:4d} {pct:5.1f}%]{Colors.RESET} "
                f"{status_colored} "
                f"Pass: {Colors.GREEN}{passed_count}{Colors.RESET} | "
                f"Fail: {Colors.RED}{failed_count}{Colors.RESET} | "
                f"Rate: {rate:4.1f}/s | "
                f"Seed: {res.seed} | "
                f"{res.config_name[:38]:<38}"
            )
            sys.stdout.flush()

            if not res.success or self.verbose:
                print()
                if not res.success:
                    print(f"  {Colors.RED}Error:{Colors.RESET} {res.error_type}: {res.error_message}")
                    reproduce_cmd = (
                        f"python worlds/insaniquarium/test/test_generation.py "
                        f"--reproduce '{json.dumps(res.options)}' --seed {res.seed}"
                    )
                    print(f"  {Colors.YELLOW}Reproduce:{Colors.RESET} {reproduce_cmd}")

        if self.max_workers > 1:
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(_worker_wrapper, t): t for t in tasks}
                try:
                    for future in as_completed(futures):
                        res = future.result()
                        handle_result(res)
                        if self.stop_on_failure and not res.success:
                            print(f"\n{Colors.RED}Aborting suite early due to --stop-on-failure.{Colors.RESET}")
                            executor.shutdown(wait=False, cancel_futures=True)
                            break
                except KeyboardInterrupt:
                    print(f"\n{Colors.YELLOW}Cancelled by user.{Colors.RESET}")
                    executor.shutdown(wait=False, cancel_futures=True)
        else:
            for t in tasks:
                res = _worker_wrapper(t)
                handle_result(res)
                if self.stop_on_failure and not res.success:
                    print(f"\n{Colors.RED}Aborting suite early due to --stop-on-failure.{Colors.RESET}")
                    break

        print("\n")
        self.print_summary(results, time.perf_counter() - start_time)
        return results

    def print_summary(self, results: List[GenerationResult], total_duration: float):
        """Displays rich test summary and failure analysis."""
        total = len(results)
        passed = sum(1 for r in results if r.status == "PASS")
        expected_err = sum(1 for r in results if r.status == "EXPECTED_ERROR")
        failed = sum(1 for r in results if r.status == "FAIL")

        print("=" * 80)
        print(f"{Colors.BOLD}{Colors.CYAN}Generation Test Results Summary{Colors.RESET}")
        print("=" * 80)
        print(f"Total Generations Tested: {Colors.BOLD}{total}{Colors.RESET}")
        print(f"Passed:                   {Colors.GREEN}{Colors.BOLD}{passed}{Colors.RESET}")
        if expected_err:
            print(f"Expected Option Errors:   {Colors.YELLOW}{expected_err}{Colors.RESET} (Expected validation rejections)")
        print(f"Failed:                   {Colors.RED if failed else Colors.GREEN}{Colors.BOLD}{failed}{Colors.RESET}")
        print(f"Total Suite Time:         {total_duration:.2f} seconds ({total / total_duration:.1f} gen/s)" if total_duration > 0 else "")
        print("=" * 80)

        if failed > 0:
            print(f"\n{Colors.RED}{Colors.BOLD}Failed Configurations Breakdown ({failed} failures):{Colors.RESET}")
            failure_dict: Dict[str, List[GenerationResult]] = {}
            for r in results:
                if not r.success:
                    failure_dict.setdefault(r.error_type or "Unknown", []).append(r)

            for err_type, err_results in failure_dict.items():
                print(f"\n  {Colors.BOLD}{Colors.RED}• {err_type} ({len(err_results)} occurrences):{Colors.RESET}")
                for sample in err_results[:5]:
                    print(f"      - Config: {sample.config_name}")
                    print(f"        Options: {sample.options}")
                    print(f"        Seed: {sample.seed}")
                    print(f"        Message: {sample.error_message}")
                    print(
                        f"        Repro: {Colors.YELLOW}python worlds/insaniquarium/test/test_generation.py "
                        f"--reproduce '{json.dumps(sample.options)}' --seed {sample.seed}{Colors.RESET}"
                    )
                if len(err_results) > 5:
                    print(f"      ... and {len(err_results) - 5} more identical error instances.")
            print()


# ---------------------------------------------------------------------------
# Reproduction Mode
# ---------------------------------------------------------------------------
def run_reproduce_mode(game_name: str, options_json: str, seed: int):
    """
    Executes a single generation with verbose debugging output for reproducing failures.
    """
    try:
        options_dict = json.loads(options_json)
    except Exception as e:
        print(f"{Colors.RED}Failed to parse options JSON: {e}{Colors.RESET}")
        sys.exit(1)

    print(f"\n{Colors.BOLD}{Colors.CYAN}=== Reproduction Run ==={Colors.RESET}")
    print(f"Game:    {game_name}")
    print(f"Seed:    {seed}")
    print(f"Options: {json.dumps(options_dict, indent=2)}")
    print("=" * 40 + "\n")

    cfg = TestCaseConfig(name="Reproduction", options=options_dict, category="reproduce")
    res = run_single_generation(game_name, cfg, seed)

    if res.success:
        print(f"\n{Colors.GREEN}{Colors.BOLD}[+] Generation SUCCESSFUL!{Colors.RESET}")
        print(f"    Locations: {res.locations_count}")
        print(f"    Items:     {res.items_count}")
        print(f"    Spheres:   {res.sphere_count}")
        print(f"    Duration:  {res.duration:.3f}s")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}[-] Generation FAILED!{Colors.RESET}")
        print(f"    Error Type: {res.error_type}")
        print(f"    Message:    {res.error_message}")
        if res.traceback_str:
            print(f"\n{Colors.DIM}Traceback:\n{res.traceback_str}{Colors.RESET}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Unittest Integration (Runs fast smoke tests under `unittest discover`)
# ---------------------------------------------------------------------------
try:
    if __package__:
        from . import InsaniquariumTestBase
    else:
        from worlds.insaniquarium.test import InsaniquariumTestBase
except (ImportError, ValueError):
    try:
        from worlds.insaniquarium.test import InsaniquariumTestBase
    except ImportError:
        InsaniquariumTestBase = None

if InsaniquariumTestBase is not None:
    class TestGenerationSmoke(InsaniquariumTestBase):
        """Smoke test ensuring multiworld generation succeeds across key presets and seeds."""

        def test_default_generation_multiple_seeds(self) -> None:
            cfg = TestCaseConfig(name="Default Options", options={}, category="smoke")
            for seed in [1001, 2002, 3003]:
                with self.subTest(seed=seed):
                    res = run_single_generation(self.game, cfg, seed)
                    self.assertTrue(res.success, f"Default gen failed on seed {seed}: {res.error_message}")

        def test_starting_tanks_generation(self) -> None:
            for tank in [0, 1, 2, 3, 4]:
                cfg = TestCaseConfig(name=f"Starting Tank {tank}", options={"starting_tank": tank}, category="smoke")
                res = run_single_generation(self.game, cfg, seed=222)
                self.assertTrue(res.success, f"Gen failed for starting_tank={tank}: {res.error_message}")

        def test_upgrade_availability_generation(self) -> None:
            for upgrade in ["always", "free", "normal_price"]:
                cfg = TestCaseConfig(name=f"Upgrade {upgrade}", options={"upgrade_availability": upgrade}, category="smoke")
                res = run_single_generation(self.game, cfg, seed=555)
                self.assertTrue(res.success, f"Gen failed for upgrade_availability={upgrade}: {res.error_message}")

        def test_max_checks_generation(self) -> None:
            cfg = TestCaseConfig(
                name="Max Checks",
                options={
                    "egg_pieces_per_level": 3,
                    "bonus_pet_locations": 4,
                    "include_time_trials": True,
                    "include_challenge_mode": True,
                    "aliensanity": True,
                    "alien_randomization": True,
                },
                category="smoke",
            )
            res = run_single_generation(self.game, cfg, seed=777)
            self.assertTrue(res.success, f"Max checks gen failed: {res.error_message}")


# ---------------------------------------------------------------------------
# CLI Argument Parser & Entry Point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive Archipelago Generation Test Script for Insaniquarium Deluxe.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--game",
        default="Insaniquarium Deluxe",
        help="Target game name (default: 'Insaniquarium Deluxe').",
    )
    parser.add_argument(
        "--mode",
        choices=["isolated", "presets", "matrix", "cartesian", "random", "all"],
        default="isolated",
        help=(
            "Test generation strategy:\n"
            "  isolated:  Test each option across all allowed values in isolation (default)\n"
            "  presets:   Test predefined gameplay and boundary presets\n"
            "  matrix:    Pairwise (all-pairs) combinatorial testing across options\n"
            "  cartesian: Full Cartesian product of selected options (--combine)\n"
            "  random:    Random fuzz testing across all options (--count)\n"
            "  all:       Run isolated + presets + matrix"
        ),
    )
    parser.add_argument(
        "--seeds",
        "-n",
        type=int,
        default=3,
        help="Number of different seeds to test for each option variation (default: 3).",
    )
    parser.add_argument(
        "--base-seed",
        type=int,
        default=10000,
        help="Base starting seed for deterministic generation (default: 10000).",
    )
    parser.add_argument(
        "--workers",
        "-j",
        type=int,
        default=None,
        help="Number of parallel worker processes (default: CPU core count).",
    )
    parser.add_argument(
        "--combine",
        nargs="+",
        help="Options to combine for --mode cartesian (e.g. --combine starting_tank egg_pieces_per_level).",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=25,
        help="Number of test cases for --mode random (default: 25).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Maximum number of Cartesian combinations to test (default: 500).",
    )
    parser.add_argument(
        "--stop-on-failure",
        "-x",
        action="store_true",
        help="Halt testing immediately upon the first failure.",
    )
    parser.add_argument(
        "--list-options",
        action="store_true",
        help="Print table of all discovered options, defaults, and allowed values, then exit.",
    )
    parser.add_argument(
        "--reproduce",
        type=str,
        help="Reproduce a specific failure given an options JSON string (requires --seed).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Seed to use with --reproduce.",
    )
    parser.add_argument(
        "--json-report",
        type=str,
        help="Output test results to a JSON report file.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI color output.",
    )

    args = parser.parse_args()

    if args.no_color:
        Colors.disable()

    # Reproduction Mode
    if args.reproduce:
        if args.seed is None:
            parser.error("--reproduce requires --seed <int>")
        run_reproduce_mode(args.game, args.reproduce, args.seed)
        return

    runner = GenerationTestRunner(
        game_name=args.game,
        seeds_per_config=args.seeds,
        base_seed=args.base_seed,
        max_workers=args.workers,
        stop_on_failure=args.stop_on_failure,
        verbose=args.verbose,
    )

    if args.list_options:
        runner.print_option_table()
        return

    # Select test case generation strategy
    test_cases: List[TestCaseConfig] = []
    if args.mode == "isolated":
        test_cases = generate_isolated_test_cases(runner.domains)
    elif args.mode == "presets":
        test_cases = generate_presets_test_cases()
    elif args.mode == "matrix":
        test_cases = generate_pairwise_test_cases(runner.domains, selected_options=args.combine)
    elif args.mode == "cartesian":
        test_cases = generate_cartesian_test_cases(runner.domains, selected_options=args.combine, limit=args.limit)
    elif args.mode == "random":
        test_cases = generate_random_fuzz_test_cases(runner.domains, count=args.count)
    elif args.mode == "all":
        test_cases = (
            generate_presets_test_cases()
            + generate_isolated_test_cases(runner.domains)
            + generate_pairwise_test_cases(runner.domains)
        )

    results = runner.run_suite(test_cases)

    # Save JSON report if requested
    if args.json_report:
        report_data = {
            "game": args.game,
            "mode": args.mode,
            "seeds_per_config": args.seeds,
            "base_seed": args.base_seed,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_generations": len(results),
            "passed": sum(1 for r in results if r.status == "PASS"),
            "failed": sum(1 for r in results if r.status == "FAIL"),
            "expected_errors": sum(1 for r in results if r.status == "EXPECTED_ERROR"),
            "results": [
                {
                    "config_name": r.config_name,
                    "options": r.options,
                    "seed": r.seed,
                    "status": r.status,
                    "duration": r.duration,
                    "error_type": r.error_type,
                    "error_message": r.error_message,
                }
                for r in results
            ],
        }
        with open(args.json_report, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        print(f"Saved JSON report to {args.json_report}")

    failed_count = sum(1 for r in results if r.status == "FAIL")
    sys.exit(1 if failed_count > 0 else 0)


if __name__ == "__main__":
    main()
