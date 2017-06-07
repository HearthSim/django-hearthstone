from django.core.management.base import BaseCommand
from hearthstone import cardxml
from ...models import Card


class Command(BaseCommand):
	def add_arguments(self, parser):
		parser.add_argument("path", nargs="?", help="CardDefs.xml file")
		parser.add_argument("--locale", default="enUS")
		parser.add_argument("--force", action="store_true", help="Force update all cards")

	def handle(self, *args, **options):
		path = options["path"]
		db, _ = cardxml.load(path, locale=options["locale"])
		self.stdout.write("%i cards available" % (len(db)))

		qs = Card.objects.all().values_list("card_id")
		known_ids = [item[0] for item in qs]
		missing = [id for id in db if id not in known_ids]
		self.stdout.write("%i known cards" % (len(known_ids)))

		new_cards = [Card.from_cardxml(db[id]) for id in missing]
		Card.objects.bulk_create(new_cards)
		self.stdout.write("%i new cards" % (len(new_cards)))

		if options["force"]:
			existing = Card.objects.filter(id__in=known_ids)
			for card in existing:
				if card.card_id not in db:
					self.stderr.write(
						"WARNING: %r (%s) not in CardDefs.xml. Skipping." % (card, card.card_id)
					)
					continue
				c = db[card.card_id]
				if c:
					card.update_from_cardxml(c, save=True)
			self.stdout.write("%i updated cards" % (len(existing)))
