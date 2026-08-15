"""The built-in CodeQuest Python curriculum."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Quest:
    id: str
    world: int
    number: int
    title: str
    concept: str
    story: str
    objective: str
    starter: str
    expected_output: str
    hint: str
    xp: int
    difficulty: str = "Easy"


QUESTS: tuple[Quest, ...] = (
    Quest(
        "signal",
        1,
        1,
        "Send a signal",
        "print()",
        "The rover is awake, but Mission Control cannot hear it yet.",
        'Use print() to send exactly: Hello, CodeQuest!',
        '# Send your first message\nprint("...")',
        "Hello, CodeQuest!",
        'Text belongs inside quotes: print("your message")',
        100,
    ),
    Quest(
        "codename",
        1,
        2,
        "Choose a codename",
        "Variables",
        "Every explorer needs a name the ship computer can remember.",
        'Create a variable named hero containing "Nova", then print it.',
        '# Store the codename, then transmit it\nhero = ""\nprint(hero)',
        "Nova",
        'Assign text with hero = "Nova", then pass hero to print().',
        120,
    ),
    Quest(
        "fuel_math",
        1,
        3,
        "Fuel the rocket",
        "Numbers",
        "Two fuel cells must be combined before launch.",
        "Set cell_a to 7 and cell_b to 5. Print their sum.",
        '# Add the two fuel cells\ncell_a = 0\ncell_b = 0\nprint(cell_a + cell_b)',
        "12",
        "Use the + operator between the two variable names.",
        140,
    ),
    Quest(
        "countdown",
        1,
        4,
        "Launch countdown",
        "Loops",
        "The launch engine needs a steady three-step countdown.",
        "Use a loop to print 3, 2, 1 on separate lines, then print Blast off!",
        '# Count down from 3\nfor number in range(3, 0, -1):\n    # Print each number here\n    pass\n\nprint("Blast off!")',
        "3\n2\n1\nBlast off!",
        "range(3, 0, -1) produces 3, 2, 1. Remember to indent the loop body.",
        180,
        "Medium",
    ),
    Quest(
        "airlock",
        2,
        5,
        "Open the airlock",
        "Conditionals",
        "A safety check decides whether the airlock may open.",
        'Set oxygen to 100. If it is at least 80, print "Airlock open".',
        '# Check the oxygen level\noxygen = 100\n\n# Add the safety check below',
        "Airlock open",
        "Use if oxygen >= 80: and indent the print statement beneath it.",
        200,
        "Medium",
    ),
    Quest(
        "cargo",
        2,
        6,
        "Pack the cargo",
        "Lists",
        "The crew must load three supplies in the correct order.",
        'Create a list with "water", "food", and "tools". Loop over it and print each item.',
        '# Pack and inspect the cargo\ncargo = []\n\n# Loop over the cargo below',
        "water\nfood\ntools",
        "Put the three strings in square brackets, then use: for item in cargo:",
        220,
        "Medium",
    ),
    Quest(
        "translator",
        2,
        7,
        "Alien translator",
        "Functions",
        "A tiny translator will make first contact possible.",
        'Create greet(name) that returns "Welcome, " plus the name. Print greet("Zed").',
        '# Build a reusable greeting\ndef greet(name):\n    # Return the greeting here\n    pass\n\nprint(greet("Zed"))',
        "Welcome, Zed",
        "A function begins with def greet(name): and sends a value back with return.",
        260,
        "Tricky",
    ),
    Quest(
        "star_map",
        2,
        8,
        "Decode the star map",
        "Dictionaries",
        "The final coordinates are stored beside their star names.",
        'Create a dictionary with Orion: 42 and Lyra: 17. Print the value for "Orion".',
        '# Read a coordinate from the map\nstars = {}\nprint(stars["Orion"])',
        "42",
        'Dictionary values are retrieved with square brackets: stars["Orion"]',
        300,
        "Tricky",
    ),
)


def quest_by_id(quest_id: str) -> Quest:
    return next(quest for quest in QUESTS if quest.id == quest_id)


def quest_index(quest_id: str) -> int:
    return next(i for i, quest in enumerate(QUESTS) if quest.id == quest_id)


def normalise_output(value: str) -> str:
    """Make learner output comparison forgiving about trailing whitespace."""
    return "\n".join(line.rstrip() for line in value.strip().splitlines())


def output_matches(quest: Quest, output: str) -> bool:
    return normalise_output(output) == normalise_output(quest.expected_output)
