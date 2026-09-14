import math
from collections import namedtuple
from unittest.mock import patch

import calc.cp_formula as cf
import calc.evolution as ce

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


BASE_NO_EVO = Pokemon(form_id=10, number=10, name="NoEvo", stamina=100, attack=100, defense=100, form="Normal")
BASE_SINGLE_EVO = Pokemon(form_id=20, number=20, name="PreEvo", stamina=100, attack=90, defense=90, form="Normal")
SINGLE_TARGET = Pokemon(form_id=21, number=21, name="PostEvo", stamina=140, attack=140, defense=130, form="Normal")
BASE_BRANCHING = Pokemon(form_id=30, number=30, name="BranchPre", stamina=110, attack=95, defense=95, form="Normal")
BRANCH_A = Pokemon(form_id=31, number=31, name="BranchA", stamina=130, attack=150, defense=100, form="Normal")
BRANCH_B = Pokemon(form_id=32, number=32, name="BranchB", stamina=130, attack=100, defense=150, form="Normal")

SPECIES_BY_ID = {
    p.form_id: p for p in [BASE_NO_EVO, BASE_SINGLE_EVO, SINGLE_TARGET, BASE_BRANCHING, BRANCH_A, BRANCH_B]
}

EVOLUTIONS_BY_ID = {
    BASE_NO_EVO.form_id: [],
    BASE_SINGLE_EVO.form_id: [SINGLE_TARGET.form_id],
    BASE_BRANCHING.form_id: [BRANCH_A.form_id, BRANCH_B.form_id],
}


def test_calc_evolution_stats_requires_a_pokemon_or_id():
    assert ce.calc_evolution_stats(0, 0, 0, 20) is None


@patch("calc.cp_formula.get_cpm", return_value=0.5974)
@patch("calc.evolution.get_pokemon", side_effect=SPECIES_BY_ID.get)
@patch("calc.evolution.get_evolutions", side_effect=lambda from_id: EVOLUTIONS_BY_ID.get(from_id, []))
def test_calc_evolution_stats_returns_empty_list_for_a_pokemon_that_does_not_evolve(mock_evo, mock_pokemon, mock_cpm):
    result = ce.calc_evolution_stats(0, 0, 0, 20, pokemon=BASE_NO_EVO)
    assert result == []


@patch("calc.cp_formula.get_cpm", return_value=0.5974)
@patch("calc.evolution.get_pokemon", side_effect=SPECIES_BY_ID.get)
@patch("calc.evolution.get_evolutions", side_effect=lambda from_id: EVOLUTIONS_BY_ID.get(from_id, []))
def test_calc_evolution_stats_returns_the_single_evolution_target(mock_evo, mock_pokemon, mock_cpm):
    result = ce.calc_evolution_stats(15, 15, 15, 20, pokemon=BASE_SINGLE_EVO)

    assert len(result) == 1
    evolution_id, stats = result[0]
    assert evolution_id == SINGLE_TARGET.form_id
    assert stats == cf.calc_stats(15, 15, 15, pokemon=SINGLE_TARGET, cpm=0.5974)


@patch("calc.cp_formula.get_cpm", return_value=0.5974)
@patch("calc.evolution.get_pokemon", side_effect=SPECIES_BY_ID.get)
@patch("calc.evolution.get_evolutions", side_effect=lambda from_id: EVOLUTIONS_BY_ID.get(from_id, []))
def test_calc_evolution_stats_returns_every_target_for_a_branching_evolution(mock_evo, mock_pokemon, mock_cpm):
    result = ce.calc_evolution_stats(0, 15, 15, 25, pokemon=BASE_BRANCHING)

    returned_ids = {evolution_id for evolution_id, _ in result}
    assert returned_ids == {BRANCH_A.form_id, BRANCH_B.form_id}


CHARMANDER = Pokemon(form_id=60, number=4, name="Charmander", stamina=118, attack=116, defense=93, form="Normal")
CHARMELEON = Pokemon(form_id=61, number=5, name="Charmeleon", stamina=151, attack=158, defense=126, form="Normal")
CHARIZARD = Pokemon(form_id=62, number=6, name="Charizard", stamina=186, attack=223, defense=173, form="Normal")
MEGA_CHARIZARD_X = Pokemon(
    form_id=63, number=6, name="Mega Charizard X", stamina=186, attack=273, defense=213, form="Mega X"
)
MEGA_CHARIZARD_Y = Pokemon(
    form_id=64, number=6, name="Mega Charizard Y", stamina=186, attack=319, defense=212, form="Mega Y"
)

SPECIES_BY_ID.update(
    {p.form_id: p for p in [CHARMANDER, CHARMELEON, CHARIZARD, MEGA_CHARIZARD_X, MEGA_CHARIZARD_Y]}
)
EVOLUTIONS_BY_ID.update(
    {
        CHARMANDER.form_id: [CHARMELEON.form_id],
        CHARMELEON.form_id: [CHARIZARD.form_id],
        CHARIZARD.form_id: [MEGA_CHARIZARD_X.form_id, MEGA_CHARIZARD_Y.form_id],
        # mega forms have no further evolutions -- left unlisted, defaults to []
    }
)


@patch("calc.cp_formula.get_cpm", return_value=0.7903)
@patch("calc.evolution.get_pokemon", side_effect=SPECIES_BY_ID.get)
@patch("calc.evolution.get_evolutions", side_effect=lambda from_id: EVOLUTIONS_BY_ID.get(from_id, []))
def test_calc_evolution_stats_recurses_through_a_chain_that_branches_at_the_end(mock_evo, mock_pokemon, mock_cpm):
    result = ce.calc_evolution_stats(15, 15, 15, 40, pokemon=CHARMANDER)

    returned_ids = [evolution_id for evolution_id, _ in result]
    assert returned_ids == [
        CHARMELEON.form_id,
        CHARIZARD.form_id,
        MEGA_CHARIZARD_X.form_id,
        MEGA_CHARIZARD_Y.form_id,
    ]

    stats_by_id = dict(result)
    assert stats_by_id[CHARMELEON.form_id] == cf.calc_stats(15, 15, 15, pokemon=CHARMELEON, cpm=0.7903)
    assert stats_by_id[CHARIZARD.form_id] == cf.calc_stats(15, 15, 15, pokemon=CHARIZARD, cpm=0.7903)
    assert stats_by_id[MEGA_CHARIZARD_X.form_id] == cf.calc_stats(15, 15, 15, pokemon=MEGA_CHARIZARD_X, cpm=0.7903)
    assert stats_by_id[MEGA_CHARIZARD_Y.form_id] == cf.calc_stats(15, 15, 15, pokemon=MEGA_CHARIZARD_Y, cpm=0.7903)
