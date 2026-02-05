from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from inventory.models import Item, ItemImage


class ItemModelTests(TestCase):
    def test_item_and_image_relationship(self):
        User = get_user_model()
        user = User.objects.create_user(username="staff", password="pw")

        item = Item.objects.create(
            title="Black Umbrella",
            description="Compact black umbrella left in lobby.",
            location_found="Lobby",
            date_found=date.today(),
            created_by=user,
        )

        image = ItemImage.objects.create(item=item, image="item_images/test.jpg")

        self.assertEqual(str(item), "Black Umbrella")
        self.assertEqual(str(image), f"Image for {item.id}")
        self.assertEqual(item.images.count(), 1)
        self.assertEqual(item.images.first(), image)



