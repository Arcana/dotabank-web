import os
import sys
sys.path.append(os.path.join(os.getcwd(), '..'))

from test_base import DotabankTestCase
import unittest
from app.dota.models import Hero, Item, Schema
from flask import url_for
from app import steam

class HeroTestCase(DotabankTestCase):
    """ Testing dota/models/Hero """

    CRYSTAL_MAIDEN = {
        'id': 5,
        'name': 'npc_dota_hero_crystal_maiden',
        'localized_name': 'Crystal Maiden',
        'image_name': 'crystal_maiden'
    }

    def test_get_all(self):
        """ Test we get a populated list of heroes """
        heroes = Hero.get_all()

        self.assertIsInstance(heroes, list)
        self.assertGreaterEqual(len(heroes), 107)  # 107 at time of test writing.  This will fail if the WebAPI is down.

    def test_get_by_id(self):
        """ Test we can get a hero by their ID """
        crystal_maiden = Hero.get_by_id(self.CRYSTAL_MAIDEN['id'])

        self.assertIsNotNone(crystal_maiden)
        self.assertEqual(crystal_maiden.id, self.CRYSTAL_MAIDEN['id'])
        self.assertEqual(crystal_maiden.name, self.CRYSTAL_MAIDEN['name'])
        self.assertEqual(crystal_maiden.localized_name, self.CRYSTAL_MAIDEN['localized_name'])
        self.assertEqual(crystal_maiden.image, url_for('hero_image', hero_name=self.CRYSTAL_MAIDEN['image_name']))

    def test_get_by_name(self):
        """ Test we can get a hero by their name """
        crystal_maiden = Hero.get_by_name(self.CRYSTAL_MAIDEN['name'])

        self.assertIsNotNone(crystal_maiden)
        self.assertEqual(crystal_maiden.id, self.CRYSTAL_MAIDEN['id'])
        self.assertEqual(crystal_maiden.name, self.CRYSTAL_MAIDEN['name'])
        self.assertEqual(crystal_maiden.localized_name, self.CRYSTAL_MAIDEN['localized_name'])
        self.assertEqual(crystal_maiden.image, url_for('hero_image', hero_name=self.CRYSTAL_MAIDEN['image_name']))


class ItemTestCase(DotabankTestCase):
    """ Testing dota/models/Item """

    # Only checking meta-data
    BLINK_DAGGER = {
        'id': 1,
        'name': 'blink',
        'localized_name': 'Blink Dagger',
        'image_filename': 'blink_lg.png'
    }

    def test_get_all(self):
        """ Test we get a populated list of items """
        items = Item.get_all()

        self.assertIsInstance(items, list)
        self.assertGreaterEqual(len(items), 159)  # 159 at time of test writing.  This will fail if the data endpoint is down.

    def test_get_by_id(self):
        """ Test we can get an item by its ID """
        blink_dagger = Item.get_by_id(self.BLINK_DAGGER['id'])

        self.assertIsNotNone(blink_dagger)
        self.assertEqual(blink_dagger.id, self.BLINK_DAGGER['id'])
        self.assertEqual(blink_dagger.name, self.BLINK_DAGGER['name'])
        self.assertEqual(blink_dagger.localized_name, self.BLINK_DAGGER['localized_name'])
        self.assertEqual(blink_dagger.image_filename, self.BLINK_DAGGER['image_filename'])
        self.assertEqual(blink_dagger.icon, url_for('item_icon', item_filename=self.BLINK_DAGGER['image_filename']))

    def test_get_by_name(self):
        """ Test we can get an item by its name """
        blink_dagger = Item.get_by_name(self.BLINK_DAGGER['name'])

        self.assertIsNotNone(blink_dagger)
        self.assertEqual(blink_dagger.id, self.BLINK_DAGGER['id'])
        self.assertEqual(blink_dagger.name, self.BLINK_DAGGER['name'])
        self.assertEqual(blink_dagger.localized_name, self.BLINK_DAGGER['localized_name'])
        self.assertEqual(blink_dagger.image_filename, self.BLINK_DAGGER['image_filename'])
        self.assertEqual(blink_dagger.icon, url_for('item_icon', item_filename=self.BLINK_DAGGER['image_filename']))


class SchemaTestCase(DotabankTestCase):

    DRODO = {
        'defindex': 10003,
        'name': 'Drodo the Druffin'
    }

    def test_get_schema(self):
        """ Test we get a Steamodd Schema object """
        schema = Schema.get_schema()

        self.assertIsInstance(schema, steam.items.schema)
        self.assertGreaterEqual(len(schema), 5033)  # 5033 at time of test writing.  This will fail if the WebAPI is down.

    def test_get_by_id(self):
        drodo = Schema.get_by_id(self.DRODO['defindex'])

        self.assertIsInstance(drodo, steam.items.item)
        self.assertEqual(drodo.schema_id, self.DRODO['defindex'])
        self.assertEqual(drodo.name, self.DRODO['name'])

if __name__ == '__main__':
    unittest.main()
