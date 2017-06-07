from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django_intenum import IntEnumField
from hearthstone import cardxml, enums


DBF_DB = {}


class Card(models.Model):
	card_id = models.CharField(primary_key=True, max_length=50)
	dbf_id = models.IntegerField(null=True, unique=True, db_index=True)

	name = models.CharField(max_length=50)
	description = models.TextField(blank=True)
	flavortext = models.TextField(blank=True)
	how_to_earn = models.TextField(blank=True)
	how_to_earn_golden = models.TextField(blank=True)
	artist = models.CharField(max_length=255, blank=True)

	card_class = IntEnumField(enum=enums.CardClass, default=enums.CardClass.INVALID)
	card_set = IntEnumField(enum=enums.CardSet, default=enums.CardSet.INVALID)
	faction = IntEnumField(enum=enums.Faction, default=enums.Faction.INVALID)
	race = IntEnumField(enum=enums.Race, default=enums.Race.INVALID)
	rarity = IntEnumField(enum=enums.Rarity, default=enums.Rarity.INVALID)
	type = IntEnumField(enum=enums.CardType, default=enums.CardType.INVALID)

	collectible = models.BooleanField(default=False)
	battlecry = models.BooleanField(default=False)
	divine_shield = models.BooleanField(default=False)
	deathrattle = models.BooleanField(default=False)
	elite = models.BooleanField(default=False)
	evil_glow = models.BooleanField(default=False)
	inspire = models.BooleanField(default=False)
	forgetful = models.BooleanField(default=False)
	one_turn_effect = models.BooleanField(default=False)
	poisonous = models.BooleanField(default=False)
	ritual = models.BooleanField(default=False)
	secret = models.BooleanField(default=False)
	taunt = models.BooleanField(default=False)
	topdeck = models.BooleanField(default=False)

	atk = models.IntegerField(default=0)
	health = models.IntegerField(default=0)
	durability = models.IntegerField(default=0)
	cost = models.IntegerField(default=0)
	windfury = models.IntegerField(default=0)

	spare_part = models.BooleanField(default=False)
	overload = models.IntegerField(default=0)
	spell_damage = models.IntegerField(default=0)

	craftable = models.BooleanField(default=False)

	class Meta:
		db_table = "card"

	@property
	def id(self):
		return self.card_id

	@classmethod
	def from_cardxml(cls, card, save=False):
		obj = cls(card_id=card.id)
		obj.update_from_cardxml(card, save=save)
		return obj

	@classmethod
	def get_string_id(cls, dbf_id):
		if not DBF_DB:
			db, _ = cardxml.load_dbf()
			DBF_DB.update(db)
		return DBF_DB[dbf_id].id

	def __str__(self):
		return self.name

	@property
	def slug(self):
		return slugify(self.name)

	def get_absolute_url(self):
		# XXX
		return reverse("card_detail", kwargs={"pk": self.dbf_id, "slug": self.slug})

	def get_card_art_url(self, resolution=256, format="jpg"):
		return "https://art.hearthstonejson.com/v1/%ix/%s.%s" % (resolution, self.id, format)

	def get_card_render_url(self, resolution=256, format="png", locale="enUS", build="latest"):
		return "https://art.hearthstonejson.com/v1/render/%s/%s/%ix/%s.%s" % (
			build, locale, resolution, self.id, format
		)

	def get_tile_url(self, format="png"):
		return "https://art.hearthstonejson.com/v1/tiles/%s.%s" % (self.id, format)

	def update_from_cardxml(self, cardxml, save=False):
		for k in dir(cardxml):
			if k.startswith("_") or k == "id":
				continue
			# Transfer all existing CardXML attributes to our model
			if hasattr(self, k):
				setattr(self, k, getattr(cardxml, k))

		if save:
			self.save()
