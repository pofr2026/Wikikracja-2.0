"""Testy modeli aplikacji bookkeeping."""
from django.contrib.auth import get_user_model
from django.test import TestCase

from bookkeeping.models import Category, Partner, Transaction

User = get_user_model()


class TransactionModelTest(TestCase):
    """Pokrycie relacji i pól modelu Transaction."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='trans_author', email='ta@example.com', password='x')
        cls.category = Category.objects.create(name='Test Cat')
        cls.partner = Partner.objects.create(name='Test Partner', email='p@example.com', phone='+48123456789', city='Warsaw', country='Poland')

    def test_transaction_create_with_all_relations(self):
        """Transaction trzyma wszystkie relacje (category, partner, author) i poprawnie zwraca pola."""
        txn = Transaction.objects.create(type='I', category=self.category, partner=self.partner, amount=1500.50, note='Workflow test', author=self.user)

        self.assertTrue(Transaction.objects.filter(note='Workflow test').exists())
        self.assertEqual(txn.category, self.category)
        self.assertEqual(txn.partner, self.partner)
        self.assertEqual(txn.author, self.user)
        self.assertEqual(float(txn.amount), 1500.50)
        self.assertEqual(txn.type, 'I')

    def test_transaction_type_choices_contain_income_and_outgoing(self):
        """Pole type ma zdefiniowane choices 'I' (income) i 'O' (outgoing)."""
        choices = [c[0] for c in Transaction._meta.get_field('type').choices]
        self.assertIn('I', choices)
        self.assertIn('O', choices)
