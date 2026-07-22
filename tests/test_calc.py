import math
from collections import namedtuple
from unittest.mock import patch

import calc.cp_formula as cf

Pokemon = namedtuple("Pokemon", ["form_id", "number", "name", "stamina", "attack", "defense", "form"])

POKEMON = Pokemon(form_id=1, number=1, name="Testmon", stamina=128, attack=118, defense=111, form="Normal")

LEVELS = [1.0, 10.0, 20.0, 25.0, 30.0, 40.0, 51.0]
MULTIPLIERS = [0.094, 0.4225, 0.5974, 0.667934, 0.7317, 0.7903, 0.84529999]
CPM_BY_LEVEL = dict(zip(LEVELS, MULTIPLIERS))


def test_calc_stats_matches_hand_computed_value():
    cpm = 0.5974
    cp, attack, defense, stamina = cf.calc_stats(0, 0, 0, pokemon=POKEMON, cpm=cpm)

    expected_attack = POKEMON.attack * cpm
    expected_defense = POKEMON.defense * cpm
    raw_stamina = POKEMON.stamina * cpm  # unfloored -- cp uses this, not the displayed hp
    expected_stamina = math.floor(raw_stamina)  # what calc_stats actually returns
    expected_cp = max(10, math.floor(expected_attack * expected_defense**0.5 * raw_stamina**0.5 / 10))

    assert attack == expected_attack
    assert defense == expected_defense
    assert stamina == expected_stamina
    assert cp == expected_cp


def test_calc_stats_higher_ivs_never_produce_a_lower_cp():
    cp_no_iv, *_ = cf.calc_stats(0, 0, 0, pokemon=POKEMON, cpm=0.5974)
    cp_max_iv, *_ = cf.calc_stats(15, 15, 15, pokemon=POKEMON, cpm=0.5974)
    assert cp_max_iv > cp_no_iv


def test_calc_stats_clamps_minimum_cp_to_10():
    # stats/cpm low enough that the raw formula would floor below 10
    weak_pokemon = POKEMON._replace(attack=30, defense=30, stamina=30)
    cp, *_ = cf.calc_stats(0, 0, 0, pokemon=weak_pokemon, cpm=0.094)  # level 1
    assert cp == 10


def test_calc_stats_requires_a_pokemon_or_id():
    assert cf.calc_stats(0, 0, 0, cpm=0.5974) is None


def test_calc_stats_requires_a_cpm_or_level():
    assert cf.calc_stats(0, 0, 0, pokemon=POKEMON) is None


@patch("calc.cp_formula.get_cpm_table", return_value=(LEVELS, MULTIPLIERS))
def test_calc_level_recovers_a_level_that_reproduces_the_same_cp(mock_table):
    for level, cpm in zip(LEVELS, MULTIPLIERS):
        cp, *_ = cf.calc_stats(0, 15, 15, pokemon=POKEMON, cpm=cpm)

        recovered_level = cf.calc_level(cp, 0, 15, 15, pokemon=POKEMON)
        recovered_cp, *_ = cf.calc_stats(0, 15, 15, pokemon=POKEMON, cpm=CPM_BY_LEVEL[recovered_level])

        assert recovered_cp == cp


def test_calc_level_assumes_level_1_at_the_cp_10_floor():
    assert cf.calc_level(10, 0, 0, 0, pokemon=POKEMON) == 1


@patch("calc.cp_formula.get_cpm_table", return_value=(LEVELS, MULTIPLIERS))
def test_calc_max_level_finds_the_highest_level_under_the_cap(mock_table):
    cp_cap = 1200

    level, cp, attack, defense, stamina, product = cf.calc_max_level(cp_cap, 0, 15, 15, pokemon=POKEMON)

    assert cp <= cp_cap
    assert product == attack * defense * stamina

    idx = LEVELS.index(level)
    if idx + 1 < len(LEVELS):
        next_cp, *_ = cf.calc_stats(0, 15, 15, pokemon=POKEMON, cpm=MULTIPLIERS[idx + 1])
        assert next_cp > cp_cap


@patch("calc.cp_formula.get_cpm_table", return_value=(LEVELS, MULTIPLIERS))
def test_calc_max_level_returns_none_if_even_the_lowest_level_exceeds_the_cap(mock_table):
    assert cf.calc_max_level(5, 15, 15, 15, pokemon=POKEMON) is None
