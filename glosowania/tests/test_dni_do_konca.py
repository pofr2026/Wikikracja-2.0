from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from glosowania.models import Decyzja


class DniDoKoncaReferendumTest(TestCase):
    def _decyzja(self, stop):
        # autor nieistotny dla tej logiki — zostawiamy None
        return Decyzja.objects.create(
            author=None, title="t", tresc="x", status=3,
            data_referendum_stop=stop,
        )

    def test_brak_daty_zwraca_none(self):
        d = self._decyzja(stop=None)
        self.assertIsNone(d.dni_do_konca_referendum)

    def test_data_w_przyszlosci_zwraca_liczbe_dni(self):
        d = self._decyzja(stop=timezone.localdate() + timedelta(days=4))
        self.assertEqual(d.dni_do_konca_referendum, 4)

    def test_data_dzis_zwraca_zero(self):
        d = self._decyzja(stop=timezone.localdate())
        self.assertEqual(d.dni_do_konca_referendum, 0)

    def test_data_w_przeszlosci_zwraca_wartosc_ujemna(self):
        d = self._decyzja(stop=timezone.localdate() - timedelta(days=2))
        self.assertEqual(d.dni_do_konca_referendum, -2)
