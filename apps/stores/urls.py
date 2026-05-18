from django.urls import path

from apps.stores import views

urlpatterns = [
    path("stores", views.StoreListView.as_view()),
    path("stores/nearby", views.NearbyStoresView.as_view()),
    path("stores/<uuid:store_id>", views.StoreDetailView.as_view()),
    path("vendor/store/open", views.StoreOpenToggleView.as_view()),
]
