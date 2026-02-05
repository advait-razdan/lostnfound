from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, ListView

from .forms import ItemForm, ItemImageFormSet
from .models import Item
from .services import analyze_item_images


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.is_staff


class ItemUploadView(LoginRequiredMixin, StaffRequiredMixin, View):
    template_name = "inventory/item_upload.html"

    def get(self, request):
        item_form = ItemForm()
        formset = ItemImageFormSet()
        return render(
            request,
            self.template_name,
            {
                "item_form": item_form,
                "formset": formset,
            },
        )

    def post(self, request):
        item_form = ItemForm(request.POST)
        formset = ItemImageFormSet(request.POST, request.FILES)

        # Debug: Log form errors if any
        if not item_form.is_valid():
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Item form errors: {item_form.errors}")
        
        if not formset.is_valid():
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Formset errors: {formset.errors}, non_form_errors: {formset.non_form_errors}")

        if not (item_form.is_valid() and formset.is_valid()):
            return render(
                request,
                self.template_name,
                {
                    "item_form": item_form,
                    "formset": formset,
                },
            )

        item = item_form.save(commit=False)
        item.created_by = request.user
        item.save()
        
        # Only save formset if there are images
        formset.instance = item
        if formset.has_changed():
            formset.save()

        messages.success(
            request,
            f'Item "{item.title}" has been successfully uploaded!',
        )
        return redirect(reverse("inventory:item_list"))


@require_http_methods(["POST"])
@csrf_exempt
def analyze_images_ajax(request):
    """AJAX endpoint to analyze images and return title/description suggestions."""
    if not (request.user.is_authenticated and request.user.is_staff):
        return JsonResponse({"error": "Unauthorized"}, status=403)
    
    uploaded_images = []
    for key in request.FILES:
        if key.startswith("image_"):
            uploaded_images.append(request.FILES[key])
    
    if not uploaded_images:
        return JsonResponse({"title": "", "description": ""})
    
    suggestions = analyze_item_images(uploaded_images)
    return JsonResponse(suggestions)


class ItemUploadConfirmView(LoginRequiredMixin, StaffRequiredMixin, View):
    template_name = "inventory/item_upload_confirm.html"

    def post(self, request):
        # Finalize save based on posted data
        item_form = ItemForm(request.POST)
        formset = ItemImageFormSet(request.POST, request.FILES)

        if not (item_form.is_valid() and formset.is_valid()):
            return render(
                request,
                self.template_name,
                {
                    "item_form": item_form,
                    "formset": formset,
                    "step": "confirm",
                },
            )

        item = item_form.save(commit=False)
        item.created_by = request.user
        item.save()
        formset.instance = item
        formset.save()

        messages.success(
            request,
            f'Item "{item.title}" has been successfully uploaded!',
        )
        return redirect(reverse("inventory:item_list"))

class ItemListView(ListView):
    model = Item
    template_name = "inventory/item_list.html"
    context_object_name = "items"
    paginate_by = 20

    def get_queryset(self):
        queryset = Item.objects.filter(status=Item.Status.FOUND)

        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | Q(description__icontains=q)
            )

        location = self.request.GET.get("location")
        if location:
            queryset = queryset.filter(location_found__icontains=location)

        date_from = parse_date(self.request.GET.get("date_from") or "")
        if date_from:
            queryset = queryset.filter(date_found__gte=date_from)

        date_to = parse_date(self.request.GET.get("date_to") or "")
        if date_to:
            queryset = queryset.filter(date_found__lte=date_to)

        return queryset


class ItemDetailView(DetailView):
    model = Item
    template_name = "inventory/item_detail.html"
    context_object_name = "item"

