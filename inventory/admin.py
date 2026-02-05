from django.contrib import admin

from .models import Item, ItemImage


class ItemImageInline(admin.TabularInline):
    model = ItemImage
    extra = 1


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "location_found", "date_found", "created_by", "created_at")
    list_filter = ("status", "location_found", "date_found", "created_at")
    search_fields = ("title", "description", "location_found")
    inlines = [ItemImageInline]


@admin.register(ItemImage)
class ItemImageAdmin(admin.ModelAdmin):
    list_display = ("item", "created_at")


