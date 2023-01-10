_getitem_dict_params = [
    # no pattern
    ({"a": 1}, [], {"a": 1}),
    ({"a": 1}, "a", 1),
    ({0: 1}, 0, 1),
    ({"a": 1}, ["b"], KeyError),
    ({}, ["b"], KeyError),
    ({"a": 1}, ["a"], 1),
    ({"a": 1}, [["a"]], TypeError),
    # globbing: len(path) == 1
    ({"a": 1}, ["*"], 1),
    ({"a": 1, "b": 2}, ["*"], [1, 2]),
    ({"a": {"b": 3}, "c": ["y", "x"]}, ["*"], [{"b": 3}, ["y", "x"]]),
    ({0: "i", "0": "j"}, [0], "i"),
    ({0: "i", "0": "j"}, ["0"], "j"),
    ({0: "i", "0": "j"}, ["[0]"], ["i", "j"]),
    ({0: "i", "0": "j"}, ["*[0]"], ["i", "j"]),
    ({1: "i", "1": "j", "a": "k"}, "*[!1]", "k"),
    ({1: "i", "1": "j", "a": "k"}, ["*[!1]"], "k"),
    # globbing: len(path) > 1
    ({"a": {"b": 3}, "c": ["x"]}, ["*", "b"], 3),
    ({"a": {"b": 3}, "c": ["x"]}, ["*", "x"], []),
    ({"a": {"b": 3}, "c": ["x"]}, ["*", "0"], []),
    ({"a": {0: 3}, "c": ["x"]}, ["*", "0"], []),
    ({"a": {0: 3}, "c": ["x"]}, ["*", 0], [3, "x"]),
    ({"a": {0: 3, "0": 4}, "c": ["x"]}, ["*", 0], [3, "x"]),
    ({"a": {5: 3, "5": 4}, "c": ["x"]}, ["*", 5], 3),
    (
        {"a": {"b": {"c": [0]}, "d": {"c": 1}}, "e": {"b": {"c": {"x": "x"}}}},
        ["*", "*", "c"],
        [[0], 1, {"x": "x"}],
    ),
    (
        {"a": {"b": {"c": {"d": 0}}}, "e": {"b": {"f": {"d": [1]}}}},
        ["*", "b", "*", "d"],
        [0, [1]],
    ),
    # globbing: with "**"
    (
        {"a": {"b": {"c": {"d": 5}}}, "d": 4},
        ["**"],
        {"a": {"b": {"c": {"d": 5}}}, "d": 4},
    ),
    ({"a": {"b": {"c": {"d": 5}}}, "d": 4}, ["**", "d"], [5, 4]),
    ({"a": {"b": {"d": {"d": 5}}}, "d": 4}, ["**", "d"], [5, {"d": 5}, 4]),
    ({"a": {"b": {"c": {"d": 5}}}, "d": 4}, ["**", "**", "d"], [5, 4]),
    ({"a": {"b": {"c": {"d": 5}}}, "d": 4}, ["a", "**", "d"], 5),
    (
        {"a": {"b": {"c": {"d": 0}}}, "e": {"f": {"b": {"g": {"d": [1]}}}}},
        ["**", "b", "*", "d"],
        [0, [1]],
    ),
    (
        {"a": {"b": {"c": {"xd": {"e": 0}, "yd": {"e": 1}, "zf": {"e": 2}}}}, "e": 3},
        ["a", "**", "?d", "e"],
        [0, 1],
    ),
    (
        {"a": {"b": {"c": {"xd": {"e": {"f": {"g": {"h": {"i": 0}}}}}}}}},
        ["a", "**", "?d", "**", "f", "**", "i"],
        0,
    ),
    (
        {"a": {"yb": {"c": {"xd": {"e": {"f": {"g": {"h": {"i": 0}}}}}}}}},
        ["a", "?b", "**", "i"],
        0,
    ),
    # ({"a": {"b": {"c": {"d": 5}}}, "d": 4}, ["a", "**", "d"], 5),
    # ({"a": {"b": {"c": {"d": 5}}}, "d": 4}, ["a", "*", "d"], []),
    # ({"a": {"b": {"c": {"d": 5}}}, "d": 4}, ["**", "d"], [5, 4]),
    # ({"a": {"b": {"c": {"d": 5}}}, "d": 4}, ["*", "b", "*", "d"], 5),
    # ({"a": {"b": {"d": 5}}, "d": 4}, ["a", "*", "d"], 5),
    # ({"a": {"b": {"c": {"d": 5}}}, "d": 4}, ["*", "d"], [5, 4]),
    # ({"a": {"b": {"c": {"d": 5}}}, "d": 4}, ["*", "*", "d"], [5, 4]),
    # ({"a": {"b": {"c": {"d": 5}}}, "d": 4}, ["*", "*", "*", "d"], [5, 4]),
    # ({"a": 1}, ["*"], {"a": 1}),
    # ({"a": 1}, ["a", "*"], 1),
    # ({"a": 1}, [], {"a": 1}),
    # ({"a": 1}, ["a", "*"], 1),
    # ({"*": 1}, ["*"], {"*": 1}),
    # ({"a": {"*": {"d": 5}}}, ["*", "d"], 5),
    # ({"a": {"*": {"d": 5}}, "d": 4}, ["*", "d"], [5, 4]),
    # ({"a": {"*": {"*": {"d": 5}}}, "d": 4}, ["*", "d"], [5, 4]),
    # ({"*": {"d": 5}}, ["*", "d"], 5),
    # ({"d": [5]}, ["d"], [5]),
    # ([0, [1, [2, [3]]]], [1, 1, 0], 2),
    # ([0, [1, [2, [3]]]], [1, 1], [2, [3]]),
    # ([0, {"a": [1, 2]}], ["*", "a"], [1, 2]),
    # ([0, {"a": [1, 2, {"b": "z"}]}], ["*", "b"], "z"),
    # ([0, {"a": [1, 2], 1: "y"}], ["*", 1], ["y"]), #
    # ([0, {"a": [1, 2]}], ["*", 5], []),
    # ({"a": None}, ["a"], None),
    # ([1], ["a"], TypeError),
    # ([1], ["?"], [1]),
    # ([1], ["[0]"], [1]),
    # ([1], ["[1]"], []),
    # ([1], ["[!1]"], [1]),
    # ([1], ["[!5-10]"], [1]),
    # ([[1]], [0, "a"], TypeError),
    # ([[1]], ['*'], [[1]]),  # XXX
    # ([[1]], ["*", 0], [1]),
    # ([[1]], ["*", 1], []),
    # ({"a": "b"}, ["*", "d"], []),
]

_getitem_list_params = [
    # no pattern
    (["a", "b", "c"], [], ["a", "b", "c"]),
    (["a", "b", "c"], [0], "a"),
    (["a", "b", "c"], ["a"], TypeError),
    (["a", "b", "c"], [5], IndexError),
    ([1, [2]], [1, 1], IndexError),
    # globbing
    (["a"], ["*"], "a"),
    (["a", "b"], ["*"], ["a", "b"]),
    (["a", "b", "c"], ["[0-1]"], ["a", "b"]),
    (["a", "b", "c"], ["[!0]"], ["b", "c"]),
    # globbing with "**"
    (
        ["a", ["b"]],
        ["**"],
        ["a", ["b"]],
    ),  # pytest shows the path here as `[]` for some reason. Works anyway.
    (["a", ["b", ["c", [{"d": 0}]]]], ["**", "d"], 0),
    (["a", ["b", "c"]], ["*", 1], "c"),
    # (["a", ["b", ["c", ["d", "e"]]]], ["**", 1], ["e"]),
    # (['a', ['b', ['c', [1, 2, ['d', ['e']], ['d', ['f']]]]]], ['**', 1], []),
]

getitem_dict_tests = ("obj, path, result", _getitem_dict_params)

getitem_list_tests = ("obj, path, result", _getitem_list_params)


getitem_tests = ("obj, path, result", _getitem_dict_params + _getitem_list_params)
