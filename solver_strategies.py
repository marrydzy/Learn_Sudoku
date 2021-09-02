from collections import defaultdict, namedtuple, OrderedDict
import singles
import intersections
import subsets
import uniqueness_tests
import intermediate_techniques
import fish
import wings
import coloring
import almost_locked_set
import questionable


Strategy = namedtuple("Strategy", ["solver", "technique", "name", "priority", "ranking", "active"])


solver_strategies = {
    "full_house": Strategy(singles.full_house, "singles", "Full House", 1, 4, True),
    "visual_elimination": Strategy(singles.visual_elimination, "singles", "Visual Elimination", 2, 4, True),
    "naked_singles": Strategy(singles.naked_singles, "singles", "Naked Single", 3, 4, True),
    "hidden_singles": Strategy(singles.hidden_singles, "singles", "Hidden Single", 4, 14, True),
    "locked_candidates": Strategy(intersections.locked_candidates, "intersections", "Locked Candidates", 5, 50, True),
    "locked_candidates_type_1": Strategy(None, "", "Locked Candidates - Type 1 (Pointing)", 999, 0, False),
    "locked_candidates_type_2": Strategy(None, "", "Locked Candidates - Type 2 (Claiming)", 999, 0, False),
    "naked_pair": Strategy(subsets.naked_pair, "subsets", "Naked Pair", 6, 60, True),
    "hidden_pair": Strategy(subsets.hidden_pair, "subsets", "Hidden Pair", 7, 70, True),
    "swordfish": Strategy(fish.swordfish, "fish", "Swordfish", 8, 140, True),
    "xy_wing": Strategy(wings.xy_wing, "wings", "XY-Wing", 9, 160, True),
    "xyz_wing": Strategy(wings.xyz_wing, "wings", "XYZ-Wing", 10, 180, True),
    "wxyz_wing": Strategy(wings.wxyz_wing, "wings", "WXYZ-Wing", 11, 240, True),
    "wxyz_wing_type_1": Strategy(None, "", "WXYZ-Wing (Type 1)", 999, 0, False),
    "wxyz_wing_type_2": Strategy(None, "", "WXYZ-Wing (Type 2)", 999, 0, False),
    "wxyz_wing_type_3": Strategy(None, "", "WXYZ-Wing (Type 3)", 999, 0, False),
    "wxyz_wing_type_4": Strategy(None, "", "WXYZ-Wing (Type 4)", 999, 0, False),
    "wxyz_wing_type_5": Strategy(None, "", "WXYZ-Wing (Type 5)", 999, 0, False),
    "w_wing": Strategy(wings.w_wing, "wings", "W-Wing", 12, 150, True),
    "naked_triplet": Strategy(subsets.naked_triplet, "subsets", "Naked Triplet", 13, 80, True),
    "test_1": Strategy(uniqueness_tests.test_1, "uniqueness_tests", "Uniqueness Test 1", 14, 100, True),
    "test_2": Strategy(uniqueness_tests.test_2, "uniqueness_tests", "Uniqueness Test 2", 15, 100, True),
    "test_3": Strategy(uniqueness_tests.test_3, "uniqueness_tests", "Uniqueness Test 3", 16, 100, True),
    "test_4": Strategy(uniqueness_tests.test_4, "uniqueness_tests", "Uniqueness Test 4", 17, 100, True),
    "test_5": Strategy(uniqueness_tests.test_5, "uniqueness_tests", "Uniqueness Test 5", 18, 100, True),
    "test_6": Strategy(uniqueness_tests.test_6, "uniqueness_tests", "Uniqueness Test 6", 19, 100, True),
    "skyscraper": Strategy(intermediate_techniques.skyscraper, "Single Digit Patterns", "Skyscraper", 20, 130, True),
    "x_wing": Strategy(fish.x_wing, "fish", "X-Wing", 21, 100, True),
    "jellyfish": Strategy(fish.jellyfish, "fish", "Jellyfish", 22, 470, True),
    "finned_x_wing": Strategy(fish.finned_x_wing, "fish", "Finned X-Wing", 23, 130, True),
    "finned_swordfish": Strategy(fish.finned_swordfish, "fish", "Finned Swordfish", 24, 200, True),
    "finned_jellyfish": Strategy(fish.finned_jellyfish, "fish", "Finned Jellyfish", 25, 240, True),
    "finned_squirmbag": Strategy(fish.finned_squirmbag, "fish", "Finned Squirmbag", 26, 470, True),
    "finned_mutant_x_wing": Strategy(wings.finned_mutant_x_wing, "wings", "Finned Mutant X-Wing", 27, 470, True),
    "finned_rccb_mutant_x_wing": Strategy(None, "", "Finned RCCB Mutant X-Wing", 999, 0, False),
    "finned_rbcc_mutant_x_wing": Strategy(None, "", "Finned RBCC Mutant X-Wing", 999, 0, False),
    "finned_cbrc_mutant_x_wing": Strategy(None, "", "Finned CBRC Mutant X-Wing", 999, 0, False),
    "simple_colors": Strategy(coloring.simple_colors, "coloring", "Simple Colors", 28, 150, True),
    "color_trap": Strategy(None, "", "Simple Colors - Color Trap", 999, 0, False),
    "color_wrap": Strategy(None, "", "Simple Colors - Color Wrap", 999, 0, False),
    "multi_colors": Strategy(coloring.multi_colors, "coloring", "Multi-Colors", 29, 200, True),
    "multi_colors-color_wrap": Strategy(None, "", "Multi-Colors - Color Wrap", 999, 0, False),
    "multi_colors-color_wing": Strategy(None, "", "Multi-Colors - Color Wing", 999, 0, False),
    "x_colors": Strategy(coloring.x_colors, "coloring", "X-Colors", 30, 200, True),
    "x_colors_elimination": Strategy(None, "", "X-Colors - Elimination", 999, 0, False),
    "x_colors_contradiction": Strategy(None, "", "X-Colors - Contradiction", 999, 0, False),
    "three_d_medusa": Strategy(coloring.three_d_medusa, "coloring", "3D Medusa", 31, 320, True),
    "naked_xy_chain": Strategy(coloring.naked_xy_chain, "coloring", "Naked XY Chain", 32, 310, True),
    "hidden_xy_chain": Strategy(coloring.hidden_xy_chain, "coloring", "Hidden XY Chain", 33, 310, True),
    "empty_rectangle": Strategy(intermediate_techniques.empty_rectangle, "intermediate_techniques",
                                "Epmpty Rectangle", 34, 130, True),
    "sue_de_coq": Strategy(intermediate_techniques.sue_de_coq, "intermediate_techniques", "Sue de Coq technique",
                           35, 130, True),
    "als_xy": Strategy(almost_locked_set.als_xy, "almost_locked_set", "ALS-XY", 36, 320, True),
    "als_xz": Strategy(almost_locked_set.als_xz, "almost_locked_set", "ALS-XZ", 37, 300, True),
    "death_blossom": Strategy(almost_locked_set.death_blossom, "almost_locked_set", "Death Blossom", 38, 360, True),
    "als_xy_wing": Strategy(almost_locked_set.als_xy_wing, "almost_locked_set", "ALS-XY-Wing", 39, 330, True),
    "hidden_triplet": Strategy(subsets.hidden_triplet, "subsets", "Hidden Triplet", 40, 100, True),
    "squirmbag": Strategy(fish.squirmbag, "fish", "Squirmbag", 41, 470, True),
    "naked_quad": Strategy(subsets.naked_quad, "subsets", "Naked Quad", 42, 120, True),
    "hidden_quad": Strategy(subsets.hidden_quad, "subsets", "Hidden Quad", 43, 150, True),
    "almost_locked_candidates": Strategy(questionable.almost_locked_candidates, "questionable",
                                         "Almost Locked Candidates", 44, 320, True),
    "franken_x_wing": Strategy(questionable.franken_x_wing, "questionable", "Franken X-Wing", 45, 300, True),
}

by_hits = {
    'Naked Single':	1,
    'Hidden Single': 2,
    'Locked Candidates': 3,
    '3D Medusa': 4,
    'Naked Pair': 5,
    'Hidden Pair': 6,
    'ALS-XZ': 7,
    'X-Colors': 8,
    'ALS-XY-Wing': 9,
    'W-Wing': 10,
    'Uniqueness Test 1': 11,
    'Uniqueness Test 4': 12,
    'XY-Wing': 13,
    'Finned X-Wing': 14,
    'ALS-XY': 15,
    'WXYZ-Wing': 16,
    'Uniqueness Test 6': 17,
    'Finned Jellyfish': 18,
    'Hidden Triplet': 19,
    'Uniqueness Test 3': 20,
    'Naked XY Chain': 21,
    'Finned Mutant X-Wing': 22,
    'Finned Swordfish': 23,
    'Swordfish': 24,
    'Finned Squirmbag': 25,
    'Skyscraper': 26,
    'Visual Elimination': 27,
    'Full House': 28,
    'XYZ-Wing': 29,
    'Simple Colors': 30,
    'Naked Triplet': 31,
    'Uniqueness Test 2': 32,
    'X-Wing': 33,
    'Multi-Colors': 34,
    'Jellyfish': 35,
    'Uniqueness Test 5': 36,
    'Hidden XY Chain': 37,
    'Epmpty Rectangle': 38,
    'Sue de Coq technique': 39,
    'Death Blossom': 40,
    'Squirmbag': 41,
    'Naked Quad': 42,
    'Hidden Quad': 43,
    'Almost Locked Candidates': 44,
    'Franken X-Wing': 45,
}


def main():

    strategy_priorities = defaultdict(list)
    # by strategy ranking
    for _, strategy in solver_strategies.items():
        if strategy.active:
            strategy_priorities[strategy.name].append(strategy.ranking)
    # by number of hits
    for strategy in by_hits:
        strategy_priorities[strategy].append(by_hits[strategy])

    print('\n')
    for strategy in strategy_priorities:
        print('%s%i, %i%s' % ('"' + strategy + '": Priority(', strategy_priorities[strategy][0],
                              strategy_priorities[strategy][1], '),'))

    """
    sorted_by = "by_ranking"
    # sorted_by = "by_hits"

    if sorted_by == "by_hits":
        for key, priority in by_hits.items():
            strategy_priorities[key] = priority
    elif sorted_by == "by_ranking":
        for _, strategy in solver_strategies.items():
            strategy_priorities[strategy.name] = strategy.ranking if strategy.active else 999

    if False:
        print('\n')
        for strategy, priority in strategy_priorities.items():
            print('%-25s    %i' %(strategy, priority))

        print('\n')
        for _, strategy in solver_strategies.items():
            priority = strategy_priorities[strategy.name]
            print('%-25s    %i' % (strategy.name, priority))

    strategies = OrderedDict(sorted(solver_strategies.items(),
                                    key=lambda key_value_pair: strategy_priorities[key_value_pair[1].name]))

    print('\n')
    for _, strategy in strategies.items():
        if strategy.active:
            print('%-25s    %i' %(strategy.name, strategy.ranking))
    """

if __name__ == "__main__":
    main()
