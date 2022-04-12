from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from hearthstone import cardxml
from hearthstone.enums import Locale

from ...models import Card, CardString, CardTag


class Command(BaseCommand):
	def add_arguments(self, parser):
		parser.add_argument("path", nargs="?", help="CardDefs.xml file")
		parser.add_argument("--locale", default="enUS")
		parser.add_argument("--force", action="store_true", help="Force update all cards")
		parser.add_argument(
			"--ignore-conflicts", action="store_true",
			help="Ignore conflicts due to existing cards"
		)

	def handle(self, *args, **options):
		path = options["path"]
		db, _ = cardxml.load_dbf(path, locale=options["locale"])
		self.stdout.write("%i cards available" % (len(db)))

		qs = Card.objects.all().values_list("dbf_id")
		known_ids = [item[0] for item in qs]
		missing = [id for id in db if id not in known_ids]
		self.stdout.write("%i known cards" % (len(known_ids)))

		new_cards = [Card.from_cardxml(db[id]) for id in missing]
		Card.objects.bulk_create(new_cards)
		self.stdout.write("%i new cards" % (len(new_cards)))

		if options["force"]:
			existing = Card.objects.filter(dbf_id__in=known_ids)
			for card in existing:
				if card.dbf_id not in db:
					self.stderr.write(
						f"WARNING: {repr(card)} ({card.dbf_id}) not in CardDefs.xml. "
						"Skipping."
					)
					continue
				c = db[card.dbf_id]
				if c:
					try:
						card.update_from_cardxml(c, save=True)
					except IntegrityError as e:
						if options["ignore_conflicts"]:
							self.stderr.write(
								f"WARNING: Ignoring {repr(card)} ({card.dbf_id}) conflict:"
								f"{e}"
							)
						else:
							raise e
			self.stdout.write("%i updated cards" % (len(existing)))

		tags = []
		for dbf_id, card in db.items():
			for tag, value in card.tags.items():
				tags.append(CardTag(card_id=dbf_id, game_tag=tag, value=value))

		locstrings = []
		for dbf_id, card in db.items():
			for tag, locstring in card.strings.items():
				if isinstance(locstring, str):
					# (non-localized string)
					continue
				for locale, value in locstring.items():
					locale = Locale[locale]
					locstrings.append(CardString(
						card_id=dbf_id, locale=locale, game_tag=tag, value=value
					))

		with transaction.atomic():
			CardTag.objects.all().delete()
			CardString.objects.all().delete()

			CardTag.objects.bulk_create(tags)
			CardString.objects.bulk_create(locstrings)
