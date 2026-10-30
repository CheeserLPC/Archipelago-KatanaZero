from test.bases import WorldTestBase


class TestKatanaZeroDefault(WorldTestBase):
    game = "Katana ZERO"

    def test_default_beatable(self) -> None:
        self.multiworld.state = self.multiworld.get_all_state()
        self.assertBeatable(True)


class TestKatanaZeroBossRush(WorldTestBase):
    game = "Katana ZERO"
    options = {
        "goal": 2,  # Boss Rush
    }

    def test_boss_rush_beatable(self) -> None:
        self.multiworld.state = self.multiworld.get_all_state()
        self.assertBeatable(True)


class TestKatanaZeroAllTapes(WorldTestBase):
    game = "Katana ZERO"
    options = {
        "goal": 1,  # All Tapes
    }

    def test_all_tapes_beatable(self) -> None:
        self.multiworld.state = self.multiworld.get_all_state()
        self.assertBeatable(True)


class TestKatanaZeroEnemysanity(WorldTestBase):
    game = "Katana ZERO"
    options = {
        "enemysanity": 1,
    }

    def test_enemysanity_beatable(self) -> None:
        self.multiworld.state = self.multiworld.get_all_state()
        self.assertBeatable(True)


class TestKatanaZeroVanillaAbilities(WorldTestBase):
    game = "Katana ZERO"
    options = {
        "shuffle_chronos": 0,
        "shuffle_throw": 0,
    }

    def test_vanilla_abilities_beatable(self) -> None:
        self.multiworld.state = self.multiworld.get_all_state()
        self.assertBeatable(True)


class TestKatanaZeroShuffledAbilities(WorldTestBase):
    game = "Katana ZERO"
    options = {
        "shuffle_chronos": 1,
        "shuffle_throw": 1,
    }

    def test_shuffled_abilities_beatable(self) -> None:
        self.multiworld.state = self.multiworld.get_all_state()
        self.assertBeatable(True)
