import os
import sys
sys.path.append(os.path.join(os.getcwd(), '..'))

from test_base import DotabankTestCase
import unittest
from app.dota.models import Hero, Item, Schema, Localization
from flask import url_for, g
from app import steam


class DotaTestCase(DotabankTestCase):
    def setUp(self):
        super(DotaTestCase, self).setUp()
        with self.ctx:
            g.localization = Localization('english')


class HeroTestCase(DotaTestCase):
    """ Testing dota/models/Hero """

    CRYSTAL_MAIDEN = {
        'id': 5,
        'token': 'npc_dota_hero_crystal_maiden',
        'name': 'crystal_maiden',
        'localized_name': 'Crystal Maiden',
        'image_name': 'crystal_maiden'
    }

    def test_get_all(self):
        """ Test we get a populated list of heroes """
        heroes = Hero.query.all()  # TODO: Refactorinate

        self.assertIsInstance(heroes, list)
        self.assertGreaterEqual(len(heroes), 107)  # 107 at time of test writing.

    def test_get_by_id(self):
        """ Test we can get a hero by their ID """
        crystal_maiden = Hero.query.filter(Hero.id == self.CRYSTAL_MAIDEN['id']).one()

        self.assertIsNotNone(crystal_maiden)
        self.assertEqual(crystal_maiden.id, self.CRYSTAL_MAIDEN['id'])
        self.assertEqual(crystal_maiden.token, self.CRYSTAL_MAIDEN['token'])
        self.assertEqual(crystal_maiden.name, self.CRYSTAL_MAIDEN['name'])
        self.assertEqual(crystal_maiden.localized_name, self.CRYSTAL_MAIDEN['localized_name'])
        self.assertEqual(crystal_maiden.image, url_for('hero_image', hero_name=self.CRYSTAL_MAIDEN['image_name']))

    def test_get_by_token(self):
        """ Test we can get a hero by their token """
        crystal_maiden = Hero.query.filter(Hero.token == self.CRYSTAL_MAIDEN['token']).one()

        self.assertIsNotNone(crystal_maiden)
        self.assertEqual(crystal_maiden.id, self.CRYSTAL_MAIDEN['id'])
        self.assertEqual(crystal_maiden.token, self.CRYSTAL_MAIDEN['token'])
        self.assertEqual(crystal_maiden.name, self.CRYSTAL_MAIDEN['name'])
        self.assertEqual(crystal_maiden.localized_name, self.CRYSTAL_MAIDEN['localized_name'])
        self.assertEqual(crystal_maiden.image, url_for('hero_image', hero_name=self.CRYSTAL_MAIDEN['image_name']))

    def test_get_by_name(self):
        """ Test we can get a hero by their token """
        crystal_maiden = Hero.query.filter(Hero.name == self.CRYSTAL_MAIDEN['name']).one()

        self.assertIsNotNone(crystal_maiden)
        self.assertEqual(crystal_maiden.id, self.CRYSTAL_MAIDEN['id'])
        self.assertEqual(crystal_maiden.token, self.CRYSTAL_MAIDEN['token'])
        self.assertEqual(crystal_maiden.name, self.CRYSTAL_MAIDEN['name'])
        self.assertEqual(crystal_maiden.localized_name, self.CRYSTAL_MAIDEN['localized_name'])
        self.assertEqual(crystal_maiden.image, url_for('hero_image', hero_name=self.CRYSTAL_MAIDEN['image_name']))


class ItemTestCase(DotaTestCase):
    """ Testing dota/models/Item """

    # Only checking meta-data
    BLINK_DAGGER = {
        'id': 1,
        'token': 'item_blink',
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
        self.assertEqual(blink_dagger.token, self.BLINK_DAGGER['token'])
        self.assertEqual(blink_dagger.localized_name, self.BLINK_DAGGER['localized_name'])
        self.assertEqual(blink_dagger.icon, url_for('item_icon', item_filename=self.BLINK_DAGGER['image_filename']))

    def test_get_by_token(self):
        """ Test we can get an item by its name """
        blink_dagger = Item.get_by_token(self.BLINK_DAGGER['token'])

        self.assertIsNotNone(blink_dagger)
        self.assertEqual(blink_dagger.id, self.BLINK_DAGGER['id'])
        self.assertEqual(blink_dagger.token, self.BLINK_DAGGER['token'])
        self.assertEqual(blink_dagger.localized_name, self.BLINK_DAGGER['localized_name'])
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
