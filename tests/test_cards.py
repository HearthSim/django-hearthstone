import pytest
from django.core.management import call_command

from django_hearthstone.cards.models import Card


@pytest.mark.django_db
def test_load_cards():
	call_command("load_cards")
	assert Card.objects.count() > 3500
