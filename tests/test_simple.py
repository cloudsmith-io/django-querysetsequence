import unittest

from django.db.models import QuerySet
from django.test import TestCase

from queryset_sequence import QuerySetSequence

from .models import Article, Author, Book

class TestQuerySetSequence(TestCase):
    @classmethod
    def setUpClass(cls):
        """Set-up some data to be tested against."""
        alice = Author.objects.create(name="Alice")
        bob = Author.objects.create(name="Bob")

        # Alice wrote some articles.
        Article.objects.create(title="Django Rocks", author=alice)
        Article.objects.create(title="Alice in Django-land", author=alice)

        # Bob wrote a couple of books and an article.
        Book.objects.create(title="Fiction", author=bob)
        Book.objects.create(title="Biography", author=bob)
        Article.objects.create(title="Some Article", author=bob)

        # Save the authors for later.
        cls.alice = alice
        cls.bob = bob

    @classmethod
    def tearDownClass(cls):
        del cls.alice
        del cls.bob

        # Clear the database.
        Author.objects.all().delete()
        Article.objects.all().delete()
        Book.objects.all().delete()

    def test_length(self):
        """
        Ensure that count() and len() are properly summed over the children
        QuerySets.
        """
        qss = QuerySetSequence(Book.objects.filter(author=self.bob),
                               Article.objects.filter(author=self.bob))

        # The proper length should be returned via database queries.
        self.assertEqual(qss.count(), 3)
        self.assertIsNone(qss._result_cache)

        # Calling len() evaluates the QuerySet.
        self.assertEqual(len(qss), 3)
        self.assertIsNotNone(qss._result_cache)

        # Count should still work (and not hit the database).
        qss.query = None
        self.assertEqual(qss.count(), 3)

    def test_filter(self):
        """
        Ensure that filter() properly filters the children QuerySets, note that
        no QuerySets are actually evaluated during this.
        """
        qss = QuerySetSequence(Book.objects.all(), Article.objects.all())

        # Check that everything is in the current list.
        self.assertEqual(qss.count(), 5)

        # Now filter to just Bob's work.
        bob_qss = qss.filter(author=self.bob)
        self.assertEqual(bob_qss.count(), 3)
        self.assertIsNone(qss._result_cache)

        # Now filter to just Alice's work.
        alice_qss = qss.filter(author=self.alice)
        self.assertEqual(alice_qss.count(), 2)
        self.assertIsNone(qss._result_cache)
        # Since we've now filtered down to a single QuerySet, we shouldn't be a
        # QuerySetSequence any longer.
        self.assertIsInstance(alice_qss, QuerySet)

    def test_exclude(self):
        """
        Ensure that exclude() properly excludes the children QuerySets, note
        that no QuerySets are actually evaluated during this.

        Note that this is the same test as test_filter, but we exclude the other
        author instead of filtering.
        """
        qss = QuerySetSequence(Book.objects.all(), Article.objects.all())

        # Check that everything is in the current list.
        self.assertEqual(qss.count(), 5)

        # Now filter to just Bob's work.
        bob_qss = qss.exclude(author=self.alice)
        self.assertEqual(bob_qss.count(), 3)
        self.assertIsNone(qss._result_cache)

        # Now filter to just Alice's work.
        alice_qss = qss.exclude(author=self.bob)
        self.assertEqual(alice_qss.count(), 2)
        self.assertIsNone(qss._result_cache)
        # Since we've now filtered down to a single QuerySet, we shouldn't be a
        # QuerySetSequence any longer.
        self.assertIsInstance(alice_qss, QuerySet)

    def test_order_by(self):
        """Ensure that order_by() propagates to QuerySets and iteration."""
        qss = QuerySetSequence(Book.objects.all(), Article.objects.all())

        # Check that everything is in the current list.
        self.assertEqual(qss.count(), 5)

        # Order by author and ensure it takes.
        qss = qss.order_by('title')
        self.assertEqual(qss.query.order_by, ['title'])

        # Check the titles are properly ordered.
        data = map(lambda it: it.title, qss)
        self.assertEqual(data[0], 'Alice in Django-land')
        self.assertEqual(data[1], 'Biography')
        self.assertEqual(data[2], 'Django Rocks')
        self.assertEqual(data[3], 'Fiction')
        self.assertEqual(data[4], 'Some Article')

    @unittest.skip('Currently not supported.')
    def test_order_by_model(self):
        """Apply order_by() with a field that returns a model."""
        qss = QuerySetSequence(Book.objects.all(), Article.objects.all())

        # Check that everything is in the current list.
        self.assertEqual(qss.count(), 5)

        # Order by author and ensure it takes.
        qss = qss.order_by('author')
        self.assertEqual(qss.query.order_by, ['author'])

        # The first two should be Alice, followed by three from Bob.
        for expected, element in zip([self.alice] * 2 + [self.bob] * 3, list(qss)):
            self.assertEqual(expected, element.author)

    def test_slicing(self):
        pass

    def test_iterating(self):
        pass
