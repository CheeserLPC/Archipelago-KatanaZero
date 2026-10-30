from test.bases import WorldTestBase


class TestKatanaZeroDefault(WorldTestBase):
    game = "Katana ZERO"

    def test_default_beatable(self) -> None:
        self.assertBeatable(True)


class TestKatanaZeroBossRush(WorldTestBase):
    game = "Katana ZERO"
    options = {
        "goal": 2,  # Boss Rush
    }

    def test_boss_rush_beatable(self) -> None:
        self.assertBeatable(True)


class TestKatanaZeroAllTapes(WorldTestBase):
    game = "Katana ZERO"
    options = {
        "goal": 1,  # All Tapes
    }

    def test_all_tapes_beatable(self) -> None:
        self.assertBeatable(True)


class TestKatanaZeroEnemysanity(WorldTestBase):
    game = "Katana ZERO"
    options = {
        "enemysanity": 1,
    }

    def test_enemysanity_beatable(self) -> None:
        self.assertBeatable(True)
