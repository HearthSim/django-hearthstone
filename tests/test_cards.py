import pytest
from django.core.management import call_command
from hearthstone.cardxml import load_dbf
from hearthstone.enums import CardClass, Locale

from django_hearthstone.cards.models import Card


db, _ = load_dbf()


@pytest.mark.django_db
def test_load_cards():
	call_command("load_cards")
	assert Card.objects.count() > 3500

	wisp = Card.objects.get(dbf_id=179)
	assert wisp.dbf_id == 179
	assert wisp.card_id == "CS2_231"
	assert wisp.name == "Wisp"

	assert wisp.localized_name(Locale.enUS) == "Wisp"
	assert wisp.localized_name(Locale.frFR) == "Feu follet"

	assert {o.game_tag: o.value for o in wisp.tags.all()} == db[179].tags
	assert wisp.strings.all().count() >= 28
	assert not wisp.fabled
	assert not wisp.is_fabled_bundle_card

	alleria = Card.objects.get(dbf_id=119705)
	assert alleria.dbf_id == 119705
	assert alleria.card_id == "TIME_609t1"
	assert alleria.name == "Ranger Captain Alleria"
	assert not alleria.fabled
	assert alleria.is_fabled_bundle_card

	sylvanas = Card.objects.get(dbf_id=119707)
	assert sylvanas.dbf_id == 119707
	assert sylvanas.card_id == "TIME_609"
	assert sylvanas.name == "Ranger General Sylvanas"
	assert sylvanas.fabled
	assert not sylvanas.is_fabled_bundle_card


class TestCard:
	@pytest.mark.django_db
	def test_classes(self):
		assert Card.objects.create(
			dbf_id=179, card_id="CS2_231", name="Wisp", card_class=CardClass.NEUTRAL
		).classes == [CardClass.NEUTRAL]

		# Gadgetzan
		assert Card.objects.create(
			dbf_id=40408, card_id="CFM_621", name="Kazakus", card_class=CardClass.NEUTRAL,
			multiple_classes=296,
		).classes == [CardClass.MAGE, CardClass.PRIEST, CardClass.WARLOCK]

		# Scholomance
		assert Card.objects.create(
			dbf_id=59726, card_id="SCH_702", name="Felosophy", card_class=CardClass.WARLOCK,
			multiple_classes=8448,
		).classes == [CardClass.WARLOCK, CardClass.DEMONHUNTER]

		# Audiopocalypse
		assert Card.objects.create(
			dbf_id=98377, card_id="JAM_022", name="Deafen", card_class=CardClass.PRIEST,
			multiple_classes=96,
		).classes == [CardClass.PRIEST, CardClass.ROGUE]
