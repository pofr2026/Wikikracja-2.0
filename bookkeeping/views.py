import json

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView, View

from .forms import AssetForm, TransactionForm
from .models import Asset, Category, Partner, Transaction

# #########################  Asset ###########################


class AssetListView(LoginRequiredMixin, ListView):
    model = Asset
    template_name = 'bookkeeping/asset_list.html'


class AssetCreateView(LoginRequiredMixin, CreateView):
    model = Asset
    form_class = AssetForm
    template_name = 'bookkeeping/asset_form.html'
    success_url = reverse_lazy('bookkeeping:asset_list')


class AssetUpdateView(LoginRequiredMixin, UpdateView):
    model = Asset
    form_class = AssetForm
    template_name = 'bookkeeping/asset_form.html'
    success_url = reverse_lazy('bookkeeping:asset_list')


class AssetDeleteView(LoginRequiredMixin, DeleteView):
    model = Asset
    template_name = 'bookkeeping/asset_confirm_delete.html'
    success_url = reverse_lazy('bookkeeping:asset_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        related_transactions = Transaction.objects.filter(asset=self.object)

        context['related_transactions'] = related_transactions
        context['has_dependencies'] = related_transactions.exists()

        if 'delete_error' in self.request.session:
            context['error'] = self.request.session.pop('delete_error')

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if Transaction.objects.filter(asset=self.object).exists():
            request.session['delete_error'] = _(
                "Cannot delete asset because it is in use. Remove all transactions that use it first."
            )
            return redirect('bookkeeping:asset_delete', pk=self.object.pk)

        try:
            return super().delete(request, *args, **kwargs)
        except Exception as e:
            request.session['delete_error'] = str(e)
            return redirect('bookkeeping:asset_delete', pk=self.object.pk)


# #########################  Category ###########################


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'bookkeeping/category_list.html'


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    fields = '__all__'
    success_url = reverse_lazy('bookkeeping:category_list')


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    fields = '__all__'
    success_url = reverse_lazy('bookkeeping:category_list')


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    success_url = reverse_lazy('bookkeeping:category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        related_transactions = Transaction.objects.filter(category=self.object)
        context['related_transactions'] = related_transactions
        context['has_dependencies'] = related_transactions.exists()
        if 'delete_error' in self.request.session:
            context['error'] = self.request.session.pop('delete_error')

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if Transaction.objects.filter(category=self.object).exists():
            request.session['delete_error'] = _("Cannot delete category because it is in use. Remove all transactions that use it first.")
            return redirect('bookkeeping:category_delete', pk=self.object.pk)

        try:
            return super().delete(request, *args, **kwargs)
        except Exception as e:
            request.session['delete_error'] = str(e)
            return redirect('bookkeeping:category_delete', pk=self.object.pk)


# #########################  Partner ###########################


class PartnerListView(LoginRequiredMixin, ListView):
    model = Partner
    template_name = 'bookkeeping/partner_list.html'


class PartnerCreateView(LoginRequiredMixin, CreateView):
    model = Partner
    fields = '__all__'
    success_url = reverse_lazy('bookkeeping:partner_list')


class PartnerUpdateView(LoginRequiredMixin, UpdateView):
    model = Partner
    fields = '__all__'
    success_url = reverse_lazy('bookkeeping:partner_list')


class PartnerDeleteView(LoginRequiredMixin, DeleteView):
    model = Partner
    success_url = reverse_lazy('bookkeeping:partner_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        related_transactions = Transaction.objects.filter(partner=self.object)
        context['related_transactions'] = related_transactions
        context['has_dependencies'] = related_transactions.exists()
        if 'delete_error' in self.request.session:
            context['error'] = self.request.session.pop('delete_error')

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if Transaction.objects.filter(partner=self.object).exists():
            request.session['delete_error'] = _("Cannot delete partner because it is in use. Remove all transactions that use it first.")
            return redirect('bookkeeping:partner_delete', pk=self.object.pk)

        try:
            return super().delete(request, *args, **kwargs)
        except Exception as e:
            request.session['delete_error'] = str(e)
            return redirect('bookkeeping:partner_delete', pk=self.object.pk)


# #########################  Transaction ###########################


class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'bookkeeping/transaction_list.html'
    context_object_name = 'transactions'

    def get_queryset(self):
        return (
            Transaction.objects
            .select_related('partner', 'category', 'asset')
            .order_by('-payment_received_date', '-id')
        )


def _asset_decimal_places_json():
    return json.dumps({str(a.pk): a.decimal_places for a in Asset.objects.all()})


class TransactionCreateView(LoginRequiredMixin, View):
    template_name = 'bookkeeping/transaction_form.html'

    def get(self, request):
        transaction_form = TransactionForm()
        return render(request, self.template_name, {
            'transaction_form': transaction_form,
            'asset_decimal_places_json': _asset_decimal_places_json(),
        })

    def post(self, request):
        transaction_form = TransactionForm(request.POST)

        if transaction_form.is_valid():
            transaction_data = transaction_form.cleaned_data

            transaction = Transaction(type=transaction_data['type'], asset=transaction_data['asset'], partner=transaction_data['partner'], category=transaction_data['category'], amount=transaction_data['amount'], payment_received_date=transaction_data['payment_received_date'], note=transaction_data['note'], author=request.user)
            transaction.created_date = timezone.now()
            transaction.save()

            return redirect('bookkeeping:transaction_list')

        return render(request, self.template_name, {
            'transaction_form': transaction_form,
            'asset_decimal_places_json': _asset_decimal_places_json(),
        })


class TransactionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'bookkeeping/transaction_form.html'

    def test_func(self):
        transaction = self.get_object()
        return self.request.user == transaction.author

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('bookkeeping:transaction_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'form' in context:
            context['transaction_form'] = context['form']
        context['asset_decimal_places_json'] = _asset_decimal_places_json()
        return context


class TransactionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Transaction
    template_name = 'bookkeeping/transaction_confirm_delete.html'
    success_url = reverse_lazy('bookkeeping:transaction_list')

    def test_func(self):
        transaction = self.get_object()
        return self.request.user == transaction.author


# #########################  Report ###########################


class ReportView(LoginRequiredMixin, View):
    template_name = 'bookkeeping/report_list.html'

    def _flat_rows(self, year=None):
        """
        Returns:
          rows   - list of {'category_name', 'net', 'symbol'} sorted by category name
          totals - list of {'asset', 'net'} one per asset that has any transactions
        """
        qs = Transaction.objects.all()
        if year:
            qs = qs.filter(payment_received_date__year=year)

        agg = (
            qs.values('category', 'asset', 'type')
            .annotate(total=Sum('amount'))
        )

        # net[(category_id, asset_id)] = net_value
        net = {}
        for row in agg:
            key = (row['category'], row['asset'])
            sign = 1 if row['type'] == Transaction.INCOMING else -1
            net[key] = net.get(key, 0) + sign * (row['total'] or 0)

        # Resolve category names
        cat_ids = {k[0] for k in net} - {None}
        cat_map = {c.id: c.name for c in Category.objects.filter(id__in=cat_ids)}

        # Resolve asset objects
        asset_ids = {k[1] for k in net}
        asset_map = {a.id: a for a in Asset.objects.filter(id__in=asset_ids)}

        # Build flat rows
        rows = []
        for (cat_id, asset_id), value in net.items():
            if value == 0:
                continue
            cat_name = cat_map.get(cat_id, '—') if cat_id is not None else '—'
            asset = asset_map.get(asset_id)
            rows.append({
                'category_name': cat_name,
                'net': value,
                'symbol': asset.symbol if asset else '',
                'asset_id': asset_id,
            })

        rows.sort(key=lambda r: (r['category_name'], r['asset_id'] or 0))

        # Totals per asset
        asset_totals = {}
        for r in rows:
            asset_totals[r['asset_id']] = asset_totals.get(r['asset_id'], 0) + r['net']

        totals = [
            {'asset': asset_map[aid], 'net': val}
            for aid, val in asset_totals.items()
            if aid in asset_map
        ]
        totals.sort(key=lambda t: t['asset'].code)

        return rows, totals

    def get(self, request, year=None):
        try:
            year = int(request.GET.get('year', year)) if year or request.GET.get('year') else timezone.now().year
        except (ValueError, TypeError):
            year = timezone.now().year

        year_rows, year_totals = self._flat_rows(year)
        all_rows, all_totals = self._flat_rows()

        available_years = (
            Transaction.objects.dates('payment_received_date', 'year')
            .values_list('payment_received_date__year', flat=True)
            .distinct()
            .order_by('-payment_received_date__year')
        )

        context = {
            'year_rows': year_rows,
            'year_totals': year_totals,
            'all_rows': all_rows,
            'all_totals': all_totals,
            'year': year,
            'available_years': available_years,
        }

        return render(request, self.template_name, context)
