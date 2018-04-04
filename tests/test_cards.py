import pytest
from django.core.management import call_command
from hearthstone.cardxml import load_dbf
from hearthstone.enums import Locale

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
