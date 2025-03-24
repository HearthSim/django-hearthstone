from django.contrib import admin

from .models import Card


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
	list_display = (
		"__str__", "card_id", "description", "card_set", "rarity", "type",
		"card_class", "artist"
	)
	list_filter = (
		"collectible", "card_set",
		"card_class", "type", "rarity", "cost",
		"battlecry", "deathrattle", "inspire",
		"divine_shield", "taunt", "windfury",
		"overload", "spell_damage"
	)
	search_fields = (
		"name", "description", "card_id",
	)

	def has_add_permission(self, request):
		return False

	def has_change_permission(self, request, obj=None):
		return False

	def has_delete_permission(self, request, obj=None):
		return False
