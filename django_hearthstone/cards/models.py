from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django_intenum import IntEnumField
from hearthstone import cardxml, enums


DBF_DB = {}


class IncludibleCardManager(models.Manager):
	def get_queryset(self):
		return super().get_queryset().filter(
			models.Q(collectible=True),
			models.Q(type__in=[
				enums.CardType.MINION,
				enums.CardType.SPELL,
				enums.CardType.WEAPON,
				enums.CardType.LOCATION,
			]) | (
				models.Q(type=enums.CardType.HERO) &
				~models.Q(card_set__in=[enums.CardSet.CORE, enums.CardSet.HERO_SKINS])
			)
		)


class Card(models.Model):
	card_id = models.CharField(primary_key=True, max_length=50)
	dbf_id = models.IntegerField(null=True, unique=True, db_index=True)

	name = models.CharField(max_length=64)
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
	multi_class_group = IntEnumField(
		enum=enums.MultiClassGroup, default=enums.MultiClassGroup.INVALID,
	)

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

	objects = models.Manager()
	includibles = IncludibleCardManager()

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

	def localized_name(self, locale) -> str:
		try:
			return self.strings.get(locale=locale, game_tag=enums.GameTag.CARDNAME).value
		except CardString.DoesNotExist:
			return ""

	def update_from_cardxml(self, cardxml, save=False):
		for k in dir(cardxml):
			if k.startswith("_") or k in ("id", "tags", "strings"):
				continue
			# Transfer all existing CardXML attributes to our model
			if hasattr(self, k):
				setattr(self, k, getattr(cardxml, k))

		if save:
			self.save()

	@property
	def playable(self):
		"""Returns whether the card can be played."""
		if self.type in [
			enums.CardType.MINION,
			enums.CardType.SPELL,
			enums.CardType.WEAPON,
			enums.CardType.LOCATION,
		]:
			return True
		# Heroes can only be played if they are not the basic heroes or hero skins.
		if self.type == enums.CardType.HERO:
			return self.card_set not in [enums.CardSet.CORE, enums.CardSet.HERO_SKINS]
		return False

	@property
	def includible(self):
		return self.collectible and self.playable


class CardTag(models.Model):
	id = models.AutoField(primary_key=True, serialize=False, verbose_name="ID")
	card = models.ForeignKey(
		"Card", to_field="dbf_id", db_column="card_dbf_id", related_name="tags",
		on_delete=models.CASCADE
	)
	game_tag = IntEnumField(enum=enums.GameTag, db_index=True)
	value = models.PositiveIntegerField()

	def __str__(self):
		return f"{str(self.card)}.{self.game_tag.name}={str(self.value)}"


class CardString(models.Model):
	id = models.AutoField(primary_key=True, serialize=False, verbose_name="ID")
	card = models.ForeignKey(
		"Card", to_field="dbf_id", db_column="card_dbf_id", related_name="strings",
		on_delete=models.CASCADE
	)
	locale = IntEnumField(enum=enums.Locale, db_index=True)
	game_tag = IntEnumField(enum=enums.GameTag, db_index=True)
	value = models.TextField(blank=True)

	def __str__(self):
		return self.value
